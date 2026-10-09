import csv
from pathlib import Path
import tempfile
import unittest

from prepare_rayyan import metadata, parse_export, prepare

RIS = 'TY  - JOUR\nTI  - A study\nAU  - One, Author\nAU  - Two, Author\nAB  - First line\n      Second line\nDO  - https://doi.org/10.1/example\nKW  - diagnosis\nPY  - 2026\nZZ  - Preserve this unknown field\nER  - \n'
NBIB = 'PMID- 123\nTI  - A study\nAB  - An abstract\nFAU - One, Author\nAID - 10.1/example [doi]\nPT  - Journal Article\nDP  - 2026 Oct\n'
ENW = '%0 Conference Paper\n%T Another study\n%A Another, Author\n%X Abstract\n%K education\n%R 10.2/test\n%D 2025\n'


class ExportTests(unittest.TestCase):
    def test_tagged_formats_and_continuations(self):
        for text, kind in [(RIS, 'ris'), (NBIB, 'nbib'), (ENW, 'enw')]:
            record = parse_export(text, kind)[0]
            self.assertTrue(metadata(record, kind)['abstract'])
            self.assertTrue(metadata(record, kind)['doi'])
        record = parse_export(RIS, 'ris')[0]
        self.assertEqual(len(record['AU']), 2)
        self.assertIn('Second line', record['AB'][0])
        self.assertEqual(len(parse_export(NBIB + '\n' + NBIB, 'nbib')), 2)

    def test_malformed_ris_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing ER'):
            parse_export(RIS.replace('ER  - \n', ''), 'ris')
        with self.assertRaisesRegex(ValueError, 'missing ER'):
            parse_export(RIS.replace('ER  - \n', '') + RIS, 'ris')

    def test_preservation_counts_and_baseline_comparison(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / 'exports'
            for db, name, content in [('Scopus', 'query1.ris', RIS), ('Scopus', 'query2.ris', RIS),
                                      ('PubMed', 'pubmed.txt', NBIB), ('ACM DL', 'query1.enw', ENW)]:
                path = root / db / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(content.replace('\n', '\r\n').encode('utf-8'))
            baseline = base / 'baseline.csv'
            with baseline.open('w', newline='') as handle:
                writer = csv.DictWriter(handle, fieldnames=['Found in', 'Title', 'DOI', 'Abstract', 'Authors', 'Keywords', 'Year', 'Document type'])
                writer.writeheader()
                writer.writerow({'Found in': 'Scopus; PubMed', 'Title': 'A STUDY', 'DOI': '10.1/example', 'Year': '2026', 'Document type': 'Article'})
            counts = base / 'counts.csv'
            counts.write_text('file,expected_count\nScopus/query1.ris,2\n')
            output = base / 'prepared'
            report = prepare(root, output, baseline, counts)
            entry = next(r for r in report['files'] if r['file'] == 'Scopus/query1.ris')
            self.assertFalse(entry['count_matches'])
            self.assertEqual(report['databases']['Scopus']['records'], 2)
            self.assertEqual(report['comparison']['Scopus']['baseline_records_matched_by_doi_or_title'], 1)
            self.assertEqual(report['comparison']['Scopus']['new_records_matched_by_doi_or_title'], 2)
            self.assertIn('ZZ  - Preserve this unknown field', (output / 'combined.ris').read_text())
            self.assertEqual(len(parse_export((output / 'combined.ris').read_text(), 'ris')), 2)
            self.assertEqual((output / 'originals/Scopus/query1.ris').read_bytes(), (root / 'Scopus/query1.ris').read_bytes())
            self.assertTrue((output / 'by_database/PubMed.nbib').exists())

    def test_invalid_input_writes_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / 'exports/Scopus'
            root.mkdir(parents=True)
            (root / 'bad.ris').write_text('TY  - JOUR\nTI  - Incomplete\n')
            with self.assertRaises(ValueError):
                prepare(root.parent, base / 'out')
            self.assertFalse((base / 'out').exists())


if __name__ == '__main__':
    unittest.main()
