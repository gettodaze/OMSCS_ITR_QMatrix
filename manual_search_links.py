"""Generate browser links and copyable queries without making API requests."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode, urlsplit

from search_databases import CONCEPTS, any_of, build_plans


@dataclass(frozen=True)
class ManualSearch:
    database: str
    label: str
    query: str
    url: str
    instructions: str


def ieee_queries() -> list[tuple[str, str]]:
    # The working doc gives the web interface a ten-wildcard limit.
    searches = []
    for index, (left, right) in enumerate(CONCEPTS, start=1):
        budget = 10 - sum(term.count("*") for term in left)
        groups: list[list[str]] = [[]]
        wildcards = 0
        for term in right:
            count = term.count("*")
            if wildcards + count > budget:
                groups.append([])
                wildcards = 0
            groups[-1].append(term)
            wildcards += count
        for part, group in enumerate(groups, start=1):
            label = f"Concept {index}" + (f", part {part}" if len(groups) > 1 else "")
            searches.append((label, f"({any_of(left)} AND {any_of(tuple(group))})"))
    return searches


def build_searches(psycinfo_url: str, eric_url: str) -> list[ManualSearch]:
    # Reuse the API runner's documented concepts, dates and language terms.
    searches = []
    for plan in build_plans():
        if plan.database == "IEEE Xplore":
            for label, query in ieee_queries():
                url = "https://ieeexplore.ieee.org/search/searchresult.jsp?" + urlencode(
                    {"newsearch": "true", "queryText": query}
                )
                searches.append(ManualSearch(plan.database, label, query, url,
                    "Prefilled URL pattern; not browser-verified. Confirm All Metadata search, "
                    "apply 2021–2027, and check English eligibility. If the link loses the query, paste it below."))
            continue
        for index, query in enumerate(plan.queries, start=1):
            label = f"Concept {index}" if plan.database == "ACM DL" else "Final search"
            if plan.database == "PubMed":
                url = "https://pubmed.ncbi.nlm.nih.gov/?" + urlencode({"term": query})
                instructions = "Prefilled search. The query includes 2021–2027 and English; inspect Search Details for its translation."
            elif plan.database == "Scopus":
                url = "https://www.scopus.com/search/form.uri?display=advanced"
                instructions = "Open Advanced document search and paste the query. Dates and English are included."
            elif plan.database == "Web of Science":
                url = "https://www.webofscience.com/wos/woscc/advanced-search"
                instructions = "Select Core Collection, open Advanced Search/Query Builder and paste the query. Dates and English are included."
            elif plan.database in ("APA PsycInfo", "ERIC"):
                url = psycinfo_url if plan.database == "APA PsycInfo" else eric_url
                instructions = f"Use your library's EBSCO link, select {plan.database}, and paste the query in Advanced Search. " \
                    "Apply 2021–2027 manually. Confirm TI/AB/KW/LA field support in your interface; the query includes English."
            else:
                url = "https://dl.acm.org/search/advanced"
                instructions = "Open Advanced Search and paste this concept query. Select metadata fields and the Full-Text Collection, " \
                    "then apply 2021–2027 and English. Repeat for all three concepts."
            searches.append(ManualSearch(plan.database, label, query, url, instructions))
    return searches


def render(searches: list[ManualSearch]) -> str:
    # Markdown keeps both the browser link and exact query available for sharing.
    lines = ["# Manual database searches", "",
             "Generated from the working document's final concepts. No API keys or API calls are needed.", "",
             "Sign in through your institution as needed. PubMed links embed the query; IEEE links use an unverified "
             "browser URL pattern. Other links open a search interface where you paste the query. "
             "The searches themselves have not been run or browser-validated.", "",
             "Dates follow the documented retrieval filter, **2021–2027**. "
             "Apply the review's first-online-date cutoff and other eligibility criteria during screening.", "",
             "For each search, record the date, displayed query/filters and result count, then export citation metadata "
             "including abstracts and identifiers where available. Merge overlapping concept searches and deduplicate "
             "across databases. Results can differ from the original October 8, 2026 search.", "",
             "PubMed URL format: [official help](https://pubmed.ncbi.nlm.nih.gov/help/#creating-a-web-link-to-pubmed).", ""]
    for search in searches:
        lines.extend([f"## {search.database} — {search.label}", "",
                      f"[Open search](<{search.url}>)", "", search.instructions, "",
                      "```text", search.query, "```", ""])
    return "\n".join(lines)


def browser_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise argparse.ArgumentTypeError("Use a full http(s) library URL")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs_agent/manual_search_links.md"))
    parser.add_argument("--psycinfo-url", type=browser_url, default="https://search.ebscohost.com/")
    parser.add_argument("--eric-url", type=browser_url, default="https://search.ebscohost.com/")
    args = parser.parse_args()
    searches = build_searches(args.psycinfo_url, args.eric_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(searches), encoding="utf-8")
    print(f"Wrote {len(searches)} manual search entries to {args.output}")


if __name__ == "__main__":
    main()
