# Search and screening code

The code and prompts behind the paper's search (§3.2), study selection (§3.3) and table of
included studies, linked from Appendix B. Data files are not included: database exports, candidate-record workbooks, the model's
batch and result files, and full texts stay local for the licensing reasons given in the
repository README.

The files are copied as they were run. Their paths assume the original project layout, so they will
not run from this folder unchanged: `search_strings.py` and `merge_exports.py` lived in `tools/`,
and the screening scripts lived in `Group Project/Screening/`, beside their input workbooks.

## Search

| File | What it does |
|---|---|
| `search_strings.py` | Holds the search terms once and renders every database's query from them. Run it to print the 24 searches of record from 9 October 2026; `--latex` prints them as the paper's Appendix A listings. |
| `merge_exports.py` | Merges the database exports, normalises DOIs and titles, removes duplicates, and writes the candidate-record workbook with stable record IDs. |

## Screening

`Screening Methodology.md` documents every step: its rules, counts, model, and validation. The
screening scripts refer to it.

| Step | File | What it does |
|---|---|---|
| 1–2 (E6, E7) | `prescreen_metadata.py` | Applies the publication-type and date rules from bibliographic metadata and Crossref dates. |
| 3 (E1–E5) | `step3_llm_screen.py` | Prepares randomised title-and-abstract batches for the model, assembles its decisions, and draws the blind validation sample. |
| 3 | `step3_llm/screening_prompt.md` | The prompt given to the model. |
| 3 pilot | `step3_llm/pilot/compare_pilot.py` | Compares the two pilot runs with known answers: the 24 test-set studies (all should be retained) and 25 records screened by hand. |
| Retrieval | `fetch_oa_pdfs.py`, `collect_fulltext.py` | Finds and downloads open-access PDFs via OpenAlex, and collects all full texts by record ID with a title check. |
| 4 (E1–E10) | `step4_llm_screen.py` | Extracts full text, prepares batches, assembles the model's full-text decisions, and lists candidate duplicate reports (E9). |
| 4 | `step4_llm/fulltext_screening_prompt.md` | The prompt given to the model. |
| 4c (E11) | `step4c_classify.py` | Prepares batches and tabulates the model's classification of what each study contributes. |
| 4c | `step4c_llm/classification_prompt.md`, `step4c_llm/fulltext_check.md` | The prompts given to the model. The second applies to the studies the first pass could not place. |

The model (Claude Opus 5.5) ran outside these scripts, as Claude Code subagents. Each subagent saw
only the prompt and one batch file. The scripts prepare the batches and check and assemble the
results.

## Included-studies table

| File | What it does |
|---|---|
| `included_table/fetch_bib.py` | Fetches BibTeX for each included study's DOI from doi.org. |
| `included_table/build.py` | Builds `included_studies.bib` and the paper's LaTeX table of the 110 included studies. |
| `included_table/export_xlsx.py` | Exports that table to a workbook, with indicator columns for counting. |

Requirements: Python 3.11, `openpyxl`, `xlrd` (Web of Science `.xls` exports), and `pymupdf`
(full-text extraction).

## AI usage

These scripts were written with Claude.
