"""Gather the full texts for the records kept at Step 3 into fulltext/, named by record ID.

Reads a Zotero CSV export (File > Export Library or Export Collection, format CSV), matches its
items to the retained records by DOI (Zotero keeps some DOIs in the Extra field) or by title, and
copies each record's PDF to fulltext/F0123.pdf. A record with no Zotero PDF falls back to the
copy fetch_oa_pdfs.py saved in fulltext/oa_download/. Existing files in fulltext/ are left alone,
so re-run it after adding more PDFs to Zotero and only the new ones are copied.

Every copied PDF is checked: its first pages must contain most of the record's title (catching
a wrong file attached to an item), and a first page stamped "arXiv" is flagged as a preprint.

It also writes fulltext/Full-text status.xlsx: one row per retained record, with where its PDF
came from or, if it has none, the likely reason and what to do. The two columns people fill in,
'Not retrieved (reason)' and 'Retrieval notes', are carried over from the previous sheet on every
re-run; the reason is cleared once the record has a PDF (see Screening Methodology.md,
'Retrieving full texts').

    .venv/Scripts/python.exe "Group Project/Screening/collect_fulltext.py" "<path to export.csv>"

When retrieval is finished, --finalize writes the step's two files from the status sheet (no
export needed): 'Retrieval - retrieved.xlsx', the input to full-text screening, and 'Retrieval -
not retrieved.xlsx', the reports not retrieved. It refuses while any record is still 'missing'.

    .venv/Scripts/python.exe "Group Project/Screening/collect_fulltext.py" --finalize
"""

import argparse
import csv
import os
import re
import shutil
from collections import defaultdict

import openpyxl
import pymupdf
from openpyxl.styles import Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from prescreen_metadata import HERE, about_sheet, normalize_doi, read_records, write_records

RETAINED = HERE / "Step 3 - E1-E5 LLM title-abstract - retained.xlsx"
FULLTEXT = HERE / "fulltext"
SCRIPT_COPIES = FULLTEXT / "oa_download"
STATUS = FULLTEXT / "Full-text status.xlsx"
RETRIEVED = HERE / "Retrieval - retrieved.xlsx"
NOT_RETRIEVED_FILE = HERE / "Retrieval - not retrieved.xlsx"

# DOI prefix -> publisher, for the publishers that appear in the retained records.
PUBLISHERS = {
    "10.1016": "Elsevier", "10.1007": "Springer", "10.1186": "Springer (BMC)",
    "10.1002": "Wiley", "10.1111": "Wiley", "10.1177": "SAGE", "10.3102": "SAGE (AERA)",
    "10.1080": "Taylor & Francis", "10.1201": "Taylor & Francis (CRC)", "10.1109": "IEEE",
    "10.1145": "ACM", "10.3389": "Frontiers", "10.3390": "MDPI", "10.1037": "APA",
    "10.4018": "IGI Global", "10.1515": "De Gruyter", "10.3233": "IOS Press",
    "10.1093": "Oxford", "10.1017": "Cambridge", "10.1103": "APS", "10.1504": "Inderscience",
    "10.1108": "Emerald", "10.1371": "PLOS", "10.1609": "AAAI", "10.48550": "arXiv",
}
# Publishers whose sites block automated PDF downloads (bot checks), even with GT access.
BOT_CHECKED = {"Elsevier", "ACM", "SAGE", "SAGE (AERA)", "Taylor & Francis", "Wiley", "APA",
               "Emerald"}
# Publishers GT often doesn't license (book chapters, small presses).
OFTEN_UNLICENSED = {"IGI Global", "De Gruyter", "IOS Press", "Taylor & Francis (CRC)",
                    "Inderscience"}

REASON, NOTES = "Not retrieved (reason)", "Retrieval notes"
# The third value is for records removed during retrieval whose individual reason wasn't noted
# (the first retrieval round: 9 records, 1 of them a security warning, unidentified).
NOT_RETRIEVED = ["no GT access", "security warning", "no GT access or security warning"]
COLUMNS = ["ID", "Status", REASON, NOTES, "Source", "Check", "Next step", "Publisher", "DOI",
           "Title", "Year", "Document type", "Zotero items"]


def normalize_title(title):
    return re.sub(r"[^a-z0-9]", "", str(title or "").lower())[:50]


def words(text):
    return set(re.findall(r"[a-z]{4,}", str(text or "").lower()))


def publisher(doi):
    if not doi:
        return "no DOI"
    return PUBLISHERS.get(doi.split("/")[0], "other journal")


def next_step(record_publisher, in_zotero):
    if record_publisher == "no DOI":
        return "Find by title (library search or Google Scholar), then add to Zotero."
    if not in_zotero:
        return "Add from the article page with the Zotero Connector (DOI unknown to Crossref)."
    if record_publisher in BOT_CHECKED:
        return ("Publisher blocks automated downloads: open in browser (VPN on), download, and "
                "drag the PDF onto the Zotero item.")
    if record_publisher in OFTEN_UNLICENSED:
        return ("Try in browser with VPN and via the GT Library site; if both ask for payment and "
                "no free copy exists, mark 'no GT access'.")
    return ("Try in browser (often open access); if paywalled with no free copy, mark "
            "'no GT access'.")


# A PDF with almost no text is a viewer printout, cover page or stub, not the article (seen for
# an Emerald "pdfviewer" page saved in place of the paper). Such files are not copied.
MIN_WORDS = 200
NOT_THE_ARTICLE = "almost no text: not the article"


def check_pdf(path, title):
    """Return '' if the PDF looks right, else a short warning."""
    try:
        doc = pymupdf.open(path)
        text = " ".join(doc[i].get_text() for i in range(min(2, len(doc))))
        pages = len(doc)
        n_words = sum(len(page.get_text().split()) for page in doc)
    except Exception as e:  # unreadable or not a PDF
        return f"unreadable PDF ({e.__class__.__name__})"
    if n_words < MIN_WORDS:
        return f"{NOT_THE_ARTICLE} ({n_words} words)"
    notes = []
    wanted = words(title)
    if wanted and len(wanted & words(text)) / len(wanted) < 0.6:
        notes.append("title not found on first pages: check it is the right paper")
    if pages < 3:
        notes.append(f"only {pages} page(s)")
    if re.search(r"\barXiv\b", text[:3000]):
        notes.append("arXiv preprint: replace with the published version if possible")
    return "; ".join(notes)


def zotero_items(export_path):
    with open(export_path, encoding="utf-8-sig", newline="") as f:
        items = list(csv.DictReader(f))
    by_doi, by_title = defaultdict(list), defaultdict(list)
    for item in items:
        dois = {normalize_doi(item.get("DOI"))}
        dois |= {normalize_doi(d) for d in re.findall(r"DOI:\s*(\S+)", item.get("Extra") or "")}
        for d in dois - {None}:
            by_doi[d].append(item)
        by_title[normalize_title(item.get("Title"))].append(item)
    return by_doi, by_title


def attached_pdfs(items):
    return [p for item in items for p in (item.get("File Attachments") or "").split("; ")
            if p.lower().endswith(".pdf") and os.path.exists(p)]


def previous_entries():
    """{ID: (reason, notes)} from the existing status sheet, so manual entries survive a re-run."""
    if not STATUS.exists():
        return {}
    ws = openpyxl.load_workbook(STATUS)["Status"]
    header = [c.value for c in ws[1]]
    if REASON not in header:
        return {}
    i, r, n = header.index("ID"), header.index(REASON), header.index(NOTES)
    return {row[i]: (row[r], row[n]) for row in ws.iter_rows(min_row=2, values_only=True)}


def main(export_path):
    _, records, _ = read_records(RETAINED)
    by_doi, by_title = zotero_items(export_path)
    previous = previous_entries()
    rows, counts = [], defaultdict(int)
    for rec in records:
        doi = normalize_doi(rec.get("DOI"))
        items = (by_doi.get(doi) if doi else None) or by_title.get(normalize_title(rec["Title"])) or []
        target = FULLTEXT / f"{rec['ID']}.pdf"
        script_copy = SCRIPT_COPIES / f"{rec['ID']}.pdf"
        candidates = [p for p in attached_pdfs(items)
                      if not check_pdf(p, rec["Title"]).startswith(NOT_THE_ARTICLE)]
        rejected = len(attached_pdfs(items)) - len(candidates)
        if target.exists():
            status, source = "have PDF", "already in fulltext/"
        elif candidates:
            shutil.copy2(candidates[0], target)
            status, source = "have PDF", f"Zotero: {os.path.basename(candidates[0])}"
            counts["copied from Zotero"] += 1
        elif script_copy.exists():
            shutil.copy2(script_copy, target)
            status, source = "have PDF", "open-access download (fetch_oa_pdfs.py)"
            counts["copied from oa_download"] += 1
        else:
            status = "missing"
            source = f"Zotero's PDF is not the article ({rejected} rejected)" if rejected else ""
        reason, notes = previous.get(rec["ID"], (None, None))
        if target.exists():
            reason = None
        elif reason in NOT_RETRIEVED:
            status = "not retrieved"
        counts[status] += 1
        pub = publisher(doi)
        rows.append({
            "ID": rec["ID"], "Status": status, REASON: reason, NOTES: notes, "Source": source,
            "Check": check_pdf(target, rec["Title"]) if target.exists() else "",
            "Next step": "" if target.exists() else next_step(pub, bool(items)),
            "Publisher": pub, "DOI": rec.get("DOI"), "Title": rec.get("Title"),
            "Year": rec.get("Year"), "Document type": rec.get("Document type"),
            "Zotero items": len(items),
        })
    write_status(rows, export_path)
    flagged = sum(bool(r["Check"]) for r in rows)
    print(", ".join(f"{k} {v}" for k, v in sorted(counts.items())),
          f"| {flagged} PDFs flagged for a check -> {STATUS.name}")


def write_status(rows, export_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Status"
    ws.append(COLUMNS)
    order = {"missing": 0, "not retrieved": 1, "have PDF": 2}
    for r in sorted(rows, key=lambda r: (order[r["Status"]], r["Publisher"], r["ID"])):
        ws.append([r[c] for c in COLUMNS])
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="DDE6F0")
    for col, width in zip("ABCDEFGHIJKLM", [7, 13, 18, 50, 40, 40, 60, 20, 30, 60, 6, 18, 8]):
        ws.column_dimensions[col].width = width
    reasons = DataValidation(type="list", formula1='"' + ",".join(NOT_RETRIEVED) + '"',
                             allow_blank=True)
    ws.add_data_validation(reasons)
    reasons.add(f"C2:C{len(rows) + 1}")
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = ws.dimensions
    about = wb.create_sheet("About")
    for line in [
        f"Full-text status of the {len(rows)} records retained at Step 3.",
        f"Built by {os.path.basename(__file__)} from the Zotero export {os.path.basename(export_path)}.",
        "Missing records are listed first, grouped by publisher; 'Next step' says what to try.",
        "'Check' flags PDFs whose first pages lack the title, very short files, and arXiv preprints.",
        f"Fill in '{REASON}' (no GT access / security warning) and '{NOTES}' (what was tried, "
        "with the date) per Screening Methodology.md, 'Retrieving full texts'. Both survive a re-run.",
    ]:
        about.append([line])
    about.column_dimensions["A"].width = 110
    wb.save(STATUS)


def finalize():
    """Split the retained records into retrieved and not retrieved, per the status sheet."""
    header, records, template = read_records(RETAINED)
    ws = openpyxl.load_workbook(STATUS)["Status"]
    sheet_header = [c.value for c in ws[1]]
    status = {row[0]: dict(zip(sheet_header, row)) for row in ws.iter_rows(min_row=2, values_only=True)}
    missing = [i for i, s in status.items() if s["Status"] == "missing"]
    if missing:
        raise SystemExit(f"{len(missing)} records are still 'missing' (e.g., {missing[:5]}): "
                         f"get them or mark a reason in {STATUS.name} first.")
    extra = ["Full text", "Retrieval source", "PDF check", REASON, NOTES]
    retrieved, not_retrieved = [], []
    for rec in records:
        s = status[rec["ID"]]
        row = {**rec, "Full text": f"fulltext/{rec['ID']}.pdf" if s["Status"] == "have PDF" else None,
               "Retrieval source": s["Source"], "PDF check": s["Check"], REASON: s[REASON],
               NOTES: s[NOTES]}
        if s["Status"] == "have PDF":
            retrieved.append(row)
        else:
            not_retrieved.append({**row, "Decision": "Not retrieved",
                                  "Excluded at stage": "Retrieval: report not retrieved"})
    if len(retrieved) + len(not_retrieved) != len(records):
        raise SystemExit("Record count mismatch")
    reasons = defaultdict(int)
    for r in not_retrieved:
        reasons[r[REASON]] += 1
    rule = ("full texts sought for every record kept at Step 3; records whose full text could not "
            "be obtained (no GT access, or a security warning) are reports not retrieved, not "
            "exclusions. See Screening Methodology.md, 'Retrieving full texts'.")
    about = about_sheet("Retrieval - full texts", rule, RETAINED, len(records), len(not_retrieved),
                        len(retrieved),
                        extra=["Not retrieved by reason: " + ", ".join(
                            f"{k} {v}" for k, v in sorted(reasons.items()))])
    write_records(RETRIEVED, header + extra, retrieved, template, about)
    write_records(NOT_RETRIEVED_FILE, header + extra, not_retrieved, template, about)
    print(f"Retrieval: {len(records)} sought, {len(retrieved)} retrieved, "
          f"{len(not_retrieved)} not retrieved ({dict(reasons)})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("export", nargs="?", help="Zotero CSV export with File Attachments")
    parser.add_argument("--finalize", action="store_true",
                        help="write the retrieval step files from the status sheet")
    args = parser.parse_args()
    if args.finalize:
        finalize()
    elif args.export:
        main(args.export)
    else:
        parser.error("give a Zotero export, or --finalize")
