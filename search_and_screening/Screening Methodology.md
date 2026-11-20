# Screening methodology

How the 1,389 candidate records from the final search are screened, step by step. Exclusion
codes (E1–E10) are the ones defined in `../Milestone 2 - Eligibility Criteria.md`; the abstract
screening rules are in `../Screening Strategy.md`.

## How the files work

Every step reads the previous step's **retained** file and writes two new workbooks:

- `Step N - <code> <name> - excluded.xlsx`: the records this step removed, each with *Decision*
  = Exclude, the code in *Exclusion reason*, the step in *Excluded at stage*, and the evidence in
  *Notes*.
- `Step N - <code> <name> - retained.xlsx`: everything else, unchanged, which becomes the next
  step's input.

Each workbook also has an **About** sheet giving the rule, the input file, the counts and when it
was built. Excluded plus retained always equals the step's input. The search results themselves
are never touched: steps start from `Candidate Records - Final Search-screening copy.xlsx`, a copy
of `../Candidate Records - Final Search.xlsx`.

## Steps

| Step | Criterion | How | In | Excluded | Retained |
|---|---|---|---|---|---|
| 1 | E6 publication type | Script, from metadata | 1,389 | 109 | 1,280 |
| 2 | E7 date | Script, from Crossref dates | 1,280 | 21 | 1,259 |
| 3 | E1–E5, title and abstract | LLM (Claude Opus 5.5), one decision and reason per record | 1,259 | 887 | 372 |
| — | Retrieval: full texts we can't get (no Georgia Tech access, or a security warning) | Scripts, Zotero and hand downloads; recorded in the status sheet | 372 | 9 *not retrieved* | 363 |
| 4 | Full text: E1–E10 except E9 | LLM (Claude Opus 5.5), one decision, reason and quoted evidence per paper | 363 | 91 | 272 |
| 4b | E9 duplicate reports | Script finds candidate pairs; decisions recorded in the script | 272 | 2 | 270 |
| 4c | E11 not a method study (adopted after full-text screening, with a revised RQ1) | LLM sorts each study into a group; script excludes all but group A | 270 | 160 | **110** |

Retrieval worked from **`Step 3 - E1-E5 LLM title-abstract - retained.xlsx`**: 179 records the
LLM marked Include and 193 it marked Maybe. Full-text screening worked from **`Retrieval -
retrieved.xlsx`**: 363 records, each with its PDF at `fulltext/<ID>.pdf`.

**The included studies are in `Step 4c - E11 not a method study - retained.xlsx`: 110 records.**
Each carries the LLM's provisional task, method family, domain and data codes for planning
extraction, and its step 4c group and reasoning. Their PDFs are copied, named by record ID, to
`Group A full texts/` for sharing with the team.

Retrieval is not an exclusion step. A record whose full text can't be obtained hasn't failed any
eligibility criterion; PRISMA 2020 reports it separately as *Reports not retrieved*. See
*Retrieving full texts* below.

### Step 1: E6, ineligible publication type

A record is excluded when its document-type labels (all databases' labels, combined) or its venue
show it is one of the types criterion C8 excludes:

| Type | Identified by | Excluded |
|---|---|---|
| Proceedings front matter | Scopus label "Conference review" (abstracts read "The proceedings contain N papers…") | 60 |
| Dissertation or thesis | Label "Dissertation" or "Dissertations/Theses", or venue *Dissertation Abstracts International*. Two dissertations also carry a journal-article label from another database; the venue catches them. | 37 |
| Erratum or correction | Labels "Erratum", "Correction", "Erratum/Correction" | 9 |
| Retracted publication | Labels "Retracted", "Retracted Publication" | 2 |
| Preprint | Label "Preprint" or an *rxiv* venue | 1 |

**Deliberately left for people to judge:**
- **Book chapters (~33):** chapters reporting original peer-reviewed research are eligible.
- **"Review" (35):** usually E5, but the label is sometimes wrong (F0101 is a primary methods
  paper).
- **"Note" and ERIC "Speeches/Meeting Papers":** these can be short research papers or
  peer-reviewed conference papers.

### Step 2: E7, first published before 2021

Criterion C9 dates a record by its **first online publication**, not its issue date. For every
record with a DOI, the script looks up Crossref's online, print and issued dates and takes the
earliest. The record is excluded if that date is before 1 January 2021. A record whose issue year
(column *Year*) is before 2021 is also excluded, since nothing is published online after its
issue year.

- **Result:** 21 excluded. Three had a 2020 issue year; 18 had a 2021 or 2022 issue year but were
  online in 2018–2020 (e.g., F0753, online 24 November 2020, issue 2021).
- **Guard against bad metadata:** a Crossref date more than 90 days before the DOI was
  registered is treated as an error and ignored. This rescued one record, F1335. Its DOI encodes
  10 February 2022, but Crossref gives a 2018 date.
- **Not checkable here:** 45 records have no DOI and 40 DOIs aren't in Crossref (18 are Zenodo
  DOIs, registered with DataCite; the rest are from smaller journals). For these 85 the issue year decides, so a 2021-issue record that was
  online in 2020 could slip through. Check the first online date at full text.
- Retained files carry a **First published (Crossref)** column showing the date used, so the date
  rule can be checked at full text.

### Step 3: E1–E5, title and abstract, screened by an LLM

**Model and setup.** Each record was screened by **Claude Opus 5.5 (`claude-opus-5-5`)**, run as
Claude Code subagents on 20 October 2026. Every subagent reported the same model ID.

- **The prompt is fixed.** It is `step3_llm/screening_prompt.md` (SHA-256 recorded in
  `step3_llm/run_log.json`): the review's scope, the three decisions, the decision sequence for
  criteria C1–C7, the hard-case rules from `../Screening Strategy.md`, and the output format.
- **Each subagent saw only the prompt and one batch.** A batch was 25 records, in randomized order
  (seed 8803; 51 batches, listed in `step3_llm/manifest.json`). Subagents had no other files, no
  web access, and no knowledge of the team's earlier decisions.
- **Records were judged one at a time.** Each got its own decision (Include, Maybe or Exclude), a
  confidence (high or medium), and a one-to-three-sentence reason. An exclusion's reason names the
  failed criterion and quotes the words in the title or abstract that fail it.
- **The decision rule favors keeping records.** Exclude only on a reason the title or abstract
  shows; doubt goes to Maybe; a low-confidence exclusion is not allowed. Include and Maybe both go
  to full text.
- **Limitation: records in a batch share context.** The prompt tells the model to judge each
  record independently. Even so, the 25 records in a batch were read in one context, not in 25
  separate calls, so there may be some carry-over between them. Randomized batch order spreads any
  such effect across topics and years. A re-run of the same batch is not guaranteed to reproduce
  the same decisions.
- **Provisional codes ride along.** For Include and Maybe, the LLM also recorded a provisional
  method family and domain. They are for planning the full-text work only, and extraction
  overrides them.

**Pilot before the run.** The prompt was piloted on two batches before the main run:

- **The 24 test-set studies.** The first version excluded 2 of them. F0049 was an expert-built
  Q-matrix in a conceptual framework, excluded for having no data. F0949 compared expert-specified
  attribute hierarchies.
- **25 records screened by hand during strategy work.** The LLM agreed on keep vs. exclude for
  24 of them.
- **Prompt revised.** The two test-set losses were gaps in the written criteria, not misreadings:
  the team had listed both papers as relevant. The prompt was changed so that both patterns are
  Maybe, and so that concept-tagging papers that name no diagnostic model are not treated as
  unclear. On re-run, 0 of 24 test-set studies were excluded.
- **Consequence for reporting.** Because the test set was used to tune the prompt, it is not an
  independent check of the final prompt.

**Completeness check.** The assembly step verifies that every record has exactly one well-formed
result. Two subagents skipped records: F0779 in batch 14, and F0093 and F0304 in batch 48. These
three were re-screened in their own batch (all three E1) and appended. The rerun is logged in
`run_log.json`.

**Result.** Of 1,259 records, **887 were excluded and 372 kept** (179 Include, 193 Maybe). By
code, the 887 exclusions break down as E1 402, E2 430, E3 11, E4 4 and E5 40. No test-set study
was excluded. Both step files carry the LLM's decision, code, confidence, reason, provisional
family and domain, and batch. For excluded records the reason is also in *Notes*.

The LLM's exclusions are final as recorded. No person re-screened them, so the methods must
state that title/abstract screening was done by the LLM alone (see *Reporting*).

### Step 4: full text, screened by an LLM

**Setup.** As in step 3, with these differences:

- **Model and prompt.** Claude Opus 5.5 (`claude-opus-5-5`), as Claude Code subagents, on
  2026-10-23. The prompt is `step4_llm/fulltext_screening_prompt.md`; its SHA-256 and the run
  details are in `step4_llm/run_log.json`.
- **Input: the paper's full text.** Each PDF's text was extracted with `[[page N]]` markers, so
  evidence can be cited by page.
- **Batches.** 74 randomized batches (seed 8804) of up to 5 papers and 60,000 words. Each
  subagent read only the prompt, its batch file, and its papers' text or PDFs. It read the PDF
  directly when the text layer was garbled, as for F0661.
- **No Maybe.** Each paper is Include, or Exclude with the code of the first failed criterion, in
  this order:
  1. language (E8);
  2. publication type (E6);
  3. date (E7);
  4. E1–E5;
  5. procedure described (E10).
- **Evidence.** Every decision carries a quote under 40 words with its page.
- **Doubt.** Errors are treated asymmetrically, as at step 3: when the full text truly cannot settle
  a criterion, the paper is included and flagged.
- **Low confidence.** A low-confidence decision must state the gap in the criteria it exposed (a
  "rule question").
- **Provisional codes.** For each Include, the LLM records task, method family, domain and data
  type. These are for planning extraction; extraction overrides them.

**Automatic checks given to the LLM as hints**, not decisions:

- **Non-English text:** F0522 and F0729 (Chinese), F0526 (Turkish), F0822 (Persian with an
  English extended abstract).
- **Garbled text layer:** F0661.
- **Two pages or fewer:** four SIGCSE papers.
- **Over 15,000 words:** 28 papers.

**Rules adopted for this step.** These were the four proposed defaults, adopted without change:

1. Papers of two pages or fewer are E6, as conference abstracts or posters.
2. A book chapter counts as peer-reviewed if any of these holds:
   - its volume is a proceedings series;
   - the volume states that chapters were refereed;
   - it belongs to a refereed research series.
3. An expert-built Q-matrix with no response data counts, if it specifies the mapping for items or
   criteria in a domain.
4. A study that specifies, compares or validates an instrument's attribute hierarchy passes E2.

**Pilot.** Eight batches before the main run.

- **The 24 test-set studies:** 23 Include. One was excluded: F0450, a doctoral-consortium paper,
  excluded under E6.
- **12 papers with known answers:** all decided as expected.
  - The four non-English papers were E8. F0822 was one of them: its English pages are only an
    extended abstract, and the body is in Persian.
  - The four 2-page papers were E6.
  - F0661 was read from its PDF.
- **Clarifications.** Five low-confidence pilot decisions exposed gaps in the criteria. The prompt
  was clarified on each:
  - doctoral-consortium papers are E6 as a class;
  - comparing candidate structures against data passes E2;
  - building the study's own mapping as a preparatory step passes E2;
  - software and tutorial papers that evaluate a method pass E5;
  - illustrative items count for an expert-built Q-matrix.
- **No pilot decision was carried over.** The main run re-screened all 363 papers, the pilot
  papers included, with the revised prompt.

**Completeness.** Every batch returned exactly one valid result per paper; no rerun was needed.

**Result.** 363 assessed; **91 excluded and 272 included.** The exclusions by code:

| Code | Excluded | Code | Excluded |
|---|---|---|---|
| E1 | 18 | E6 | 10 |
| E2 | 50 | E7 | 0 |
| E3 | 3 | E8 | 5 |
| E4 | 0 | E10 | 3 |
| E5 | 2 | | |

- **Step 3 decisions against step 4:**
  - Of step 3's 176 retrieved Includes, 158 stayed Include and 18 were excluded at full text.
  - Of the 187 Maybes, 114 were included and 73 excluded.
- **Test set:** one study excluded, F0450, the doctoral-consortium paper.
- **Low confidence:** 35 decisions, 29 Includes and 6 Excludes. Each carries a rule question in
  the step files, in the *FT rule question* column, for the team to settle and record in the
  criteria. The six low-confidence exclusions:
  - F0065, F0485 (E1);
  - F0092, F0500, F0724, F1022 (E2).

### Step 4b: duplicate reports (E9)

**Finding candidates.** `step4_llm_screen.py duplicates` lists pairs among the step 4 includes
that share either of these:

- a near-identical title (similarity of 0.85 or more);
- the same first author and year (±1) with overlapping titles.

**Decisions.** Each pair was read, and the decisions are recorded in the script (`E9_DECISIONS`,
`LINKED`). 13 candidate pairs were found.

- **Two duplicates, excluded under E9:**
  - F0996 duplicates F0995. They are the same article, and F0996 is the Scopus record with a
    mistyped DOI.
  - F0865 duplicates F0449. F0865 is the IMPS conference-proceedings version; F0449, the journal
    article, is kept.
- **One linked pair, both kept:** F1032 and F1325 use the same sample of 74 second-graders but
  report different analyses. Both records note the link.
- **The other ten pairs are separate studies.** Some share authors and topic but use different
  instruments or samples. For example, F1221 and F1346 have samples of 90 and 128 pupils.

**Result.** 272 in, **2 excluded, 270 included.**

**Flags for extraction:**

- **Preprints:** F0576, F0604, F0682 and F1169 are arXiv copies. Use the published versions where
  Georgia Tech has them.
- **Prior versions:** eight papers say they extend an earlier conference or journal version. See
  the *FT flags* column.

### Step 4c: E11, method studies only

**Why this step exists.** After step 4b, the team looked at what each of the 270 included studies
could contribute to the research questions. RQ2–RQ4 ask about the conditions under which Q-matrix
*methods* are tested, and about their evaluation criteria and limitations. Many included studies
build a Q-matrix for one test and report on something else. On 2026-10-27 the team chose to limit
the review to method studies (option 5 in `Step 4c - Team decision brief.html`), to add
criterion E11, and to revise RQ1.

**Revised RQ1 (adopted 2026-10-27):**

> How does the distribution of proposed Q-matrix generation, validation and refinement methods
> across method families (expert-informed, statistical, machine learning, LLM) differ between
> educational measurement and intelligent tutoring / learning analytics settings?

RQ2–RQ4 are unchanged. The revision makes three changes to RQ1:

- **Methods, not practice.** RQ1 now describes the methods researchers propose and test, not how
  Q-matrices are built in applied work.
- **Two domains, not three.** Only 4 method studies use psych/clinical data. They stay in for
  RQ2–RQ4 and are reported in a sentence, not as a comparison group. Simulation-only studies (6)
  are reported separately.
- **"Expert" becomes "expert-informed".** Only 1 method study is expert-only. Expert judgment
  appears in 18, nearly always combined with another family, such as an expert draft refined from
  data, or LLM output a person reviews.

**Counting rules for RQ1.** A study that combines families is counted under each family it uses.
A study's domain is the setting of the real data its method is tested on.

**E11, not a method study.** Exclude a study whose contribution isn't a method for generating,
validating or refining a Q-matrix. This excludes application and instrument studies, and
hierarchy-only studies.

**Numbering.** The decision brief calls this criterion E12, because it also proposed a different
E11 ("Q-matrix not evaluated") that the team did not adopt. The adopted criterion was renumbered E11
on 2026-10-31, so the codes run E1–E11 with no gap.

**How studies were sorted.** Each study was put in one group:

| Group | What it is | Studies | E11 |
|---|---|---|---|
| A | Method study: the contribution is a method for generating, validating or refining the mapping, and the method is evaluated | 110 | Retained |
| B | Application or instrument study whose Q-matrix is checked against evidence outside its own construction (fit comparison, GDI/PVAF, Wald, think-aloud, independent expert review) | 111 | Excluded |
| C | Application where the Q-matrix is only a preparatory step, with no evidence about its quality beyond its construction | 41 | Excluded |
| H | Hierarchy-only: the Q-matrix is taken as given, and the study's own mapping work concerns the attribute hierarchy | 8 | Excluded |

- **Model and prompt.** Claude Opus 5.5 (`claude-opus-5-5`), as Claude Code subagents, on
  2026-10-26. The prompt is `step4c_llm/classification_prompt.md` (SHA-256 `b10e02c1…0f57`).
- **Input.** The sort ran on each study's record from step 4: the title, the abstract, and the
  full-text screener's reasoning, quoted evidence and provisional codes. It was not a new read of
  the paper.
- **Batches.** 9 randomized batches of 30 (seed 8805, listed in `step4c_llm/manifest.json`).
- **Output.** Each study got a group, a study type, the evaluation criteria applied to the mapping
  or method, a confidence and a reason. A fifth group, U, was allowed when the record couldn't
  settle the group.
- **Pilot.** Before the run, 30 studies drawn at random (seed 2611) were sorted by hand from their
  step-4 reasoning. The LLM agreed on 26 of the 30. Two of the four disagreements fell on the A/B
  line (F0583 and F0727), one on A/H (F0796) and one on B/C (F1300). The prompt was not changed
  after the pilot.
- **Full-text check for U.** Six studies came back as U. Each was re-sorted from its full text,
  with U no longer allowed and page-cited evidence required (addendum
  `step4c_llm/fulltext_check.md`, SHA-256 `1be0741f…bc68`). One went to A (F0593) and five to C
  (F0467, F0650, F0937, F1318, F1370). The *Group source* column shows which studies were sorted
  from the full text.

**Confidence.** 82 of the 110 A calls are high confidence, 26 medium and 2 low (F0363, F1368). The
A/B line is the one E11 rests on. It is firmer than the B/C line, but the pilot shows it isn't
exact.

**Test set.** E11 excludes 8 of the 23 test-set studies still included after step 4: F0049,
F0178, F0307, F0496, F0518, F0924, F0949 and F1309. These are application or hierarchy studies,
and their exclusion follows from narrowing the scope, not from a misapplied rule. So step 4c
reports them instead of stopping on them, as earlier steps would.

**Result.** 270 in; **160 excluded (B 111, C 41, H 8), 110 included.** Of the 110, 98 propose a
new method, 11 compare existing methods and 1 is a software or tutorial paper.

**Files:**

- `Step 4c - RQ contribution groups.xlsx`: all 270 studies with their group, reasoning and
  evidence. Nothing is excluded in this file.
- `Step 4c - E11 not a method study - excluded.xlsx` (160) and `- retained.xlsx` (110): the
  step's usual pair.
- `Step 4c - Team decision brief.html`: the options the team chose between, with the counts.

**What this changes elsewhere.** The eligibility criteria need E11 added, the C6 rationale
reworded (it says RQ1 compares three domains), and C7 narrowed: C7 admits studies that "apply" a
Q-matrix method, and E11 now excludes those.

**Flags for extraction:**

- **Preprints:** all four arXiv copies flagged at step 4b (F0576, F0604, F0682, F1169) are in
  group A.
- **Prior versions:** the step-4b note on papers that extend an earlier version still applies to
  the A studies that carry the flag.
- **Linked pair:** F1032 and F1325, the linked pair from step 4b, are both group B and are
  excluded.

### Table of included studies (2026-11-03)

`included_table/` builds the 110-row LaTeX table (`Group Project/included_studies_table.tex`, three
`table*` parts) and the bibliography (`Group Project/included_studies.bib`, 104 entries; the six
studies already in the paper's `references.bib` reuse its keys). `fetch_bib.py` gets BibTeX for the
103 DOIs from doi.org (cached in `bib_raw.json`); `build.py` writes both files. Seven studies have no
DOI and are built from database metadata.

- **Year is the first-online year,** matching the date criterion (C9). For DOI records it is the
  publisher's registered date; for the rest, the database year. By year: 2021 10, 2022 16,
  2023 13, 2024 16, 2025 27, 2026 28. No study is dated 2027 (F0001, F0007 and F0009, which carry
  a 2027 issue date, were online in 2026). Twelve studies differ from the spreadsheet's issue year.
- **Characteristics are screening labels,** not extraction results: task, family, domain and data
  from step 4, study type and evaluation criteria from step 4c. Rebuild from extraction when it is
  done.
- **Publication type matches the bib entry type** (fixed 2026-11-04): a study is a conference paper
  if the database calls it one or its DOI record is a proceedings paper or chapter. Before the fix
  the table took the database label alone, which marked two proceedings papers as journal articles
  (`wang2021relevanceaware`, ICANN 2021; `fan2025adaptive`, UKICER 2025). 71 journal, 39
  conference. By year (journal/conference): 2021 6/4, 2022 10/6, 2023 10/3, 2024 14/2, 2025 15/12,
  2026 16/12. The figure is `Group Project/figure_papers_per_year.tex` (pgfplots).
- **Spreadsheet for charting:** `export_xlsx.py` writes `Group Project/Included Studies - Table 4
  data.xlsx` from the table, the bib and `keymap.json` (ID to citation key): one row per study,
  with 0/1 columns for each task, family, domain and evaluation code. Rerun it after any rebuild.

## Retrieving full texts

Every record kept at step 3 needs its full text before step 4. Two kinds of record are set aside
as **not retrieved** instead.

### Where full texts come from, in order

1. **Open-access copies.** These came from `fetch_oa_pdfs.py`, plus any free copy found later,
   such as the journal's own site, a repository or the author's page.
2. **Zotero's *Find Available PDF*, with the Georgia Tech VPN connected.** This reaches what
   Georgia Tech subscribes to.
3. **The browser, with the VPN connected or through the GT Library website.** This covers
   publishers whose sites block automated downloads: Elsevier, ACM, SAGE, Taylor & Francis,
   Wiley, APA and Emerald. Download the PDF and drag it onto the Zotero item.

`collect_fulltext.py` copies the PDFs from Zotero into `fulltext/`, named by record ID. It also
writes `fulltext/Full-text status.xlsx`, which shows for each record where its PDF came from or
what to try next.

### Rule 1: no access through Georgia Tech

**A record is *not retrieved: no GT access*** when every one of these is true:

- The publisher's page asks for payment, both with the VPN connected and through the GT Library
  website.
- The library catalog search finds no other way to get the full text.
- No free copy turns up in a search of the DOI and title, on Google Scholar's "All versions" or
  the journal's own site.

A preprint, such as arXiv, does not count as retrieved when the published version can't be had.
Its content may differ from the peer-reviewed paper.

**What's left out:** interlibrary loan and requests to authors. They take one to three weeks,
longer than the review's schedule allows. This narrows criterion C13 in the eligibility criteria,
which allowed both. State the change, and the number of records it affects, as a limitation.

### Rule 2: security warning during download

**A record is *not retrieved: security warning*** when every source tried produces a warning:

- the browser blocks the site or the download as unsafe;
- Windows Security or antivirus flags or quarantines the file;
- the "PDF" turns out to be an executable, an archive, or a file that asks to run code.

**What to do when it happens:**

- **Don't override the warning,** open the file, or turn off protection to get it.
- **Delete the file,** or leave it in quarantine.
- **Try the other sources** in the list above; a different source often has a clean copy.
- **Only if every source warns,** record the record as not retrieved.

### Recording it

In `fulltext/Full-text status.xlsx`:

- **Not retrieved (reason):** set to *no GT access* or *security warning*.
- **Retrieval notes:** say what was tried, with the date. For example: "2026-10-23: publisher
  paywall via VPN and proxy; no OA copy in Scholar." Name the warning if there was one.

Both columns survive a re-run of `collect_fulltext.py`. If a PDF turns up later, the reason
clears itself.

**First retrieval round (2026-10-22): one reason wasn't recorded.** Nine records were removed
from Zotero after retrieval failed: F0162, F0325, F0404, F0413, F0517, F0602, F1231, F1235 and
F1271. Eight had no GT access and one raised a security warning, but which one wasn't noted. All
nine carry the reason *no GT access or security warning*, and the flow diagram reports them as
8 and 1. Record the reason for each record from here on.

When retrieval is finished, `collect_fulltext.py --finalize` writes the step's pair of files
from the status sheet. It refuses while any record is still unaccounted for. The not-retrieved
records are reported, not excluded.

### Retrieval result (2026-10-22)

**All 372 full texts were sought: 363 retrieved and 9 not retrieved.**

- **Not retrieved (9):** F0162, F0325, F0404, F0413, F0517, F0602, F1231, F1235, F1271. Eight had
  no GT access and one raised a security warning; which one was not recorded. Five of the nine
  are Springer book chapters.
- **Files:** `Retrieval - retrieved.xlsx` (363) and `Retrieval - not retrieved.xlsx` (9). Both
  carry the PDF path, the retrieval source, the PDF check and the retrieval notes.
- **Where the 363 PDFs came from:**
  - Zotero, through the GT VPN, for most of them;
  - open-access downloads by script, from OpenAlex links and a title search for records without a
    DOI;
  - hand downloads in a browser for sites that block scripts.

  The status sheet records each record's source.
- **Every PDF was checked:** its first pages must contain the record's title, and near-empty files
  are rejected. One Zotero file was a printout of a viewer page (F0983) and was replaced. One was a
  whole 788-page journal volume (F1345); its article's 16 pages were cut out.

**For full-text screening** (listed in the *PDF check* column):

- **Possible E8 (full text not in English):** F0522 and F0729 are in Chinese.
- **E6 or eligible short paper:** F0121, F0324, F0329 and F0502 are 2-page SIGCSE papers. The
  team decides whether they are short papers, which are eligible, or conference abstracts, which
  are E6.
- **Preprints, not the published versions:** F0576, F0604, F0682 and F1169 are arXiv copies.
- **Text layer:** F0661's extractable text is scrambled, though the PDF reads correctly.
- **E9 duplicate:** F0996 is the same paper as F0995. A mistyped DOI in Scopus let it past
  de-duplication.
- **Peer review:** the remaining book chapters need their volume's peer review confirmed (see
  C8).

## The code

`prescreen_metadata.py` runs steps 1 and 2. Run it from the project root:

```bash
.venv/Scripts/python.exe "Group Project/Screening/prescreen_metadata.py"
```

- It reads the screening copy and writes the four step files, overwriting earlier versions.
- Crossref responses are cached in `crossref_dates.json`, so a re-run gives the same result
  without going online. `--offline` makes this strict: the run fails rather than looking anything
  up.
- **Two checks stop the run if they fail:** every input record must land in exactly one output
  file, and none of the 24 known-relevant studies in `test_set_dois.txt` (the search-validation
  set) may be excluded. A test-set study being excluded means a rule is wrong.
- The rules are constants near the top of each step (`E6_LABEL_RULES`, `E6_VENUE_RULES`,
  `EARLIEST_ELIGIBLE_YEAR`, `MAX_DAYS_BEFORE_REGISTRATION`), so a change the team agrees on is a
  one-line edit followed by a re-run.

`step3_llm_screen.py` handles step 3 around the LLM run:

- **`prepare`** splits Step 2's retained records into randomized batches in `step3_llm/batches/`.
- **`assemble`** checks that `step3_llm/results/` holds exactly one valid result per record,
  then writes the Step 3 excluded and retained files and reports any test-set exclusions.

`step4c_classify.py` handles step 4c:

- **`prepare`** writes the randomized batches and the pilot batch from step 4b's retained file.
- **`pilot`** compares the pilot results with the hand sort.
- **`report`** checks the results, takes the full-text results for U studies, prints the group
  tables, and writes `Step 4c - RQ contribution groups.xlsx`.
- **`e11`** applies E11. It writes the step's pair of files and copies the retained studies' PDFs
  to `Group A full texts/`, removing any PDF there that is no longer retained.

The LLM run itself happens between `prepare` and `assemble` (or `report`). Each batch gets one subagent with the
instruction to read `screening_prompt.md` and the batch file, and to write one JSON line per
record to `results/`. Pilot material is in `step3_llm/pilot/`, and the rerun in `step3_llm/rerun/`.

## Reporting

**The flow diagram** is `../PRISMA 2020 flow diagram.docx` (with a PDF and PNG beside it). It is
built by `prisma_flow_diagram.py` from PRISMA's own Word template
(`PRISMA_2020_flow_diagram_new_SRs_v1.docx`, version for new reviews searching databases and
registers only). The counts are written into the script, so change them there if a count changes.

In the PRISMA 2020 flow diagram, steps 1 and 2 belong under *Records removed before screening*,
as "marked as ineligible by automation tools" (130: 109 for publication type and 21 for date),
with the rules above stated in the methods.

Title/abstract screening reports **1,259 records screened** and **887 excluded**, with reasons
by code. The methods say:

- that an LLM made the title/abstract decisions alone, with no human screener (PRISMA item 8
  asks how many screened each record);
- which model, on what dates, and with what prompt (an appendix);
- how the prompt was piloted, on the test set and on hand-screened records.

PRISMA 2020 and the course both require disclosing automation and AI tools.

**Limitation: search vocabulary (found 2026-10-23, not acted on).** The search string named
item-to-skill mappings with a fixed list of terms. A probe of OpenAlex for 2021–2026 found
relevant papers the string never retrieved. They use these terms:

- "concept tagging" or "question tagging" of exercises;
- "knowledge point" labeling, common in Chinese tutoring-systems work;
- "knowledge concept" annotation;
- KC models described with verbs outside the action-term list (e.g., "co-engineering");
- the "attribute hierarchy method";
- "restricted latent class" models.

**Effect:** most of these fall in the tutoring-systems domain, so its share of studies is likely
understated. The rough estimate is 10–30 eligible studies missed.

**Why it wasn't fixed:** a supplementary search was judged right for a publishable review but
wasn't run, for lack of time. The methods report this as a limitation of the search.

Full-text retrieval reports **372 reports sought** and **9 reports not retrieved** (8 no GT
access, 1 security warning), leaving **363 reports assessed for eligibility**. The not-retrieved
records are not counted as exclusions. The methods
state the retrieval rules above, including that interlibrary loan and author requests were not
used.

**Full-text eligibility, PRISMA:**

- **Reports assessed:** 363.
- **Reports excluded, with reasons:** 253.
  - E1 18, E2 50, E3 3, E5 2, E6 10, E8 5, E10 3, all from step 4;
  - E9 2, the duplicate reports from step 4b;
  - E11 160, from step 4c.
- **Studies included:** 110.

**The methods say, as at step 3:**

- that the LLM made the full-text decisions alone, with no human screener;
- the model, the dates and the prompt;
- the pilot and how the prompt was clarified;
- the four rules adopted for this step.

**Step 4c: the methods must also say:**

- **E11 was added after full-text screening.** It was not in the eligibility criteria set before screening. RQ1 was
  revised at the same time: from three domains to two, and from how Q-matrices are produced to the
  methods proposed for producing them.
- **The search covered three domains.** The comparison was narrowed after screening, because
  only 4 method studies use psych/clinical data.
- **How the sort was done.** An LLM sorted the studies, from the full-text screener's records,
  with a 30-study hand-sorted pilot (26 of 30 agreed). The 6 unresolved studies were sorted from
  their full text.
- **The test-set loss.** E11 removed 8 of the test-set studies, as a consequence of the narrower
  scope.
- **The review is now about methods.** Applied validation evidence (group B) and expert-only
  Q-matrices are out of scope. This is a limitation of coverage.
