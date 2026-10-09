"""Generate browser links and copyable queries without making API requests."""

from __future__ import annotations

import argparse
from collections import defaultdict
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
                url = "https://ieeexplore.ieee.org/"
                searches.append(ManualSearch(plan.database, label, query, url,
                    "Open Advanced/Command Search and run each query separately in All Metadata. "
                    "Apply 2021–2027 and check English eligibility during screening."))
            continue
        for index, query in enumerate(plan.queries, start=1):
            label = f"Concept {index}" if plan.database == "ACM DL" else f"Search query {index}"
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


EXPORT_STEPS = {
    "Scopus": "Select all results (or successive batches), choose Export → RIS, and include all available citation, bibliographic, abstract and keyword fields. Download each batch. [Scopus export help](https://www.elsevier.support/scopus/answer/how-do-i-export-documents-from-scopus).",
    "Web of Science": "Select all results or a record range, choose Export → RIS, and select Full Record and Cited References where offered. Include abstracts and download successive ranges until every result is exported. [Export help](https://webofscience.zendesk.com/hc/en-us/articles/20135824927505-Saving-and-Exporting-Marked-Lists).",
    "APA PsycInfo": "Select the results, use Share/Export (or add them to the folder and open its Export manager), choose RIS, and include abstracts and all available fields. Download every batch; some interfaces deliver the bulk export by email. Menu names depend on your institution's interface.",
    "ERIC": "Select the results, use Share/Export (or add them to the folder and open its Export manager), choose RIS, and include abstracts and all available fields. Download every batch; some interfaces deliver the bulk export by email. Menu names depend on your institution's interface.",
    "PubMed": "Choose Save → All results → PubMed format → Create file to download NBIB/tagged PubMed records, including available abstracts. If the export limit is reached, split into nonoverlapping date ranges and save every batch. [PubMed save help](https://pubmed.ncbi.nlm.nih.gov/help/#saving-citations-as-a-text-file).",
    "IEEE Xplore": "For each query, select the results, choose Export/Download Citations → RIS, and include abstracts where offered. Export all result pages or batches. Inspect the file for abstracts; download an additional full-metadata export if the citation export omits them. [Rayyan database import guidance](https://help.rayyan.ai/hc/en-us/articles/45589301098769-How-to-Import-References-from-Major-Databases).",
    "ACM DL": "For each query, select the results and choose Export Citation → EndNote, then download every batch as .enw. Inspect the downloaded records for abstracts (%X), keywords (%K), DOI (%R), and bibliographic details. Keep any richer supplementary export alongside it if these fields are omitted. [ACM guide](https://libraries.acm.org/binaries/content/assets/libraries/acm-digital-library-user-guide.pdf).",
}


def render(searches: list[ManualSearch]) -> str:
    groups: dict[str, list[ManualSearch]] = defaultdict(list)
    for search in searches:
        groups[search.database].append(search)
    lines = ["# Manual database searches", "",
             "Queries follow the working document's concepts and **2021–2027** retrieval filter. "
             "Sign in through your institution as needed. Apply the first-online-date cutoff and other eligibility criteria during screening. "
             "These searches have not been run or browser-validated.", "",
             "Use full-record **RIS** exports where available, native **NBIB** for PubMed, and **EndNote (.enw)** for ACM. "
             "Keep all exported fields and the original files; there is no need to reshape them into the old CSV. "
             "Rayyan accepts these formats, but its import may normalize fields or replace source accession IDs. "
             "[Supported formats](https://help.rayyan.ai/hc/en-us/articles/4406426903825-Supported-File-Formats-for-Importing-into-Rayyan).", ""]
    for database, entries in groups.items():
        instructions = entries[0].instructions.replace("this concept query", "each query separately")
        lines.extend([f"## {database}", "", "**Instructions**", "",
                      f"1. {instructions}",
                      "2. Record the search date, exact query, filters, and displayed count for each query before exporting.",
                      f"3. {EXPORT_STEPS[database]}",
                      f"4. Save original downloads in `input/exports/{database}/`, with query and batch numbers in filenames. "
                      "Check that exported counts match the displayed counts; overlapping queries can contain duplicates. "
                      "Then follow the [export preparation and Rayyan import workflow](rayyan_exports.md).", "",
                      f"[Open search](<{entries[0].url}>)", ""])
        for index, entry in enumerate(entries, 1):
            lines.extend([f"**Search query {index}**", "", "```text", entry.query, "```", ""])
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
