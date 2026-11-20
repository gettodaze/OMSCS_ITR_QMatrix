#!/usr/bin/env python3
"""Descriptive Q-matrix SLR analysis of an automated extraction workbook.

Run: python qmatrix_analysis.py final_extraction_20261030.xlsx --output results
No API calls, paper verification, outcome pooling, or workbook modifications.
The matching notebook embeds this same implementation and runs independently.
"""
# %% Imports and analysis definitions
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import re
import textwrap
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import openpyxl
import pandas as pd

VERSION = "1.0.0"
PROVENANCE_LABEL = "Automated extraction · not manually verified"
FAMILIES = ["expert_driven", "statistical", "machine_learning", "llm_based"]
FAMILY_LABELS = {
    "expert_driven": "Expert-driven", "statistical": "Statistical",
    "machine_learning": "Machine learning", "llm_based": "LLM-based",
    "unclassified": "Unclassified",
}
DOMAIN_MAP = {
    "educational_measurement": "Educational measurement",
    "intelligent_tutoring_systems": "Tutoring / learning analytics",
    "learning_analytics": "Tutoring / learning analytics",
    "psychological_assessment": "Psychological / clinical [scope flag]",
    "clinical_assessment": "Psychological / clinical [scope flag]",
    "unclassified": "Unspecified",
}
DOMAINS = list(dict.fromkeys(DOMAIN_MAP.values()))
CRITERIA = {
    "q_matrix_recovery": "Q-matrix recovery",
    "attribute_classification_accuracy": "Attribute classification accuracy",
    "classification_reliability": "Classification reliability",
    "statistical_power": "Validation-test power",
    "type_i_error": "Type I error",
    "model_fit": "Model fit",
    "held_out_response_prediction": "Held-out response prediction",
    "expert_q_matrix_agreement": "Expert Q-matrix agreement",
    "expert_or_think_aloud_review": "Expert / think-aloud review",
    "computational_cost": "Computational cost",
    "other": "Other (unresolved category)",
}
THEMES = {
    "small_sample_size": "Small sample size",
    "limited_generalizability": "Limited generalizability",
    "computational_cost": "Computational cost",
    "data_requirements": "Data requirements",
    "model_assumptions": "Model assumptions",
    "interpretability": "Interpretability",
    "lack_of_external_validation": "Lack of external validation",
    "benchmark_limitations": "Benchmark limitations",
    "expert_subjectivity": "Expert subjectivity",
    "reproducibility": "Reproducibility",
    "other": "Other (unresolved category)",
}
CONDITION_FIELDS = [
    "data_type", "sample_size", "number_of_items", "number_of_attributes",
    "response_type", "attribute_structure", "diagnostic_model",
    "misspecification", "item_quality", "benchmark_datasets",
]
CONDITION_LABELS = {
    "sample_size": "Sample size", "number_of_items": "Item count",
    "number_of_attributes": "Attribute count", "response_type": "Response type",
    "attribute_structure": "Attribute structure", "diagnostic_model": "Diagnostic model",
    "misspecification": "Misspecification", "item_quality": "Item quality",
    "benchmark_datasets": "Benchmark datasets", "data_type": "Data type",
}
STATUSES = ["extracted", "not_reported", "not_applicable", "ambiguous"]
DATA_LABELS = {"empirical": "Empirical", "simulated": "Simulated", "mixed": "Mixed", "unclassified": "Unknown"}
COLORS = {"statistical": "#346A91", "machine_learning": "#168B80", "llm_based": "#A36548", "expert_driven": "#A88B32", "unclassified": "#929BA4"}

# Explicit aliases only. Versions remain distinct. Unrecognized strings are exported.
BENCHMARK_ALIASES = {
    "ASSISTments 2009/2010": r"\bassist(?:ments)?[\s_(-]*(?:2009|09)(?!\d)",
    "ASSISTments 2012": r"\bassist(?:ments)?[\s_(-]*(?:2012|12)(?!\d)",
    "ASSISTments 2015": r"\bassist(?:ments)?[\s_(-]*(?:2015|15)(?!\d)",
    "ASSISTments 2017": r"\bassist(?:ments)?[\s_(-]*(?:2017|17)(?!\d)",
    "Junyi": r"\bjunyi(?:academy)?\b",
    "Statics 2011": r"\bstatics[\s_(-]*(?:2011|11)\b",
    "CodeWorkout": r"\bcodeworkout\b",
    "XES3G5M": r"\bxes3g5m\b",
    "ECPE": r"\becpe\b|examination for the certificate of proficiency in english",
    "Fraction subtraction (dataset family)": r"fraction[- ]subtraction|data\.fraction4|\bfracsub\b",
    "TIMSS 2007": r"\btimss[\s_(-]*(?:2007|07)\b",
    "TIMSS 2011": r"\btimss[\s_(-]*(?:2011|11)\b",
    "TIMSS 2019": r"\btimss[\s_(-]*(?:2019|19)\b",
    "PISA 2012": r"\bpisa[\s_(-]*2012\b",
    "PIRLS 2011": r"(?:\bpirls\)?|progress in international reading literacy study)[\s_(-]*2011\b",
    "Algebra 2005": r"\balgebra[\s_(-]*(?:2005|05)\b",
    "Bridge Algebra 2006": r"\bbridge(?:[ -]algebra)?[\s_(-]*(?:2006|06)\b",
    "Python Grids": r"\bpython[ -]grids\b",
    "NIPS Edu": r"\bnips[ _-]edu\b",
    "EdNet": r"\bednet\b",
    "ScienceQA": r"\bscienceqa\b",
    "Thermal Concept Evaluation": r"thermal concept evaluation|\btce\b",
}

# Exact unit aliases, not substring guesses. Units such as 'per item', percentages,
# researchers, annotators, interactions and simulation replications stay separate.
UNIT_ALIASES = {
    "sample_size": {s: "participants" for s in [
        "students", "learners", "participants", "respondents", "examinees",
        "subjects", "individuals", "test takers", "children", "students (n)",
        "respondents (i)", "subjects (n)", "participants (n)",
    ]},
    "number_of_items": {s: "items" for s in [
        "items", "exercises", "problems", "questions", "assessment items", "mcqs",
        "math exercises", "items (j)", "problem items", "unique items", "question items",
    ]},
    "number_of_attributes": {s: "attributes" for s in [
        "skills", "kcs", "attributes", "knowledge concepts", "columns/attributes",
        "concepts", "knowledge components", "knowledge points", "attributes (k)",
        "skills/kcs", "unique skills", "knowledge attributes", "kcs (knowledge components)",
    ]},
}


def values(field):
    """All primary/additional values; retain zero, exclude null only."""
    if not isinstance(field, dict):
        return []
    return [v for v in [field.get("value"), *field.get("other", [])] if v is not None]


def accepted(field):
    return values(field) if field.get("status") == "extracted" else []


def inherited(local, parent):
    """Mirror the exporter: inherit only not_reported method/domain overrides."""
    return parent if local.get("status") == "not_reported" else local


def labels(field):
    return sorted({str(x) for x in accepted(field)})


def data_flags(field):
    vals = set(labels(field))
    if "mixed" in vals:
        vals |= {"empirical", "simulated"}
    return vals & {"empirical", "simulated"}


def data_label(flags):
    return "mixed" if len(flags) == 2 else next(iter(flags), "unclassified")


def normalized_unit(variable, unit):
    raw = (unit or "unspecified").strip().casefold()
    return UNIT_ALIASES.get(variable, {}).get(raw, raw)


def bounds(setting):
    explicit = [x for x in setting.get("values", []) if isinstance(x, (int, float)) and not isinstance(x, bool)]
    interval = setting.get("range") or {}
    lo, hi = interval.get("minimum"), interval.get("maximum")
    # Never turn an open-ended range into a closed one or invent a midpoint.
    lower = min(explicit + ([lo] if lo is not None else [])) if explicit or lo is not None else None
    upper = max(explicit + ([hi] if hi is not None else [])) if explicit or hi is not None else None
    if interval and lo is None:
        lower = None
    if interval and hi is None:
        upper = None
    return lower, upper


def recognized_benchmarks(text):
    return sorted(name for name, pattern in BENCHMARK_ALIASES.items() if re.search(pattern, text, re.I))


def frame(records, columns):
    return pd.DataFrame(records, columns=columns)


# %% Read canonical records, including Excel overflow
def load_source(path):
    """Read only. Canonical Papers JSON preserves statuses, evidence and scopes."""
    path = Path(path)
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    required = {"Papers", "Overflow", "Flat", "Paper Summary", "Experiment Roles"}
    if not required <= set(wb.sheetnames):
        raise ValueError(f"Missing workbook sheets: {sorted(required - set(wb.sheetnames))}")
    sheets = {name: list(wb[name].iter_rows(values_only=True)) for name in wb.sheetnames}
    wb.close()
    chunks = defaultdict(list)
    for row in sheets["Overflow"][1:]:
        if row and row[0]:
            chunks[row[0]].append((int(row[1]), row[2]))
    overflow = {}
    for ref, parts in chunks.items():
        parts.sort()
        if [i for i, _ in parts] != list(range(1, len(parts) + 1)):
            raise ValueError(f"Missing/duplicate overflow chunk: {ref}")
        overflow[ref] = "".join(text for _, text in parts)

    def decode(row, row_number, col):
        raw = overflow.get(f"Papers!{openpyxl.utils.get_column_letter(col + 1)}{row_number}", row[col])
        return json.loads(raw) if raw else {}

    roles = {r[2]: r[3] for r in sheets["Experiment Roles"][1:] if r and r[0]}
    primary = {r[15]: r[16] for r in sheets["Paper Summary"][3:] if r and r[0] is not None}
    papers = []
    ids = set()
    canonical_experiments = set()
    for row_number, row in enumerate(sheets["Papers"][1:], 2):
        if not row or not row[0]:
            continue
        pid = row[0]
        if pid in ids:
            raise ValueError(f"Duplicate Paper ID: {pid}")
        ids.add(pid)
        paper = decode(row, row_number, 3)
        bib = decode(row, row_number, 5).get("fields", {})
        if len(paper["experiments"]) != int(row[2]):
            raise ValueError(f"Experiment count differs from canonical JSON: {pid}")
        for i in range(len(paper["experiments"])):
            canonical_experiments.add(f"{pid}:E{i + 1:03d}")
        papers.append({"paper_id": pid, "source": row[1], "paper": paper,
                       "metadata": bib, "provenance": decode(row, row_number, 4),
                       "representative_id": primary.get(pid)})
    flat_ids = [r[16] for r in sheets["Flat"][1:] if r and r[0] is not None]
    if len(flat_ids) != len(set(flat_ids)) or set(flat_ids) != canonical_experiments:
        raise ValueError("Canonical experiment identities do not match Flat; do not infer row identities.")
    # Verify that E001 etc. identify the corresponding canonical experiment, not display order.
    flat_descriptions = {r[16]: r[18] for r in sheets["Flat"][1:] if r and r[0] is not None}
    for p in papers:
        for i, exp in enumerate(p["paper"]["experiments"]):
            eid = f"{p['paper_id']}:E{i + 1:03d}"
            if flat_descriptions[eid] != exp["description"].get("value"):
                raise ValueError(f"Experiment order differs from canonical IDs: {eid}")
    review_rows = []
    for name in ["Manual Review A", "Manual Review B"]:
        rows = [r for r in sheets.get(name, [])[3:] if r and r[0] is not None]
        review_rows.append({"sheet": name, "papers": len(rows),
                           "papers_with_review_entries": sum(any(v not in (None, "") for v in r[15:53]) for r in rows)})
    return {"papers": papers, "roles": roles, "overflow_cells": len(overflow),
            "review_entries": review_rows, "path": path,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def select_experiments(source, policy):
    if policy not in {"all", "main", "representative"}:
        raise ValueError("experiment_policy must be all, main, or representative")
    selected = []
    fallback_papers = []
    for p in source["papers"]:
        candidates = [(f"{p['paper_id']}:E{i + 1:03d}", e) for i, e in enumerate(p["paper"]["experiments"])]
        if policy == "main":
            chosen = [(eid, e) for eid, e in candidates if source["roles"].get(eid) in {"Primary main experiment", "Additional main experiment"}]
            if not chosen and candidates:
                chosen = [(eid, e) for eid, e in candidates if eid == p["representative_id"]]
                fallback_papers.append(p["paper_id"])
        elif policy == "representative":
            chosen = [(eid, e) for eid, e in candidates if eid == p["representative_id"]]
        else:
            chosen = candidates
        if candidates and not chosen:
            raise ValueError(f"No defensible selection for {p['paper_id']} under {policy}")
        for eid, exp in chosen:
            effective = {k: inherited(exp["method"][k], p["paper"]["method"][k]) for k in ["family", "name", "task"]}
            domain = inherited(exp["domain"], p["paper"]["domain"])
            selected.append({"paper_id": p["paper_id"], "experiment_id": eid, "experiment": exp,
                "families": labels(effective["family"]) or ["unclassified"],
                "tasks": labels(effective["task"]), "domains_raw": labels(domain),
                "domains": sorted({DOMAIN_MAP.get(x, f"Unmapped: {x}") for x in labels(domain)}) or ["Unspecified"],
                "data_flags": data_flags(exp["conditions"]["data_type"]),
                "role": source["roles"].get(eid, "Unclassified"),
                "effective_method": effective, "effective_domain": domain})
    return selected, fallback_papers


# %% Normalize into traceable experiment records and paper-level presences
def normalize(source, policy="all"):
    selected, fallback = select_experiments(source, policy)
    membership = defaultdict(set)
    event_rows, condition_rows, numeric_rows, evaluation_rows, limitation_rows, benchmark_rows = [], [], [], [], [], []
    paper_rows, scope_rows, category_rows = [], [], []

    def add_event(pid, eid, kind, category, families, domains):
        for family in families:
            for domain in domains:
                event_rows.append({"paper_id": pid, "experiment_id": eid, "kind": kind,
                                   "category": category, "family": family, "domain": domain})

    def add_limitations(pid, eid, scope, limits, families, domains):
        for lim in limits:
            cats = labels(lim["theme"])
            desc = values(lim["description"])
            limitation_rows.append({"paper_id": pid, "experiment_id": eid, "scope": scope,
                "themes": cats, "theme_status": lim["theme"]["status"],
                "description_status": lim["description"]["status"], "descriptions": desc,
                "evidence": lim["description"].get("raw_text", [])})
            for category in cats:
                add_event(pid, eid, "limitation", category, families, domains)

    by_paper = defaultdict(list)
    for s in selected:
        by_paper[s["paper_id"]].append(s)
        pid, eid, exp = s["paper_id"], s["experiment_id"], s["experiment"]
        fam, dom = s["families"], s["domains"]
        membership["all", "All papers"].add(pid)
        for family in fam:
            membership["family", family].add(pid)
            for domain in dom:
                add_event(pid, eid, "family", family, [family], [domain])
        for domain in dom:
            membership["domain", domain].add(pid)
        for task in s["tasks"]:
            add_event(pid, eid, "task", task, fam, dom)
        for variable, field in [(f"method.{k}", v) for k, v in s["effective_method"].items()] + [("domain", s["effective_domain"])]:
            category_rows.append({"paper_id": pid, "experiment_id": eid, "field": variable,
                "status": field["status"], "primary_value": field.get("value"),
                "additional_values": field.get("other", []), "evidence": field.get("raw_text", [])})
        dtype = data_label(s["data_flags"])
        for variable in CONDITION_FIELDS:
            field = exp["conditions"][variable]
            condition_rows.append({"paper_id": pid, "experiment_id": eid, "data_type": dtype,
                "variable": variable, "status": field["status"], "has_value": bool(values(field)),
                "values": values(field), "families": fam, "domains": dom, "evidence": field.get("raw_text", [])})
            if variable in ["response_type", "attribute_structure", "diagnostic_model"]:
                for value in accepted(field):
                    category = (value.get("canonical") if value.get("canonical") != "other" else value.get("reported_name")) if isinstance(value, dict) else str(value)
                    add_event(pid, eid, variable, category, fam, dom)
            if variable in ["sample_size", "number_of_items", "number_of_attributes", "misspecification"]:
                for j, setting in enumerate(values(field)):
                    if not isinstance(setting, dict):
                        raise ValueError(f"Invalid numeric setting: {pid} {variable}")
                    lower, upper = bounds(setting)
                    numeric_rows.append({"paper_id": pid, "experiment_id": eid, "data_type": dtype,
                        "variable": variable, "status": field["status"], "slot": "primary" if j == 0 and field.get("value") is not None else "additional",
                        "condition": setting.get("condition"), "raw_unit": setting.get("unit"),
                        "unit": normalized_unit(variable, setting.get("unit")), "explicit_values": setting.get("values", []),
                        "reported_range": setting.get("range"), "lower": lower, "upper": upper,
                        "families": fam, "domains": dom})
        for i, ev in enumerate(exp["evaluations"], 1):
            cats = labels(ev["criterion"])
            evaluation_rows.append({"paper_id": pid, "experiment_id": eid, "evaluation_index": i,
                "criteria": cats, "criterion_status": ev["criterion"]["status"],
                "metrics": values(ev["metrics"]), "metric_status": ev["metrics"]["status"],
                "evidence": ev["criterion"].get("raw_text", [])})
            for category in cats:
                add_event(pid, eid, "criterion", category, fam, dom)
        for raw in accepted(exp["conditions"]["benchmark_datasets"]):
            names = recognized_benchmarks(raw)
            benchmark_rows.append({"paper_id": pid, "experiment_id": eid, "raw_text": raw,
                "recognized_names": names, "has_recognized_name": bool(names)})
            for name in names:
                add_event(pid, eid, "benchmark", name, fam, dom)
        add_limitations(pid, eid, "experiment", exp["limitations"], fam, dom)

    for p in source["papers"]:
        pid, meta = p["paper_id"], p["metadata"]
        exps = by_paper[pid]
        fam = sorted({f for s in exps for f in s["families"]}) or labels(p["paper"]["method"]["family"]) or ["unclassified"]
        dom = sorted({d for s in exps for d in s["domains"]}) or ["Unspecified"]
        raw_dom = sorted({d for s in exps for d in s["domains_raw"]})
        flags = {f for s in exps for f in s["data_flags"]}
        membership["all", "All papers"].add(pid)
        for f in fam:
            membership["family", f].add(pid)
        for d in dom:
            membership["domain", d].add(pid)
        year_string = str(meta.get("year", ""))
        year = int(year_string) if re.fullmatch(r"\d{4}", year_string) else None
        paper_rows.append({"paper_id": pid, "source": p["source"], "title": meta.get("title", ""),
            "doi": meta.get("doi", ""), "year": year, "families": fam, "domains": dom,
            "data_coverage": data_label(flags), "selected_experiments": len(exps),
            "all_experiments": len(p["paper"]["experiments"]), "representative_id": p["representative_id"],
            "venue": meta.get("journal") or meta.get("booktitle") or meta.get("journaltitle") or "Not recorded"})
        if year and year > 2026:
            scope_rows.append({"paper_id": pid, "issue": "bibliographic_year_after_2026", "detail": str(year), "action": "Retained. First-online eligibility date is not established by the bibliographic year."})
        if set(raw_dom) & {"psychological_assessment", "clinical_assessment"}:
            scope_rows.append({"paper_id": pid, "issue": "domain_outside_revised_RQ1", "detail": "; ".join(raw_dom), "action": "Retained with a separate domain label; no automatic exclusion or recoding."})
        if "expert_driven" in fam:
            scope_rows.append({"paper_id": pid, "issue": "expert_label_definition", "detail": "expert_driven", "action": "Original code retained; not automatically broadened to expert-informed."})
        add_limitations(pid, "", "paper", p["paper"]["limitations"], fam, dom)
    events = frame(event_rows, ["paper_id", "experiment_id", "kind", "category", "family", "domain"]).drop_duplicates()
    # All-paper denominator includes records lacking any classifiable field.
    return {"selected": selected, "fallback_papers": fallback, "membership": membership,
        "papers": pd.DataFrame(paper_rows), "events": events,
        "conditions": pd.DataFrame(condition_rows), "numeric": pd.DataFrame(numeric_rows),
        "evaluations": pd.DataFrame(evaluation_rows), "limitations": pd.DataFrame(limitation_rows),
        "benchmarks": pd.DataFrame(benchmark_rows), "scope_flags": frame(scope_rows, ["paper_id", "issue", "detail", "action"]),
        "categorical_fields": pd.DataFrame(category_rows)}


# %% Tables: denominators, missingness, multi-label categories and numeric settings
def frequency(data, kind, categories=None):
    events = data["events"]
    sub = events[events["kind"] == kind]
    cats = list(categories) if categories is not None else sorted(sub["category"].dropna().unique())
    records = []
    for (group_type, group), papers in sorted(data["membership"].items()):
        relevant = sub if group_type == "all" else sub[sub[group_type] == group]
        for cat in cats:
            n = relevant.loc[relevant["category"] == cat, "paper_id"].nunique()
            records.append({"group_type": group_type, "group": group, "category": cat,
                "papers": n, "denominator_papers": len(papers), "percent": 100 * n / len(papers) if papers else np.nan})
    return pd.DataFrame(records)


def coverage_table(data):
    rows = []
    for (group_type, group), members in sorted(data["membership"].items()):
        by_paper = {p: set() for p in members}
        for s in data["selected"]:
            if group_type == "all" or group in s["families" if group_type == "family" else "domains"]:
                by_paper[s["paper_id"]].update(s["data_flags"])
        counts = Counter(data_label(v) for v in by_paper.values())
        for cat in ["empirical", "simulated", "mixed", "unclassified"]:
            rows.append({"group_type": group_type, "group": group, "coverage": cat,
                "papers": counts[cat], "denominator_papers": len(members), "percent": 100 * counts[cat] / len(members) if members else np.nan})
    return pd.DataFrame(rows)


def condition_coverage(data):
    """Statuses are counts of experiment fields, not mutually exclusive paper states."""
    rows = []
    for dtype in ["empirical", "simulated", "mixed", "unclassified"]:
        for variable in CONDITION_FIELDS:
            sub = data["conditions"].query("data_type == @dtype and variable == @variable")
            for status in STATUSES:
                n = int((sub["status"] == status).sum())
                rows.append({"data_type": dtype, "variable": variable, "status": status,
                    "experiment_fields": n, "denominator_experiments": len(sub),
                    "percent": 100 * n / len(sub) if len(sub) else np.nan})
    return pd.DataFrame(rows)


def condition_coverage_by_group(data):
    """Within-family/domain reporting, deduplicated by experiment and field."""
    expanded = []
    for row in data["conditions"].to_dict("records"):
        for group_type, groups in [("family", row["families"]), ("domain", row["domains"])]:
            for group in groups:
                expanded.append({"group_type": group_type, "group": group,
                    **{k: row[k] for k in ["experiment_id", "data_type", "variable", "status"]}})
    df = pd.DataFrame(expanded).drop_duplicates()
    records = []
    for key, sub in df.groupby(["group_type", "group", "data_type", "variable"], sort=True):
        for status in STATUSES:
            n = int((sub.status == status).sum())
            records.append(dict(zip(["group_type", "group", "data_type", "variable"], key),
                status=status, experiment_fields=n, denominator_experiments=len(sub), percent=100 * n / len(sub)))
    return pd.DataFrame(records)


def numeric_tables(data):
    """Summarize explicit settings with one interval per paper/unit/data type/group.

    Never average condition values or use sample size as an analysis weight.
    Median lower/upper bounds describe coverage, not a typical sample size.
    """
    valid = data["numeric"].query("status == 'extracted'").copy()
    expanded = []
    for row in valid.to_dict("records"):
        for gt, groups in [("all", ["All papers"]), ("family", row["families"]), ("domain", row["domains"])]:
            for group in groups:
                expanded.append({**row, "group_type": gt, "group": group})
    columns = ["group_type", "group", "paper_id", "variable", "unit", "data_type", "lower", "upper", "settings", "open_lower", "open_upper"]
    intervals = []
    if expanded:
        df = pd.DataFrame(expanded)
        keys = ["group_type", "group", "paper_id", "variable", "unit", "data_type"]
        for key, sub in df.groupby(keys, dropna=False, sort=True):
            missing_lo, missing_hi = sub["lower"].isna().any(), sub["upper"].isna().any()
            intervals.append(dict(zip(keys, key), lower=np.nan if missing_lo else sub["lower"].min(),
                upper=np.nan if missing_hi else sub["upper"].max(), settings=len(sub),
                open_lower=bool(missing_lo), open_upper=bool(missing_hi)))
    intervals = frame(intervals, columns)
    summary = []
    keys = ["group_type", "group", "variable", "unit", "data_type"]
    for key, sub in intervals.groupby(keys, sort=True, dropna=False):
        entry = dict(zip(keys, key), papers=len(sub))
        for side in ["lower", "upper"]:
            vals = sub[side].dropna()
            entry.update({f"{side}_n": len(vals), f"{side}_min": vals.min(), f"{side}_q25": vals.quantile(.25),
                f"{side}_median": vals.median(), f"{side}_q75": vals.quantile(.75), f"{side}_max": vals.max()})
        summary.append(entry)
    return intervals, pd.DataFrame(summary)


def build_tables(data):
    intervals, summary = numeric_tables(data)
    tables = {
        "paper_inventory": data["papers"], "rq1_method_family": frequency(data, "family", FAMILIES + ["unclassified"]),
        "rq1_tasks": frequency(data, "task", ["generation", "validation", "refinement"]),
        "rq2_data_coverage": coverage_table(data), "rq2_condition_status": condition_coverage(data),
        "rq2_condition_status_by_group": condition_coverage_by_group(data),
        "rq2_response_types": frequency(data, "response_type"), "rq2_attribute_structures": frequency(data, "attribute_structure"),
        "rq2_diagnostic_models": frequency(data, "diagnostic_model"),
        "rq2_numeric_settings": data["numeric"], "rq2_paper_numeric_intervals": intervals, "rq2_numeric_summary": summary,
        "rq2_condition_evidence": data["conditions"],
        "rq3_criteria": frequency(data, "criterion", CRITERIA), "rq3_benchmarks": frequency(data, "benchmark"),
        "rq3_evaluation_evidence": data["evaluations"], "rq3_benchmark_text": data["benchmarks"],
        "rq4_limitation_themes": frequency(data, "limitation", THEMES), "rq4_limitation_evidence": data["limitations"],
        "scope_flags": data["scope_flags"], "categorical_field_evidence": data["categorical_fields"],
        "event_membership": data["events"],
    }
    groups = [{"group_type": gt, "group": group, "papers": len(ids)} for (gt, group), ids in sorted(data["membership"].items())]
    tables["denominators"] = pd.DataFrame(groups)
    tables["publication_years"] = data["papers"].groupby("year", dropna=False).size().rename("papers").reset_index()
    for name, table in tables.items():
        if {"papers", "denominator_papers"} <= set(table.columns):
            assert (table["papers"] <= table["denominator_papers"]).all(), name
            assert (table["papers"] >= 0).all(), name
    assert len(data["papers"]) == data["papers"]["paper_id"].nunique()
    return tables


# %% Figures
def plot_style():
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 12,
        "axes.labelcolor": "#33414C", "text.color": "#243540", "axes.edgecolor": "#CBD3D8",
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": False,
        "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
        "pdf.fonttype": 42, "svg.fonttype": "none"})


def heatmap(ax, table, groups, categories, label_map, group_type="family"):
    sub = table[table["group_type"] == group_type]
    perc = sub.pivot(index="category", columns="group", values="percent").reindex(index=categories, columns=groups)
    counts = sub.pivot(index="category", columns="group", values="papers").reindex(index=categories, columns=groups).fillna(0)
    mat = np.ma.masked_invalid(perc.to_numpy(dtype=float))
    ax.imshow(mat, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    group_labels = []
    denominator_column = next((c for c in ["denominator_papers", "denominator_experiments"] if c in sub), None)
    for g in groups:
        label = "\n".join(textwrap.wrap(FAMILY_LABELS.get(g, g), 17))
        denominator = sub.loc[sub.group == g, denominator_column] if denominator_column else []
        if len(denominator):
            label += f"\n(n={int(denominator.iloc[0])})"
        group_labels.append(label)
    ax.set_xticks(range(len(groups)), group_labels, fontsize=9)
    ax.set_yticks(range(len(categories)), [label_map.get(c, c) for c in categories], fontsize=10)
    for i in range(len(categories)):
        for j in range(len(groups)):
            p = perc.iloc[i, j]
            text = f"{int(counts.iloc[i, j])}\n{p:.0f}%" if pd.notna(p) else "—"
            ax.text(j, i, text, ha="center", va="center", fontsize=9, color="white" if pd.notna(p) and p >= 55 else "#243540")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0, pad=8)


def bar_counts(ax, sub, label_map, color="#346A91", limit=None):
    sub = sub.sort_values(["papers", "category"], ascending=[False, True])
    if limit:
        sub = sub.head(limit)
    sub = sub.iloc[::-1]
    labels_ = [label_map.get(c, c) for c in sub["category"]]
    ax.barh(range(len(sub)), sub["papers"], color=[COLORS.get(c, color) for c in sub["category"]], height=.65)
    ax.set_yticks(range(len(sub)), labels_, fontsize=10)
    mx = max(sub["papers"].max() if len(sub) else 0, 1)
    ax.set_xlim(0, mx * 1.31)
    ax.set_xlabel("Unique papers")
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True, nbins=5))
    for i, (_, r) in enumerate(sub.iterrows()):
        ax.text(r["papers"] + mx * .025, i, f"{int(r['papers'])} ({r['percent']:.0f}%)", va="center", fontsize=9)
    ax.grid(axis="x", alpha=.15)
    ax.set_axisbelow(True)


def save_figure(fig, name, output, title, subtitle, note, n_papers, n_experiments, policy):
    fig.suptitle(title, x=.02, y=.985, ha="left", fontsize=19, weight="bold")
    fig.text(.02, .93, subtitle, fontsize=10.5, color="#536572", va="top")
    fig.text(.02, .035, note, fontsize=9, color="#536572", va="bottom")
    fig.text(.02, .012, f"{PROVENANCE_LABEL} | {n_papers} papers | {n_experiments} selected experiments | policy: {policy}", fontsize=8, color="#7B5B42")
    fig.tight_layout(rect=(.012, .09, .99, .885), w_pad=3)
    paths = {}
    for ext in ["png", "pdf"]:
        path = output / f"{name}.{ext}"
        metadata = {"Software": f"qmatrix_analysis {VERSION}"} if ext == "png" else {"Creator": f"qmatrix_analysis {VERSION}", "CreationDate": None, "ModDate": None}
        fig.savefig(path, dpi=180, metadata=metadata)
        paths[ext] = str(path)
    plt.close(fig)
    return paths


def make_figures(tables, data, output, policy):
    plot_style()
    output.mkdir(parents=True, exist_ok=True)
    n, ne = len(data["papers"]), len(data["selected"])
    groups = [f for f in FAMILIES if ("family", f) in data["membership"]]
    figs = {}
    fig, axes = plt.subplots(1, 2, figsize=(15.5, 8), gridspec_kw={"width_ratios": [1, 1.45]})
    sub = tables["rq1_method_family"].query("group_type == 'all' and category != 'unclassified'")
    bar_counts(axes[0], sub, FAMILY_LABELS)
    axes[0].set_title("Method families across the corpus", loc="left", pad=14)
    heatmap(axes[1], tables["rq1_method_family"], DOMAINS, FAMILIES, FAMILY_LABELS, "domain")
    axes[1].set_title("Family within domain: count / % of domain papers", loc="left", pad=14)
    figs["rq1"] = save_figure(fig, "rq1_method_landscape", output, "RQ1 · Method families and application domains",
        "Primary and additional family labels are retained. Each paper counts at most once in each cell.",
        "Categories overlap. Original expert_driven code retained; it has not been broadened to expert-informed.\nPsychological/clinical and unspecified domains remain visible; no papers were automatically excluded.", n, ne, policy)

    fig, axes = plt.subplots(1, 2, figsize=(15.5, 8), gridspec_kw={"width_ratios": [1.1, 1]})
    cov = tables["rq2_data_coverage"].query("group_type == 'family'")
    bottom = np.zeros(len(groups))
    for cat, color in [("empirical", "#346A91"), ("simulated", "#168B80"), ("mixed", "#A36548"), ("unclassified", "#AAB2B8")]:
        vals = [float(cov.loc[(cov.group == g) & (cov.coverage == cat), "percent"].iloc[0]) for g in groups]
        axes[0].barh(range(len(groups)), vals, left=bottom, label={"empirical": "Empirical only", "simulated": "Simulation only", "mixed": "Both", "unclassified": "Unknown"}[cat], color=color, height=.6)
        for i, val in enumerate(vals):
            count = int(cov.loc[(cov.group == groups[i]) & (cov.coverage == cat), "papers"].iloc[0])
            if val >= 7:
                axes[0].text(bottom[i] + val / 2, i, str(count), color="white", ha="center", va="center", weight="bold")
        bottom += vals
    axes[0].set_yticks(range(len(groups)), [f"{FAMILY_LABELS[g]} (n={len(data['membership']['family', g])})" for g in groups])
    axes[0].set_xlim(0, 100)
    axes[0].set_xlabel("% of papers in method family; labels show paper counts")
    axes[0].set_title("Data coverage across selected experiments", loc="left", pad=14)
    axes[0].legend(loc="upper left", bbox_to_anchor=(0, -.16), ncol=2, frameon=False, fontsize=9)
    cs = tables["rq2_condition_status"].query("status == 'extracted'").copy()
    cs = cs.rename(columns={"data_type": "group", "variable": "category", "experiment_fields": "papers"})
    cs["group_type"] = "data"
    fields = ["sample_size", "number_of_items", "number_of_attributes", "response_type", "attribute_structure", "diagnostic_model", "misspecification", "item_quality"]
    heatmap(axes[1], cs, ["empirical", "simulated", "mixed"], fields, CONDITION_LABELS, "data")
    axes[1].set_xticklabels([f"{DATA_LABELS[d]}\n(n={sum(s['data_flags'] == ({'empirical', 'simulated'} if d == 'mixed' else {d}) for s in data['selected'])})" for d in ["empirical", "simulated", "mixed"]])
    axes[1].set_title("Fields recorded: count / % of experiments", loc="left", pad=14)
    figs["rq2"] = save_figure(fig, "rq2_testing_conditions", output, "RQ2 · Data coverage and testing conditions",
        "Left: unique-paper coverage. Right: extraction reporting by experiment data type; different denominators.",
        "Recorded means status=extracted, not verified. Blank/inapplicable/ambiguous fields remain separate in CSV tables.\nItem quality and misspecification are not required of empirical-only designs; their absence is not a quality score.", n, ne, policy)

    fig, axes = plt.subplots(1, 2, figsize=(16, 10), gridspec_kw={"width_ratios": [1.35, 1]})
    heatmap(axes[0], tables["rq3_criteria"], groups, list(CRITERIA), CRITERIA)
    axes[0].set_title("Evaluation criteria by method family", loc="left", pad=14)
    sub = tables["rq3_benchmarks"].query("group_type == 'all'")
    bar_counts(axes[1], sub, {}, color="#168B80", limit=12)
    axes[1].set_title("Recognized benchmark names: most frequent 12", loc="left", pad=14)
    figs["rq3"] = save_figure(fig, "rq3_evaluation_and_benchmarks", output, "RQ3 · Evaluation practices and benchmarks",
        "Heatmap cells show unique papers and % of family papers. Family–criterion links use the same experiment.",
        "Metric names describe evaluation practice; numerical performance outcomes were not extracted.\nBenchmark aliases are explicit and incomplete. Dataset versions are distinct; fraction subtraction is grouped as a dataset family.", n, ne, policy)

    fig, axes = plt.subplots(1, 2, figsize=(16.5, 10), gridspec_kw={"width_ratios": [1.1, 1.25]})
    sub = tables["rq4_limitation_themes"].query("group_type == 'all'")
    bar_counts(axes[0], sub, THEMES, color="#A36548")
    axes[0].set_title("Papers with each extracted limitation theme", loc="left", pad=14)
    order = sub.sort_values(["papers", "category"], ascending=[False, True])["category"].tolist()
    heatmap(axes[1], tables["rq4_limitation_themes"], groups, order, THEMES)
    axes[1].set_title("Themes by method family", loc="left", pad=14)
    figs["rq4"] = save_figure(fig, "rq4_author_reported_limitations", output, "RQ4 · Extracted author-reported limitations",
        "Paper-level and experiment-level statements are combined; each theme counts once per paper per group.",
        "Counts describe reporting, not the actual prevalence or severity of a weakness. Themes overlap.\nOther is an unresolved category, not a substantive limitation theme; original statements and evidence are exported.", n, ne, policy)

    fig, axes = plt.subplots(1, 3, figsize=(16, 7.8))
    ints = tables["rq2_paper_numeric_intervals"].query("group_type == 'all'")
    specs = [("sample_size", "participants", "Largest reported participant N"), ("number_of_items", "items", "Largest reported item count"), ("number_of_attributes", "attributes", "Largest reported attribute count")]
    for ax, (variable, unit, title) in zip(axes, specs):
        for j, dtype in enumerate(["empirical", "simulated", "mixed"]):
            sub = ints[(ints.variable == variable) & (ints.unit == unit) & (ints.data_type == dtype)].dropna(subset=["upper"])
            vals = sub.loc[sub.upper > 0, "upper"].sort_values().to_numpy()
            if len(vals):
                jitter = np.linspace(-.12, .12, len(vals))
                ax.scatter(np.full(len(vals), j) + jitter, vals, color=["#346A91", "#168B80", "#A36548"][j], alpha=.65, s=24, edgecolors="none")
                ax.hlines(np.median(vals), j - .25, j + .25, color="#243540", lw=2)
            ax.text(j, .99, f"n={len(vals)}", transform=ax.get_xaxis_transform(), ha="center", va="top", fontsize=9)
        ax.set_xticks(range(3), ["Empirical", "Simulated", "Mixed"])
        ax.set_yscale("log")
        ax.set_title(title, loc="left", pad=16)
        ax.grid(axis="y", alpha=.2)
        ax.set_ylabel("Count (log scale)")
    figs["rq2_numeric"] = save_figure(fig, "rq2_numeric_design_sizes", output, "RQ2 appendix · Reported design sizes",
        "One point per paper and experiment data type: the largest upper bound among matching extracted settings.",
        "Black lines show medians of these paper-level maxima, not typical condition sizes. A paper may appear in several panels/groups.\nOnly explicit unit aliases are combined. Open upper bounds and nonpositive values are omitted from this log plot; raw settings remain in CSV.", n, ne, policy)

    fig, ax = plt.subplots(figsize=(11, 6.4))
    yrs = tables["publication_years"].dropna(subset=["year"])
    bars = ax.bar(yrs.year.astype(int).astype(str), yrs.papers, color=["#A36548" if y > 2026 else "#346A91" for y in yrs.year], width=.65)
    ax.bar_label(bars, padding=4)
    ax.set_ylabel("Papers")
    ax.set_ylim(0, max(yrs.papers.max(), 1) * 1.2)
    figs["overview"] = save_figure(fig, "overview_publication_years", output, "Corpus overview · Recorded publication years",
        "Bibliographic years are retained exactly as recorded; this is not a first-online publication-date analysis.",
        "Orange identifies a recorded year after 2026. Such records are flagged, retained, and not silently excluded.", n, ne, policy)
    return figs


# %% Export and command-line entry point
def csv_ready(table):
    table = table.copy()
    for col in table.columns:
        table[col] = table[col].map(lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True) if isinstance(x, (list, dict, tuple, set)) else x)
    return table


def run_analysis(input_path, output_dir="results", experiment_policy="all"):
    """Generate all four RQ outputs, supporting CSVs, figures and a run manifest."""
    source = load_source(input_path)
    data = normalize(source, experiment_policy)
    tables = build_tables(data)
    # Show the effect of selection without pretending different experiments are independent papers.
    sensitivity = []
    for policy in ["all", "main", "representative"]:
        alternative = data if policy == experiment_policy else normalize(source, policy)
        for kind, cats in [("family", FAMILIES), ("criterion", CRITERIA), ("limitation", THEMES)]:
            freq = frequency(alternative, kind, cats).query("group_type == 'all'")
            for r in freq.to_dict("records"):
                sensitivity.append({"experiment_policy": policy, "kind": kind, **r})
    tables["experiment_policy_sensitivity"] = pd.DataFrame(sensitivity)
    tables["review_sheet_entries"] = pd.DataFrame(source["review_entries"])
    output = Path(output_dir)
    table_dir, fig_dir = output / "tables", output / "figures"
    table_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        csv_ready(table).to_csv(table_dir / f"{name}.csv", index=False, float_format="%.6g")
    figures = make_figures(tables, data, fig_dir, experiment_policy)
    manifest = {
        "analysis_version": VERSION, "input_filename": Path(input_path).name, "input_sha256": source["sha256"],
        "verification": "Automated extraction; no manual paper verification performed.",
        "analysis_unit": "Unique paper per category or cell; counts are not independent across overlapping categories.",
        "experiment_policy": experiment_policy, "paper_count": len(data["papers"]),
        "source_experiment_count": sum(len(p["paper"]["experiments"]) for p in source["papers"]),
        "selected_experiment_count": len(data["selected"]), "overflow_cells_restored": source["overflow_cells"],
        "fallback_papers": data["fallback_papers"], "domain_map": DOMAIN_MAP,
        "status_rule": "Only status=extracted enters categorical/quantitative summaries; ambiguous values remain in evidence tables. Extracted does not mean verified.",
        "source_layer": "Canonical Papers JSON, Experiment Roles and Paper Summary identity. Human-review sheets are not used to override canonical extraction.",
        "numeric_rule": "Preserve conditions, units, values and ranges. Summaries are per-paper bounds within data type and unit. No midpoint or outcome imputation.",
        "benchmark_rule": "Explicit regex alias matches; unmatched text retained. Names are not inferred from a general dataset description.",
        "association_rule": "Family/domain/criterion links are formed within an experiment then deduplicated by paper. General paper limitations are linked to that paper's families/domains.",
        "exclusion_rule": "No papers removed for missing labels, domain flags or bibliographic year.",
        "review_sheet_entries": source["review_entries"],
        "versions": {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "matplotlib", "openpyxl"]},
        "python": platform.python_version(), "table_files": [f"tables/{n}.csv" for n in tables],
        "figure_files": [f"figures/{Path(p).name}" for paths in figures.values() for p in paths.values()],
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    notes = [
        "Q-MATRIX SLR: AUTOMATED DESCRIPTIVE ANALYSIS", PROVENANCE_LABEL, "",
        f"Input: {Path(input_path).name}", f"Papers: {manifest['paper_count']}; selected experiments: {manifest['selected_experiment_count']}; policy: {experiment_policy}",
        "", "RQ1: paper counts and overlapping family/domain/task categories.",
        "RQ2: data coverage, status counts, categorical conditions and numeric design settings.",
        "RQ3: evaluation-criterion and recognized-benchmark frequencies; not performance comparisons.",
        "RQ4: extracted author-reported limitation themes and original descriptions.",
        "", "Percentages always use the denominator_papers or denominator_experiments column in the corresponding table.",
        "Paper percentages use every paper in the group, including papers with missing extraction items.",
        "An absent extracted label is not proof that a paper did not use/report a method or criterion.",
        "Primary and additional values are retained. Ambiguous values are available in evidence tables but are not counted as extracted.",
        "Data type 'mixed' in source numeric settings remains mixed; it is not duplicated as empirical and simulated.",
        "Numeric upper-bound plots represent largest recorded design sizes, not typical sample sizes or independent condition observations.",
        "The same script can rerun an automated workbook, but it does not automatically consume later manual-review overrides.",
        "No hypothesis tests, outcome meta-analysis, causal comparison, or inter-rater agreement estimates are computed.",
    ]
    (output / "analysis_notes.txt").write_text("\n".join(notes) + "\n", encoding="utf-8")
    return {"tables": tables, "figures": figures, "manifest": manifest, "data": data}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Path to the extraction .xlsx")
    parser.add_argument("--output", type=Path, default=Path("results"))
    parser.add_argument("--experiment-policy", choices=["all", "main", "representative"], default="all")
    args = parser.parse_args()
    result = run_analysis(args.input, args.output, args.experiment_policy)
    m = result["manifest"]
    print(f"Generated {len(result['figures'])} figures and {len(result['tables'])} CSV tables.")
    print(f"{m['paper_count']} papers; {m['selected_experiment_count']} experiments; {PROVENANCE_LABEL}.")
    print(f"Outputs: {args.output.resolve()}")


if __name__ == "__main__":
    main()
