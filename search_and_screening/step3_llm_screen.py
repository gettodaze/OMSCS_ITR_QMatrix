"""Step 3: LLM title/abstract screening, and the human validation of its exclusions.

The LLM itself is run outside this script (see "Screening Methodology.md", step 3): it reads
step3_llm/screening_prompt.md and one batch file, and writes one JSON line per record to
step3_llm/results/. This script prepares those batches and turns the results into the step files.

Subcommands, in order (run from the project root with the project's Python):

    prepare   split Step 2's retained records into randomized batches for the LLM
    assemble  check the LLM results and write the Step 3 excluded / retained workbooks
    sample    draw the random sample of LLM exclusions for human review (blind file + key)
    report    after review, estimate the LLM's false-exclusion rate from the completed sample

Example:
    .venv/Scripts/python.exe "Group Project/Screening/step3_llm_screen.py" prepare
"""

import argparse
import json
import math
import random
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from prescreen_metadata import (
    HERE,
    STEP2_RETAINED,
    TEST_SET,
    check_counts,
    mark_excluded,
    normalize_doi,
    read_records,
    write_records,
    about_sheet,
)

LLM_DIR = HERE / "step3_llm"
PROMPT = LLM_DIR / "screening_prompt.md"
BATCH_DIR = LLM_DIR / "batches"
RESULT_DIR = LLM_DIR / "results"
MANIFEST = LLM_DIR / "manifest.json"
RUN_LOG = LLM_DIR / "run_log.json"

STEP3_EXCLUDED = HERE / "Step 3 - E1-E5 LLM title-abstract - excluded.xlsx"
STEP3_RETAINED = HERE / "Step 3 - E1-E5 LLM title-abstract - retained.xlsx"
SAMPLE_BLIND = HERE / "Step 3 - validation sample (blind).xlsx"
SAMPLE_KEY = HERE / "Step 3 - validation key.xlsx"

BATCH_SIZE = 25
SHUFFLE_SEED = 8803
SAMPLE_SEED = 20261020

DECISIONS = {"Include", "Maybe", "Exclude"}
CODES = {"E1", "E2", "E3", "E4", "E5"}
CONFIDENCE = {"high", "medium"}
LLM_COLUMNS = [
    "LLM decision", "LLM code", "LLM confidence", "LLM reasoning", "LLM family", "LLM domain",
    "LLM batch",
]

# Validation design (see Screening Methodology.md, step 3).
CONFIDENCE_LEVEL = 0.95
# Title/abstract recall to demonstrate: found / (found + missed). The eligible records found are
# approximated by the LLM's Include count: Maybes often fail at full text, so counting them would
# make the target too lenient.
MIN_RECALL = 0.95
DECOY_SHARE = 0.10        # LLM-retained records mixed into the review set so it is blind


def allowed_misses(retained):
    """Most wrongly excluded eligible records compatible with MIN_RECALL, and the Include count."""
    includes = sum(r.get("LLM decision") == "Include" for r in retained)
    return math.floor(includes * (1 - MIN_RECALL) / MIN_RECALL + 1e-9), includes


def hypergeom_cdf(k, N, M, n):
    """P(at most k bad records in a sample of n drawn without replacement from N holding M bad)."""
    return sum(math.comb(M, i) * math.comb(N - M, n - i) for i in range(k + 1)) / math.comb(N, n)


# ---------------------------------------------------------------------------------------------
# prepare
# ---------------------------------------------------------------------------------------------


def prepare():
    _, rows, _ = read_records(STEP2_RETAINED)
    order = list(rows)
    random.Random(SHUFFLE_SEED).shuffle(order)
    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    batches = {}
    for start in range(0, len(order), BATCH_SIZE):
        name = f"batch_{start // BATCH_SIZE + 1:03d}"
        chunk = order[start:start + BATCH_SIZE]
        with open(BATCH_DIR / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in chunk:
                f.write(json.dumps({
                    "id": r["ID"],
                    "title": r.get("Title"),
                    "abstract": r.get("Abstract"),
                    "keywords": r.get("Keywords"),
                    "venue": r.get("Venue"),
                    "year": r.get("Year"),
                    "document_type": r.get("Document type"),
                }, ensure_ascii=False) + "\n")
        batches[name] = [r["ID"] for r in chunk]
    MANIFEST.write_text(json.dumps({
        "input": STEP2_RETAINED.name, "records": len(rows), "batch_size": BATCH_SIZE,
        "shuffle_seed": SHUFFLE_SEED, "batches": batches,
    }, indent=1), encoding="utf-8")
    print(f"{len(rows)} records in {len(batches)} batches of up to {BATCH_SIZE} -> {BATCH_DIR}")


# ---------------------------------------------------------------------------------------------
# assemble
# ---------------------------------------------------------------------------------------------


def load_results():
    """Return {id: result} after checking every batch's results are complete and well formed."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    results, problems = {}, []
    for name, ids in manifest["batches"].items():
        path = RESULT_DIR / f"{name}.jsonl"
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
        missing, extra = set(ids) - set(seen), set(seen) - set(ids)
        if missing:
            problems.append(f"{name}: missing {sorted(missing)}")
        if extra:
            problems.append(f"{name}: unexpected {sorted(extra)}")
        for i in ids:
            if i in seen:
                results[i] = {**seen[i], "batch": name}
    if problems:
        sys.exit("LLM results incomplete or malformed:\n  " + "\n  ".join(problems))
    return results


def check_result(r):
    problems = []
    if r.get("decision") not in DECISIONS:
        problems.append(f"decision {r.get('decision')!r}")
    if r.get("decision") == "Exclude" and r.get("code") not in CODES:
        problems.append(f"Exclude needs a code, got {r.get('code')!r}")
    if r.get("decision") != "Exclude" and r.get("code") is not None:
        problems.append("code given for a non-exclusion")
    if r.get("confidence") not in CONFIDENCE:
        problems.append(f"confidence {r.get('confidence')!r}")
    if not str(r.get("reasoning") or "").strip():
        problems.append("no reasoning")
    return problems


def run_model():
    log = json.loads(RUN_LOG.read_text(encoding="utf-8")) if RUN_LOG.exists() else {}
    return log.get("model", "unknown model")


def assemble():
    header, rows, template = read_records(STEP2_RETAINED)
    results = load_results()
    model = run_model()
    header = header + LLM_COLUMNS
    excluded, retained = [], []
    for row in rows:
        r = results[row["ID"]]
        row = {
            **row,
            "Screener 1": f"LLM ({model})",
            "LLM decision": r["decision"], "LLM code": r.get("code"),
            "LLM confidence": r["confidence"], "LLM reasoning": r["reasoning"],
            "LLM family": r.get("family"), "LLM domain": r.get("domain"),
            "LLM batch": r["batch"],
        }
        if r["decision"] == "Exclude":
            excluded.append(mark_excluded(
                row, r["code"], "Step 3: title/abstract (LLM)", f"LLM: {r['reasoning']}"))
        else:
            retained.append({**row, "Decision": r["decision"]})
    check_counts(len(rows), excluded, retained)

    test_hits = test_set_exclusions(excluded)
    counts = count_by(excluded, "Exclusion reason")
    rule = ("LLM title/abstract screening against criteria C1-C7 (codes E1-E5) using "
            "step3_llm/screening_prompt.md; Include and Maybe are retained for full text.")
    extra = [
        f"Model: {model}. Batches of {BATCH_SIZE} in randomized order (seed {SHUFFLE_SEED}).",
        "Excluded by code: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())),
        f"Retained: Include {sum(r['Decision'] == 'Include' for r in retained)}, "
        f"Maybe {sum(r['Decision'] == 'Maybe' for r in retained)}.",
        "Test-set studies excluded: " + (", ".join(test_hits) if test_hits else "none"),
    ]
    about = about_sheet("Step 3 - E1-E5 LLM title-abstract", rule, STEP2_RETAINED, len(rows),
                        len(excluded), len(retained), extra=extra)
    write_records(STEP3_EXCLUDED, header, excluded, template, about)
    write_records(STEP3_RETAINED, header, retained, template, about)
    print(f"Step 3 (LLM): {len(rows)} in, {len(excluded)} excluded, {len(retained)} retained")
    for line in extra[1:]:
        print(f"    {line}")


def test_set_exclusions(excluded):
    known = {
        line.strip().lower() for line in TEST_SET.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }
    return [r["ID"] for r in excluded if normalize_doi(r.get("DOI")) in known]


def count_by(rows, key):
    counts = {}
    for r in rows:
        counts[r[key]] = counts.get(r[key], 0) + 1
    return counts


# ---------------------------------------------------------------------------------------------
# sample
# ---------------------------------------------------------------------------------------------


def zero_failure_sample_size(N, allowed, confidence=CONFIDENCE_LEVEL):
    """Smallest n such that, if none of n exclusions drawn without replacement from N is wrong,
    more than `allowed` wrong exclusions in the N is ruled out at the given confidence."""
    for n in range(1, N + 1):
        if hypergeom_cdf(0, N, allowed + 1, n) <= 1 - confidence:
            return n
    return N


def sample():
    _, excluded, _ = read_records(STEP3_EXCLUDED)
    _, retained, _ = read_records(STEP3_RETAINED)
    allowed, includes = allowed_misses(retained)
    n = zero_failure_sample_size(len(excluded), allowed)
    n_decoy = math.ceil(DECOY_SHARE * n)
    rng = random.Random(SAMPLE_SEED)
    picked = [(r, "exclusion sample") for r in rng.sample(excluded, n)]
    picked += [(r, "decoy (LLM retained)") for r in rng.sample(retained, n_decoy)]
    rng.shuffle(picked)

    blind_cols = ["Sample no.", "ID", "Title", "Abstract", "Keywords", "Venue", "Year",
                  "Document type", "Reviewer", "Reviewer decision", "Reviewer code",
                  "Reviewer notes"]
    widths = [8, 7, 50, 90, 30, 30, 6, 18, 14, 14, 12, 40]
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Review"
    ws.append(blind_cols)
    for i, (r, _) in enumerate(picked, 1):
        ws.append([i, r["ID"], r.get("Title"), r.get("Abstract"), r.get("Keywords"),
                   r.get("Venue"), r.get("Year"), r.get("Document type"), None, None, None, None])
    style_sheet(ws, widths, wrap_cols={3, 4, 12})
    decision = DataValidation(type="list", formula1='"Include,Maybe,Exclude"', allow_blank=True)
    code = DataValidation(type="list", formula1='"E1,E2,E3,E4,E5"', allow_blank=True)
    ws.add_data_validation(decision)
    ws.add_data_validation(code)
    decision.add(f"J2:J{len(picked) + 1}")
    code.add(f"K2:K{len(picked) + 1}")
    guide = wb.create_sheet("How to review")
    for line in REVIEW_GUIDE:
        guide.append([line])
    guide.column_dimensions["A"].width = 120
    wb.save(SAMPLE_BLIND)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Key"
    ws.append(["Sample no.", "ID", "In sample as", "LLM decision", "LLM code", "LLM confidence",
               "LLM reasoning"])
    for i, (r, role) in enumerate(picked, 1):
        ws.append([i, r["ID"], role, r.get("LLM decision"), r.get("LLM code"),
                   r.get("LLM confidence"), r.get("LLM reasoning")])
    style_sheet(ws, [8, 7, 20, 12, 9, 12, 100], wrap_cols={7})
    about = wb.create_sheet("About")
    for line in [
        "Unblinding key for the Step 3 validation sample. Do not open until review is done.",
        f"Exclusions: {len(excluded)}; retained: {len(retained)}.",
        f"Target: at {CONFIDENCE_LEVEL:.0%} confidence, recall of at least {MIN_RECALL:.0%} "
        f"against the {includes} LLM Includes, i.e., at most {allowed} of the "
        f"{len(excluded)} exclusions wrong.",
        f"Sample: {n} exclusions (simple random sample without replacement, seed {SAMPLE_SEED}; "
        f"size from the hypergeometric zero-failure bound) plus {n_decoy} LLM-retained decoys, "
        "shuffled together.",
    ]:
        about.append([line])
    about.column_dimensions["A"].width = 120
    wb.save(SAMPLE_KEY)
    print(f"Exclusions {len(excluded)}, Includes {includes} -> at most {allowed} wrong exclusions")
    print(f"Sample: {n} exclusions + {n_decoy} decoys = {len(picked)} records to review")
    print(f"    {SAMPLE_BLIND.name}\n    {SAMPLE_KEY.name} (keep closed until review is done)")


REVIEW_GUIDE = [
    "How to review the Step 3 validation sample",
    "",
    "Full instructions: Screening Methodology.md, section 'Instructions for human reviewers'. "
    "Read them before starting. In short:",
    "- Your rows: Reviewer 1 takes Sample no. ending in 1 or 6, Reviewer 2 in 2 or 7, "
    "Reviewer 3 in 3 or 8, Reviewer 4 in 4 or 9, Reviewer 5 in 5 or 0.",
    "- Judge each row from its title and abstract alone. Don't look the paper up, don't open "
    "the key file or the LLM's output, and don't discuss individual rows until all are done.",
    "- Ask the five questions in order (E1 mapping, E2 builds/validates/refines it, E3 discrete "
    "attributes, E4 human respondents, E5 primary study in scope) and stop at the first clear no.",
    "- Fill in Reviewer, Reviewer decision (Include, Maybe or Exclude), Reviewer code for "
    "Exclude, and a one-sentence note for every Include and Maybe.",
    "- Exclude only on a reason you can point to in the title or abstract; when in doubt, Maybe.",
    "- Once entered, a decision stands; correct only slips, and say so in the notes.",
]


def style_sheet(ws, widths, wrap_cols=()):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="DDE6F0")
    for row in ws.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=cell.column in wrap_cols)
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions


# ---------------------------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------------------------


def upper_bound(k, n, N, confidence=CONFIDENCE_LEVEL):
    """Exact one-sided upper confidence bound on the number of wrong exclusions among N, given k
    wrong in a sample of n drawn without replacement: the largest count not rejected."""
    M = k
    while M + 1 <= N - (n - k) and hypergeom_cdf(k, N, M + 1, n) > 1 - confidence:
        M += 1
    return M


def report():
    review = {r["Sample no."]: r for r in sheet_rows(SAMPLE_BLIND, "Review")}
    key = {r["Sample no."]: r for r in sheet_rows(SAMPLE_KEY, "Key")}
    # The rows are in random order, so the reviewed rows are a random sample of the rows even if
    # review stops early; the bound is then simply wider.
    done = {n for n, r in review.items() if r.get("Reviewer decision") in DECISIONS}
    if len(done) < len(review):
        print(f"Partial review: {len(done)} of {len(review)} rows decided; estimating from those.")
    _, excluded, _ = read_records(STEP3_EXCLUDED)
    _, retained, _ = read_records(STEP3_RETAINED)

    sampled = [n for n, k in key.items() if k["In sample as"] == "exclusion sample" and n in done]
    misses = [n for n in sampled if review[n]["Reviewer decision"] in ("Include", "Maybe")]
    n, k = len(sampled), len(misses)
    if not n:
        sys.exit("No sampled exclusions reviewed yet.")
    bound = upper_bound(k, n, len(excluded))
    allowed, includes = allowed_misses(retained)
    decoys = [n for n, k_ in key.items() if k_["In sample as"] != "exclusion sample" and n in done]
    decoy_agree = sum(review[d]["Reviewer decision"] in ("Include", "Maybe") for d in decoys)

    print(f"Reviewed exclusions: {n}; reviewer would have kept {k}: "
          f"{[key[m]['ID'] for m in misses]}")
    print(f"{CONFIDENCE_LEVEL:.0%} upper bound: at most {bound} of {len(excluded)} exclusions "
          f"wrong, so recall at least {includes / (includes + bound):.1%}")
    print(f"Target (at most {allowed} wrong, recall >= {MIN_RECALL:.0%}): "
          f"{'MET' if bound <= allowed else 'NOT MET'}")
    print(f"Decoys the reviewer also kept: {decoy_agree} of {len(decoys)}")


def sheet_rows(path, sheet):
    ws = openpyxl.load_workbook(path)[sheet]
    header = [c.value for c in ws[1]]
    return [dict(zip(header, v)) for v in ws.iter_rows(min_row=2, values_only=True) if v[0]]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["prepare", "assemble", "sample", "report"])
    {"prepare": prepare, "assemble": assemble, "sample": sample, "report": report}[
        parser.parse_args().command]()
