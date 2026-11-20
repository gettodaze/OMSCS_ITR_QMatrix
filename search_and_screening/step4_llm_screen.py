"""Step 4: LLM full-text screening.

As in step 3, the LLM runs outside this script: one subagent per batch reads
step4_llm/fulltext_screening_prompt.md, the batch file and each paper's extracted text, and writes
one JSON line per paper to step4_llm/results/ (pilot runs write to step4_llm/pilot/). This script
prepares the inputs and turns the results into the step files.

    prepare   extract each PDF's text (with [[page N]] markers) to step4_llm/text/, run the
              automatic checks, and write randomized batches and the two pilot batches
    assemble  check the results and write the Step 4 excluded / retained workbooks
    pilot     compare pilot results with the expected answers
    duplicates  step 4b (E9): list candidate duplicate reports among the Step 4 includes and
              apply the decisions recorded in E9_DECISIONS, writing the Step 4b files

    .venv/Scripts/python.exe "Group Project/Screening/step4_llm_screen.py" prepare
"""

import argparse
import json
import random
import re
import sys
from pathlib import Path

import pymupdf

from prescreen_metadata import (
    HERE, TEST_SET, about_sheet, check_counts, mark_excluded, normalize_doi, read_records,
    write_records,
)

RETRIEVED = HERE / "Retrieval - retrieved.xlsx"
LLM_DIR = HERE / "step4_llm"
PROMPT = LLM_DIR / "fulltext_screening_prompt.md"
TEXT_DIR = LLM_DIR / "text"
BATCH_DIR = LLM_DIR / "batches"
RESULT_DIR = LLM_DIR / "results"
PILOT_DIR = LLM_DIR / "pilot"
MANIFEST = LLM_DIR / "manifest.json"
RUN_LOG = LLM_DIR / "run_log.json"

STEP4_EXCLUDED = HERE / "Step 4 - E1-E10 LLM full text - excluded.xlsx"
STEP4_RETAINED = HERE / "Step 4 - E1-E10 LLM full text - retained.xlsx"

SHUFFLE_SEED = 8804
MAX_PAPERS = 5
MAX_WORDS = 60_000

CODES = {f"E{i}" for i in range(1, 11)} - {"E9"}
CONFIDENCE = {"high", "medium", "low"}
LLM_COLUMNS = ["FT decision", "FT code", "FT confidence", "FT reasoning", "FT evidence",
               "FT task", "FT family", "FT domain", "FT data", "FT flags", "FT rule question",
               "FT batch"]

# Expected answers for the known-answer pilot batch (pilot_B), from the automatic checks and
# the four team defaults.
PILOT_B_EXPECTED = {
    "F0522": "E8", "F0526": "E8", "F0729": "E8", "F0822": "not E8",
    "F0121": "E6", "F0324": "E6", "F0329": "E6", "F0502": "E6",
    "F0661": "readable via PDF", "F0043": "any", "F0478": "any", "F1328": "any",
}

# Words common in English prose; their share of tokens separates English from other Latin-script
# languages (Turkish) and from garbled text layers.
COMMON = set("the of and to in a is that for with as on are by this be we an from which or at it "
             "model data results method".split())


def extract(path):
    """Text with a [[page N]] marker before each page."""
    doc = pymupdf.open(path)
    return "\n".join(f"[[page {i + 1}]]\n{page.get_text()}" for i, page in enumerate(doc)), len(doc)


def checks(text, pages):
    letters = [c for c in text if c.isalpha()]
    non_latin = sum(ord(c) > 0x2FF for c in letters) / max(1, len(letters))
    tokens = re.findall(r"[A-Za-z]+", text)
    english = sum(t.lower() in COMMON for t in tokens) / max(1, len(tokens))
    words = len(text.split())
    notes = []
    if non_latin > 0.3:
        notes.append(f"about {non_latin:.0%} of letters are non-Latin script: check E8")
    elif english < 0.05:
        notes.append("little English vocabulary: the text is in another language or garbled; "
                     "if garbled, read the PDF instead")
    if pages <= 2:
        notes.append(f"{pages} page(s): check E6 (two pages or fewer)")
    if words > 15_000:
        notes.append(f"long paper ({words} words): read the methods closely")
    return words, notes


def batch_entry(rec, words, notes):
    return {
        "id": rec["ID"], "title": rec.get("Title"), "venue": rec.get("Venue"),
        "year": rec.get("Year"), "document_type": rec.get("Document type"),
        "text_file": str(TEXT_DIR / f"{rec['ID']}.txt"),
        "pdf_file": str(HERE / rec["Full text"]), "words": words, "automatic_checks": notes,
    }


def pack(entries):
    """Greedy batches of up to MAX_PAPERS papers and MAX_WORDS words, in the given order."""
    batches, current, size = [], [], 0
    for e in entries:
        if current and (len(current) == MAX_PAPERS or size + e["words"] > MAX_WORDS):
            batches.append(current)
            current, size = [], 0
        current.append(e)
        size += e["words"]
    if current:
        batches.append(current)
    return batches


def write_batches(batches, directory, prefix):
    directory.mkdir(parents=True, exist_ok=True)
    names = {}
    for n, batch in enumerate(batches, 1):
        name = f"{prefix}_{n:03d}"
        with open(directory / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for e in batch:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
        names[name] = [e["id"] for e in batch]
    return names


def test_set_ids(records):
    known = {line.strip().lower() for line in TEST_SET.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")}
    return [r["ID"] for r in records if normalize_doi(r.get("DOI")) in known]


def prepare():
    _, records, _ = read_records(RETRIEVED)
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    entries = {}
    for rec in records:
        text, pages = extract(HERE / rec["Full text"])
        (TEXT_DIR / f"{rec['ID']}.txt").write_text(text, encoding="utf-8")
        words, notes = checks(text, pages)
        entries[rec["ID"]] = batch_entry(rec, words, notes)

    order = list(entries.values())
    random.Random(SHUFFLE_SEED).shuffle(order)
    main = write_batches(pack(order), BATCH_DIR, "batch")
    pilot = {}
    pilot.update(write_batches(pack([entries[i] for i in test_set_ids(records)]), PILOT_DIR,
                               "pilot_A_test_set"))
    pilot.update(write_batches(pack([entries[i] for i in PILOT_B_EXPECTED]), PILOT_DIR,
                               "pilot_B_known"))
    MANIFEST.write_text(json.dumps({
        "input": RETRIEVED.name, "records": len(records), "shuffle_seed": SHUFFLE_SEED,
        "max_papers": MAX_PAPERS, "max_words": MAX_WORDS, "batches": main, "pilot": pilot,
    }, indent=1), encoding="utf-8")
    flagged = sum(bool(e["automatic_checks"]) for e in entries.values())
    print(f"{len(records)} texts extracted; {flagged} with automatic-check notes")
    print(f"{len(main)} batches (up to {MAX_PAPERS} papers / {MAX_WORDS} words); "
          f"pilot batches: {', '.join(pilot)}")


# ---------------------------------------------------------------------------------------------


def check_result(r):
    problems = []
    if r.get("decision") not in ("Include", "Exclude"):
        problems.append(f"decision {r.get('decision')!r}")
    if r.get("decision") == "Exclude" and r.get("code") not in CODES:
        problems.append(f"Exclude needs a code E1-E10 (not E9), got {r.get('code')!r}")
    if r.get("decision") == "Include" and r.get("code") is not None:
        problems.append("code given for an Include")
    if r.get("confidence") not in CONFIDENCE:
        problems.append(f"confidence {r.get('confidence')!r}")
    if not str(r.get("reasoning") or "").strip():
        problems.append("no reasoning")
    if not r.get("evidence"):
        problems.append("no evidence quote")
    if r.get("confidence") == "low" and not r.get("rule_question"):
        problems.append("low confidence without a rule_question")
    return problems


def load_results(batches, directory):
    results, problems = {}, []
    for name, ids in batches.items():
        path = directory / f"{name}.results.jsonl" if directory == PILOT_DIR else directory / f"{name}.jsonl"
        if not path.exists():
            problems.append(f"{name}: no results file")
            continue
        seen = {}
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                problems.append(f"{name} line {n}: not JSON")
                continue
            seen[r.get("id")] = r
            problems += [f"{name} {r.get('id')}: {p}" for p in check_result(r)]
        if set(ids) - set(seen):
            problems.append(f"{name}: missing {sorted(set(ids) - set(seen))}")
        if set(seen) - set(ids):
            problems.append(f"{name}: unexpected {sorted(set(seen) - set(ids))}")
        for i in ids:
            if i in seen:
                results[i] = {**seen[i], "batch": name}
    return results, problems


def pilot():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    results, problems = load_results(manifest["pilot"], PILOT_DIR)
    for p in problems:
        print("PROBLEM", p)
    _, records, _ = read_records(RETRIEVED)
    test_ids = set(test_set_ids(records))
    print("\nTest-set studies (expected: Include unless a full-text criterion clearly fails)")
    for i in sorted(test_ids & set(results)):
        r = results[i]
        if r["decision"] == "Exclude" or r["confidence"] == "low":
            print(f"  {i} {r['decision']} {r.get('code') or ''} ({r['confidence']}): {r['reasoning']}")
    inc = sum(results[i]["decision"] == "Include" for i in test_ids & set(results))
    print(f"  Included {inc} of {len(test_ids & set(results))}")
    print("\nKnown-answer set")
    for i, expected in PILOT_B_EXPECTED.items():
        r = results.get(i)
        if not r:
            continue
        got = r["decision"] + (f" {r['code']}" if r.get("code") else "")
        print(f"  {i} expected {expected:16s} got {got:12s} flags {r.get('flags')} | {r['reasoning'][:110]}")


# ---------------------------------------------------------------------------------------------


def assemble():
    header, rows, template = read_records(RETRIEVED)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    results, problems = load_results(manifest["batches"], RESULT_DIR)
    if problems:
        sys.exit("LLM results incomplete or malformed:\n  " + "\n  ".join(problems))
    log = json.loads(RUN_LOG.read_text(encoding="utf-8")) if RUN_LOG.exists() else {}
    model = log.get("model", "unknown model")
    header = header + LLM_COLUMNS
    excluded, retained = [], []
    for row in rows:
        r = results[row["ID"]]
        evidence = "; ".join(f"p. {e.get('page')}: \"{e.get('quote')}\"" for e in r["evidence"])
        row = {**row, "Screener 2": f"LLM full text ({model})",
               "FT decision": r["decision"], "FT code": r.get("code"),
               "FT confidence": r["confidence"], "FT reasoning": r["reasoning"],
               "FT evidence": evidence, "FT task": r.get("task"), "FT family": r.get("family"),
               "FT domain": r.get("domain"), "FT data": r.get("data"),
               "FT flags": "; ".join(r.get("flags") or []) or None,
               "FT rule question": r.get("rule_question"), "FT batch": r["batch"]}
        if r["decision"] == "Exclude":
            excluded.append(mark_excluded(row, r["code"], "Step 4: full text (LLM)",
                                          f"LLM full text: {r['reasoning']}"))
        else:
            retained.append({**row, "Decision": "Include"})
    check_counts(len(rows), excluded, retained)

    test_ids = set(test_set_ids(rows))
    codes = {}
    for r in excluded:
        codes[r["Exclusion reason"]] = codes.get(r["Exclusion reason"], 0) + 1
    low = [r["ID"] for r in excluded + retained if r["FT confidence"] == "low"]
    extra = [
        f"Model: {model}. Batches of up to {MAX_PAPERS} papers / {MAX_WORDS} words, randomized "
        f"(seed {SHUFFLE_SEED}).",
        "Excluded by code: " + ", ".join(f"{k} {v}" for k, v in sorted(codes.items())),
        "Test-set studies excluded: " + (", ".join(sorted(r["ID"] for r in excluded if r["ID"] in test_ids)) or "none"),
        "Low-confidence decisions (see 'FT rule question'): " + (", ".join(sorted(low)) or "none"),
        "Duplicate reports (E9) are resolved in step 4b, on the retained file.",
    ]
    rule = ("LLM full-text screening against the eligibility criteria (codes E1-E10 except E9) "
            "using step4_llm/fulltext_screening_prompt.md.")
    about = about_sheet("Step 4 - E1-E10 LLM full text", rule, RETRIEVED, len(rows),
                        len(excluded), len(retained), extra=extra)
    write_records(STEP4_EXCLUDED, header, excluded, template, about)
    write_records(STEP4_RETAINED, header, retained, template, about)
    print(f"Step 4 (LLM full text): {len(rows)} in, {len(excluded)} excluded, {len(retained)} retained")
    for line in extra[1:4]:
        print(f"    {line}")


# ---------------------------------------------------------------------------------------------
# Step 4b: duplicate reports (E9)
# ---------------------------------------------------------------------------------------------

STEP4B_EXCLUDED = HERE / "Step 4b - E9 duplicates - excluded.xlsx"
STEP4B_RETAINED = HERE / "Step 4b - E9 duplicates - retained.xlsx"

# Decisions on the candidate pairs `duplicates` lists (2026-10-23), made by reading both reports:
# {excluded ID: (kept ID, reason)}. The most complete report is kept: journal over conference,
# then the correctly indexed record.
E9_DECISIONS = {
    "F0996": ("F0995", "same article; Scopus record with a mistyped DOI (10.21031/epod1574880)"),
    "F0865": ("F0449", "conference-proceedings version (IMPS, Springer Proceedings) of the journal "
                       "article in the British Journal of Mathematical and Statistical Psychology"),
}
# Pairs checked and kept as separate studies, noted on both records.
LINKED = {
    ("F1032", "F1325"): "same sample of 74 second-grade students, different analyses (short-form "
                        "construction vs. evaluation of the full COPA); kept as two reports",
}


def duplicate_candidates(rows):
    import difflib
    import itertools
    norm = lambda s: re.sub(r"[^a-z0-9 ]", "", str(s).lower())
    words = lambda s: {w for w in norm(s).split() if len(w) > 3}
    first_author = lambda r: re.split(r"[,;]", str(r.get("Authors")))[0].strip().lower()
    found = []
    for a, b in itertools.combinations(rows, 2):
        ratio = difflib.SequenceMatcher(None, norm(a["Title"]), norm(b["Title"])).ratio()
        union = words(a["Title"]) | words(b["Title"])
        jaccard = len(words(a["Title"]) & words(b["Title"])) / max(1, len(union))
        same_author = first_author(a) == first_author(b) and first_author(a) != "none"
        close_year = abs(int(a.get("Year") or 0) - int(b.get("Year") or 0)) <= 1
        if ratio >= 0.85 or (same_author and close_year and jaccard >= 0.35):
            found.append((a["ID"], b["ID"], round(ratio, 2)))
    return found


def duplicates():
    header, rows, template = read_records(STEP4_RETAINED)
    candidates = duplicate_candidates(rows)
    decided = {tuple(sorted((x, k))) for x, (k, _) in E9_DECISIONS.items()} | {tuple(sorted(p)) for p in LINKED}
    print(f"{len(candidates)} candidate pairs (title similarity or same first author/year):")
    for a, b, ratio in candidates:
        mark = "decided" if tuple(sorted((a, b))) in decided else "checked: separate studies"
        print(f"    {a} / {b} (title similarity {ratio}) - {mark}")
    links = {}
    for (a, b), note in LINKED.items():
        links[a] = f"Linked report: {b} ({note})"
        links[b] = f"Linked report: {a} ({note})"
    excluded, retained = [], []
    for row in rows:
        if row["ID"] in links:
            row = {**row, "Notes": "; ".join(filter(None, [row.get("Notes"), links[row["ID"]]]))}
        if row["ID"] in E9_DECISIONS:
            kept, reason = E9_DECISIONS[row["ID"]]
            excluded.append(mark_excluded(row, "E9", "Step 4b: duplicate report",
                                          f"Duplicate of {kept}: {reason}"))
        else:
            retained.append(row)
    check_counts(len(rows), excluded, retained)
    rule = ("exclude additional reports of an included study (E9), keeping the most complete "
            "report; candidates found by title similarity or same first author and year.")
    about = about_sheet("Step 4b - E9 duplicates", rule, STEP4_RETAINED, len(rows), len(excluded),
                        len(retained), extra=[f"{len(candidates)} candidate pairs checked; decisions "
                                              "in step4_llm_screen.py (E9_DECISIONS, LINKED)."])
    write_records(STEP4B_EXCLUDED, header, excluded, template, about)
    write_records(STEP4B_RETAINED, header, retained, template, about)
    print(f"Step 4b (E9): {len(rows)} in, {len(excluded)} excluded, {len(retained)} retained "
          f"(the included studies)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["prepare", "pilot", "assemble", "duplicates"])
    {"prepare": prepare, "pilot": pilot, "assemble": assemble,
     "duplicates": duplicates}[parser.parse_args().command]()
