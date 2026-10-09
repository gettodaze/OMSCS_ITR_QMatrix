# Label native exports in Google Colab

[Open the notebook in Colab](https://colab.research.google.com/github/gettodaze/OMSCS_ITR_QMatrix/blob/default/docs_agent/label_exports.ipynb). Choose **Save a copy in Drive** if you want a persistent personal copy, then run the cells in order. A standard CPU runtime is sufficient.

The notebook loads code from the public GitHub repository, mounts your Google Drive, processes a local snapshot of the exports, and writes results back to your chosen Drive folder. It prints only aggregate counts and labels. Google documents [opening notebooks and Drive access](https://research.google.com/colaboratory/faq.html) and the [Drive mount recipe](https://colab.research.google.com/notebooks/io.ipynb).

## Arrange your Drive files

Create this structure in My Drive:

```text
QMatrix/
  exports/
    Scopus/query1_batch1.ris
    Web of Science/query1_batch1.ris
    APA PsycInfo/query1_batch1.ris
    ERIC/query1_batch1.ris
    PubMed/query1_batch1.nbib
    IEEE Xplore/query1_batch1.ris
    ACM DL/query1_batch1.enw
  input.csv           # Optional old candidate records, for comparison only.
  export_counts.csv   # Optional expected counts per downloaded batch.
```

Only the `exports/` directory is required. It accepts RIS, NBIB, EndNote `.enw`, and `.txt` files containing one of those tagged formats. Put other files outside it. Provider-specific CSV, BibTeX, XML and API JSON are not supported by the native labeling reader. Use the formats in the [manual search/download instructions](manual_search_links.md).

Set `DATA_ROOT` in the notebook to `/content/drive/MyDrive/QMatrix`, or the location you chose. To include comparison/count checks, set `BASELINE_FILE = "input.csv"` and/or `COUNTS_FILE = "export_counts.csv"`; leave either blank to omit it. The counts CSV uses `file,expected_count`, with filenames relative to `exports/`, as described in the [export workflow](rayyan_exports.md).

## What runs

`prepare_rayyan.py` validates and concatenates the native records and reports metadata/counts. `label_exports.py` reads the validated originals and applies the same title, abstract and keyword rules used by `parse_records.py`. Missing fields remain empty; missing abstracts are counted. Labels are keyword-based suggestions that require review, not model-generated predictions or eligibility decisions.

The native preparation and labeling path uses only Python's standard library. No old-schema CSV conversion is required. Each raw record stays distinct, including overlaps between queries/databases. Each output record has its database, source filename, position and source-file checksum. Unknown tags and repeated values are retained. There are no database requests or model API calls in the labeling run.

Each run writes a separate timestamped folder under `QMatrix/output/`:

- `labels/labelled_records.csv`: common citation fields, suggested labels in their own column and notes, provenance, and one column per native tag. Repeated values in tag columns use JSON lists.
- `labels/labelled_records.jsonl`: every source field as a list, plus suggested labels, metadata and provenance.
- `labels/label_summary.json`: counts by database and label, and counts of missing abstracts/unlabeled records.
- `prepared/`: original downloads, native concatenations and the count/metadata audit.
- `run_metadata.json`: the exact GitHub commit used and run settings.

Count mismatches stop labeling and save the prepared files/audit into a separate Drive folder for investigation. Every run uses a fresh code checkout and data snapshot. The branch defaults to `default`; use a published tag for a fixed code version, and retain `run_metadata.json` for reproducibility.

## Rayyan and privacy

Use `prepared/by_database/` for native Rayyan imports with source-specific names. The CSV is useful for reviewing suggestions and has standard citation columns, but extra tag columns may be ignored by Rayyan. Importing notes does not establish that Rayyan creates its own label objects from them. Test a small sample before selecting the CSV for a full import. [Rayyan formats](https://help.rayyan.ai/hc/en-us/articles/4406426903825-Supported-File-Formats-for-Importing-into-Rayyan).

Keep the exports, results and any executed notebook containing record previews private. The repository notebook has no saved execution outputs. Mounting Drive gives notebook code access to Drive files; processing in Colab is a cloud use, subject to the applicable institution/provider permissions. See [data sharing guidance](data_sharing.md).

## Run locally

The same reader and labeler can run outside Colab:

```bash
uv run --no-project --with-requirements requirements.txt python label_exports.py input/exports
```

Use `--output <new-directory>` to choose the destination. Inputs are never rewritten. The old `parse_records.py` remains available for the historical candidate CSV.
