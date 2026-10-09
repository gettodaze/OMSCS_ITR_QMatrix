"""Preserve native citation exports, concatenate by format, and audit against a CSV baseline."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

FORMATS = {'.ris': 'ris', '.nbib': 'nbib', '.enw': 'enw'}


def export_paths(root: Path) -> list[Path]:
    files = sorted(p for p in root.rglob('*') if p.is_file() and p.suffix.lower() in {*FORMATS, '.txt'})
    if not files:
        raise ValueError(f'No RIS, NBIB or EndNote exports under {root}')
    for path in files:
        if len(path.relative_to(root).parts) < 2:
            raise ValueError(f'Place {path.name} inside a database-named subfolder')
    return files


def read_export(path: Path):
    raw = path.read_bytes()
    text = raw.decode('utf-8-sig')
    kind = FORMATS.get(path.suffix.lower())
    if kind is None:
        first_line = text.lstrip().splitlines()[0] if text.strip() else ''
        kind = ('nbib' if first_line.startswith('PMID-') else
                'ris' if first_line.startswith('TY  -') else
                'enw' if first_line.startswith('%0') else None)
        if kind is None:
            raise ValueError(f'{path.name}: .txt file is not tagged RIS, PubMed or EndNote')
    return raw, text, kind, parse_export(text, kind)


def parse_export(text: str, kind: str) -> list[dict[str, list[str]]]:
    """Read tags for auditing only; concatenation uses the original text."""
    if kind not in FORMATS.values():
        raise ValueError(f'Unsupported format: {kind}')
    records = []
    current = None
    last = None
    patterns = {
        'ris': re.compile(r'^([A-Z0-9]{2})  -\s?(.*)$'),
        'nbib': re.compile(r'^([A-Z0-9]{2,4})\s*-\s?(.*)$'),
        'enw': re.compile(r'^%(\S)\s?(.*)$'),
    }
    start = {'ris': 'TY', 'nbib': 'PMID', 'enw': '0'}[kind]
    for number, line in enumerate(text.splitlines(), 1):
        match = patterns[kind].match(line)
        if match:
            tag, value = match.groups()
            if tag == start:
                if current is not None:
                    if kind == 'ris':
                        raise ValueError(f'Line {number}: RIS record missing ER terminator')
                    records.append(dict(current))
                current = defaultdict(list)
                last = None
            if current is None:
                raise ValueError(f'Line {number}: tag outside a record')
            current[tag].append(value)
            last = tag
            if kind == 'ris' and tag == 'ER':
                records.append(dict(current))
                current = None
                last = None
        elif line.strip():
            if current is None or last is None:
                raise ValueError(f'Line {number}: text outside a record')
            current[last][-1] += '\n' + line
    if current is not None:
        if kind == 'ris':
            raise ValueError('Last RIS record missing ER terminator')
        records.append(dict(current))
    if not records:
        raise ValueError('No citation records found')
    return records


def values(record, *tags):
    return [value.strip() for tag in tags for value in record.get(tag, []) if value.strip()]


def normalize_title(value):
    return re.sub(r'\W+', ' ', value.casefold()).strip()


def normalize_doi(value):
    return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', value.strip(), flags=re.I).casefold()


def metadata(record, kind):
    tags = {
        'ris': (('TI', 'T1'), ('AB', 'N2'), ('DO',), ('AU', 'A1'), ('KW',), ('TY',), ('PY', 'Y1', 'DA')),
        'nbib': (('TI',), ('AB',), ('AID', 'LID'), ('FAU', 'AU'), ('OT', 'MH'), ('PT',), ('DP',)),
        'enw': (('T',), ('X',), ('R',), ('A',), ('K',), ('0',), ('D',)),
    }[kind]
    title, abstract, doi, authors, keywords, types, dates = [values(record, *group) for group in tags]
    if kind == 'nbib':
        authors = values(record, 'FAU') or values(record, 'AU')
    elif kind == 'ris':
        authors = values(record, 'AU') or values(record, 'A1')
    if kind == 'nbib':
        doi = [v.removesuffix(' [doi]') for v in doi if v.endswith(' [doi]')]
    years = [m.group() for v in dates if (m := re.search(r'\b(?:19|20)\d{2}\b', v))]
    return {'title': title, 'abstract': abstract, 'doi': doi, 'authors': authors,
            'keywords': keywords, 'types': types, 'years': years}


def profile(records):
    return {'records': len(records),
            'document_types': dict(Counter(t for r in records for t in r['types'])),
            'years': dict(Counter(y for r in records for y in r['years'])),
            'with_fields': {field: sum(bool(r[field]) for r in records)
                            for field in ('title', 'abstract', 'doi', 'authors', 'keywords')}}


def identity(record):
    return ({normalize_doi(v) for v in record['doi'] if normalize_doi(v)},
            {normalize_title(v) for v in record['title'] if normalize_title(v)})


def compare(old, new):
    def match_counts(left, right):
        dois, titles = set(), set()
        for record in right:
            d, t = identity(record)
            dois.update(d)
            titles.update(t)
        return sum(bool(d & dois or t & titles) for d, t in map(identity, left))
    return {'baseline': profile(old), 'new_exports': profile(new),
            'baseline_records_matched_by_doi_or_title': match_counts(old, new),
            'new_records_matched_by_doi_or_title': match_counts(new, old)}


def read_baseline(path):
    grouped = defaultdict(list)
    with path.open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        required = {'Found in', 'Title', 'DOI', 'Abstract', 'Authors', 'Keywords', 'Year', 'Document type'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('Baseline is missing required comparison columns')
        for row in reader:
            record = {name: [row[column]] if row[column].strip() else [] for name, column in
                      [('title', 'Title'), ('doi', 'DOI'), ('abstract', 'Abstract'), ('authors', 'Authors'),
                       ('keywords', 'Keywords'), ('years', 'Year'), ('types', 'Document type')]}
            for database in set(v.strip() for v in row['Found in'].split(';') if v.strip()):
                grouped[database].append(record)
    return grouped


def prepare(root: Path, output: Path, baseline: Path | None = None, counts: Path | None = None):
    if output.resolve().is_relative_to(root.resolve()):
        raise ValueError('Output must be outside the input export folder')
    files = export_paths(root)
    expected = {}
    if counts:
        with counts.open(encoding='utf-8-sig', newline='') as handle:
            for row in csv.DictReader(handle):
                name = row['file']
                if name in expected:
                    raise ValueError(f'Duplicate expected count: {name}')
                expected[name] = int(row['expected_count'])
                if expected[name] < 0:
                    raise ValueError(f'Negative expected count: {name}')
    manifest, by_database, by_format, records = [], defaultdict(list), defaultdict(list), defaultdict(list)
    # Validate everything before writing outputs.
    for path in files:
        relative = path.relative_to(root)
        database = relative.parts[0]
        raw, text, kind, parsed = read_export(path)
        data = [metadata(r, kind) for r in parsed]
        records[database].extend(data)
        # Separate complete records, preserving all tags and multiline content.
        by_database[database, kind].append(text.rstrip('\r\n') + '\n\n')
        by_format[kind].append(text.rstrip('\r\n') + '\n\n')
        name = relative.as_posix()
        manifest.append({'file': name, 'database': database, 'format': kind,
                         'sha256': hashlib.sha256(raw).hexdigest(), **profile(data),
                         'exported_tags': dict(Counter(tag for r in parsed for tag in r)),
                         'expected_count': expected.get(name),
                         'count_matches': len(parsed) == expected[name] if name in expected else None})
    unknown = set(expected) - {entry['file'] for entry in manifest}
    if unknown:
        raise ValueError(f'Expected-count files not found: {sorted(unknown)}')
    old = read_baseline(baseline) if baseline else {}
    report = {'files': manifest, 'databases': {db: profile(data) for db, data in records.items()},
              'comparison': {db: compare(old.get(db, []), records.get(db, []))
                             for db in sorted(set(old) | set(records))},
              'notes': ['Exports are not deduplicated or filtered.',
                        'Baseline counts reflect CSV database membership, not original search hit counts.',
                        'Document type vocabularies differ between export formats; compare categories manually.',
                        'DOI/title matches are an audit heuristic, not proof of equivalent searches.']}
    output.mkdir(parents=True, exist_ok=False)
    originals = output / 'originals'
    for path in files:
        destination = originals / path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(path.read_bytes())
    for (database, kind), texts in by_database.items():
        destination = output / 'by_database' / f'{database}.{kind}'
        destination.parent.mkdir(exist_ok=True)
        destination.write_text(''.join(texts), encoding='utf-8')
    for kind, texts in by_format.items():
        (output / f'combined.{kind}').write_text(''.join(texts), encoding='utf-8')
    (output / 'audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', nargs='?', type=Path, default=Path('input/exports'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--baseline', type=Path, help='Optional previous candidate CSV for comparison')
    parser.add_argument('--counts', type=Path, help='CSV with file,expected_count columns; paths relative to input')
    args = parser.parse_args()
    output = args.output or Path('output') / datetime.now().strftime('rayyan_%Y%m%d_%H%M%S_%f')
    try:
        report = prepare(args.input, output, args.baseline, args.counts)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f'{error}\n')
    print(f'Prepared {sum(r["records"] for r in report["files"])} records in {output}')
    if any(r['count_matches'] is False for r in report['files']):
        parser.exit(1, 'Export counts differ from expected counts; inspect audit.json before importing.\n')


if __name__ == '__main__':
    main()
