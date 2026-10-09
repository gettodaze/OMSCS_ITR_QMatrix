"""Parse input/input.csv into one example-shaped CSV per database.

Run: python parse_records.py
Defaults: input/input.csv -> output/yyyymmdd_hhss/<database>.csv
Each record belongs to its alphabetically first database (case-insensitive).
Unavailable bibliographic fields remain blank; no external lookup is performed.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Mapping


class Label(str, Enum):
    """Descriptive categories from the Check-in 2 working doc (RQ1–RQ2)."""

    EXPERT_DRIVEN = "expert-driven"
    STATISTICAL = "statistical"
    MACHINE_LEARNING = "machine learning"
    LLM_BASED = "LLM-based"
    EDUCATIONAL_MEASUREMENT = "educational measurement"
    ITS_LEARNING_ANALYTICS = "intelligent tutoring systems and learning analytics"
    PSYCHOLOGICAL_CLINICAL = "psychological and clinical assessment"
    GENERATION = "Q-matrix generation"
    VALIDATION = "Q-matrix validation"
    REFINEMENT = "Q-matrix refinement"
    SIMULATED = "simulated data"
    EMPIRICAL = "empirical data"

    def __str__(self) -> str:
        return self.value


# Parse the source's list fields and represent each input row.
def split_list(value: str) -> tuple[str, ...]:
    """Parse the input's semicolon-separated fields."""
    return tuple(part.strip() for part in value.split(";") if part.strip())


@dataclass(frozen=True)
class SourceRecord:
    """All columns from the original record; parsed lists are immutable."""

    id: str
    sept_id: str
    year: int | None
    title: str
    authors: tuple[str, ...]
    venue: str
    document_type: str
    databases: tuple[str, ...]
    doi: str
    abstract: str
    keywords: tuple[str, ...]
    language: str
    screening_flags: str
    stage: str
    assigned_to: str
    screener_1: str
    screener_2: str
    decision: str
    exclusion_reason: str
    excluded_at_stage: str
    notes: str
    labels: list[Label] = field(default_factory=list)

    @classmethod
    def from_csv_row(cls, row: Mapping[str, str]) -> SourceRecord:
        year = row["Year"].strip()
        return cls(
            id=row["ID"],
            sept_id=row["Sept ID"],
            year=int(year) if year else None,
            title=row["Title"],
            authors=split_list(row["Authors"]),
            venue=row["Venue"],
            document_type=row["Document type"],
            databases=split_list(row["Found in"]),
            doi=row["DOI"],
            abstract=row["Abstract"],
            keywords=split_list(row["Keywords"]),
            language=row["Language"],
            screening_flags=row["Screening flags"],
            stage=row["Stage"],
            assigned_to=row["Assigned to"],
            screener_1=row["Screener 1"],
            screener_2=row["Screener 2"],
            decision=row["Decision"],
            exclusion_reason=row["Exclusion reason"],
            excluded_at_stage=row["Excluded at stage"],
            notes=row["Notes"],
            labels=[Label(value) for value in split_list(row.get("Labels", ""))],
        )

    @property
    def database(self) -> str:
        if not self.databases:
            raise ValueError(f"Record {self.id!r} has no database in 'Found in'")
        return min(self.databases, key=lambda name: (name.casefold(), name))


# Convert source rows to the example's output columns.
@dataclass(frozen=True)
class OutputRecord:
    """Column names and order match input/excel-example.csv."""

    key: str
    title: str
    authors: str
    journal: str
    issn: str
    volume: str
    issue: str
    pages: str
    year: str
    publisher: str
    url: str
    abstract: str
    notes: str
    doi: str
    keywords: str

    @classmethod
    def from_record(cls, record: SourceRecord) -> OutputRecord:
        """Convert an old-format record to the new format.

        Remove trailing numeric author identifiers and use the example's
        ' and ' separator. Venue maps to journal, including conference venues.
        Source-only screening metadata remains available on SourceRecord.
        """
        authors = tuple(re.sub(r"\s*\(\d+\)$", "", author) for author in record.authors)
        return cls(
            key=record.id,
            title=record.title,
            authors=" and ".join(authors),
            journal=record.venue,
            issn="",
            volume="",
            issue="",
            pages="",
            year=str(record.year) if record.year is not None else "",
            publisher="",
            url="",
            abstract=record.abstract,
            notes=(
                f"{record.notes} | Labels: {'; '.join(label.value for label in record.labels)}"
                if record.notes else f"Labels: {'; '.join(label.value for label in record.labels)}"
            ) if record.labels else record.notes,
            doi=record.doi,
            keywords=";".join(record.keywords),
        )


def read_records(path: Path) -> list[SourceRecord]:
    import pandas as pd

    # Read strings and preserve empty fields instead of converting them to NaN.
    frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    return [SourceRecord.from_csv_row(row) for row in frame.to_dict(orient="records")]


LABEL_PATTERNS: dict[Label, str] = {
    Label.EXPERT_DRIVEN: r"\b(?:expert(?:s| driven| specified| review| judgment| judgement)?|think aloud|delphi|manual annotation)\b",
    Label.STATISTICAL: r"\b(?:statistical|bayesian|regulariz\w*|regularis\w*|logistic regression|factor analysis|structural equation|nonnegative matrix factorization|non negative matrix factorization|nmf|learning factors analysis|lfa|wald|likelihood ratio)\b",
    Label.MACHINE_LEARNING: r"\b(?:machine learning|deep learning|neural\w*|random forests?|support vector|gradient boosting|graph attention|clustering)\b",
    Label.LLM_BASED: r"\b(?:large language models?|llms?|gpt\w*|chatgpt|generative ai|prompting|zero shot|few shot)\b",
    Label.EDUCATIONAL_MEASUREMENT: r"\b(?:educational (?:measurement|assessment)|psychometric\w*|achievement tests?|assessment items?|examinees?|dina|g dina|dino|lcdm)\b",
    Label.ITS_LEARNING_ANALYTICS: r"\b(?:intelligent tutor\w*(?: systems?)?|learning analytics|knowledge tracing|educational data mining|learning factors analysis|skill tag\w*|knowledge (?:component|concept)\w*|assistments?|assist2009|eedi)\b",
    Label.PSYCHOLOGICAL_CLINICAL: r"\b(?:clinical|psychological assessment|psychiatr\w*|psychopatholog\w*|mental health|symptom\w*|dsm|personality|disorder\w*|depress\w*|anxiety|non cognitive|noncognitive|socio emotional|social emotional)\b",
    Label.SIMULATED: r"\b(?:simulat\w*|monte carlo|synthetic data)\b",
    Label.EMPIRICAL: r"\b(?:empirical|real (?:world|data)|observed (?:data|responses)|student (?:responses?|interactions?)|response data|benchmark datasets?)\b",
}

TASK_PATTERNS: dict[Label, str] = {
    Label.GENERATION: r"\b(?:generat\w*|construct\w*|discover\w*|specif\w*|estimat\w*|extract\w*|tagg\w*|attribution|learn\w*)\b",
    Label.VALIDATION: r"\b(?:validat\w*|evaluat\w*|check\w*|test\w*|assess\w*)\b",
    Label.REFINEMENT: r"\b(?:refin\w*|revis\w*|correct\w*|updat\w*|repair\w*)\b",
}


def get_labels(record: SourceRecord) -> list[Label]:
    """Suggest labels for a legacy candidate record using the shared rules."""
    return get_labels_from_text(record.title, record.abstract, record.keywords)


def get_labels_from_text(title: str, abstract: str, keywords: tuple[str, ...]) -> list[Label]:
    """Suggest descriptive labels using title, abstract, and keywords.

    These keyword heuristics follow the working doc, not final eligibility
    decisions. Mentions can describe prior work; full-text review is needed
    to confirm a study's method and domain. Missing evidence gets no label.
    """
    text = "\n".join((title, abstract, "; ".join(keywords)))
    text = re.sub(r"[-‐‑–—_]", " ", text.casefold())
    text = re.sub(r"[^\S\n]+", " ", text)
    matched = {label for label, pattern in LABEL_PATTERNS.items() if re.search(pattern, text)}
    # Require task terms near a Q-matrix or an equivalent mapping, in the
    # same sentence/keyword, instead of labeling every mention of evaluation.
    mapping = r"\b(?:q matri(?:x|ces)|knowledge component\w*(?: models?)?|skill (?:models?|tags?|tagging)|knowledge concept tagging|item skill)\b"
    for sentence in re.split(r"[.!?;\n]", text):
        for target in re.finditer(mapping, sentence):
            context = sentence[max(0, target.start() - 100):target.end() + 100]
            for label, pattern in TASK_PATTERNS.items():
                if re.search(pattern, context):
                    matched.add(label)
    # Enum order makes output stable; a set deduplicates repeated matches.
    return [label for label in Label if label in matched]


def update_records(records: list[SourceRecord]) -> list[SourceRecord]:
    """Return copies with newly computed labels, preserving source notes."""
    return [replace(record, labels=get_labels(record)) for record in records]


def write_records(records: list[SourceRecord], output_root: Path) -> Path:
    import pandas as pd

    # Assign each record to its alphabetically first database and convert it.
    grouped: dict[str, list[OutputRecord]] = defaultdict(list)
    for record in records:
        grouped[record.database].append(OutputRecord.from_record(record))

    # Create the requested timestamp folder (hhss means hour and second).
    directory = output_root / datetime.now().strftime("%Y%m%d_%H%S")
    directory.mkdir(parents=True, exist_ok=False)

    # Write one CSV per database, preserving the output dataclass's column order.
    for database, rows in grouped.items():
        frame = pd.DataFrame([asdict(row) for row in rows])
        frame.to_csv(directory / f"{database}.csv", index=False, encoding="utf-8")
    return directory


def main() -> None:
    # Parse command-line paths.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, default=Path("input/input.csv"))
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()

    # Read, convert, and write the records.
    records = read_records(args.input)
    records = update_records(records)
    directory = write_records(records, args.output)
    print(f"Wrote {len(records)} records to {directory}")


if __name__ == "__main__":
    main()
