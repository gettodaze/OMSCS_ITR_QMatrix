"""Build included_studies.bib and the LaTeX table of the 110 included studies.

Inputs: the step 4c retained workbook and bib_raw.json (BibTeX fetched from doi.org).
Studies already in the team's references.bib reuse those keys and are not re-emitted.
"""
import json, re, sys, unicodedata
import openpyxl

SRC, RAW, OUT_BIB, OUT_TEX, OUT_MAP = sys.argv[1:6]

# Keys already in the team's references.bib, by DOI.
EXISTING = {
    "10.3758/s13428-026-02991-5": "qin_theory_2026",
    "10.3390/jintelligence14050079": "Du2026",
    "10.1111/jedm.70028": "Xue2026",
    "10.1007/s11336-021-09828-4": "Li2022",
    "10.1145/3657604.3662030": "Moore2024",
    "10.1177/01466216241284418": "Khn2024",
}

# Clean booktitles for venues the databases give in capitals or truncated.
VENUE_FIX = {
    "33RD INTERNATIONAL CONFERENCE ON COMPUTERS IN EDUCATION CONFERENCE PROCEEDINGS, ICCE 2025, VOL I":
        "Proceedings of the 33rd International Conference on Computers in Education (ICCE 2025)",
    "30th International Conference on Computers in Education Conference, ICCE 2022 - Proceedings":
        "Proceedings of the 30th International Conference on Computers in Education (ICCE 2022)",
    "Proceedings of International Conference of the Learning Sciences, ICLS":
        "Proceedings of the International Conference of the Learning Sciences (ICLS)",
    "Proceedings of the 14th International Conference on Educational Data Mining, EDM 2021":
        "Proceedings of the 14th International Conference on Educational Data Mining (EDM 2021)",
    "Proceedings of the International Conference on Educational Data Mining":
        "Proceedings of the International Conference on Educational Data Mining",
}

STOP = {"a", "an", "the", "of", "on", "for", "and", "in", "to", "with", "via", "from", "by",
        "using", "based", "towards", "toward", "new", "how", "what", "when", "are", "is", "can", "do"}


def parse_bib(s):
    """Return (type, fields) from one BibTeX entry, tolerating Crossref's one-line form."""
    m = re.match(r"\s*@(\w+)\s*\{\s*[^,]*,", s)
    etype, i, fields = m.group(1).lower(), m.end(), {}
    while i < len(s):
        m = re.compile(r"\s*([A-Za-z_]+)\s*=\s*").match(s, i)
        if not m:
            break
        name, i = m.group(1).lower(), m.end()
        if s[i] == "{":
            depth, j = 0, i
            while True:
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            val, i = s[i + 1:j], j + 1
        elif s[i] == '"':
            j = s.index('"', i + 1)
            val, i = s[i + 1:j], j + 1
        else:
            m2 = re.compile(r"[^,}\s]+").match(s, i)
            val, i = m2.group(0), m2.end()
        fields[name] = val.strip()
        m3 = re.compile(r"\s*,").match(s, i)
        if m3:
            i = m3.end()
    return etype, fields


def tex_escape(t):
    t = re.sub(r"<[^>]+>", "", t)                      # <i>Q</i>, <scp>, MathML
    t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    t = re.sub(r"\s+", " ", t).strip()
    for ch in "&%#_$":
        t = re.sub(r"(?<!\\)" + re.escape(ch), "\\" + ch, t)
    return (t.replace("–", "--").replace("—", "---").replace("‐", "-").replace("‑", "-")
            .replace("’", "'"))


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if c.isascii() and c.isalpha()).lower()


def clean_authors(a):
    a = re.sub(r"\s*\(\d+\)", "", a)                     # Scopus author IDs
    a = a.replace("‐", "-").replace("‑", "-").replace("’", "'")
    if ";" in a:                                          # Scopus/ERIC "A, B; C, D"
        a = " and ".join(p.strip() for p in a.split(";") if p.strip())
    parts = [p.strip().rstrip(",").strip() for p in re.split(r"(?:^|\s+)and\s+", a.strip())]
    return " and ".join(p for p in parts if p)


def first_surname(authors):
    first = authors.split(" and ")[0]
    return first.split(",")[0] if "," in first else first.split()[-1]


wb = openpyxl.load_workbook(SRC, read_only=True)
rows = list(wb.active.iter_rows(values_only=True))
I = {c: i for i, c in enumerate(rows[0])}
raw = json.load(open(RAW, encoding="utf-8"))

entries, keymap, used = [], {}, set(EXISTING.values())
x_conf = {}  # conference paper, judged as for the bib entry type
for r in rows[1:]:
    fid = r[I["ID"]]
    doi = (r[I["DOI"]] or "").strip()
    venue = r[I["Venue"]] or ""
    if doi.lower() in EXISTING:
        year = parse_bib(raw[fid]["bib"])[1].get("year") if fid in raw else r[I["Year"]]
        keymap[fid] = {"key": EXISTING[doi.lower()], "year": int(year)}
        x_conf[fid] = "Conference" in (r[I["Document type"]] or "")
        continue
    if fid in raw:
        etype, f = parse_bib(raw[fid]["bib"])
    else:
        etype, f = "", {}
    is_conf = "Conference" in (r[I["Document type"]] or "")
    etype = "inproceedings" if is_conf or etype in ("inbook", "inproceedings", "misc") else "article"
    x_conf[fid] = etype == "inproceedings"

    authors = clean_authors(f.get("author") or r[I["Authors"]])
    title = tex_escape(f.get("title") or r[I["Title"]])
    year = str(f.get("year") or r[I["Year"]])
    out = {"author": authors, "title": "{" + title + "}", "year": year}
    if etype == "article":
        out["journal"] = tex_escape(f.get("journal") or venue)
    else:
        bt = f.get("booktitle") or f.get("journal") or VENUE_FIX.get(venue, venue)
        out["booktitle"] = tex_escape(VENUE_FIX.get(bt, bt))
    for k in ("volume", "number", "pages"):
        if f.get(k):
            out[k] = tex_escape(f[k]).replace("--", "-").replace("-", "--")
    if etype == "inproceedings" and f.get("publisher"):
        out["publisher"] = tex_escape(f["publisher"])
    if doi:
        out["doi"] = doi

    base = fold(first_surname(authors)) + year
    word = next((fold(w) for w in re.findall(r"[A-Za-z][A-Za-z\-]+", re.sub(r"\\.", "", title))
                 if fold(w) not in STOP and len(fold(w)) > 2), "x")
    key = base + word
    n = 2
    while key in used:
        key, n = f"{base}{word}{n}", n + 1
    used.add(key)
    keymap[fid] = {"key": key, "year": int(year)}
    body = ",\n".join(f"  {k:<9} = {{{v}}}" for k, v in out.items())
    entries.append(f"@{etype}{{{key},\n{body}\n}}")

open(OUT_BIB, "w", encoding="utf-8").write(
    "% Included studies (110) for the Q-matrix SLR. Generated from DOI metadata (Crossref/DataCite);\n"
    "% six studies already in references.bib reuse those keys and are not repeated here.\n\n"
    + "\n\n".join(entries) + "\n")
json.dump(keymap, open(OUT_MAP, "w", encoding="utf-8"), indent=1)
print(len(entries), "entries written;", len(keymap), "studies mapped")

# ---------------------------------------------------------------- table
FAM = {"expert": "Exp", "statistical": "Stat", "ML": "ML", "LLM": "LLM"}
FAM_ORDER = list(FAM)
DOM = {"education": "EM", "ITS/LA": "ITS/LA", "psych/clinical": "PC"}
TASK = {"generation": "G", "validation": "V", "refinement": "R"}
DATA = {"empirical": "Emp", "simulated": "Sim", "both": "Both"}
TYPE = {"method_new": "New", "method_comparison": "Comp", "tool": "Tool"}
EVAL = {"Q_recovery": "QR", "classification_accuracy": "CA", "validation_power_type1": "PT",
        "model_fit_comparison": "MF", "prediction_heldout": "HP", "agreement_with_expert": "EA",
        "expert_or_thinkaloud_review": "ER", "computational_cost": "CC",
        "learning_curves": "LC", "validation_index": "VI"}
EVAL_ORDER = list(EVAL)


def ordered(parts, order):
    return sorted(set(parts), key=order.index)


recs = []
for r in rows[1:]:
    fid = r[I["ID"]]
    fams = ordered(r[I["FT family"]].split("+"), FAM_ORDER)
    doms = [d for d in r[I["FT domain"]].split("+") if d != "simulation"]
    doms = ordered(doms, list(DOM))
    tasks = ordered(r[I["FT task"]].split("+"), list(TASK))
    evals = ordered([e.strip() for e in r[I["Q evaluation"]].split(",") if e.strip()], EVAL_ORDER)
    recs.append({
        "key": keymap[fid]["key"], "year": keymap[fid]["year"],
        "pub": "C" if x_conf.get(fid) else "J",
        "type": TYPE[r[I["Study type"]]],
        "task": ", ".join(TASK[t] for t in tasks),
        "fam_sort": [FAM_ORDER.index(f) for f in fams],
        "fam": " + ".join(FAM[f] for f in fams),
        "dom": ", ".join(DOM[d] for d in doms) or "--",
        "data": DATA[r[I["FT data"]]],
        "eval": ", ".join(EVAL[e] for e in evals),
        "surname": fold(first_surname(clean_authors(r[I["Authors"]]))),
    })

# Single-family studies first, in family order, then hybrids; within a group by year, then author.
recs.sort(key=lambda x: (len(x["fam_sort"]), x["fam_sort"], x["year"], x["surname"]))

CHUNKS = [recs[:55], recs[55:]]
LEGEND = (
    "Pub.: J journal article, C conference paper. Type: New method, Comp(arison) of existing methods, "
    "Tool (software or tutorial paper). Task: G generation, V validation, R refinement. "
    "Family: Exp expert-informed, Stat statistical, ML machine learning, LLM large language model; "
    "+ marks a hybrid. Domain (setting of the empirical data): EM educational measurement, "
    "ITS/LA intelligent tutoring systems and learning analytics, PC psychological and clinical "
    "assessment; -- simulated data only. Data: Emp empirical, Sim simulated, Both. "
    "Evaluation: QR Q-matrix recovery, CA attribute classification accuracy, PT power and Type I error, "
    "MF model fit, HP prediction of held-out responses, EA agreement with an expert-specified "
    "Q-matrix, ER expert or think-aloud review, CC computational cost, LC learning curves, "
    "VI validation index.")

# Fixed widths so both pages line up; they sum to 0.86\textwidth plus column separation.
COLS = ("@{}p{0.22\\textwidth} p{0.035\\textwidth} p{0.03\\textwidth} p{0.04\\textwidth} "
        "p{0.05\\textwidth} p{0.12\\textwidth} p{0.08\\textwidth} p{0.04\\textwidth} p{0.245\\textwidth}@{}")

out = ["% Table of the 110 included studies: one numbered table on two pages (acmart's two-column",
       "% layout cannot break a float across pages). Rules separate method-family groups.",
       "% Requires booktabs (loaded by acmart). Citations use \\citet (natbib, loaded by acmart).", ""]
for n, chunk in enumerate(CHUNKS, 1):
    out.append("\\begin{table*}[p]")
    if n == 1:
        out += ["  \\caption{Characteristics of the included studies.}", "  \\label{tab:included}"]
    else:
        out += ["  \\addtocounter{table}{-1}",
                "  \\caption{Characteristics of the included studies (continued).}"]
    out += ["  \\scriptsize",
            "  \\setlength{\\tabcolsep}{4pt}",
            "  \\begin{tabular}{" + COLS + "}",
            "    \\toprule",
            "    Study & Year & Pub. & Type & Task & Family & Domain & Data & Evaluation \\\\",
            "    \\midrule"]
    prev = None
    for x in chunk:
        if prev is not None and x["fam"] != prev:
            out.append("    \\midrule")
        prev = x["fam"]
        out.append(f"    \\citet{{{x['key']}}} & {x['year']} & {x['pub']} & {x['type']} & {x['task']} & "
                   f"{x['fam']} & {x['dom']} & {x['data']} & {x['eval']} \\\\")
    out += ["    \\bottomrule", "  \\end{tabular}"]
    if n == 1:
        out += ["", "  \\smallskip", "  \\parbox{\\textwidth}{\\footnotesize " + LEGEND + "}"]
    out += ["\\end{table*}", ""]
open(OUT_TEX, "w", encoding="utf-8").write("\n".join(out))
print("table rows:", sum(len(c) for c in CHUNKS))
