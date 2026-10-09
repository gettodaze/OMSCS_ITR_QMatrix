# Native exports and Rayyan import

Use **full-record RIS** as the default export. It holds repeated authors, keywords, abstracts, DOI, journal, volume, issue, pages, dates, URLs and other tagged metadata without requiring a common CSV header. Keep **PubMed NBIB** and **ACM EndNote (.enw)** in their native formats when those are the available full-record exports. This is a practical choice to minimize transformations, not a guarantee that every provider exports every field. [Rayyan's supported formats](https://help.rayyan.ai/hc/en-us/articles/4406426903825-Supported-File-Formats-for-Importing-into-Rayyan).

The [manual database search page](manual_search_links.md) gives database-specific search and download instructions. Select abstracts and all available bibliographic fields when exporting. Inspect a small download before exporting the whole search: a supported format alone does not guarantee complete metadata.

## Save exports

Database exports and derived files stay local in the ignored `input/` and `output/` directories. See [data sharing](data_sharing.md) before publishing records or uploading them to an external service.

Keep each database in its own directory, with separate files for queries and batches:

```text
input/exports/
  Scopus/query1_batch1.ris
  Web of Science/query1_batch1.ris
  APA PsycInfo/query1_batch1.ris
  ERIC/query1_batch1.ris
  PubMed/query1_batch1.nbib
  IEEE Xplore/query1_batch1.ris
  IEEE Xplore/query2_batch1.ris
  IEEE Xplore/query3_batch1.ris
  ACM DL/query1_batch1.enw
```

Tagged PubMed downloads ending in `.txt` are supported too. Use UTF-8 exports; the preparation tool rejects other encodings rather than guessing. Put supplementary CSV/BibTeX exports outside this folder: the tool processes RIS, NBIB, EndNote and recognized tagged `.txt` files only. Preserve supplementary exports separately if they contain fields omitted by the chosen citation format.

Record the search date, query, filters, and displayed hit count in your search log. For batches, record the exported range and its expected count. Overlapping queries should remain separate until the review's duplicate-resolution step.

## Prepare and audit

Run from the repository root; the new tool uses only Python's standard library:

```bash
python prepare_rayyan.py input/exports --baseline input/input.csv
```

The old CSV is an optional comparison baseline. It is no longer an input requirement for the native-export workflow. To check individual export counts, supply a CSV such as `input/export_counts.csv`:

```csv
file,expected_count
Scopus/query1_batch1.ris,500
PubMed/query1_batch1.nbib,120
```

Paths are relative to `input/exports/`. Each expected count refers to that file's batch, not the total count across several batches. Replace these example counts with the numbers recorded during export.

```bash
python prepare_rayyan.py input/exports --baseline input/input.csv --counts input/export_counts.csv
```

Outputs go into a new `output/rayyan_<timestamp>/` directory:

- `originals/`: byte-for-byte copies of supported input files.
- `by_database/`: batches concatenated into one file per database and format, retaining database provenance for named Rayyan imports.
- `combined.ris`, `combined.nbib`, `combined.enw`: optional concatenations across databases, with one file per format present.
- `audit.json`: source hashes, counts per file and database, exported tag inventories, document types, years, metadata coverage, expected-count checks, and comparison with the old CSV.

The tool retains all tags, repeated fields and continuation text in import files. It only normalizes encoding markers and record separators when concatenating. It performs no metadata remapping, labeling, filtering or deduplication. Incomplete RIS records and malformed input fail before output is written. Count mismatches still produce the audit and files, but return exit status 1 so they can be investigated before importing.

## Compare results

1. Check each file's `records`, `expected_count` and `count_matches`. Sum batch counts for each query and compare with the database's displayed hit count. Without `--counts`, count agreement remains unverified.
2. Inspect `databases` for document-type and year distributions, and `with_fields` for title, abstract, DOI, authors and keywords. Missing abstracts should trigger an export-settings check.
3. Inspect `comparison` for baseline and new counts, and record matches by normalized DOI or title. The baseline counts include every database listed in `Found in`; they represent the existing candidate CSV, not necessarily the original raw search counts.
4. Compare document types manually: `JOUR`, `Journal Article` and `Article` can represent the same category in different sources. Count equality and a DOI/title match do not prove identical eligibility or record sets. Query overlaps inflate raw export counts until duplicates are resolved.

New searches can differ because of indexing updates and search dates. Actual result equivalence can only be checked after the new exports and logged hit counts are available.

## Import into Rayyan

Use the files in `by_database/` for clearly named imports such as “Scopus — 2026-10-09”. Alternatively upload the `combined.*` files if a combined import is preferable. Choose one set; importing both duplicates every record.

Open the review → **Add References** → select the files → name the import → **Continue**. Check each import's count in the Review data panel against the audit. First try 10–20 records and inspect title, abstract, DOI, authors and journal fields. [Rayyan upload instructions](https://help.rayyan.ai/hc/en-us/articles/17216953358353-How-to-Import-References-into-Rayyan).

Keep the original exports and audit after upload. Rayyan stores its own internal record structure and replaces source accession numbers; retaining arbitrary provider tags inside Rayyan is not guaranteed. The original files preserve information independently of Rayyan's importer. [Rayyan format handling](https://help.rayyan.ai/hc/en-us/articles/4406426903825-Supported-File-Formats-for-Importing-into-Rayyan).

The existing `parse_records.py` remains available for converting the old candidate CSV and applying its labels. The native-export path bypasses that fixed-column conversion so additional metadata survives preparation.
