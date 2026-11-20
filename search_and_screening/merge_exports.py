"""Merge and de-duplicate the final-search exports into one candidate-records workbook.

Usage (from the project root):
    .venv/Scripts/python.exe tools/merge_exports.py [export folder]

The folder defaults to "Group Project/search_exports" (the 8-9 October runs). For the full rerun, pass
"Group Project/search_exports_rerun". Files are found by name pattern (scopus*.csv, wos*.xls, ...).

Reads every export in "Group Project/search_exports/" (Scopus CSV, Web of Science XLS, EBSCO CSVs for
PsycInfo and ERIC, PubMed MEDLINE text, IEEE CSVs, ACM BibTeX when present), maps each to one schema,
and groups records that share a DOI or a normalized title. Writes
"Group Project/Candidate Records - Final Search.xlsx" with a Records sheet (one row per unique study
report, PRISMA tracking columns empty), a Counts sheet (per-database totals and unique contributions)
and an About sheet.
"""
import csv
import datetime
import pathlib
import re

import openpyxl
import xlrd
from openpyxl.styles import Alignment, Font, PatternFill

import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXP = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / 'Group Project' / 'search_exports'
OUT = ROOT / 'Group Project' / 'Candidate Records - Final Search.xlsx'
SEPT = ROOT / 'CS8803 Group SLR - Candidate Records 2021-2026.xlsx'

NON_STUDY = re.compile(r'conference review|erratum|correction|retract|editorial|note$|letter|book review',
                       re.I)
CHINESE_JOURNALS = re.compile(r'acta psychologica sinica|journal of psychological science|'
                              r'psychological exploration|china examinations', re.I)


def norm_doi(d):
    d = (d or '').strip().lower()
    d = re.sub(r'^(https?://)?(dx\.)?doi\.org/', '', d)
    return d.rstrip('.')


def norm_title(t):
    t = re.sub(r'\[subscript (\w+)\]', r'\1', (t or '').lower())
    return re.sub(r'[^a-z0-9]', '', t)


def rec(source, sid, title, authors, year, venue, doctype, doi, abstract, keywords, language,
        issn='', pmid=''):
    y = re.search(r'(19|20)\d\d', str(year or ''))
    return {'source': source, 'source_id': str(sid or ''), 'title': (title or '').strip(),
            'authors': (authors or '').strip(), 'year': int(y.group(0)) if y else None,
            'venue': (venue or '').strip(), 'doc_type': (doctype or '').strip(),
            'doi': norm_doi(doi), 'abstract': (abstract or '').strip(),
            'keywords': (keywords or '').strip(), 'language': (language or '').strip(),
            'issn': str(issn or '').strip(), 'pmid': str(pmid or '').strip().split('.')[0]}


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def scopus(path):
    for r in read_csv(path):
        # Very long fields (e.g., a survey's full reference list) can break Scopus's CSV quoting, splitting
        # one record over two rows. The first part keeps every field up to the break; the fragment after
        # it has no real year. Keep the first part, drop the fragment.
        if not (r.get('EID') or '').startswith('2-s2.0') and not re.fullmatch(r'(19|20)\d\d', (r.get('Year') or '').strip()):
            continue
        abstract = '' if r.get('Abstract', '').startswith('[No abstract') else r.get('Abstract')
        kw = '; '.join(x for x in (r.get('Author Keywords'), r.get('Index Keywords')) if x)
        yield rec('Scopus', r.get('EID'), r['Title'], r.get('Author full names') or r.get('Authors'),
                  r.get('Year'), r.get('Source title'), r.get('Document Type'), r.get('DOI'), abstract,
                  kw, r.get('Language of Original Document'), r.get('ISSN'), r.get('PubMed ID'))


def wos(path):
    sh = xlrd.open_workbook(path).sheet_by_index(0)
    head = [str(c) for c in sh.row_values(0)]
    for i in range(1, sh.nrows):
        r = dict(zip(head, sh.row_values(i)))
        kw = '; '.join(str(x) for x in (r.get('Author Keywords'), r.get('Keywords Plus')) if x)
        yield rec('Web of Science', r.get('UT (Unique WOS ID)'), str(r.get('Article Title')),
                  str(r.get('Author Full Names')), r.get('Publication Year'), str(r.get('Source Title')),
                  str(r.get('Document Type')), str(r.get('DOI')), str(r.get('Abstract')), kw,
                  str(r.get('Language')), r.get('ISSN') or r.get('eISSN'), r.get('Pubmed Id'))


def ebsco(path, name):
    for r in read_csv(path):
        venue = re.split(r'[.,;]', r.get('source', ''))[0]
        yield rec(name, r.get('accessionNumber'), r['title'], r.get('authors'), r.get('publicationDate'),
                  venue, r.get('docType') or r.get('pubType'), r.get('doi'), r.get('abstract'),
                  r.get('subjects') or r.get('keywords'), r.get('language'), r.get('issn'), r.get('pmid'))


def pubmed(path):
    text = path.read_text(encoding='utf-8')
    for block in re.split(r'\n\s*\n(?=PMID-)', text.strip()):
        if not block.startswith('PMID-'):
            continue
        fields = {}
        for m in re.finditer(r'^([A-Z]{2,4})\s*- (.*(?:\n {6}.*)*)', block, flags=re.M):
            fields.setdefault(m.group(1), []).append(re.sub(r'\s+', ' ', m.group(2)).strip())
        doi = next((x[:-6] for x in fields.get('LID', []) + fields.get('AID', []) if x.endswith('[doi]')), '')
        yield rec('PubMed', fields['PMID'][0], fields.get('TI', [''])[0], '; '.join(fields.get('FAU', [])),
                  fields.get('DP', [''])[0], fields.get('JT', [''])[0], '; '.join(fields.get('PT', [])),
                  doi, ' '.join(fields.get('AB', [])), '; '.join(fields.get('OT', []) + fields.get('MH', [])),
                  '; '.join(fields.get('LA', [])), '; '.join(fields.get('IS', [])), fields['PMID'][0])


def ieee(path):
    for r in read_csv(path):
        kw = '; '.join(x for x in (r.get('Author Keywords'), r.get('IEEE Terms')) if x)
        dtype = 'Conference paper' if 'Conference' in (r.get('Document Identifier') or '') else \
            (r.get('Document Identifier') or '')
        yield rec('IEEE Xplore', r.get('PDF Link') or r.get('DOI'), r['Document Title'], r.get('Authors'),
                  r.get('Publication Year'), r.get('Publication Title'), dtype, r.get('DOI'),
                  r.get('Abstract'), kw, 'English', r.get('ISSN'))


def acm(path):
    text = path.read_text(encoding='utf-8')
    for entry in re.split(r'\n(?=@)', text):
        m = re.match(r'@(\w+)\{([^,]*),', entry.strip())
        if not m:
            continue

        def field(name):
            f = re.search(rf'\b{name}\s*=\s*[{{"](.*?)[}}"],?\s*\n', entry, flags=re.S | re.I)
            return re.sub(r'\s+', ' ', f.group(1)).strip('{} ') if f else ''
        yield rec('ACM DL', m.group(2), field('title'), field('author'), field('year'),
                  field('booktitle') or field('journal'), m.group(1), field('doi'), field('abstract'),
                  field('keywords'), 'English', field('issn'))


def load():
    """Read every export in EXP, matched by file-name pattern, one reader per database."""
    records, raw = [], {}
    readers = [('Scopus', ['scopus*.csv'], scopus),
               ('Web of Science', ['wos*.xls'], wos),
               ('APA PsycInfo', ['psycinfo*.csv', 'APAPsych*.csv'], lambda p: ebsco(p, 'APA PsycInfo')),
               ('ERIC', ['eric*.csv'], lambda p: ebsco(p, 'ERIC')),
               ('PubMed', ['pubmed*.txt'], pubmed),
               ('IEEE Xplore', ['ieee*.csv'], ieee),
               ('ACM DL', ['acm*.bib'], acm)]
    for name, patterns, fn in readers:
        got = []
        for pattern in patterns:
            for f in sorted(EXP.glob(pattern)):
                got.extend(fn(f))
        if got:
            raw[name] = len(got)
            records.extend(got)
    return records, raw


def group(records):
    """Union-find. Records are one study report if they share a DOI, or if they share a normalized title
    (25+ characters) and nothing contradicts it: two different DOIs mean two reports (e.g., a conference
    paper and its journal version, linked later at screening under C11), and two DOI-less records from
    the same database are separate entries (e.g., one proceedings front matter per volume)."""
    parent = list(range(len(records)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def compatible(a, b):
        ra, rb = records[a], records[b]
        if ra['doi'] and rb['doi'] and ra['doi'] != rb['doi']:
            return False
        if not ra['doi'] and not rb['doi'] and ra['source'] == rb['source']:
            return False
        return True

    by_doi, by_title = {}, {}
    for i, r in enumerate(records):
        if r['doi']:
            if r['doi'] in by_doi:
                parent[find(i)] = find(by_doi[r['doi']])
            else:
                by_doi[r['doi']] = i
    for i, r in enumerate(records):
        t = norm_title(r['title'])
        if len(t) < 25:
            continue
        for j in by_title.get(t, []):
            if compatible(i, j):
                parent[find(i)] = find(j)
                break
        by_title.setdefault(t, []).append(i)
    groups = {}
    for i in range(len(records)):
        groups.setdefault(find(i), []).append(records[i])
    return list(groups.values())


def sept_index():
    if not SEPT.exists():
        return {}, {}
    rows = list(openpyxl.load_workbook(SEPT, read_only=True)['Records'].iter_rows(values_only=True))
    h = rows[0]
    i_id, i_doi, i_t = h.index('ID'), h.index('DOI'), h.index('Title')
    by_doi = {norm_doi(r[i_doi]): r[i_id] for r in rows[1:] if r[i_doi]}
    by_t = {norm_title(r[i_t]): r[i_id] for r in rows[1:]}
    return by_doi, by_t


def merge(g, order):
    g = sorted(g, key=lambda r: order.index(r['source']))
    best = lambda k: max((r[k] for r in g), key=len, default='')
    out = dict(g[0])
    for k in ('abstract', 'keywords', 'authors', 'venue', 'doi', 'pmid', 'issn'):
        out[k] = best(k)
    out['year'] = min((r['year'] for r in g if r['year']), default=None)
    out['found_in'] = '; '.join(dict.fromkeys(r['source'] for r in g))
    out['doc_types'] = ' | '.join(dict.fromkeys(r['doc_type'] for r in g if r['doc_type']))
    out['languages'] = '; '.join(dict.fromkeys(r['language'] for r in g if r['language']))
    return out


def flags(r):
    f = []
    if NON_STUDY.search(r['doc_types']):
        f.append('non-study type')
    if re.search(r'dissertation|thesis', r['doc_types'], re.I):
        f.append('dissertation')
    if re.search(r'chapter|book', r['doc_types'], re.I):
        f.append('book/chapter')
    if not r['abstract']:
        f.append('no abstract')
    if CHINESE_JOURNALS.search(r['venue']) or re.search(r'chi|zho', r['languages'], re.I):
        f.append('check full-text language')
    if r['year'] and not 2021 <= r['year'] <= 2026:
        f.append(f'check date ({r["year"]})')
    return '; '.join(f)


TRACKING = ['Stage', 'Assigned to', 'Screener 1', 'Screener 2', 'Decision', 'Exclusion reason',
            'Excluded at stage', 'Notes']


def previous():
    """IDs and tracking entries from the last build, so re-running never renumbers or erases."""
    if not OUT.exists():
        return {}, {}, 0
    rows = list(openpyxl.load_workbook(OUT, read_only=True)['Records'].iter_rows(values_only=True))
    h = rows[0]
    by_key, kept = {}, {}
    top = 0
    for r in rows[1:]:
        d = dict(zip(h, r))
        top = max(top, int(d['ID'][1:]))
        for k in (('doi:' + norm_doi(d['DOI'])) if d['DOI'] else None, 't:' + norm_title(d['Title'])):
            if k:
                by_key.setdefault(k, []).append(d['ID'])   # several rows can share a title
        kept[d['ID']] = [d.get(c) for c in TRACKING]
    return by_key, kept, top


def main():
    records, raw = load()
    order = ['Scopus', 'Web of Science', 'APA PsycInfo', 'ERIC', 'PubMed', 'IEEE Xplore', 'ACM DL']
    groups = group(records)
    merged = [merge(g, order) for g in groups]
    merged.sort(key=lambda r: (-(r['year'] or 0), r['title'].lower()))
    by_doi, by_t = sept_index()
    old_ids, kept, top = previous()
    used = set()

    def claim(key):
        for cand in sorted(old_ids.get(key, [])):
            if cand not in used:
                used.add(cand)
                return cand
        return None

    for r in merged:   # DOI matches first, then titles; each existing ID goes to one row only
        r['id'] = claim('doi:' + r['doi']) if r['doi'] else None
    for r in merged:
        if not r['id']:
            r['id'] = claim('t:' + norm_title(r['title']))
    for r in merged:
        if not r['id']:
            top += 1
            r['id'] = f'F{top:04d}'
    merged.sort(key=lambda r: r['id'])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Records'
    cols = ['ID', 'Sept ID', 'Year', 'Title', 'Authors', 'Venue', 'Document type', 'DOI', 'Found in',
            'Abstract', 'Keywords', 'Language', 'Screening flags'] + TRACKING
    ws.append(cols)
    for r in merged:
        sept = by_doi.get(r['doi']) or by_t.get(norm_title(r['title'])) or ''
        track = kept.get(r['id']) or ['Title/abstract screening'] + [''] * (len(TRACKING) - 1)
        ws.append([r['id'], sept, r['year'], r['title'], r['authors'], r['venue'], r['doc_types'],
                   r['doi'], r['found_in'], r['abstract'], r['keywords'], r['languages'], flags(r)]
                  + list(track))
    widths = [7, 7, 6, 60, 30, 30, 18, 26, 22, 80, 30, 9, 24, 22, 12, 11, 11, 10, 22, 16, 30]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill('solid', fgColor='DDE6F0')
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(vertical='top', wrap_text=c.column in (4, 10))
    ws.freeze_panes = 'E2'
    ws.auto_filter.ref = ws.dimensions

    cs = wb.create_sheet('Counts')
    cs.append(['Database', 'Rows exported', 'Records (de-duplicated within database)',
               'Found only in this database'])
    for name in order:
        if name in raw:
            within = sum(1 for r in merged if name in r['found_in'].split('; '))
            only = sum(1 for r in merged if r['found_in'] == name)
            cs.append([name, raw[name], within, only])
    cs.append(['Total exported', sum(raw.values()), ''])
    cs.append(['Duplicates removed', sum(raw.values()) - len(merged), ''])
    cs.append(['Unique records', len(merged), ''])
    for c in cs[1]:
        c.font = Font(bold=True)
    cs.column_dimensions['A'].width = 22
    cs.column_dimensions['B'].width = 18
    cs.column_dimensions['C'].width = 36
    cs.column_dimensions['D'].width = 26

    ab = wb.create_sheet('About')
    for line in [
        f'Built {datetime.date.today().isoformat()} by tools/merge_exports.py from Group Project/search_exports/.',
        'Search run 2026-10-08; queries in Group Project/Final Search Log.xlsx.',
        'De-duplication: records sharing a normalized DOI are one row; so are records sharing a normalized '
        'title of 25+ characters, unless they carry different DOIs (separate reports) or are DOI-less '
        'entries from the same database. Abstract, keywords and authors are taken from whichever source has the longest.',
        '"Records exported" counts rows per database before de-duplication; IEEE and EBSCO counts are '
        'already unions of their per-path searches (IEEE rows matching two paths count twice here).',
        'IDs are permanent: re-running keeps every existing ID and screening entry, and new records get the next free ID.',
        'Sept ID links a row to the 26 Sept scoping-search spreadsheet, where the same record appears.',
        'Screening flags are prompts for the screener, not decisions.',
    ]:
        ab.append([line])
    ab.column_dimensions['A'].width = 150
    wb.save(OUT)
    print({k: raw[k] for k in raw}, 'total', sum(raw.values()), 'unique', len(merged))


if __name__ == '__main__':
    main()
