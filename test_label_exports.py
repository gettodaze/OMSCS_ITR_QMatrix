import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from label_exports import ExportRecord, default_labels, label_exports
from parse_records import Label, get_labels_from_text
from prepare_rayyan import metadata, parse_export

TITLE = 'Refining a Q-matrix with neural networks'
ABSTRACT = 'A simulation study of psychometric assessment items using machine learning.'
RIS = f'TY  - JOUR\nTI  - {TITLE}\nAB  - {ABSTRACT}\nAU  - Example, First\nAU  - Example, Second\nJF  - Synthetic Journal\nJO  - Synth J\nVL  - 2\nIS  - 3\nSP  - 12\nEP  - 18\nSN  - 0000-0000\nDO  - 10.0/synthetic\nKW  - statistical\nN1  - Original note\nZZ  - Unknown field\nZZ  - Second value\nER  - \n'
NBIB = f'PMID- 123\nTI  - {TITLE}\nAB  - {ABSTRACT}\nFAU - Example, First\nAU  - Example F\nJT  - Synthetic Journal\nPG  - 12-18\nVI  - 2\nOT  - statistical\nAID - 10.0/synthetic [doi]\n'
ENW = f'%0 Journal Article\n%T {TITLE}\n%X {ABSTRACT}\n%A Example, First\n%J Synthetic Journal\n%P 12-18\n%V 2\n%K statistical\n%R 10.0/synthetic\n%+ Synthetic affiliation\n%> https://example.org/synthetic.pdf\n'


class LabelExportTests(unittest.TestCase):
    def make_exports(self, root):
        for db, name, text in [('Scopus', 'query.ris', RIS), ('PubMed', 'query.txt', NBIB), ('ACM DL', 'query.enw', ENW)]:
            path = root / db / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')

    def test_shared_rules_have_expected_labels(self):
        self.assertEqual(get_labels_from_text(TITLE, ABSTRACT, ('statistical',)), [
            Label.STATISTICAL, Label.MACHINE_LEARNING, Label.EDUCATIONAL_MEASUREMENT,
            Label.REFINEMENT, Label.SIMULATED])
        self.assertEqual(get_labels_from_text('', '', ()), [])

    def test_native_formats_keep_extra_fields_and_repeated_values(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'exports'
            self.make_exports(root)
            hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}
            output = Path(directory) / 'labels'
            summary = label_exports(root, output)
            self.assertEqual(summary['records'], 3)
            self.assertEqual(summary['by_label']['Q-matrix refinement'], 3)
            self.assertEqual(summary['without_abstract'], 0)
            full = [json.loads(line) for line in (output / 'labelled_records.jsonl').read_text().splitlines()]
            self.assertEqual(next(r for r in full if r['source_format'] == 'enw')['source_fields']['+'], ['Synthetic affiliation'])
            self.assertEqual(next(r for r in full if r['source_format'] == 'enw')['source_fields']['>'], ['https://example.org/synthetic.pdf'])
            with (output / 'labelled_records.csv').open(newline='') as handle:
                rows = list(csv.DictReader(handle))
            ris = next(r for r in rows if r['source_format'] == 'ris')
            self.assertEqual(json.loads(ris['source_ris_ZZ']), ['Unknown field', 'Second value'])
            self.assertEqual(ris['pages'], '12-18')
            self.assertEqual(ris['journal'], 'Synthetic Journal')
            self.assertEqual(ris['authors'], 'Example, First and Example, Second')
            self.assertTrue(ris['notes'].startswith('Original note | Suggested labels:'))
            nbib = next(r for r in rows if r['source_format'] == 'nbib')
            self.assertEqual(nbib['authors'], 'Example, First')
            self.assertEqual(nbib['doi'], '10.0/synthetic')
            for path, expected in hashes.items():
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)

    def test_missing_abstract_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'exports/Scopus'
            root.mkdir(parents=True)
            (root / 'query.ris').write_text('TY  - JOUR\nTI  - Synthetic title\nER  - \n')
            output = Path(directory) / 'labels'
            summary = label_exports(root.parent, output)
            self.assertEqual(summary['without_abstract'], 1)
            self.assertEqual(summary['without_suggested_labels'], 1)
            (root / 'query.ris').write_text('TY  - JOUR\nTI  - Incomplete\n')
            bad_output = Path(directory) / 'invalid'
            with self.assertRaises(ValueError):
                label_exports(root.parent, bad_output)
            self.assertFalse(bad_output.exists())

    def test_custom_callback_receives_full_typed_record(self):
        seen = []

        def custom_labels(record: ExportRecord) -> list[Label | str]:
            self.assertIsInstance(record, ExportRecord)
            self.assertEqual(record.journal, 'Synthetic Journal')
            self.assertEqual(record.authors[0], 'Example, First')
            self.assertEqual(record.source_index, 1)
            self.assertTrue(record.source_file.startswith(record.database + '/'))
            seen.append(record)
            labels: list[Label | str] = list(default_labels(record))
            if record.source_fields.get('ZZ') == ('Unknown field', 'Second value'):
                self.assertEqual(record.notes, 'Original note')
                self.assertEqual(record.volume, '2')
                self.assertEqual(record.document_type, 'JOUR')
                labels.extend(['provider-specific label', 'provider-specific label'])
                with self.assertRaises(TypeError):
                    record.source_fields['ZZ'] = ('changed',)
            return labels

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'exports'
            self.make_exports(root)
            output = Path(directory) / 'custom'
            summary = label_exports(root, output, labeler=custom_labels)
            self.assertEqual(len(seen), 3)
            self.assertEqual(summary['by_label']['provider-specific label'], 1)
            self.assertTrue(summary['labeling_method'].startswith('Custom callback:'))
            records = [json.loads(line) for line in (output / 'labelled_records.jsonl').read_text().splitlines()]
            ris = next(record for record in records if record['source_format'] == 'ris')
            self.assertEqual(ris['suggested_labels'].count('provider-specific label'), 1)
            self.assertEqual(ris['source_fields']['ZZ'], ['Unknown field', 'Second value'])

    def test_invalid_custom_labels_write_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / 'exports'
            self.make_exports(root)
            output = Path(directory) / 'bad-labels'
            with self.assertRaisesRegex(ValueError, 'must not be empty'):
                label_exports(root, output, labeler=lambda record: [''])
            self.assertFalse(output.exists())
            with self.assertRaisesRegex(ValueError, 'not a single string'):
                label_exports(root, output, labeler=lambda record: 'label')
            self.assertFalse(output.exists())

    def test_notebook_local_data_workflow(self):
        notebook = json.loads(Path('docs_agent/label_exports.ipynb').read_text())
        code_cells = [''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'code']
        for cell in notebook['cells']:
            if cell['cell_type'] == 'code':
                self.assertEqual(cell['outputs'], [])
                compile(''.join(cell['source']), '<notebook>', 'exec')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.make_exports(root / 'exports')
            namespace = {'test_data_root': root, 'CODE_URL': 'synthetic', 'CODE_REF': 'test', 'CODE_REVISION': 'synthetic'}
            # Drive authentication and GitHub installation need a live Colab session;
            # execute the actual remaining notebook cells against a synthetic Drive folder.
            exec('from pathlib import Path\nimport json, shutil, tempfile', namespace)
            for cell in code_cells[2:]:
                cell = cell.replace('Path("/content/drive/MyDrive/QMatrix")', 'test_data_root')
                if '# def custom_labels(' in cell:
                    # Enable the actual commented customization example.
                    lines = cell.splitlines(keepends=True)
                    enabled = False
                    for index, line in enumerate(lines):
                        if line.startswith('# def custom_labels('):
                            enabled = True
                        if enabled and line.startswith('# '):
                            lines[index] = line[2:]
                    cell = ''.join(lines)
                exec(cell, namespace)
            run = namespace['RUN_OUTPUT']
            self.assertTrue((run / 'prepared/by_database/Scopus.ris').exists())
            self.assertTrue((run / 'labels/labelled_records.csv').exists())
            self.assertEqual(json.loads((run / 'run_metadata.json').read_text())['records'], 3)
            self.assertTrue(json.loads((run / 'run_metadata.json').read_text())['custom_labeling'])
            self.assertTrue(namespace['summary']['labeling_method'].startswith('Custom callback:'))


if __name__ == '__main__':
    unittest.main()
