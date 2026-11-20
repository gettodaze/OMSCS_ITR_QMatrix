"""Step 4c: sort the included studies by what they contribute to the research questions.

A sorting pass on the 270 studies retained at step 4b, to inform possible new exclusion criteria;
it excludes nothing. As in steps 3 and 4 the LLM runs outside this script: one subagent per batch
reads step4c_llm/classification_prompt.md and its batch file and writes one JSON line per study
to step4c_llm/results/.

    prepare   write batches from the step 4b retained file (title, abstract, step-4 reasoning
              and evidence, provisional codes) plus the pilot batch
    pilot     compare the pilot results with the groups assigned by hand to the same 30 studies
    report    check the results and tabulate groups by family, domain and study type; write
              'Step 4c - RQ contribution groups.xlsx' (all 270, nothing excluded)
    e11       apply E11, adopted 2026-10-27 (option 5 of the team decision brief): exclude every
              study not in group A; write the step's excluded and retained files and copy the
              retained studies' PDFs to 'Group A full texts/' for sharing

    .venv/Scripts/python.exe "Group Project/Screening/step4c_classify.py" prepare
"""

import argparse
import json
import random
import re
import shutil
import sys
from collections import Counter

from prescreen_metadata import (HERE, TEST_SET, about_sheet, check_counts, mark_excluded,
                                normalize_doi, read_records, write_records)

SOURCE = HERE / "Step 4b - E9 duplicates - retained.xlsx"
LLM_DIR = HERE / "step4c_llm"
BATCH_DIR = LLM_DIR / "batches"
RESULT_DIR = LLM_DIR / "results"
PILOT_DIR = LLM_DIR / "pilot"
MANIFEST = LLM_DIR / "manifest.json"
OUTPUT = HERE / "Step 4c - RQ contribution groups.xlsx"
FULLTEXT_RESULTS = RESULT_DIR / "fulltext_U.jsonl"
E11_EXCLUDED = HERE / "Step 4c - E11 not a method study - excluded.xlsx"
E11_RETAINED = HERE / "Step 4c - E11 not a method study - retained.xlsx"
SHARE_DIR = HERE / "Group A full texts"

BATCH_SIZE = 30
SHUFFLE_SEED = 8805
GROUPS = {"A", "B", "C", "H", "U"}
STUDY_TYPES = {"method_new", "method_comparison", "application", "tool"}
EVALUATION = {"Q_recovery", "classification_accuracy", "classification_reliability",
              "validation_power_type1", "model_fit_comparison", "validation_index",
              "prediction_heldout", "agreement_with_expert", "expert_or_thinkaloud_review",
              "learning_curves", "hierarchy_consistency", "computational_cost"}
COLUMNS = ["RQ group", "Study type", "Q evaluation", "Group confidence", "Group reasoning",
           "Group source", "Group evidence"]

# Groups assigned by hand on 2026-10-26 to a random sample of 30 (seed 2611), before this pass,
# from the step-4 reasoning. Ambiguous cases are marked with both letters; either counts as a match.
HAND = {
    "F1112": "H", "F0659": "A", "F0028": "A", "F0938": "C", "F0007": "A", "F1345": "B",
    "F0243": "C", "F0695": "A", "F1132": "B", "F0379": "A", "F1300": "B", "F0166": "A",
    "F1094": "H", "F0796": "A", "F0583": "B", "F1304": "BC", "F1295": "C", "F0915": "C",
    "F1355": "C", "F0105": "A", "F0937": "C", "F1221": "B", "F1236": "BC", "F0727": "A",
    "F0582": "B", "F0511": "A", "F0648": "A", "F1071": "A", "F0025": "A", "F0586": "B",
}


def group_of(text, pattern):
    return "+".join(sorted(set(re.findall(pattern, str(text))))) or "none"


def family(r):
    return group_of(r.get("FT family"), r"expert|statistical|ML|LLM")


def domain(r):
    d = group_of(r.get("FT domain"), r"education|ITS/LA|psych/clinical|simulation")
    # A study with empirical data in a domain is counted in that domain; simulation-only stands alone.
    parts = [p for p in d.split("+") if p != "simulation"]
    return "+".join(parts) if parts else d


def entry(r):
    return {
        "id": r["ID"], "title": r.get("Title"), "abstract": r.get("Abstract"),
        "venue": r.get("Venue"), "year": r.get("Year"), "document_type": r.get("Document type"),
        "ft_reasoning": r.get("FT reasoning"), "ft_evidence": r.get("FT evidence"),
        "ft_task": r.get("FT task"), "ft_family": r.get("FT family"),
        "ft_domain": r.get("FT domain"), "ft_data": r.get("FT data"),
    }


def write_batch(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(entry(r), ensure_ascii=False) + "\n")


def prepare():
    _, rows, _ = read_records(SOURCE)
    order = list(rows)
    random.Random(SHUFFLE_SEED).shuffle(order)
    batches = {}
    for start in range(0, len(order), BATCH_SIZE):
        name = f"batch_{start // BATCH_SIZE + 1:03d}"
        chunk = order[start:start + BATCH_SIZE]
        write_batch(BATCH_DIR / f"{name}.jsonl", chunk)
        batches[name] = [r["ID"] for r in chunk]
    by_id = {r["ID"]: r for r in rows}
    write_batch(PILOT_DIR / "pilot.jsonl", [by_id[i] for i in HAND])
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({"input": SOURCE.name, "records": len(rows),
                                    "batch_size": BATCH_SIZE, "shuffle_seed": SHUFFLE_SEED,
                                    "batches": batches}, indent=1), encoding="utf-8")
    print(f"{len(rows)} studies in {len(batches)} batches; pilot of {len(HAND)} hand-sorted studies")


def read_results(path):
    out, problems = {}, []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            problems.append(f"{path.name} line {n}: not JSON")
            continue
        if r.get("group") not in GROUPS:
            problems.append(f"{r.get('id')}: group {r.get('group')!r}")
        if r.get("study_type") not in STUDY_TYPES:
            problems.append(f"{r.get('id')}: study_type {r.get('study_type')!r}")
        bad = set(r.get("evaluation") or []) - EVALUATION
        if bad:
            problems.append(f"{r.get('id')}: unknown evaluation {sorted(bad)}")
        out[r.get("id")] = r
    return out, problems


def pilot():
    results, problems = read_results(PILOT_DIR / "pilot.results.jsonl")
    for p in problems:
        print("PROBLEM", p)
    agree = 0
    for i, hand in HAND.items():
        got = results.get(i, {}).get("group")
        ok = got is not None and got in hand
        agree += ok
        if not ok:
            print(f"  {i} hand {hand} / LLM {got}: {results.get(i, {}).get('reasoning')}")
    print(f"Agreement with the hand sort: {agree} of {len(HAND)}")


def table(rows, key):
    groups = ["A", "B", "C", "H", "U"]
    values = Counter(key(r) for r in rows)
    lines = [f"{'':28s}" + "".join(f"{g:>6s}" for g in groups) + f"{'total':>7s}"]
    for value, _ in values.most_common():
        sub = [r for r in rows if key(r) == value]
        counts = Counter(r["RQ group"] for r in sub)
        lines.append(f"{value[:28]:28s}" + "".join(f"{counts[g]:6d}" for g in groups) + f"{len(sub):7d}")
    return "\n".join(lines)


def evidence_text(ev):
    return " | ".join(map(str, ev)) if isinstance(ev, list) else ev


def report():
    header, rows, template = read_records(SOURCE)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    results, problems = {}, []
    for name, ids in manifest["batches"].items():
        path = RESULT_DIR / f"{name}.jsonl"
        if not path.exists():
            problems.append(f"{name}: no results file")
            continue
        got, p = read_results(path)
        problems += p
        missing = set(ids) - set(got)
        if missing:
            problems.append(f"{name}: missing {sorted(missing)}")
        results.update({i: got[i] for i in ids if i in got})
    # Studies left as U were re-classified from the full text (fulltext_check.md); those results win.
    unresolved = {i for i, g in results.items() if g["group"] == "U"}
    if unresolved:
        if not FULLTEXT_RESULTS.exists():
            problems.append(f"U studies without a full-text check: {sorted(unresolved)}")
        else:
            got, p = read_results(FULLTEXT_RESULTS)
            problems += p
            if set(got) != unresolved:
                problems.append(f"full-text check covers {sorted(got)}, U studies are {sorted(unresolved)}")
            problems += [f"{i}: still U after the full-text check" for i, g in got.items() if g["group"] == "U"]
            for i, g in got.items():
                results[i] = {**g, "source": "full text"}
    if problems:
        sys.exit("Results incomplete or malformed:\n  " + "\n  ".join(problems))
    for r in rows:
        g = results[r["ID"]]
        r.update({"RQ group": g["group"], "Study type": g["study_type"],
                  "Q evaluation": ", ".join(g.get("evaluation") or []) or None,
                  "Group confidence": g["confidence"], "Group reasoning": g["reasoning"],
                  "Group source": g.get("source", "step-4 summary"),
                  "Group evidence": evidence_text(g.get("evidence"))})
    about = about_sheet(
        "Step 4c - RQ contribution groups (sorting only; nothing excluded)",
        "A method study; B instrument with an evaluated Q-matrix; C Q-matrix only a preparatory "
        "step; H hierarchy only. U studies were re-classified from the full text. See "
        "step4c_llm/classification_prompt.md and fulltext_check.md.",
        SOURCE, len(rows), 0, len(rows))
    write_records(OUTPUT, header + COLUMNS, rows, template, about)
    print("Groups:", dict(sorted(Counter(r["RQ group"] for r in rows).items())))
    print("\nBy method family\n" + table(rows, family))
    print("\nBy domain (empirical domain; simulation only if no empirical data)\n" + table(rows, domain))
    print("\nBy study type\n" + table(rows, lambda r: r["Study type"]))
    print(f"\n-> {OUTPUT.name}")


# E11, as adopted: a study is excluded when its contribution isn't a method for generating,
# validating or refining a Q-matrix. That is every group but A.
E11_KEEP = "A"
E11_LABEL = {"B": "an application or instrument study (group B)",
             "C": "an application study; the Q-matrix is a preparatory step (group C)",
             "H": "hierarchy-only; the Q-matrix is taken as given (group H)"}


def e11():
    header, rows, template = read_records(OUTPUT)
    excluded, retained = [], []
    for r in rows:
        if r["RQ group"] == E11_KEEP:
            retained.append(r)
        else:
            excluded.append(mark_excluded(r, "E11", "Step 4c: RQ group (LLM)",
                                          f"E11: not a method study, {E11_LABEL[r['RQ group']]}"))
    check_counts(len(rows), excluded, retained)
    known = {line.strip().lower() for line in TEST_SET.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")}
    lost = [r["ID"] for r in excluded if normalize_doi(r.get("DOI")) in known]
    rule = ("E11, not a method study: exclude a study whose contribution isn't a method for "
            "generating, validating or refining a Q-matrix (step 4c groups B, C and H).")
    extra = [f"Adopted 2026-10-27 with the revised RQ1. Test-set studies excluded by design "
             f"({len(lost)}): {', '.join(lost)}."]
    write_records(E11_EXCLUDED, header, excluded, template,
                  about_sheet("Step 4c - E11 not a method study - excluded", rule, OUTPUT,
                              len(rows), len(excluded), len(retained), extra))
    write_records(E11_RETAINED, header, retained, template,
                  about_sheet("Step 4c - E11 not a method study - retained", rule, OUTPUT,
                              len(rows), len(excluded), len(retained), extra))
    # The share folder holds exactly the retained studies' PDFs, named by record ID.
    SHARE_DIR.mkdir(exist_ok=True)
    keep = {f"{r['ID']}.pdf" for r in retained}
    for old in SHARE_DIR.glob("*.pdf"):
        if old.name not in keep:
            old.unlink()
    for r in retained:
        shutil.copy2(HERE / r["Full text"], SHARE_DIR / f"{r['ID']}.pdf")
    print(f"{len(rows)} in: {len(excluded)} excluded "
          f"{dict(sorted(Counter(r['RQ group'] for r in excluded).items()))}, {len(retained)} retained")
    print(f"Test-set studies excluded by E11: {lost}")
    print(f"{len(keep)} PDFs in {SHARE_DIR.name}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["prepare", "pilot", "report", "e11"])
    {"prepare": prepare, "pilot": pilot, "report": report,
     "e11": e11}[parser.parse_args().command]()
