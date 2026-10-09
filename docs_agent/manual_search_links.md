# Manual database searches

Queries follow the working document's concepts and **2021–2027** retrieval filter. Sign in through your institution as needed. Apply the first-online-date cutoff and other eligibility criteria during screening. These searches have not been run or browser-validated.

Use full-record **RIS** exports where available, native **NBIB** for PubMed, and **EndNote (.enw)** for ACM. Keep all exported fields and the original files; there is no need to reshape them into the old CSV. Rayyan accepts these formats, but its import may normalize fields or replace source accession IDs. [Supported formats](https://help.rayyan.ai/hc/en-us/articles/4406426903825-Supported-File-Formats-for-Importing-into-Rayyan).

## Scopus

**Instructions**

1. Open Advanced document search and paste the query. Dates and English are included.
2. Record the search date, exact query, filters, and displayed count for each query before exporting.
3. Select all results (or successive batches), choose Export → RIS, and include all available citation, bibliographic, abstract and keyword fields. Download each batch. [Scopus export help](https://www.elsevier.support/scopus/answer/how-do-i-export-documents-from-scopus).
4. Save original downloads in `input/exports/Scopus/`, with query and batch numbers in filenames. Check that exported counts match the displayed counts; overlapping queries can contain duplicates. Then follow the [export preparation and Rayyan import workflow](rayyan_exports.md).

[Open search](<https://www.scopus.com/search/form.uri?display=advanced>)

**Search query 1**

```text
(TITLE-ABS-KEY(("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR TITLE-ABS-KEY(("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR TITLE-ABS-KEY(("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional"))) AND PUBYEAR > 2020 AND PUBYEAR < 2028 AND LANGUAGE(english)
```

## Web of Science

**Instructions**

1. Select Core Collection, open Advanced Search/Query Builder and paste the query. Dates and English are included.
2. Record the search date, exact query, filters, and displayed count for each query before exporting.
3. Select all results or a record range, choose Export → RIS, and select Full Record and Cited References where offered. Include abstracts and download successive ranges until every result is exported. [Export help](https://webofscience.zendesk.com/hc/en-us/articles/20135824927505-Saving-and-Exporting-Marked-Lists).
4. Save original downloads in `input/exports/Web of Science/`, with query and batch numbers in filenames. Check that exported counts match the displayed counts; overlapping queries can contain duplicates. Then follow the [export preparation and Rayyan import workflow](rayyan_exports.md).

[Open search](<https://www.webofscience.com/wos/woscc/advanced-search>)

**Search query 1**

```text
(TS=(("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR TS=(("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR TS=(("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional"))) AND PY=(2021-2027) AND LA=(English)
```

## APA PsycInfo

**Instructions**

1. Use your library's EBSCO link, select APA PsycInfo, and paste the query in Advanced Search. Apply 2021–2027 manually. Confirm TI/AB/KW/LA field support in your interface; the query includes English.
2. Record the search date, exact query, filters, and displayed count for each query before exporting.
3. Select the results, use Share/Export (or add them to the folder and open its Export manager), choose RIS, and include abstracts and all available fields. Download every batch; some interfaces deliver the bulk export by email. Menu names depend on your institution's interface.
4. Save original downloads in `input/exports/APA PsycInfo/`, with query and batch numbers in filenames. Check that exported counts match the displayed counts; overlapping queries can contain duplicates. Then follow the [export preparation and Rayyan import workflow](rayyan_exports.md).

[Open search](<https://search.ebscohost.com/>)

**Search query 1**

```text
((TI (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR AB (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR KW (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*))) OR (TI (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR AB (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR KW (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution))) OR (TI (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")) OR AB (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")) OR KW (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")))) AND LA English
```

## ERIC

**Instructions**

1. Use your library's EBSCO link, select ERIC, and paste the query in Advanced Search. Apply 2021–2027 manually. Confirm TI/AB/KW/LA field support in your interface; the query includes English.
2. Record the search date, exact query, filters, and displayed count for each query before exporting.
3. Select the results, use Share/Export (or add them to the folder and open its Export manager), choose RIS, and include abstracts and all available fields. Download every batch; some interfaces deliver the bulk export by email. Menu names depend on your institution's interface.
4. Save original downloads in `input/exports/ERIC/`, with query and batch numbers in filenames. Check that exported counts match the displayed counts; overlapping queries can contain duplicates. Then follow the [export preparation and Rayyan import workflow](rayyan_exports.md).

[Open search](<https://search.ebscohost.com/>)

**Search query 1**

```text
((TI (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR AB (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR KW (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*))) OR (TI (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR AB (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR KW (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution))) OR (TI (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")) OR AB (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")) OR KW (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")))) AND LA English
```

## PubMed

**Instructions**

1. Prefilled search. The query includes 2021–2027 and English; inspect Search Details for its translation.
2. Record the search date, exact query, filters, and displayed count for each query before exporting.
3. Choose Save → All results → PubMed format → Create file to download NBIB/tagged PubMed records, including available abstracts. If the export limit is reached, split into nonoverlapping date ranges and save every batch. [PubMed save help](https://pubmed.ncbi.nlm.nih.gov/help/#saving-citations-as-a-text-file).
4. Save original downloads in `input/exports/PubMed/`, with query and batch numbers in filenames. Check that exported counts match the displayed counts; overlapping queries can contain duplicates. Then follow the [export preparation and Rayyan import workflow](rayyan_exports.md).

[Open search](<https://pubmed.ncbi.nlm.nih.gov/?term=%28%28%28%22Q-matri%2A%22%5Btiab%5D+OR+%22Q+matri%2A%22%5Btiab%5D%29+AND+%28%22cognitive+diagnos%2A%22%5Btiab%5D+OR+%22diagnostic+classification%2A%22%5Btiab%5D+OR+%22diagnostic+assessment%2A%22%5Btiab%5D+OR+DINA%5Btiab%5D+OR+attribute%2A%5Btiab%5D+OR+skill%2A%5Btiab%5D+OR+%22knowledge+component%2A%22%5Btiab%5D+OR+assessment%2A%5Btiab%5D%29%29+OR+%28%28%22knowledge+component%2A%22%5Btiab%5D+OR+%22skill+model%2A%22%5Btiab%5D+OR+%22cognitive+model+discover%2A%22%5Btiab%5D+OR+%22knowledge+concept+tagging%22%5Btiab%5D+OR+%22skill+tagging%22%5Btiab%5D+OR+%22knowledge+tagging%22%5Btiab%5D+OR+%22item-skill%22%5Btiab%5D%29+AND+%28discover%2A%5Btiab%5D+OR+refin%2A%5Btiab%5D+OR+generat%2A%5Btiab%5D+OR+tagging%5Btiab%5D+OR+%22data+driven%22%5Btiab%5D+OR+%22learning+factors+analysis%22%5Btiab%5D+OR+automat%2A%5Btiab%5D+OR+extract%2A%5Btiab%5D+OR+attribution%5Btiab%5D%29%29+OR+%28%28%22cognitive+diagnostic+model%2A%22%5Btiab%5D+OR+%22cognitive+diagnosis+model%2A%22%5Btiab%5D+OR+%22diagnostic+classification+model%2A%22%5Btiab%5D+OR+%22DINA+model%2A%22%5Btiab%5D+OR+%22G-DINA%22%5Btiab%5D+OR+%22cognitive+diagnostic+assessment%2A%22%5Btiab%5D%29+AND+%28clinical%5Btiab%5D+OR+psychiatr%2A%5Btiab%5D+OR+psychopatholog%2A%5Btiab%5D+OR+%22mental+health%22%5Btiab%5D+OR+symptom%2A%5Btiab%5D+OR+DSM%5Btiab%5D+OR+personality%5Btiab%5D+OR+disorder%2A%5Btiab%5D+OR+depress%2A%5Btiab%5D+OR+anxiety%5Btiab%5D+OR+%22non-cognitive%22%5Btiab%5D+OR+noncognitive%5Btiab%5D+OR+%22socio-emotional%22%5Btiab%5D+OR+%22social-emotional%22%5Btiab%5D%29%29%29+AND+2021%3A2027%5Bdp%5D+AND+english%5Blang%5D>)

**Search query 1**

```text
((("Q-matri*"[tiab] OR "Q matri*"[tiab]) AND ("cognitive diagnos*"[tiab] OR "diagnostic classification*"[tiab] OR "diagnostic assessment*"[tiab] OR DINA[tiab] OR attribute*[tiab] OR skill*[tiab] OR "knowledge component*"[tiab] OR assessment*[tiab])) OR (("knowledge component*"[tiab] OR "skill model*"[tiab] OR "cognitive model discover*"[tiab] OR "knowledge concept tagging"[tiab] OR "skill tagging"[tiab] OR "knowledge tagging"[tiab] OR "item-skill"[tiab]) AND (discover*[tiab] OR refin*[tiab] OR generat*[tiab] OR tagging[tiab] OR "data driven"[tiab] OR "learning factors analysis"[tiab] OR automat*[tiab] OR extract*[tiab] OR attribution[tiab])) OR (("cognitive diagnostic model*"[tiab] OR "cognitive diagnosis model*"[tiab] OR "diagnostic classification model*"[tiab] OR "DINA model*"[tiab] OR "G-DINA"[tiab] OR "cognitive diagnostic assessment*"[tiab]) AND (clinical[tiab] OR psychiatr*[tiab] OR psychopatholog*[tiab] OR "mental health"[tiab] OR symptom*[tiab] OR DSM[tiab] OR personality[tiab] OR disorder*[tiab] OR depress*[tiab] OR anxiety[tiab] OR "non-cognitive"[tiab] OR noncognitive[tiab] OR "socio-emotional"[tiab] OR "social-emotional"[tiab]))) AND 2021:2027[dp] AND english[lang]
```

## IEEE Xplore

**Instructions**

1. Open Advanced/Command Search and run each query separately in All Metadata. Apply 2021–2027 and check English eligibility during screening.
2. Record the search date, exact query, filters, and displayed count for each query before exporting.
3. For each query, select the results, choose Export/Download Citations → RIS, and include abstracts where offered. Export all result pages or batches. Inspect the file for abstracts; download an additional full-metadata export if the citation export omits them. [Rayyan database import guidance](https://help.rayyan.ai/hc/en-us/articles/45589301098769-How-to-Import-References-from-Major-Databases).
4. Save original downloads in `input/exports/IEEE Xplore/`, with query and batch numbers in filenames. Check that exported counts match the displayed counts; overlapping queries can contain duplicates. Then follow the [export preparation and Rayyan import workflow](rayyan_exports.md).

[Open search](<https://ieeexplore.ieee.org/>)

**Search query 1**

```text
(("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*))
```

**Search query 2**

```text
(("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution))
```

**Search query 3**

```text
(("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional"))
```

## ACM DL

**Instructions**

1. Open Advanced Search and paste each query separately. Select metadata fields and the Full-Text Collection, then apply 2021–2027 and English. Repeat for all three concepts.
2. Record the search date, exact query, filters, and displayed count for each query before exporting.
3. For each query, select the results and choose Export Citation → EndNote, then download every batch as .enw. Inspect the downloaded records for abstracts (%X), keywords (%K), DOI (%R), and bibliographic details. Keep any richer supplementary export alongside it if these fields are omitted. [ACM guide](https://libraries.acm.org/binaries/content/assets/libraries/acm-digital-library-user-guide.pdf).
4. Save original downloads in `input/exports/ACM DL/`, with query and batch numbers in filenames. Check that exported counts match the displayed counts; overlapping queries can contain duplicates. Then follow the [export preparation and Rayyan import workflow](rayyan_exports.md).

[Open search](<https://dl.acm.org/search/advanced>)

**Search query 1**

```text
((("Q-matrix" OR "Q-matrices") OR ("Q matrix" OR "Q matrices")) AND (("cognitive diagnosis" OR "cognitive diagnostic") OR "diagnostic classification" OR "diagnostic assessment" OR DINA OR attribute* OR skill* OR "knowledge component" OR assessment*))
```

**Search query 2**

```text
(("knowledge component" OR "skill model" OR "cognitive model discovery" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution))
```

**Search query 3**

```text
(("cognitive diagnostic model" OR "cognitive diagnosis model" OR "diagnostic classification model" OR "DINA model" OR "G-DINA" OR "cognitive diagnostic assessment") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional"))
```
