"""Rerun the final searches from Check-in 2 working doc.md.

Default: print the search plan without network access. --execute calls APIs.
Results are raw provider JSON (PubMed also has XML), not screening-ready CSVs.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from itertools import product
from pathlib import Path

import requests

# Allow query previews from a fresh checkout before private config is created.
try:
    import config
except ModuleNotFoundError as exc:
    if exc.name != "config":
        raise
    config = None


# Three final search concepts, transcribed from the working document.
CONCEPTS = (
    (
        ('"Q-matri*"', '"Q matri*"'),
        ('"cognitive diagnos*"', '"diagnostic classification*"',
         '"diagnostic assessment*"', 'DINA', 'attribute*', 'skill*',
         '"knowledge component*"', 'assessment*'),
    ),
    (
        ('"knowledge component*"', '"skill model*"', '"cognitive model discover*"',
         '"knowledge concept tagging"', '"skill tagging"', '"knowledge tagging"',
         '"item-skill"'),
        ('discover*', 'refin*', 'generat*', 'tagging', '"data driven"',
         '"learning factors analysis"', 'automat*', 'extract*', 'attribution'),
    ),
    (
        ('"cognitive diagnostic model*"', '"cognitive diagnosis model*"',
         '"diagnostic classification model*"', '"DINA model*"', '"G-DINA"',
         '"cognitive diagnostic assessment*"'),
        ('clinical', 'psychiatr*', 'psychopatholog*', '"mental health"',
         'symptom*', 'DSM', 'personality', 'disorder*', 'depress*', 'anxiety',
         '"non-cognitive"', 'noncognitive', '"socio-emotional"', '"social-emotional"'),
    ),
)


@dataclass(frozen=True)
class SearchPlan:
    database: str
    queries: tuple[str, ...]
    notes: str = ""


def any_of(terms: tuple[str, ...]) -> str:
    return "(" + " OR ".join(terms) + ")"


def concept_queries() -> tuple[str, ...]:
    return tuple(f"({any_of(left)} AND {any_of(right)})" for left, right in CONCEPTS)


def wildcard_groups(terms: tuple[str, ...]) -> list[tuple[str, ...]]:
    # Distribute OR blocks so each group has at most one wildcard word.
    literal = tuple(term for term in terms if "*" not in term)
    return ([literal] if literal else []) + [(term,) for term in terms if "*" in term]


def build_plans() -> tuple[SearchPlan, ...]:
    concepts = concept_queries()
    scopus = any_of(tuple(f"TITLE-ABS-KEY{q}" for q in concepts))
    wos = any_of(tuple(f"TS={q}" for q in concepts))
    ebsco = any_of(tuple(f"(TI {q} OR AB {q} OR KW {q})" for q in concepts))
    pubmed = any_of(tuple(
        f"({any_of(tuple(t + '[tiab]' for t in left))} AND "
        f"{any_of(tuple(t + '[tiab]' for t in right))})"
        for left, right in CONCEPTS
    ))
    # The IEEE API permits two wildcard words, fewer than the web interface.
    ieee = tuple(
        f"({any_of(left)} AND {any_of(right)})"
        for left_terms, right_terms in CONCEPTS
        for left, right in product(wildcard_groups(left_terms), wildcard_groups(right_terms))
    )
    # ACM ignores phrase wildcards; expand the quoted terms for manual searches.
    expansions = {
        '"Q-matri*"': '("Q-matrix" OR "Q-matrices")',
        '"Q matri*"': '("Q matrix" OR "Q matrices")',
        '"cognitive diagnos*"': '("cognitive diagnosis" OR "cognitive diagnostic")',
        '"cognitive model discover*"': '"cognitive model discovery"',
    }
    acm = []
    for query in concepts:
        for term in (t for pair in CONCEPTS for block in pair for t in block):
            if term.startswith('"') and "*" in term:
                # The doc says ACM automatically matches plurals and stems.
                query = query.replace(term, expansions.get(term, term.replace("*", "")))
        acm.append(query)
    return (
        SearchPlan("Scopus", (scopus + " AND PUBYEAR > 2020 AND PUBYEAR < 2028 AND LANGUAGE(english)",)),
        SearchPlan("Web of Science", (wos + " AND PY=(2021-2027) AND LA=(English)",),
                   "Requires the Expanded API; Starter does not support TS searches."),
        SearchPlan("APA PsycInfo", (ebsco + " AND LA English",),
                   "EBSCO EDS profile must expose TI, AB, KW, LA and DT1; set the exact ContentProvider facet."),
        SearchPlan("ERIC", (ebsco + " AND LA English",),
                   "Uses EBSCO EDS to follow the working doc; configure the ERIC ContentProvider facet."),
        SearchPlan("PubMed", (pubmed + ' AND 2021:2027[dp] AND english[lang]',)),
        SearchPlan("IEEE Xplore", ieee,
                   "API splits preserve the three concepts; English eligibility requires later screening."),
        SearchPlan("ACM DL", tuple(acm),
                   "Manual only: no verified search API. Select metadata fields, 2021-2027, English and Full-Text Collection in the UI."),
    )


def required(name: str) -> str:
    value = getattr(config, name, "").strip()
    if not value:
        raise ValueError(f"Set {name} in config.py (copy config.py.template) before executing this database")
    return value


class Client:
    def __init__(self, directory: Path):
        self.directory = directory
        self.session = requests.Session()
        self.counter = 0

    def get(self, url: str, params: dict, headers: dict | None = None, xml: bool = False):
        # Pace requests and retry transient failures; never print credential URLs.
        for attempt in range(4):
            time.sleep(0.4 * (2 ** attempt))
            response = self.session.get(url, params=params, headers=headers, timeout=60)
            if response.status_code != 429 and response.status_code < 500:
                break
        if not response.ok:
            raise RuntimeError(f"Provider returned HTTP {response.status_code}")
        self.counter += 1
        if xml:
            (self.directory / f"response_{self.counter:04d}.xml").write_text(response.text, encoding="utf-8")
            return response.text
        payload = response.json()
        (self.directory / f"response_{self.counter:04d}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return payload


def search_page(client: Client, database: str, query: str, offset: int) -> tuple[list[dict], int]:
    # Provider-specific authentication, paging and response shapes.
    if database == "Scopus":
        headers = {"X-ELS-APIKey": required("SCOPUS_API_KEY"), "Accept": "application/json"}
        if getattr(config, "SCOPUS_INST_TOKEN", ""):
            headers["X-ELS-Insttoken"] = config.SCOPUS_INST_TOKEN
        data = client.get("https://api.elsevier.com/content/search/scopus",
                          {"query": query, "start": offset, "count": 25}, headers)["search-results"]
        total = int(data["opensearch:totalResults"])
        return (data.get("entry", []) if total else []), total
    if database == "Web of Science":
        data = client.get("https://api.clarivate.com/api/wos",
                          {"databaseId": "WOS", "usrQuery": query, "count": 100, "firstRecord": offset + 1},
                          {"X-ApiKey": required("WOS_API_KEY"), "Accept": "application/json"})
        rows = data.get("Data", {}).get("Records", {}).get("records", {}).get("REC", [])
        return ([rows] if isinstance(rows, dict) else rows), int(data["QueryResult"]["RecordsFound"])
    if database in ("APA PsycInfo", "ERIC"):
        prefix = "PSYCINFO" if database == "APA PsycInfo" else "ERIC"
        # Use current EDS tokens from the institution's authenticated session.
        provider = required(f"EBSCO_{prefix}_PROVIDER")
        data = client.get("https://eds-api.ebscohost.com/edsapi/rest/search", {
            "query": query, "searchmode": "bool", "view": "detailed", "highlight": "n",
            "resultsperpage": 100, "pagenumber": offset // 100 + 1,
            "limiter": "DT1:2021-01/2027-12", "facetfilter": f"1,ContentProvider:{provider}",
        }, {"x-authenticationToken": required("EBSCO_AUTH_TOKEN"),
            "x-sessionToken": required("EBSCO_SESSION_TOKEN"), "Accept": "application/json"})["SearchResult"]
        return data.get("Data", {}).get("Records", []), int(data["Statistics"]["TotalHits"])
    if database == "IEEE Xplore":
        data = client.get("https://ieeexploreapi.ieee.org/api/v1/search/articles", {
            "apikey": required("IEEE_API_KEY"), "querytext": query,
            "start_year": 2021, "end_year": 2027, "start_record": offset + 1,
            "max_records": 200, "format": "json", "sort_field": "article_number", "sort_order": "asc",
        })
        return data.get("articles", []), int(data["total_records"])
    raise ValueError(f"No API adapter for {database}")


def run_search(plan: SearchPlan, client: Client) -> list[dict]:
    # PubMed search returns IDs; fetch complete metadata in XML batches.
    if plan.database == "PubMed":
        common = {"db": "pubmed", "tool": "qmatrix_search", "email": required("NCBI_EMAIL")}
        if getattr(config, "NCBI_API_KEY", ""):
            common["api_key"] = config.NCBI_API_KEY
        data = client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                          {**common, "term": plan.queries[0], "retmode": "json", "retmax": 10000})["esearchresult"]
        ids = data["idlist"]
        if len(ids) != int(data["count"]):
            raise RuntimeError("PubMed results exceed the 10,000-ID limit or are incomplete; partition the date range")
        for start in range(0, len(ids), 200):
            client.get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                       {**common, "id": ",".join(ids[start:start + 200]), "retmode": "xml"}, xml=True)
        return [{"pmid": pmid} for pmid in ids]

    # Retrieve every page of every query; merge overlapping concept results.
    unique = {}
    for query in plan.queries:
        offset = 0
        while True:
            rows, total = search_page(client, plan.database, query, offset)
            for row in rows:
                header = row.get("Header", {})
                identifier = (row.get("dc:identifier") or row.get("UID") or row.get("article_number")
                              or ((header.get("DbId"), header["An"]) if header.get("An") else None))
                if identifier is None:
                    raise RuntimeError("Response record has no provider ID for deduplication")
                unique[str(identifier)] = row
            offset += len(rows)
            if offset >= total:
                break
            if not rows:
                raise RuntimeError("Provider returned an empty page before all results were retrieved")
    return list(unique.values())


def main() -> None:
    # Preview by default; network access requires the explicit --execute flag.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--database", action="append", choices=[p.database for p in build_plans()])
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()
    plans = [p for p in build_plans() if not args.database or p.database in args.database]
    if not args.execute:
        print(json.dumps([asdict(p) for p in plans], indent=2))
        return

    # Save the plan, raw responses and a status report; keep failures explicit.
    directory = args.output / datetime.now().strftime("%Y%m%d_%H%S")
    directory.mkdir(parents=True, exist_ok=False)
    (directory / "queries.json").write_text(json.dumps([asdict(p) for p in plans], indent=2), encoding="utf-8")
    summary = []
    for plan in plans:
        destination = directory / plan.database
        destination.mkdir()
        status, count, error = "complete", 0, ""
        if plan.database == "ACM DL":
            status = "manual_required"
        else:
            client = Client(destination)
            try:
                rows = run_search(plan, client)
                count = len(rows)
                (destination / "records.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
            except (ValueError, KeyError, TypeError, RuntimeError, requests.RequestException) as exc:
                status = "failed"
                # requests errors can contain API keys in URLs; report type only.
                error = type(exc).__name__ if isinstance(exc, requests.RequestException) else str(exc)
            finally:
                client.session.close()
        summary.append({"database": plan.database, "status": status, "records": count, "error": error, "notes": plan.notes})
        print(f"{plan.database}: {status}, {count} records" + (f" ({error})" if error else ""))
    import pandas as pd

    pd.DataFrame(summary).to_csv(directory / "summary.csv", index=False)
    print(f"Saved search run to {directory}")
    if any(row["status"] == "failed" for row in summary):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
