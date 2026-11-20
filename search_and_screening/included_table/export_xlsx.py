"""Export Table 4 (the 110 included studies) to an Excel workbook for charting.

Usage: export_xlsx.py SRC_XLSX TABLE_TEX INCLUDED_BIB KEYMAP_JSON OUT_XLSX

One row per study. Multi-valued fields (task, family, domain, evaluation) appear both as the
table's text and as 0/1 indicator columns, so a pivot table or COUNTIF can count each value.
"""
import json, re, sys
import openpyxl
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

SRC, TEX, BIB, KEYMAP, OUT = sys.argv[1:6]

# Table rows by citation key.
rows = {}
for line in open(TEX, encoding="utf-8"):
    s = line.strip()
    if s.startswith("\\citet{"):
        cells = [c.strip() for c in s.rstrip("\\").split("&")]
        key = re.match(r"\\citet\{([^}]+)\}", cells[0]).group(1)
        rows[key] = cells[1:]
assert len(rows) == 110, len(rows)

# Venue and authors from the generated bib, where the study has an entry there.
bib = {}
for m in re.finditer(r"@\w+\{([^,]+),(.*?)\n\}", open(BIB, encoding="utf-8").read(), re.S):
    f = dict(re.findall(r"(\w+)\s*=\s*\{(.*)\},?\s*$", m.group(2), re.M))
    bib[m.group(1)] = f

def untex(t):
    t = re.sub(r"^\{+|\}+$", "", t or "")
    return t.replace("&amp;", "&").replace("\\&", "&").replace("\\%", "%").replace("\\_", "_").replace("--", "–")

ws = openpyxl.load_workbook(SRC, read_only=True).active
src = list(ws.iter_rows(values_only=True))
I = {c: i for i, c in enumerate(src[0])}
by_id = {r[I["ID"]]: r for r in src[1:]}
keymap = json.load(open(KEYMAP, encoding="utf-8"))

PUB = {"J": "Journal article", "C": "Conference paper"}
TYPE = {"New": "New method", "Comp": "Comparison", "Tool": "Tool"}
DATA = {"Emp": "Empirical", "Sim": "Simulated", "Both": "Both"}
TASKS = [("G", "Generation"), ("V", "Validation"), ("R", "Refinement")]
FAMS = [("Exp", "Expert-informed"), ("Stat", "Statistical"), ("ML", "Machine learning"), ("LLM", "LLM")]
DOMS = [("EM", "Educational measurement"), ("ITS/LA", "ITS/LA"), ("PC", "Psych/clinical"),
        ("--", "Simulated only")]
EVALS = [("QR", "Q-matrix recovery"), ("CA", "Classification accuracy"), ("PT", "Power/Type I error"),
         ("MF", "Model fit"), ("HP", "Held-out prediction"), ("EA", "Expert agreement"),
         ("ER", "Expert/think-aloud review"), ("CC", "Computational cost"), ("LC", "Learning curves"),
         ("VI", "Validation index")]

head = (["ID", "Citation key", "Authors", "Title", "Year (first online)", "Publication type", "Venue",
         "Contribution type", "Task", "Method family", "Hybrid", "Domain", "Data", "Evaluation"]
        + [f"Task: {n}" for _, n in TASKS] + [f"Family: {n}" for _, n in FAMS]
        + [f"Domain: {n}" for _, n in DOMS] + [f"Eval: {n}" for _, n in EVALS])
out = []
for fid, km in keymap.items():
    key = km["key"]
    year, pub, typ, task, fam, dom, data, ev = rows[key]
    r, b = by_id[fid], bib.get(key, {})
    tasks = [t.strip() for t in task.split(",")]
    fams = [t.strip() for t in fam.split("+")]
    doms = [t.strip() for t in dom.split(",")]
    evs = [t.strip() for t in ev.split(",")]
    venue = untex(b.get("journal") or b.get("booktitle")) or (r[I["Venue"]] or "")
    authors = untex(b.get("author")) or " and ".join(
        p.strip() for p in re.sub(r"\s*\(\d+\)", "", r[I["Authors"]] or "").split(";") if p.strip())
    out.append([fid, key, authors, untex(b.get("title")) or r[I["Title"]], int(year), PUB[pub], venue,
                TYPE[typ], task, fam, "Yes" if len(fams) > 1 else "No",
                "Simulated only" if dom == "--" else dom, DATA[data], ev]
               + [int(a in tasks) for a, _ in TASKS] + [int(a in fams) for a, _ in FAMS]
               + [int(a in doms) for a, _ in DOMS] + [int(a in evs) for a, _ in EVALS])
out.sort(key=lambda x: (x[4], x[1].lower()))

wb = openpyxl.Workbook()
sh = wb.active
sh.title = "Studies"
sh.append(head)
for row in out:
    sh.append(row)
for c in sh[1]:
    c.font = Font(bold=True)
sh.freeze_panes = "C2"
sh.auto_filter.ref = sh.dimensions
widths = {"Authors": 40, "Title": 60, "Venue": 40, "Citation key": 28}
for i, h in enumerate(head, 1):
    sh.column_dimensions[get_column_letter(i)].width = widths.get(h, max(10, min(len(h) + 2, 26)))

lg = wb.create_sheet("Legend")
lg.append(["Column", "Meaning"])
for k, v in [
    ("Year (first online)", "First-online year, as in Table 4 and the date criterion; 2026 runs to October 8."),
    ("Publication type", "Journal article or conference paper (proceedings papers with chapter DOIs count as conference)."),
    ("Task / Method family / Domain / Evaluation", "Table 4's codes; a study can have several, so use the 0/1 columns to count."),
    ("Family codes", "Exp expert-informed, Stat statistical, ML machine learning, LLM; '+' marks a hybrid."),
    ("Domain codes", "EM educational measurement, ITS/LA intelligent tutoring systems and learning analytics, PC psychological and clinical; 'Simulated only' has no empirical setting."),
    ("Evaluation codes", "; ".join(f"{a} {n}" for a, n in EVALS)),
    ("Source", "Screening labels from steps 4 and 4c, not extraction results. Regenerate with Screening/included_table/export_xlsx.py."),
]:
    lg.append([k, v])
lg["A1"].font = lg["B1"].font = Font(bold=True)
lg.column_dimensions["A"].width = 42
lg.column_dimensions["B"].width = 110
wb.save(OUT)
print(len(out), "studies written to", OUT)
