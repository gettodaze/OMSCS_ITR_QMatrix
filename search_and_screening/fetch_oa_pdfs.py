"""Download open-access full texts for the records kept at Step 3.

Two subcommands, run from the project root:

    plan      look up every retained record's DOI in OpenAlex and write the download plan
              (fulltext/OA download plan.xlsx): which records have an open-access PDF link,
              from where, and how large the file is said to be. Downloads nothing.
    download  fetch the PDFs listed in the plan into fulltext/, named by record ID
              (F0123.pdf), and record each outcome in the plan's Result column.

Only links OpenAlex marks as open access are used; nothing goes through the GT Library proxy.
A file is kept only if it is a real PDF (it starts with %PDF), so publisher landing pages
served in place of a PDF are rejected, not saved.

    .venv/Scripts/python.exe "Group Project/Screening/fetch_oa_pdfs.py" plan
"""

import argparse
import http.client
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import openpyxl
from openpyxl.styles import Font, PatternFill

from prescreen_metadata import HERE, normalize_doi, read_records

RETAINED = HERE / "Step 3 - E1-E5 LLM title-abstract - retained.xlsx"
FULLTEXT = HERE / "fulltext"
PLAN = FULLTEXT / "OA download plan.xlsx"

USER_AGENT = "CS8803-QMatrix-SLR-fulltext/1.0 (python-urllib)"
PAUSE_SECONDS = 1.0   # between downloads, to stay polite to repositories and publishers
# Network failures of any kind: URLError and dropped connections are OSErrors; a malformed
# response is an HTTPException.
NETWORK_ERRORS = (OSError, http.client.HTTPException)
PLAN_COLUMNS = ["ID", "File", "DOI", "Title", "Host", "PDF URL", "Other PDF URLs",
                "Size (MB, reported)", "Result"]


def openalex_works(dois):
    """Return {doi: work} for the DOIs OpenAlex knows, 50 per request."""
    found = {}
    for i in range(0, len(dois), 50):
        batch = dois[i:i + 50]
        url = ("https://api.openalex.org/works?per-page=50"
               "&select=doi,open_access,best_oa_location,locations&filter=doi:"
               + "|".join(urllib.parse.quote(d, safe="/") for d in batch))
        with urllib.request.urlopen(urllib.request.Request(
                url, headers={"User-Agent": USER_AGENT}), timeout=60) as response:
            for work in json.load(response)["results"]:
                found[normalize_doi(work.get("doi"))] = work
    return found


def pdf_urls(work):
    """Open-access PDF links, best location first, without duplicates."""
    urls = []
    oa_locations = [loc for loc in work.get("locations") or [] if (loc or {}).get("is_oa")]
    for loc in [work.get("best_oa_location") or {}] + oa_locations:
        url = (loc or {}).get("pdf_url")
        if url and url not in urls:
            urls.append(url)
    return urls


def reported_size(url):
    """Content-Length from a HEAD request, in MB, or None when the server doesn't say."""
    try:
        request = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=20) as response:
            length = response.headers.get("Content-Length")
            return round(int(length) / 1e6, 2) if length else None
    except (*NETWORK_ERRORS, ValueError):
        return None


def plan():
    _, rows, _ = read_records(RETAINED)
    dois = sorted({d for d in (normalize_doi(r.get("DOI")) for r in rows) if d})
    works = openalex_works(dois)
    entries = []
    for r in rows:
        work = works.get(normalize_doi(r.get("DOI")))
        urls = pdf_urls(work) if work and work["open_access"]["is_oa"] else []
        if not urls:
            continue
        entries.append({
            "ID": r["ID"], "File": f"{r['ID']}.pdf", "DOI": r.get("DOI"), "Title": r.get("Title"),
            "Host": urlparse(urls[0]).netloc, "PDF URL": urls[0],
            "Other PDF URLs": " ".join(urls[1:]) or None,
            "Size (MB, reported)": reported_size(urls[0]), "Result": None,
        })
    entries.sort(key=lambda e: e["ID"])
    FULLTEXT.mkdir(exist_ok=True)
    write_plan(entries, len(rows), len(dois), len(works))
    sizes = [e["Size (MB, reported)"] for e in entries if e["Size (MB, reported)"]]
    print(f"{len(rows)} retained; {len(dois)} with a DOI; {len(works)} in OpenAlex; "
          f"{len(entries)} with an open-access PDF link -> {PLAN.name}")
    print(f"Reported sizes for {len(sizes)} files: {sum(sizes):.0f} MB "
          f"(the other {len(entries) - len(sizes)} don't report a size)")


def write_plan(entries, n_rows, n_dois, n_found):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Plan"
    ws.append(PLAN_COLUMNS)
    for e in entries:
        ws.append([e[c] for c in PLAN_COLUMNS])
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="DDE6F0")
    for col, width in zip("ABCDEFGHI", [7, 11, 30, 60, 28, 60, 30, 10, 30]):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    about = wb.create_sheet("About")
    for line in [
        f"Open-access PDFs for the records retained at Step 3 ({RETAINED.name}).",
        f"{n_rows} retained records, {n_dois} with a DOI, {n_found} found in OpenAlex, "
        f"{len(entries)} with an open-access PDF link.",
        "Links come from OpenAlex's best_oa_location and its open-access locations; no library "
        "proxy is used.",
        f"Built by {Path(__file__).name}. 'download' fills the Result column.",
    ]:
        about.append([line])
    about.column_dimensions["A"].width = 110
    wb.save(PLAN)


def fetch(url):
    """Return the body if it is a PDF, else raise ValueError with the reason."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "application/pdf,*/*"})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read()
    if not body.startswith(b"%PDF"):
        raise ValueError(f"not a PDF ({response.headers.get('Content-Type')})")
    return body


def download():
    if not PLAN.exists():
        sys.exit("No plan yet: run 'plan' first.")
    wb = openpyxl.load_workbook(PLAN)
    ws = wb["Plan"]
    header = [c.value for c in ws[1]]
    col = {name: header.index(name) for name in PLAN_COLUMNS}
    counts = {"saved": 0, "already there": 0, "failed": 0}
    for row in ws.iter_rows(min_row=2):
        target = FULLTEXT / row[col["File"]].value
        if target.exists():
            row[col["Result"]].value = "already there"
            counts["already there"] += 1
            continue
        urls = [row[col["PDF URL"]].value] + (row[col["Other PDF URLs"]].value or "").split()
        errors = []
        for url in urls:
            try:
                body = fetch(url)
            except (*NETWORK_ERRORS, ValueError) as e:
                errors.append(f"{urlparse(url).netloc}: {e}")
                continue
            target.write_bytes(body)
            row[col["Result"]].value = f"saved {len(body) / 1e6:.1f} MB from {urlparse(url).netloc}"
            counts["saved"] += 1
            break
        else:
            row[col["Result"]].value = "failed: " + "; ".join(errors)
            counts["failed"] += 1
        time.sleep(PAUSE_SECONDS)
    wb.save(PLAN)
    print(", ".join(f"{k} {v}" for k, v in counts.items()), f"-> {FULLTEXT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["plan", "download"])
    {"plan": plan, "download": download}[parser.parse_args().command]()
