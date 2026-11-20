#!/usr/bin/env python3
"""
Q-matrix SLR statistics and figures from the completed Full Review sheet.

Run:
    python qmatrix_analysis.py final_sheet_updated.xlsx --output results_final

Outputs:
    tables/             RQ statistics, source values, and review audit
    figures/            Four figures, each saved as PNG and PDF
    summary.txt         Counts and analysis conventions
    run_manifest.json   Input hash, exclusions, and software versions

"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import openpyxl
import pandas as pd


VERSION = "2.1"


EXCLUDED = {
    "wang_determining_2025-1": "E2; paper 38, team exclusion",
}

# Corresponding columns:
# Full Review: O:AG
# Manual Review A/B: P:BA, alternating Value and Note
# Flat: S:BW, alternating Value, Other, and Raw Text
FIELDS = {
    "description": "Description",
    "family": "Primary Family",
    "method": "Method name",
    "task": "Q-Matrix Task",
    "domain": "Application Domain",
    "data_type": "Data Type",
    "sample_size": "Sample Size",
    "items": "Number of Items",
    "attributes": "Number of Attributes",
    "response": "Response Type",
    "structure": "Attribute Structure",
    "model": "Diagnostic Model",
    "misspecification": "Misspecification",
    "item_quality": "Item Quality",
    "benchmarks": "Benchmark Datasets",
    "criteria": "Criteria Used",
    "metrics": "Metrics",
    "themes": "Limitation Themes",
    "limitations": "Limitation Descriptions",
}

FAMILIES = [
    "expert_driven",
    "statistical",
    "machine_learning",
    "llm_based",
]

DOMAIN_MAP = {
    "educational_measurement": "Educational measurement",
    "intelligent_tutoring_systems": "Tutoring / learning analytics",
    "learning_analytics": "Tutoring / learning analytics",
    "psychological_assessment": "Psychological / clinical",
    "clinical_assessment": "Psychological / clinical",
}
DOMAINS = list(dict.fromkeys(DOMAIN_MAP.values()))

CRITERIA = [
    "q_matrix_recovery",
    "attribute_classification_accuracy",
    "classification_reliability",
    "statistical_power",
    "type_i_error",
    "model_fit",
    "held_out_response_prediction",
    "expert_q_matrix_agreement",
    "expert_or_think_aloud_review",
    "computational_cost",
    "other",
]

THEMES = [
    "model_assumptions",
    "limited_generalizability",
    "data_requirements",
    "benchmark_limitations",
    "computational_cost",
    "interpretability",
    "lack_of_external_validation",
    "small_sample_size",
    "expert_subjectivity",
    "reproducibility",
    "other",
]

ALLOWED = {
    "family": FAMILIES,
    "domain": list(DOMAIN_MAP),
    "task": ["generation", "validation", "refinement"],
    "data_type": ["empirical", "simulated", "mixed"],
    "response": ["dichotomous", "polytomous", "mixed", "other"],
    "structure": ["independent", "correlated", "hierarchical", "other"],
    "criteria": CRITERIA,
    "themes": THEMES,
}

LABELS = {
    "expert_driven": "Expert-driven",
    "statistical": "Statistical",
    "machine_learning": "Machine learning",
    "llm_based": "LLM-based",
    "q_matrix_recovery": "Q-matrix recovery",
    "attribute_classification_accuracy": "Attribute classification accuracy",
    "held_out_response_prediction": "Held-out response prediction",
    "expert_q_matrix_agreement": "Agreement with expert Q-matrix",
    "expert_or_think_aloud_review": "Expert / think-aloud review",
    "statistical_power": "Validation-test power",
    "type_i_error": "Type I error",
    "mixed": "Mixed / both",
    "other": "Other",
}

# Explicit dataset aliases. Unmatched descriptions remain in the exports.
BENCHMARKS = {
    "ASSISTments 2009/2010":
        r"\bassist(?:ment|ments)?[\s_(-]*(?:2009|09)(?:10)?\b",
    "ASSISTments 2012/2013":
        r"\bassist(?:ment|ments)?[\s_(-]*(?:2012|1213)\b",
    "ASSISTments 2015":
        r"\bassist(?:ment|ments)?[\s_(-]*(?:2015|15)\b",
    "ASSISTments 2017":
        r"\bassist(?:ment|ments)?[\s_(-]*(?:2017|17)\b",
    "Junyi": r"\bjunyi(?:academy)?\b",
    "Statics 2011":
        r"\bstatics[\s_(-]*(?:2011|11)\b|\bstatics\s*\(fall 2011\)",
    "CodeWorkout": r"\bcodeworkout\b",
    "XES3G5M": r"\bxes3g5m\b",
    "ECPE":
        r"\becpe\b|examination for the certificate of proficiency in english",
    "Fraction subtraction":
        r"fraction[- ]subtraction|data\.fraction4|\b(?:fracsub|frcsub)\b",
    "TIMSS 2007": r"\btimss[\s_(-]*(?:2007|07)\b",
    "TIMSS 2011": r"\btimss[\s_(-]*(?:2011|11)\b",
    "TIMSS 2019": r"\btimss[\s_(-]*(?:2019|19)\b",
    "PISA 2012": r"\bpisa[\s_(-]*2012\b",
    "Algebra 2005": r"\balgebra[\s_(-]*(?:2005|05)\b",
    "Bridge Algebra 2006":
        r"\bbridge(?:[ -]algebra)?[\s_(-]*(?:2006|06)\b",
    "EdNet": r"\bednet\b",
    "Python Grids": r"\bpython[ -]grids\b",
    "NIPS Edu": r"\bnips[ _-]edu\b",
    "Thermal Concept Evaluation": r"thermal concept evaluation|\btce\b",
    "Math1": r"\bmath1\b",
    "Math2": r"\bmath2\b",
    "S-Math": r"\bs-math\b",
    "U-Math": r"\bu-math\b",
    "GSM8K": r"\bgsm8k\b",
    "ASDiv": r"\basdiv\b",
}

# Qualified units such as "items per attribute" remain separate.
UNIT_GROUPS = {
    "sample_size": {
        "participants": (
            "students|learners|participants|respondents|examinees|"
            "subjects|individuals|test takers|children|students (n)|"
            "respondents (i)|subjects (n)|participants (n)"
        )
    },
    "items": {
        "items": (
            "items|exercises|problems|questions|assessment items|"
            "mcqs|math exercises|items (j)|question items"
        )
    },
    "attributes": {
        "attributes": (
            "skills|kcs|attributes|knowledge concepts|concepts|"
            "knowledge components|knowledge points|attributes (k)|"
            "skills/kcs|unique skills|knowledge attributes|"
            "kcs (knowledge components)"
        )
    },
}

UNITS = {
    field: {
        alias: unit
        for unit, aliases in groups.items()
        for alias in aliases.split("|")
    }
    for field, groups in UNIT_GROUPS.items()
}


def text(value):
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def decode(value):
    try:
        return json.loads(text(value))
    except (ValueError, TypeError):
        return value


def status(value):
    s = text(value).casefold()

    if s.startswith("a!=b"):
        return "conflict"
    if not s:
        return "blank"
    if s in {"n/a", "na", "not applicable", "not_applicable"}:
        return "not_applicable"
    if s in {"not reported", "not_reported", "unknown", "null"}:
        return "not_reported"
    if s == "[]":
        return "empty_list"

    return "available"


def tokens(value):
    if status(value) != "available":
        return []

    value = decode(value)

    if isinstance(value, list):
        return [token for item in value for token in tokens(item)]

    if isinstance(value, dict):
        canonical = value.get("canonical", "")
        return [
            value.get("reported_name", "other")
            if canonical == "other" else canonical
        ]

    return [
        part.strip()
        for part in re.split(r"[;,\n]", text(value))
        if part.strip()
    ]


def key(value):
    return re.sub(r"[\s-]+", "_", value.strip().casefold())


def label(value):
    fallback = (
        value.replace("_", " ").capitalize()
        if "_" in value else value
    )
    return LABELS.get(value, fallback)


def numeric_settings(raw, field, notes=""):
    """Parse explicit counts without treating years or labels as observations."""
    obj = decode(raw)
    default_unit = {
        "items": "items",
        "attributes": "attributes",
    }.get(field, "unspecified")

    if isinstance(obj, dict):
        return [obj]

    if isinstance(obj, list):
        if obj and all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            for value in obj
        ):
            return [{
                "values": obj,
                "unit": default_unit,
                "condition": "Explicit list in final sheet",
            }]
        return obj

    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        match = re.search(
            rf"\b{re.escape(text(obj))}\s+"
            r"(students|learners|participants|examinees)\b",
            notes,
            re.I,
        )
        unit = (
            match.group(1)
            if field == "sample_size" and match else default_unit
        )
        return [{
            "values": [obj],
            "unit": unit,
            "condition": "Scalar in final sheet",
        }]

    source = text(raw)
    number = r"(\d[\d,]*(?:\.\d+)?)"
    units = (
        r"(students|learners|participants|examinees|items|questions|"
        r"problems|exercises|KCs|attributes|skills)"
    )

    tail = re.search(units + r"$", source, re.I)
    common_unit = tail.group(1) if tail else default_unit

    original_kcs = source.startswith("Original KCs: ")
    if original_kcs:
        source = source[len("Original KCs: "):]

    settings = []

    for part in source.split(";"):
        part = part.strip()
        match = re.fullmatch(r"K=(\d+): J=(\d+) or (\d+)", part)

        if match and field == "items":
            condition = f"K={match[1]}"
            unit = "items"
            numbers = [int(match[2]), int(match[3])]

        elif (
            match := re.fullmatch(number + r" when K=(\d+)", part)
        ) and field == "items":
            condition = f"K={match[2]}"
            unit = "items"
            numbers = [float(match[1].replace(",", ""))]

        elif match := re.fullmatch(
            r"(.+?):\s*" + number + r"(?:\s+" + units + r")?",
            part,
            re.I,
        ):
            condition = match[1]
            unit = match[3] or common_unit
            numbers = [float(match[2].replace(",", ""))]

        elif original_kcs and (
            match := re.fullmatch(r"(.+?)\s+" + number, part)
        ):
            condition = "Original KCs: " + match[1]
            unit = "KCs"
            numbers = [float(match[2].replace(",", ""))]

        elif match := re.fullmatch(
            number + r" (main units|subunits|retained content records)",
            part,
        ):
            condition = part
            unit = match[2].replace("retained ", "")
            numbers = [float(match[1].replace(",", ""))]

        elif field == "items" and (
            match := re.fullmatch(
                number + r" ((?:before|after) .+)",
                part,
            )
        ):
            condition = match[2]
            unit = "items"
            numbers = [float(match[1].replace(",", ""))]

        else:
            return []

        settings.append({
            "values": numbers,
            "unit": unit,
            "condition": condition,
        })

    return settings


def analyze(path, output, exclusions, require_reviewed=True):
    tables = output / "tables"
    figures = output / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    records = []
    audit = []
    issues = []
    excluded = []

    def add_issue(paper_id, field, problem, raw=""):
        issues.append({
            "paper_id": paper_id,
            "field": field,
            "issue": problem,
            "raw_value": text(raw),
        })

    def save(name, rows, columns=None):
        frame = (
            rows if isinstance(rows, pd.DataFrame)
            else pd.DataFrame(rows, columns=columns)
        )
        frame.to_csv(tables / f"{name}.csv", index=False)
        return frame

    input_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    workbook = openpyxl.load_workbook(path, data_only=True)
    formula_book = openpyxl.load_workbook(path, data_only=False)

    required_sheets = {
        "Full Review",
        "Manual Review A",
        "Manual Review B",
        "Flat",
    }
    missing_sheets = required_sheets - set(workbook.sheetnames)
    if missing_sheets:
        raise ValueError(f"Missing sheets: {sorted(missing_sheets)}")

    full = workbook["Full Review"]

    for index, name in enumerate(FIELDS.values()):
        if full.cell(2, 15 + index).value != name:
            raise ValueError(
                f"Unexpected Full Review layout: expected {name} "
                f"in column {15 + index}."
            )
        for sheet in ("Manual Review A", "Manual Review B"):
            if workbook[sheet].cell(2, 16 + 2 * index).value != name:
                raise ValueError(f"Unexpected layout in {sheet}: {name}")
        if name not in text(
            workbook["Flat"].cell(1, 19 + 3 * index).value
        ):
            raise ValueError(f"Unexpected Flat layout: {name}")

    def review_rows(sheet):
        return {
            text(row[13]): row
            for row in workbook[sheet].iter_rows(
                min_row=4,
                values_only=True,
            )
            if text(row[13])
        }

    review_maps = [
        review_rows("Manual Review A"),
        review_rows("Manual Review B"),
    ]

    flat = {
        (text(row[15]), int(row[1])): row
        for row in workbook["Flat"].iter_rows(
            min_row=2,
            values_only=True,
        )
        if text(row[15])
    }

    seen = set()
    cache_errors = []

    for row in full.iter_rows(min_row=4):
        excel_row = row[0].row
        paper_id = text(row[12].value)

        if not paper_id:
            continue
        if paper_id in seen:
            raise ValueError(f"Duplicate Paper ID: {paper_id}")
        seen.add(paper_id)

        if paper_id in exclusions:
            excluded.append({
                "paper_id": paper_id,
                "paper_index": row[0].value,
                "filename": row[3].value,
                "reason": exclusions[paper_id],
            })
            continue

        review_a, review_b = [
            mapping.get(paper_id, (None,) * 53)
            for mapping in review_maps
        ]

        representative = row[1].value
        representative_conflict = status(representative) == "conflict"

        if representative_conflict:
            add_issue(
                paper_id,
                "representative_experiment",
                "conflict",
                representative,
            )
            baseline = (None,) * 75
        else:
            try:
                baseline = flat[(paper_id, int(representative))]
            except (KeyError, TypeError, ValueError):
                raise ValueError(
                    f"Invalid representative experiment for "
                    f"{paper_id}: {representative}"
                )

        record = {
            "paper_id": paper_id,
            "paper_index": int(row[0].value),
            "filename": row[3].value,
            "title": row[5].value,
            "citation": row[2].value,
            "year": row[7].value,
            "representative_experiment": text(representative),
            "reviewed_fields": 0,
        }

        # Validate cached formulas against the workbook's A/B rules.
        # Full Review values remain authoritative; this does not change them.
        selector = formula_book["Full Review"].cell(excel_row, 2)

        if selector.data_type == "f":
            active = [
                text(review[4]) != "1"
                or any(text(value) for value in review[15:53])
                for review in (review_a, review_b)
            ]
            expected_representative = (
                f"A!=B\nA: {text(review_a[4])}\nB: {text(review_b[4])}"
                if all(active)
                and text(review_a[4]) != text(review_b[4])
                else text(review_a[4] if active[0] else 1)
            )
            if text(representative) != expected_representative:
                cache_errors.append(f"Full Review!B{excel_row}")

        for index, field in enumerate(FIELDS):
            raw = row[14 + index].value

            a_value, a_note = review_a[
                15 + 2 * index:17 + 2 * index
            ]
            b_value, b_note = review_b[
                15 + 2 * index:17 + 2 * index
            ]

            touched_a = bool(text(a_value) or text(a_note))
            touched_b = bool(text(b_value) or text(b_note))

            resolved_a = (
                a_value if text(a_value)
                else baseline[18 + 3 * index]
            )
            resolved_b = (
                b_value if text(b_value)
                else baseline[18 + 3 * index]
            )

            expected = (
                f"A!=B\nA: {text(resolved_a) or '(blank)'}"
                f"\nB: {text(resolved_b) or '(blank)'}"
                if touched_a and touched_b
                and text(resolved_a) != text(resolved_b)
                else text(resolved_a)
            )

            cell = formula_book["Full Review"].cell(
                excel_row, 15 + index
            )

            if (
                cell.data_type == "f"
                and not representative_conflict
                and text(raw) != expected
            ):
                cache_errors.append(
                    f"Full Review!{cell.coordinate}"
                )

            field_status = (
                "conflict"
                if representative_conflict
                else status(raw)
            )

            if field_status == "conflict":
                add_issue(paper_id, field, "conflict", raw)

            if cell.data_type == "e":
                cache_errors.append(
                    f"Full Review!{cell.coordinate}"
                )

            if (
                touched_b
                and not touched_a
                and text(b_value)
                and text(raw) != text(b_value)
            ):
                add_issue(
                    paper_id,
                    field,
                    "B-only edit not adopted by Full Review",
                    b_value,
                )

            record[field] = (
                raw if field_status == "available" else None
            )
            record[field + "_status"] = field_status
            record[field + "_notes"] = " | ".join(
                filter(None, [text(a_note), text(b_note)])
            )
            record["reviewed_fields"] += int(
                touched_a or touched_b
            )

            audit.append({
                "paper_id": paper_id,
                "paper_index": record["paper_index"],
                "field": field,
                "full_cell": cell.coordinate,
                "final_value": text(raw),
                "status": field_status,
                "review_a": touched_a,
                "review_b": touched_b,
                "a_value": text(a_value),
                "a_note": text(a_note),
                "b_value": text(b_value),
                "b_note": text(b_note),
            })

        records.append(record)

    workbook.close()
    formula_book.close()

    save("review_audit", audit)
    save(
        "excluded_papers",
        excluded,
        ["paper_id", "paper_index", "filename", "reason"],
    )

    if cache_errors:
        raise ValueError(
            "Stale or missing Excel formula results at "
            + ", ".join(cache_errors[:12])
            + ". Recalculate in Excel or Google Sheets, "
              "save/download the workbook, then rerun."
        )

    if not records:
        raise ValueError("No included papers were found.")

    # Categories come from Full Review only. Do not recover secondary
    # families or additional experiments from the original automated data.
    for record in records:
        for field, allowed in ALLOWED.items():
            values = {
                key(value) for value in tokens(record[field])
            }
            for unknown in values - set(allowed):
                add_issue(
                    record["paper_id"],
                    field,
                    "unmapped category",
                    unknown,
                )
            record[field + "_set"] = values & set(allowed)

        record["domain_set"] = {
            DOMAIN_MAP[value]
            for value in record["domain_set"]
        }

        if (
            "mixed" in record["data_type_set"]
            or {"empirical", "simulated"}
            <= record["data_type_set"]
        ):
            record["data_type_set"] = {"mixed"}

        model_aliases = {
            "acdm": "A-CDM",
            "a_cdm": "A-CDM",
            "dina": "DINA",
            "gdina": "G-DINA",
            "g_dina": "G-DINA",
            "saturated_g_dina": "G-DINA",
            "dino": "DINO",
            "lcdm": "LCDM",
            "gdm": "GDM",
            "r_rum": "R-RUM",
        }
        record["model_set"] = {
            model_aliases.get(key(value), value)
            for value in tokens(record["model"])
        }

        record["benchmarks_set"] = {
            name
            for name, pattern in BENCHMARKS.items()
            if re.search(
                pattern,
                text(record["benchmarks"]),
                re.I,
            )
        }
        if record["benchmarks"] and not record["benchmarks_set"]:
            add_issue(
                record["paper_id"],
                "benchmarks",
                "no named-dataset alias matched",
                record["benchmarks"],
            )

    def memberships(record):
        return [("overall", "All papers")] + [
            (kind, value)
            for kind in ("family", "domain")
            for value in sorted(record[kind + "_set"])
        ]

    group_list = (
        [("overall", "All papers")]
        + [("family", family) for family in FAMILIES]
        + [("domain", domain) for domain in DOMAINS]
    )

    def counts(field, categories=None):
        if categories is None:
            categories = sorted(
                set().union(
                    *(record[field + "_set"] for record in records)
                )
            )

        rows = []

        for kind, group in group_list:
            members = [
                record
                for record in records
                if (kind, group) in memberships(record)
            ]
            denominator = len(members)

            for category in categories:
                count = sum(
                    category in record[field + "_set"]
                    for record in members
                )
                rows.append({
                    "group_type": kind,
                    "group": group,
                    "category": category,
                    "papers": count,
                    "denominator_papers": denominator,
                    "percent": (
                        100 * count / denominator
                        if denominator else None
                    ),
                    "papers_with_recorded_category": sum(
                        bool(record[field + "_set"])
                        for record in members
                    ),
                })

        return pd.DataFrame(rows, columns=[
            "group_type",
            "group",
            "category",
            "papers",
            "denominator_papers",
            "percent",
            "papers_with_recorded_category",
        ])

    jobs = {
        "rq1_method_family": ("family", FAMILIES),
        "rq1_tasks": ("task", ALLOWED["task"]),
        "rq2_data_types": ("data_type", ALLOWED["data_type"]),
        "rq2_response_types": ("response", ALLOWED["response"]),
        "rq2_attribute_structures": (
            "structure", ALLOWED["structure"]
        ),
        "rq2_diagnostic_models": ("model", None),
        "rq3_criteria": ("criteria", CRITERIA),
        "rq3_benchmarks": ("benchmarks", None),
        "rq4_limitation_themes": ("themes", THEMES),
    }
    results = {
        name: save(name, counts(*specification))
        for name, specification in jobs.items()
    }

    save("paper_inventory", [
        {
            field: value
            for field, value in record.items()
            if not field.endswith("_set")
        }
        for record in records
    ])

    save("group_membership", [
        {
            "paper_id": record["paper_id"],
            "group_type": kind,
            "group": group,
        }
        for record in records
        for kind, group in memberships(record)
    ])

    save("field_coverage", [
        {
            "group_type": kind,
            "group": group,
            "field": field,
            "status": field_status,
            "papers": sum(
                record[field + "_status"] == field_status
                for record in records
                if (kind, group) in memberships(record)
            ),
        }
        for kind, group in group_list
        for field in FIELDS
        for field_status in (
            "available",
            "blank",
            "not_reported",
            "not_applicable",
            "empty_list",
            "conflict",
        )
    ])

    # Keep numeric settings separated by data type and compatible unit.
    numeric_rows = []

    for record in records:
        for field in ("sample_size", "items", "attributes"):
            raw = record[field]
            if raw is None:
                continue

            settings = numeric_settings(
                raw,
                field,
                record[field + "_notes"],
            )

            if not settings:
                add_issue(
                    record["paper_id"],
                    field,
                    "unparsed numeric setting; retained without pooling",
                    raw,
                )

            for setting in settings:
                if (
                    not isinstance(setting, dict)
                    or not ({"values", "range"} & set(setting))
                ):
                    add_issue(
                        record["paper_id"],
                        field,
                        "unparsed numeric setting; retained without pooling",
                        raw,
                    )
                    continue

                values = setting.get("values") or []
                interval = setting.get("range") or {}

                if not isinstance(values, list) or not isinstance(
                    interval, dict
                ):
                    add_issue(
                        record["paper_id"],
                        field,
                        "invalid numeric structure",
                        raw,
                    )
                    continue

                numbers = values + [
                    value
                    for value in (
                        interval.get("minimum"),
                        interval.get("maximum"),
                    )
                    if value is not None
                ]

                if not numbers or any(
                    not isinstance(value, (int, float))
                    or isinstance(value, bool)
                    or not math.isfinite(value)
                    or value < 0
                    for value in numbers
                ):
                    add_issue(
                        record["paper_id"],
                        field,
                        "invalid numeric setting",
                        raw,
                    )
                    continue

                if (
                    interval.get("minimum") is not None
                    and interval.get("maximum") is not None
                    and interval["minimum"] > interval["maximum"]
                ):
                    add_issue(
                        record["paper_id"],
                        field,
                        "inverted numeric interval",
                        raw,
                    )
                    continue

                lower, upper = min(numbers), max(numbers)

                if interval and interval.get("minimum") is None:
                    lower = None
                if interval and interval.get("maximum") is None:
                    upper = None

                unit = (
                    text(setting.get("unit")).casefold()
                    or "unspecified"
                )
                unit = UNITS[field].get(unit, unit)
                data_type = next(
                    iter(record["data_type_set"]),
                    "unknown",
                )

                for kind, group in memberships(record):
                    numeric_rows.append({
                        "paper_id": record["paper_id"],
                        "group_type": kind,
                        "group": group,
                        "variable": field,
                        "data_type": data_type,
                        "unit": unit,
                        "lower": lower,
                        "upper": upper,
                        "condition": setting.get("condition", ""),
                        "raw_value": text(raw),
                    })

    numeric_frame = save(
        "rq2_numeric_settings",
        numeric_rows,
        [
            "paper_id",
            "group_type",
            "group",
            "variable",
            "data_type",
            "unit",
            "lower",
            "upper",
            "condition",
            "raw_value",
        ],
    )

    numeric_keys = [
        "group_type",
        "group",
        "variable",
        "data_type",
        "unit",
    ]
    numeric_summaries = []

    for group, subset in numeric_frame.groupby(
        numeric_keys,
        dropna=False,
    ):
        # One maximum per paper. An open upper bound remains unknown.
        maxima = subset.groupby("paper_id")["upper"].agg(
            lambda values: (
                values.max()
                if values.notna().all()
                else float("nan")
            )
        )
        usable = maxima.dropna()

        numeric_summaries.append(dict(
            zip(numeric_keys, group),
            papers_with_settings=len(maxima),
            n_numeric=len(usable),
            median_paper_max=usable.median(),
            q25_paper_max=usable.quantile(.25),
            q75_paper_max=usable.quantile(.75),
            min_paper_max=usable.min(),
            max_paper_max=usable.max(),
        ))

    save(
        "rq2_numeric_summary",
        numeric_summaries,
        numeric_keys + [
            "papers_with_settings",
            "n_numeric",
            "median_paper_max",
            "q25_paper_max",
            "q75_paper_max",
            "min_paper_max",
            "max_paper_max",
        ],
    )

    evidence_exports = {
        "rq2_condition_evidence": [
            "sample_size",
            "items",
            "attributes",
            "misspecification",
            "item_quality",
        ],
        "rq3_evaluation_evidence": [
            "benchmarks",
            "criteria",
            "metrics",
        ],
        "rq4_limitation_evidence": [
            "themes",
            "limitations",
        ],
    }

    for name, fields in evidence_exports.items():
        save(name, [
            {
                "paper_id": record["paper_id"],
                "field": entry["field"],
                "raw_value": entry["final_value"],
                "status": entry["status"],
                "families": "; ".join(
                    sorted(record["family_set"])
                ),
                "domains": "; ".join(
                    sorted(record["domain_set"])
                ),
            }
            for record in records
            for entry in audit
            if entry["paper_id"] == record["paper_id"]
            and entry["field"] in fields
        ])

    # These are paper-summary co-occurrences, not claims that each
    # criterion was applied to every dataset named in the paper.
    cooccurrence_rows = []

    for record in records:
        for dataset in sorted(record["benchmarks_set"]):
            for criterion in sorted(record["criteria_set"]):
                for kind, group in memberships(record):
                    cooccurrence_rows.append({
                        "paper_id": record["paper_id"],
                        "group_type": kind,
                        "group": group,
                        "benchmark": dataset,
                        "criterion": criterion,
                    })

    cooccurrence = pd.DataFrame(
        cooccurrence_rows,
        columns=[
            "paper_id",
            "group_type",
            "group",
            "benchmark",
            "criterion",
        ],
    )

    save(
        "rq3_benchmark_criteria",
        cooccurrence.groupby([
            "group_type",
            "group",
            "benchmark",
            "criterion",
        ])["paper_id"].nunique().reset_index(name="papers"),
    )

    save(
        "issues",
        issues,
        ["paper_id", "field", "issue", "raw_value"],
    )

    paper_count = len(records)
    untouched = [
        record["paper_index"]
        for record in records
        if record["reviewed_fields"] == 0
    ]
    partially_marked = sum(
        record["reviewed_fields"] < len(FIELDS)
        for record in records
    )
    conflicts = sum(
        entry["status"] == "conflict"
        for entry in audit
    )

    # Do not require an individual mark in every field.
    # Retain checks for untouched papers and unresolved data decisions.
    provisional = bool(
        untouched
        or conflicts
        or any(
            entry["issue"] in {
                "unmapped category",
                "B-only edit not adopted by Full Review",
            }
            for entry in issues
        )
    )

    report = [
        f"Included papers: {paper_count}.",
        f"Excluded rows present in this upload: {len(excluded)}.",
        f"Papers with any review entry: "
        f"{paper_count - len(untouched)}/{paper_count}.",
        f"Papers with all {len(FIELDS)} fields marked: "
        f"{paper_count - partially_marked}/{paper_count}.",
        f"Paper indices without review entries: {untouched}.",
        f"Cells containing unresolved conflict markers: {conflicts}.",
        "",
        "Analysis conventions",
        "Source: Full Review, one selected summary per paper.",
        "Primary-family values are used as recorded in Full Review.",
        "Secondary values and other experiments are not merged "
        "from the original automated extraction.",
        "Each paper counts once per category and group.",
        "Explicit multi-value categories may overlap.",
        "Percentages use all included papers in the relevant group.",
        "Blank, disputed, or unmapped fields contribute no category "
        "values but remain in group denominators.",
        "Numeric summaries use one maximum per paper within each "
        "compatible unit and data type.",
        "Mixed data types remain separate in numeric summaries.",
        "Open upper bounds are excluded from finite-maximum summaries.",
        "Missing values are not imputed.",
        "Explicit labelled numeric text is parsed conservatively.",
        "Unparsed numeric entries remain in the evidence and issue exports.",
        "Misspecification and item-quality descriptions are preserved "
        "without pooling incompatible quantities.",
        "Benchmark aliases are explicit and not exhaustive.",
        "Benchmark/criterion links represent paper-summary co-occurrence.",
        "Review markers describe recorded activity, not an independent "
        "assessment of verification quality.",
        "No hypothesis tests, causal estimates, or pooled method-performance "
        "comparisons are performed.",
        "",
        "Category totals",
    ]

    for field in ("family", "domain", "data_type"):
        categories = sorted(
            set().union(
                *(record[field + "_set"] for record in records)
            )
        )
        report.append(
            field + ": " + "; ".join(
                f"{category}="
                f"{sum(category in r[field + '_set'] for r in records)}"
                for category in categories
            )
        )

    (output / "summary.txt").write_text(
        "\n".join(report) + "\n",
        encoding="utf-8",
    )

    manifest = {
        "version": VERSION,
        "input_file": path.name,
        "input_sha256": input_hash,
        "included_papers": paper_count,
        "exclusions": exclusions,
        "unit_of_analysis": "Full Review paper summary",
        "papers_without_review_entries": untouched,
        "conflict_cells": conflicts,
        "provisional": provisional,
        "python_packages": {
            "pandas": pd.__version__,
            "openpyxl": openpyxl.__version__,
            "matplotlib": matplotlib.__version__,
        },
    }
    (output / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print("\n".join(report[:6]))

    if require_reviewed and provisional:
        raise SystemExit(
            "\nFinal figures were not generated because the workbook "
            "still contains untouched papers or unresolved data decisions. "
            "See tables/review_audit.csv and tables/issues.csv. "
            "Use --allow-incomplete only for a provisional preview."
        )

    plt.rcParams.update({
        "font.size": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "savefig.facecolor": "white",
    })

    def draw_panel(
        axis,
        frame,
        group_type,
        groups,
        categories,
        title,
    ):
        colors = ["#246A91", "#DB8643", "#2A917C", "#9967A7"]
        bar_height = .8 / max(len(groups), 1)

        for index, group in enumerate(groups):
            subset = frame[
                (frame.group_type == group_type)
                & (frame.group == group)
            ].set_index("category")

            denominator = (
                int(subset.denominator_papers.iloc[0])
                if len(subset) else 0
            )

            positions = [
                j - .4 + bar_height / 2 + index * bar_height
                for j in range(len(categories))
            ]
            percentages = [
                float(subset.loc[category, "percent"])
                if denominator else 0
                for category in categories
            ]

            axis.barh(
                positions,
                percentages,
                height=bar_height * .9,
                color=colors[index % len(colors)],
                label=f"{label(group)} (N={denominator})",
            )

            for position, percentage, category in zip(
                positions, percentages, categories
            ):
                count = (
                    int(subset.loc[category, "papers"])
                    if len(subset) else 0
                )
                axis.text(
                    percentage + .7,
                    position,
                    str(count) if denominator else "NA",
                    va="center",
                    fontsize=9,
                )

        axis.set_yticks(
            range(len(categories)),
            [label(category) for category in categories],
        )
        axis.invert_yaxis()
        axis.set_xlim(0, 110)
        axis.set_xticks([0, 25, 50, 75, 100])
        axis.set_xlabel(
            "Papers in group (%) · labels show paper counts"
        )
        axis.set_title(title, loc="left", pad=14)
        axis.xaxis.grid(True, alpha=.18)
        axis.set_axisbelow(True)
        axis.legend(
            loc="upper center",
            bbox_to_anchor=(.5, -.14),
            ncol=2,
            frameon=False,
            fontsize=10,
        )

    benchmark_table = results["rq3_benchmarks"]
    top_benchmarks = (
        benchmark_table[
            benchmark_table.group_type == "overall"
        ]
        .sort_values(
            ["papers", "category"],
            ascending=[False, True],
        )
        .head(8)
        .category.tolist()
    )

    figure_specs = [
        (
            "rq1_method_landscape",
            [
                (
                    "rq1_method_family",
                    "domain",
                    DOMAINS[:2],
                    FAMILIES,
                    "RQ1 · Primary method families by domain",
                )
            ],
        ),
        (
            "rq2_testing_conditions",
            [
                (
                    "rq2_data_types",
                    "family",
                    FAMILIES,
                    ALLOWED["data_type"],
                    "RQ2 · Data type by primary family",
                ),
                (
                    "rq2_data_types",
                    "domain",
                    DOMAINS,
                    ALLOWED["data_type"],
                    "Data type by domain",
                ),
            ],
        ),
        (
            "rq3_evaluation_and_benchmarks",
            [
                (
                    "rq3_criteria",
                    "family",
                    FAMILIES,
                    CRITERIA,
                    "RQ3 · Evaluation criteria by primary family",
                ),
                (
                    "rq3_benchmarks",
                    "domain",
                    DOMAINS,
                    top_benchmarks,
                    "Named benchmarks by domain",
                ),
            ],
        ),
        (
            "rq4_author_reported_limitations",
            [
                (
                    "rq4_limitation_themes",
                    "family",
                    FAMILIES,
                    THEMES,
                    "RQ4 · Limitation themes by primary family",
                ),
                (
                    "rq4_limitation_themes",
                    "domain",
                    DOMAINS,
                    THEMES,
                    "Limitation themes by domain",
                ),
            ],
        ),
    ]

    for filename, panels in figure_specs:
        heights = [
            max(3.8, len(specification[3]) * .6 + 1.5)
            for specification in panels
        ]

        figure, axes = plt.subplots(
            len(panels),
            1,
            figsize=(12, sum(heights) + 1.2),
            squeeze=False,
            gridspec_kw={"height_ratios": heights},
        )

        for axis, specification in zip(axes[:, 0], panels):
            table_name, group_type, groups, categories, title = specification
            draw_panel(
                axis,
                results[table_name],
                group_type,
                groups,
                categories,
                title,
            )

        footer = f"Included studies: {paper_count}"
        if provisional:
            footer += " · Provisional snapshot"

        figure.text(
            .5,
            .008,
            footer,
            ha="center",
            fontsize=10,
        )
        figure.tight_layout(
            rect=(0, .045, 1, 1),
            h_pad=4,
        )

        for extension in ("png", "pdf"):
            figure.savefig(
                figures / f"{filename}.{extension}",
                dpi=300,
                bbox_inches="tight",
            )

        plt.close(figure)

    if hashlib.sha256(path.read_bytes()).hexdigest() != input_hash:
        raise RuntimeError(
            "The input workbook changed during analysis. "
            "Rerun using a stable saved copy."
        )

    print(
        f"\nSaved tables, four PNG/PDF figures, summary, and manifest to:\n"
        f"{output.resolve()}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results_final"),
    )
    parser.add_argument(
        "--exclude-paper",
        action="append",
        default=[],
        help="Additional confirmed Paper ID to exclude; repeat as needed.",
    )
    parser.add_argument(
        "--allow-incomplete",
        action="store_true",
        help="Generate provisional figures before reviews are finished.",
    )
    args = parser.parse_args()

    exclusions = dict(EXCLUDED)
    exclusions.update({
        paper_id: "Additional user-specified exclusion"
        for paper_id in args.exclude_paper
    })

    analyze(
        args.workbook,
        args.output,
        exclusions,
        require_reviewed=not args.allow_incomplete,
    )