"""Fetch BibTeX for each included study's DOI via doi.org content negotiation (Crossref or DataCite)."""
import json, sys, time, urllib.request, urllib.error
import openpyxl

SRC = sys.argv[1]
OUT = sys.argv[2]

ws = openpyxl.load_workbook(SRC, read_only=True).active
rows = list(ws.iter_rows(values_only=True))
I = {c: i for i, c in enumerate(rows[0])}
try:
    done = json.load(open(OUT, encoding="utf-8"))
except FileNotFoundError:
    done = {}

for r in rows[1:]:
    fid, doi = r[I["ID"]], r[I["DOI"]]
    if not doi or fid in done:
        continue
    req = urllib.request.Request("https://doi.org/" + doi.strip(),
                                 headers={"Accept": "application/x-bibtex; charset=utf-8",
                                          "User-Agent": "slr-bib-builder/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            done[fid] = {"doi": doi, "bib": resp.read().decode("utf-8")}
    except Exception as e:
        done[fid] = {"doi": doi, "error": str(e)}
    print(fid, "error" if "error" in done[fid] else "ok", flush=True)
    json.dump(done, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    time.sleep(0.3)
