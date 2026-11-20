"""Metadata pre-screen: steps 1 and 2 of the screening methodology.

Step 1 (E6) excludes ineligible publication types using the database document-type labels.
Step 2 (E7) excludes records first published before 1 January 2021, using Crossref dates.

Each step reads the previous step's retained file and writes two workbooks: the records it
excluded and the records it kept. The candidate file itself is never modified. See
"Screening Methodology.md" for the rules and the reasons for them.

Usage (from the project root):
    .venv/Scripts/python.exe "Group Project/Screening/prescreen_metadata.py"
    .venv/Scripts/python.exe "Group Project/Screening/prescreen_metadata.py" --offline

--offline uses only the cached Crossref dates (crossref_dates.json) and fails if any are missing.
"""

import argparse
import concurrent.futures
import copy
import datetime
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "Candidate Records - Final Search-screening copy.xlsx"
CROSSREF_CACHE = HERE / "crossref_dates.json"
TEST_SET = HERE / "test_set_dois.txt"

STEP1_EXCLUDED = HERE / "Step 1 - E6 publication type - excluded.xlsx"
STEP1_RETAINED = HERE / "Step 1 - E6 publication type - retained.xlsx"
STEP2_EXCLUDED = HERE / "Step 2 - E7 date - excluded.xlsx"
STEP2_RETAINED = HERE / "Step 2 - E7 date - retained.xlsx"

DATE_COLUMN = "First published (Crossref)"
EARLIEST_ELIGIBLE_YEAR = 2021

# ---------------------------------------------------------------------------------------------
# Reading and writing workbooks
# ---------------------------------------------------------------------------------------------


def read_records(path):
    """Return (header, rows, template) for the Records sheet. Rows are dicts keyed by header."""
    wb = openpyxl.load_workbook(path)
    ws = wb["Records"]
    header = [c.value for c in ws[1]]
    rows = []
    for values in ws.iter_rows(min_row=2, values_only=True):
        if values[0] is None:
            continue
        rows.append(dict(zip(header, values)))
    return header, rows, ws


def write_records(path, header, rows, template, about_lines):
    """Write rows to a new workbook, copying the source sheet's layout, plus an About sheet."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Records"
    ws.append(header)
    for row in rows:
        ws.append([row.get(h) for h in header])

    # Header style, column widths and per-column alignment come from the source sheet. Columns
    # the source lacks (e.g., the Crossref date) get the style of the last source column.
    src_cols = template.max_column
    for i in range(1, len(header) + 1):
        src = min(i, src_cols)
        letter = get_column_letter(i)
        src_letter = get_column_letter(src)
        head, src_head = ws.cell(1, i), template.cell(1, src)
        head.font, head.fill = copy.copy(src_head.font), copy.copy(src_head.fill)
        head.alignment, head.border = copy.copy(src_head.alignment), copy.copy(src_head.border)
        width = template.column_dimensions[src_letter].width
        ws.column_dimensions[letter].width = width if i <= src_cols else 30
        body_alignment = template.cell(2, src).alignment
        for r in range(2, len(rows) + 2):
            ws.cell(r, i).alignment = copy.copy(body_alignment)
    ws.freeze_panes = template.freeze_panes
    ws.auto_filter.ref = f"A1:{get_column_letter(len(header))}{len(rows) + 1}"

    about = wb.create_sheet("About")
    for line in about_lines:
        about.append([line])
    about.column_dimensions["A"].width = 120
    wb.save(path)


def about_sheet(step, rule, input_path, n_in, n_excluded, n_retained, extra=()):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return [
        f"{step}",
        f"Rule: {rule}",
        f"Input: {input_path.name} ({n_in} records)",
        f"Excluded: {n_excluded}    Retained: {n_retained}",
        *extra,
        f"Built {stamp} by {Path(__file__).name}. See Screening Methodology.md.",
    ]


def mark_excluded(row, code, stage, evidence):
    row = dict(row)
    row["Decision"] = "Exclude"
    row["Exclusion reason"] = code
    row["Excluded at stage"] = stage
    row["Notes"] = evidence if not row.get("Notes") else f"{row['Notes']}; {evidence}"
    return row


def check_counts(n_in, excluded, retained):
    if len(excluded) + len(retained) != n_in:
        sys.exit(f"Record count mismatch: {n_in} in, {len(excluded)} + {len(retained)} out")


def check_test_set(excluded, step):
    """Stop if any known-relevant study was excluded: that means a rule is wrong."""
    if not TEST_SET.exists():
        return
    known = {
        line.strip().lower()
        for line in TEST_SET.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    hit = [r["ID"] for r in excluded if normalize_doi(r.get("DOI")) in known]
    if hit:
        sys.exit(f"{step} excluded test-set studies {hit}. Fix the rule before using the output.")


def normalize_doi(doi):
    if not doi:
        return None
    doi = str(doi).strip().lower()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:\s*)", "", doi)
    return doi or None


# ---------------------------------------------------------------------------------------------
# Step 1: E6, ineligible publication type
# ---------------------------------------------------------------------------------------------

# Matched against the document-type labels, which combine every database's label for the record
# ("Article | Journal Article | Dissertation"). First match wins. Each entry is
# (labels, description written to Notes).
E6_LABEL_RULES = [
    ({"retracted", "retracted publication"}, "retracted publication"),
    ({"erratum", "correction", "erratum/correction"}, "erratum or correction"),
    ({"conference review"}, "proceedings front matter (Scopus 'Conference review')"),
    ({"dissertation", "dissertations/theses - doctoral dissertations"}, "dissertation or thesis"),
    ({"preprint"}, "preprint"),
]
# Some dissertations are merged with a journal-article label from another database; their venue
# still identifies them.
E6_VENUE_RULES = [
    (r"^dissertation abstracts international", "dissertation or thesis"),
    (r"rxiv\b", "preprint"),
]


def e6_reason(row):
    raw = str(row.get("Document type") or "")
    labels = {p.strip().lower() for p in re.split(r"[|;]", raw) if p.strip()}
    for wanted, description in E6_LABEL_RULES:
        if labels & wanted:
            return f"E6: {description}. Document type: {raw}"
    venue = str(row.get("Venue") or "").strip().lower()
    for pattern, description in E6_VENUE_RULES:
        if re.search(pattern, venue):
            return f"E6: {description}. Venue: {row.get('Venue')}"
    return None


def step1():
    header, rows, template = read_records(SOURCE)
    excluded, retained = [], []
    for row in rows:
        reason = e6_reason(row)
        if reason:
            excluded.append(mark_excluded(row, "E6", "Step 1: publication type", reason))
        else:
            retained.append(row)
    check_counts(len(rows), excluded, retained)
    check_test_set(excluded, "Step 1")

    rule = (
        "exclude retracted publications, errata and corrections, proceedings front matter, "
        "dissertations and theses, and preprints, identified from document-type labels and venue."
    )
    about = about_sheet(
        "Step 1 - E6 publication type", rule, SOURCE, len(rows), len(excluded), len(retained)
    )
    write_records(STEP1_EXCLUDED, header, excluded, template, about)
    write_records(STEP1_RETAINED, header, retained, template, about)
    print(f"Step 1 (E6): {len(rows)} in, {len(excluded)} excluded, {len(retained)} retained")
    for _, description in E6_LABEL_RULES:
        n = sum(description in r["Notes"] for r in excluded)
        print(f"    {n:4d}  {description}")


# ---------------------------------------------------------------------------------------------
# Step 2: E7, first published before 2021
# ---------------------------------------------------------------------------------------------

USER_AGENT = "CS8803-QMatrix-SLR-screening/1.0 (python-urllib)"


def crossref_lookup(doi):
    """Return {'online': [y,m,d], 'print': [...], 'issued': [...]} or {'status': 'not found'}."""
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                message = json.load(response)["message"]
            result = {"status": "ok"}
            for key, field in (
                ("online", "published-online"),
                ("print", "published-print"),
                ("issued", "issued"),
                ("created", "created"),
            ):
                parts = (message.get(field) or {}).get("date-parts") or [[None]]
                if parts[0] and parts[0][0]:
                    result[key] = parts[0]
            return result
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return {"status": "not found"}
            if e.code not in (429, 500, 502, 503, 504):
                return {"status": f"HTTP {e.code}"}
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(2 ** attempt)
    return {"status": "lookup failed"}


def crossref_dates(dois, offline):
    cache = json.loads(CROSSREF_CACHE.read_text(encoding="utf-8")) if CROSSREF_CACHE.exists() else {}
    # Retry earlier transient failures, and entries cached before the registration date was
    # recorded; a 404 is a settled answer.
    todo = [
        d for d in dois
        if d not in cache
        or cache[d]["status"] not in ("ok", "not found")
        or (cache[d]["status"] == "ok" and "created" not in cache[d])
    ]
    if todo and offline:
        sys.exit(f"--offline, but {len(todo)} DOIs have no cached Crossref date")
    if todo:
        print(f"Looking up {len(todo)} DOIs in Crossref...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            for doi, result in zip(todo, pool.map(crossref_lookup, todo)):
                cache[doi] = result
        CROSSREF_CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True), encoding="utf-8")
    return cache


def first_published(entry):
    """Earliest of the online, print and issued dates, as (date-parts, which field)."""
    dated = [(entry[k], k) for k in ("online", "print", "issued") if k in entry]
    if not dated:
        return None, None
    return min(dated, key=lambda d: d[0])


def fmt(parts):
    return "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(parts))


def as_date(parts):
    return datetime.date(parts[0], *(list(parts[1:3]) + [1, 1])[:2])


# A publisher can't put a DOI online long before registering it. A first-published date more
# than this far before the DOI's Crossref registration is a metadata error (seen for EAI
# journals, which deposit a 2018 date on DOIs that encode their 2022 publication date).
MAX_DAYS_BEFORE_REGISTRATION = 90


def e7_check(row, cache):
    """Return (exclusion evidence or None, value for the Crossref date column)."""
    year = int(row["Year"]) if str(row.get("Year") or "").isdigit() else None
    doi = normalize_doi(row.get("DOI"))
    entry = cache.get(doi) if doi else None

    if not doi:
        shown = "no DOI; not checked"
    elif entry["status"] != "ok":
        shown = f"DOI {entry['status']} in Crossref"
    else:
        parts, field = first_published(entry)
        shown = f"{fmt(parts)} ({field})" if parts else "Crossref has no date"
        if parts and parts[0] < 2000:
            # Implausible for a 2021-2026 search hit: a data error, not evidence.
            shown += "; implausible, ignored"
        elif parts and parts[0] < EARLIEST_ELIGIBLE_YEAR:
            # Conference "print" dates routinely precede registration by months, so the check is
            # applied only where the date would exclude the record.
            created = entry.get("created")
            if created and (as_date(created) - as_date(parts)).days > MAX_DAYS_BEFORE_REGISTRATION:
                shown += f"; before DOI registration {fmt(created)}, ignored"
            else:
                evidence = f"E7: first published {fmt(parts)} per Crossref {field} (issue year {year})"
                return evidence, shown

    # A publication is never online after its issue year, so an issue year before 2021 is enough
    # on its own.
    if year is not None and year < EARLIEST_ELIGIBLE_YEAR:
        return f"E7: issue year {year}", shown
    return None, shown


def step2(offline):
    header, rows, template = read_records(STEP1_RETAINED)
    dois = sorted({d for d in (normalize_doi(r.get("DOI")) for r in rows) if d})
    cache = crossref_dates(dois, offline)

    header = header + [DATE_COLUMN]
    excluded, retained = [], []
    for row in rows:
        evidence, shown = e7_check(row, cache)
        row = {**row, DATE_COLUMN: shown}
        if evidence:
            excluded.append(mark_excluded(row, "E7", "Step 2: date", evidence))
        else:
            retained.append(row)
    check_counts(len(rows), excluded, retained)
    check_test_set(excluded, "Step 2")

    no_doi = sum(1 for r in rows if not normalize_doi(r.get("DOI")))
    unresolved = sum(1 for d in dois if cache[d]["status"] != "ok")
    rule = (
        f"exclude records first published before 1 January {EARLIEST_ELIGIBLE_YEAR}: the earliest "
        "Crossref online, print or issued date, or an issue year before then."
    )
    about = about_sheet(
        "Step 2 - E7 date", rule, STEP1_RETAINED, len(rows), len(excluded), len(retained),
        extra=[
            f"Crossref dates found for {len(dois) - unresolved} of {len(dois)} DOIs; "
            f"{unresolved} DOIs not in Crossref and {no_doi} records without a DOI fall back "
            "on the issue year (column 'Year').",
            f"Crossref responses are cached in {CROSSREF_CACHE.name}.",
        ],
    )
    write_records(STEP2_EXCLUDED, header, excluded, template, about)
    write_records(STEP2_RETAINED, header, retained, template, about)
    print(f"Step 2 (E7): {len(rows)} in, {len(excluded)} excluded, {len(retained)} retained")
    print(f"    Crossref dates for {len(dois) - unresolved}/{len(dois)} DOIs; {no_doi} without DOI")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true", help="use cached Crossref dates only")
    args = parser.parse_args()
    step1()
    step2(args.offline)
