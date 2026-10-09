"""Label native RIS, NBIB and EndNote exports without requiring the old candidate CSV."""
from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Callable, Iterable, Mapping
import csv
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from pathlib import Path
from types import MappingProxyType

from parse_records import Label, get_labels_from_text
from prepare_rayyan import export_paths, metadata, read_export, values

# Standard review columns; every original tag is also retained separately.
FIELDS = ['key', 'title', 'authors', 'journal', 'issn', 'volume', 'issue', 'pages',
          'year', 'publisher', 'url', 'abstract', 'notes', 'doi', 'keywords',
          'document_type', 'language', 'suggested_labels', 'database', 'source_file',
          'source_format', 'source_index', 'source_sha256']
EXTRA_TAGS = {
    'ris': {'journal': ('JF', 'JO', 'T2'), 'issn': ('SN',), 'volume': ('VL',),
            'issue': ('IS',), 'publisher': ('PB',), 'url': ('UR',),
            'notes': ('N1',), 'language': ('LA',)},
    'nbib': {'journal': ('JT', 'TA'), 'issn': ('IS',), 'volume': ('VI',),
             'issue': ('IP',), 'publisher': (), 'url': (),
             'notes': ('GN',), 'language': ('LA',)},
    'enw': {'journal': ('J', 'B'), 'issn': ('@',), 'volume': ('V',),
            'issue': ('N',), 'publisher': ('I',), 'url': ('U',),
            'notes': ('Z',), 'language': ('G',)},
}


@dataclass(frozen=True)
class ExportRecord:
    """Complete labeling input: common citation fields and all native tags.

    Authors and keywords are tuples. Other common citation fields are strings;
    absent values are empty. source_fields retains every original tag and its
    repeated/continued values, including fields without a common equivalent.
    """

    key: str
    title: str
    authors: tuple[str, ...]
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
    keywords: tuple[str, ...]
    document_type: str
    language: str
    database: str
    source_file: str
    source_format: str
    source_index: int
    source_sha256: str
    source_fields: Mapping[str, tuple[str, ...]]


Labeler = Callable[[ExportRecord], Iterable[Label | str]]


def default_labels(record: ExportRecord) -> list[Label]:
    """Apply the existing title/abstract/keyword rules to a full export record."""
    return get_labels_from_text(record.title, record.abstract, record.keywords)


def label_values(labels: Iterable[Label | str]) -> list[str]:
    if isinstance(labels, str):
        raise ValueError('Return a list or iterable of labels, not a single string')
    result = []
    for label in labels:
        if not isinstance(label, str):
            raise ValueError('Custom labels must be Label members or strings')
        value = label.value if isinstance(label, Label) else label.strip()
        if not value:
            raise ValueError('Custom label names must not be empty')
        if value not in result:
            result.append(value)
    return result


def review_fields(tags, kind, data):
    row = {'title': '\n'.join(data['title']), 'authors': ' and '.join(data['authors']),
           'year': data['years'][0] if data['years'] else '',
           'abstract': '\n'.join(data['abstract']), 'doi': '; '.join(data['doi']),
           'keywords': '; '.join(data['keywords']), 'document_type': '; '.join(data['types'])}
    for field, alternatives in EXTRA_TAGS[kind].items():
        # Prefer the full journal name; raw alternate fields remain available.
        available = values(tags, *alternatives)
        row[field] = available[0] if field == 'journal' and available else '; '.join(available)
    if kind == 'ris':
        row['pages'] = '-'.join(values(tags, 'SP')[:1] + values(tags, 'EP')[:1])
    else:
        row['pages'] = '; '.join(values(tags, 'PG' if kind == 'nbib' else 'P'))
    return row


def label_exports(root: Path, output: Path, *, labeler: Labeler | None = None):
    """Label each complete record with the default rules or a custom callback."""
    if output.resolve().is_relative_to(root.resolve()):
        raise ValueError('Output must be outside the input export folder')
    rows, full_records, tag_columns = [], [], set()
    by_database, by_label = Counter(), Counter()
    selected_labeler = default_labels if labeler is None else labeler
    # Parse and label everything before creating output files.
    for path in export_paths(root):
        relative = path.relative_to(root)
        database = relative.parts[0]
        raw, _, kind, records = read_export(path)
        checksum = hashlib.sha256(raw).hexdigest()
        for index, tags in enumerate(records, 1):
            data = metadata(tags, kind)
            fields = review_fields(tags, kind, data)
            key = hashlib.sha256(f'{relative.as_posix()}:{checksum}:{index}'.encode()).hexdigest()[:24]
            record = ExportRecord(
                **{**fields, 'authors': tuple(data['authors']), 'keywords': tuple(data['keywords'])},
                key=key, database=database, source_file=relative.as_posix(), source_format=kind,
                source_index=index, source_sha256=checksum,
                source_fields=MappingProxyType({tag: tuple(entries) for tag, entries in tags.items()}))
            labels = label_values(selected_labeler(record))
            row = {'key': key, **fields, 'suggested_labels': '; '.join(labels),
                   'database': database, 'source_file': relative.as_posix(),
                   'source_format': kind, 'source_index': index, 'source_sha256': checksum}
            if labels:
                note = 'Suggested labels: ' + '; '.join(labels)
                row['notes'] = f"{row['notes']} | {note}" if row['notes'] else note
            for tag, entries in tags.items():
                column = f'source_{kind}_{tag}'
                tag_columns.add(column)
                row[column] = json.dumps(entries, ensure_ascii=False)
            rows.append(row)
            full_records.append({'key': key, 'database': database, 'source_file': relative.as_posix(),
                                 'source_format': kind, 'source_index': index, 'source_sha256': checksum,
                                 'suggested_labels': labels, 'metadata': data, 'source_fields': tags})
            by_database[database] += 1
            by_label.update(labels)
    output.mkdir(parents=True, exist_ok=False)
    with (output / 'labelled_records.csv').open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS + sorted(tag_columns))
        writer.writeheader()
        writer.writerows(rows)
    with (output / 'labelled_records.jsonl').open('w', encoding='utf-8') as handle:
        for record in full_records:
            handle.write(json.dumps(record, ensure_ascii=False) + '\n')
    summary = {'records': len(rows), 'by_database': dict(by_database), 'by_label': dict(by_label),
               'without_abstract': sum(not row['abstract'] for row in rows),
               'without_suggested_labels': sum(not row['suggested_labels'] for row in rows),
               'deduplicated': False,
               'labeling_method': ('Existing title/abstract/keyword regex heuristics'
                                   if selected_labeler is default_labels else
                                   f'Custom callback: {getattr(selected_labeler, "__qualname__", type(selected_labeler).__name__)}')}
    (output / 'label_summary.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path, default=Path('input/exports'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = args.output or Path('output') / datetime.now().strftime('labels_%Y%m%d_%H%M%S_%f')
    try:
        summary = label_exports(args.input, output)
    except (OSError, ValueError) as error:
        parser.exit(2, f'{error}\n')
    print(f'Labelled {summary["records"]} records in {output}')


if __name__ == '__main__':
    main()
