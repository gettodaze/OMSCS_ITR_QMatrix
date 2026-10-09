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

Count mismatches stop labeling and save the prepared files/audit into a separate Drive folder for investigation. Every run uses a fresh code checkout and data snapshot. The notebook fetches and checks out the exact code commit `12112a782d0a4d049d6991177bb0f2cade529874` in detached mode, and verifies that HEAD matches that SHA. Later branch updates cannot change the code used by this notebook. Keep `run_metadata.json` for reproducibility. To intentionally update the code, test a new commit and replace `CODE_REF` with its full 40-character SHA.

## Customize labeling directly in the notebook

The optional customization cell defines `custom_labels(record: ExportRecord) -> list[Label | str]`. Uncomment that function and `custom_labeler = custom_labels` to enable it. Leave `custom_labeler = None` for the default rules. The labeling cell passes your callback explicitly to `label_exports(..., labeler=custom_labeler)`; no module monkey-patching is needed.

`ExportRecord` is a frozen dataclass exposing all fields:

- Citation content: `title`, `abstract`, `authors`, `keywords`, `notes`.
- Bibliographic details: `journal`, `issn`, `volume`, `issue`, `pages`, `year`, `publisher`, `url`, `doi`, `document_type`, `language`.
- Provenance: `key`, `database`, `source_file`, `source_format`, `source_index`, `source_sha256`.
- Native export fields: `source_fields`, a read-only mapping from every original tag to a tuple of its values. This includes repeated fields, affiliations, subject headings, identifiers, and provider-specific fields that have no normalized counterpart.

`authors` and `keywords` are tuples; the other common citation fields are strings, empty when missing. `source_index` is an integer. Native type codes vary by format: RIS `CONF`/`CPAPER`, EndNote `Conference Paper`, and PubMed publication-type names require appropriate rules.

Call `default_labels(record)` if you want to extend the existing suggestions, or omit that call to replace them. Return existing `Label` enum members and/or custom string names in a list. Empty names and invalid label values are rejected; repeated names are removed in output order. Changes do not alter source records.

The customization cell links to the exact source files: [record dataclass, default adapter and writer](https://github.com/gettodaze/OMSCS_ITR_QMatrix/blob/12112a782d0a4d049d6991177bb0f2cade529874/label_exports.py) and [default categories, patterns and matching function](https://github.com/gettodaze/OMSCS_ITR_QMatrix/blob/12112a782d0a4d049d6991177bb0f2cade529874/parse_records.py). Default rules continue to use title, abstract and keywords; your custom function can use every record field.

After changing rules, rerun from “Prepare native files and check counts” through the remaining cells. The summary identifies custom callbacks, and the run metadata records that customization was enabled. Retain the edited notebook to reproduce your custom logic; the GitHub revision alone does not capture notebook edits.

## Rayyan and privacy

Use `prepared/by_database/` for native Rayyan imports with source-specific names. The CSV is useful for reviewing suggestions and has standard citation columns, but extra tag columns may be ignored by Rayyan. Importing notes does not establish that Rayyan creates its own label objects from them. Test a small sample before selecting the CSV for a full import. [Rayyan formats](https://help.rayyan.ai/hc/en-us/articles/4406426903825-Supported-File-Formats-for-Importing-into-Rayyan).

Keep the exports, results and any executed notebook containing record previews private. The repository notebook has no saved execution outputs. Mounting Drive gives notebook code access to Drive files; processing in Colab is a cloud use, subject to the applicable institution/provider permissions. See [data sharing guidance](data_sharing.md).

## Run locally

The same reader and labeler can run outside Colab:

```bash
uv run --no-project --with-requirements requirements.txt python label_exports.py input/exports
```

Use `--output <new-directory>` to choose the destination. Inputs are never rewritten. The old `parse_records.py` remains available for the historical candidate CSV.
