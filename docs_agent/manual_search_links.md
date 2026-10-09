# Manual database searches

Generated from the working document's final concepts. No API keys or API calls are needed.

Sign in through your institution as needed. PubMed links embed the query; IEEE links use an unverified browser URL pattern. Other links open a search interface where you paste the query. The searches themselves have not been run or browser-validated.

Dates follow the documented retrieval filter, **2021–2027**. Apply the review's first-online-date cutoff and other eligibility criteria during screening.

For each search, record the date, displayed query/filters and result count, then export citation metadata including abstracts and identifiers where available. Merge overlapping concept searches and deduplicate across databases. Results can differ from the original October 8, 2026 search.

PubMed URL format: [official help](https://pubmed.ncbi.nlm.nih.gov/help/#creating-a-web-link-to-pubmed).

## Scopus — Final search

[Open search](<https://www.scopus.com/search/form.uri?display=advanced>)

Open Advanced document search and paste the query. Dates and English are included.

```text
(TITLE-ABS-KEY(("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR TITLE-ABS-KEY(("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR TITLE-ABS-KEY(("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional"))) AND PUBYEAR > 2020 AND PUBYEAR < 2028 AND LANGUAGE(english)
```

## Web of Science — Final search

[Open search](<https://www.webofscience.com/wos/woscc/advanced-search>)

Select Core Collection, open Advanced Search/Query Builder and paste the query. Dates and English are included.

```text
(TS=(("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR TS=(("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR TS=(("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional"))) AND PY=(2021-2027) AND LA=(English)
```

## APA PsycInfo — Final search

[Open search](<https://search.ebscohost.com/>)

Use your library's EBSCO link, select APA PsycInfo, and paste the query in Advanced Search. Apply 2021–2027 manually. Confirm TI/AB/KW/LA field support in your interface; the query includes English.

```text
((TI (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR AB (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR KW (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*))) OR (TI (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR AB (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR KW (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution))) OR (TI (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")) OR AB (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")) OR KW (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")))) AND LA English
```

## ERIC — Final search

[Open search](<https://search.ebscohost.com/>)

Use your library's EBSCO link, select ERIC, and paste the query in Advanced Search. Apply 2021–2027 manually. Confirm TI/AB/KW/LA field support in your interface; the query includes English.

```text
((TI (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR AB (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*)) OR KW (("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*))) OR (TI (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR AB (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution)) OR KW (("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution))) OR (TI (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")) OR AB (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")) OR KW (("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional")))) AND LA English
```

## PubMed — Final search

[Open search](<https://pubmed.ncbi.nlm.nih.gov/?term=%28%28%28%22Q-matri%2A%22%5Btiab%5D+OR+%22Q+matri%2A%22%5Btiab%5D%29+AND+%28%22cognitive+diagnos%2A%22%5Btiab%5D+OR+%22diagnostic+classification%2A%22%5Btiab%5D+OR+%22diagnostic+assessment%2A%22%5Btiab%5D+OR+DINA%5Btiab%5D+OR+attribute%2A%5Btiab%5D+OR+skill%2A%5Btiab%5D+OR+%22knowledge+component%2A%22%5Btiab%5D+OR+assessment%2A%5Btiab%5D%29%29+OR+%28%28%22knowledge+component%2A%22%5Btiab%5D+OR+%22skill+model%2A%22%5Btiab%5D+OR+%22cognitive+model+discover%2A%22%5Btiab%5D+OR+%22knowledge+concept+tagging%22%5Btiab%5D+OR+%22skill+tagging%22%5Btiab%5D+OR+%22knowledge+tagging%22%5Btiab%5D+OR+%22item-skill%22%5Btiab%5D%29+AND+%28discover%2A%5Btiab%5D+OR+refin%2A%5Btiab%5D+OR+generat%2A%5Btiab%5D+OR+tagging%5Btiab%5D+OR+%22data+driven%22%5Btiab%5D+OR+%22learning+factors+analysis%22%5Btiab%5D+OR+automat%2A%5Btiab%5D+OR+extract%2A%5Btiab%5D+OR+attribution%5Btiab%5D%29%29+OR+%28%28%22cognitive+diagnostic+model%2A%22%5Btiab%5D+OR+%22cognitive+diagnosis+model%2A%22%5Btiab%5D+OR+%22diagnostic+classification+model%2A%22%5Btiab%5D+OR+%22DINA+model%2A%22%5Btiab%5D+OR+%22G-DINA%22%5Btiab%5D+OR+%22cognitive+diagnostic+assessment%2A%22%5Btiab%5D%29+AND+%28clinical%5Btiab%5D+OR+psychiatr%2A%5Btiab%5D+OR+psychopatholog%2A%5Btiab%5D+OR+%22mental+health%22%5Btiab%5D+OR+symptom%2A%5Btiab%5D+OR+DSM%5Btiab%5D+OR+personality%5Btiab%5D+OR+disorder%2A%5Btiab%5D+OR+depress%2A%5Btiab%5D+OR+anxiety%5Btiab%5D+OR+%22non-cognitive%22%5Btiab%5D+OR+noncognitive%5Btiab%5D+OR+%22socio-emotional%22%5Btiab%5D+OR+%22social-emotional%22%5Btiab%5D%29%29%29+AND+2021%3A2027%5Bdp%5D+AND+english%5Blang%5D>)

Prefilled search. The query includes 2021–2027 and English; inspect Search Details for its translation.

```text
((("Q-matri*"[tiab] OR "Q matri*"[tiab]) AND ("cognitive diagnos*"[tiab] OR "diagnostic classification*"[tiab] OR "diagnostic assessment*"[tiab] OR DINA[tiab] OR attribute*[tiab] OR skill*[tiab] OR "knowledge component*"[tiab] OR assessment*[tiab])) OR (("knowledge component*"[tiab] OR "skill model*"[tiab] OR "cognitive model discover*"[tiab] OR "knowledge concept tagging"[tiab] OR "skill tagging"[tiab] OR "knowledge tagging"[tiab] OR "item-skill"[tiab]) AND (discover*[tiab] OR refin*[tiab] OR generat*[tiab] OR tagging[tiab] OR "data driven"[tiab] OR "learning factors analysis"[tiab] OR automat*[tiab] OR extract*[tiab] OR attribution[tiab])) OR (("cognitive diagnostic model*"[tiab] OR "cognitive diagnosis model*"[tiab] OR "diagnostic classification model*"[tiab] OR "DINA model*"[tiab] OR "G-DINA"[tiab] OR "cognitive diagnostic assessment*"[tiab]) AND (clinical[tiab] OR psychiatr*[tiab] OR psychopatholog*[tiab] OR "mental health"[tiab] OR symptom*[tiab] OR DSM[tiab] OR personality[tiab] OR disorder*[tiab] OR depress*[tiab] OR anxiety[tiab] OR "non-cognitive"[tiab] OR noncognitive[tiab] OR "socio-emotional"[tiab] OR "social-emotional"[tiab]))) AND 2021:2027[dp] AND english[lang]
```

## IEEE Xplore — Concept 1

[Open search](<https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText=%28%28%22Q-matri%2A%22+OR+%22Q+matri%2A%22%29+AND+%28%22cognitive+diagnos%2A%22+OR+%22diagnostic+classification%2A%22+OR+%22diagnostic+assessment%2A%22+OR+DINA+OR+attribute%2A+OR+skill%2A+OR+%22knowledge+component%2A%22+OR+assessment%2A%29%29>)

Prefilled URL pattern; not browser-verified. Confirm All Metadata search, apply 2021–2027, and check English eligibility. If the link loses the query, paste it below.

```text
(("Q-matri*" OR "Q matri*") AND ("cognitive diagnos*" OR "diagnostic classification*" OR "diagnostic assessment*" OR DINA OR attribute* OR skill* OR "knowledge component*" OR assessment*))
```

## IEEE Xplore — Concept 2

[Open search](<https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText=%28%28%22knowledge+component%2A%22+OR+%22skill+model%2A%22+OR+%22cognitive+model+discover%2A%22+OR+%22knowledge+concept+tagging%22+OR+%22skill+tagging%22+OR+%22knowledge+tagging%22+OR+%22item-skill%22%29+AND+%28discover%2A+OR+refin%2A+OR+generat%2A+OR+tagging+OR+%22data+driven%22+OR+%22learning+factors+analysis%22+OR+automat%2A+OR+extract%2A+OR+attribution%29%29>)

Prefilled URL pattern; not browser-verified. Confirm All Metadata search, apply 2021–2027, and check English eligibility. If the link loses the query, paste it below.

```text
(("knowledge component*" OR "skill model*" OR "cognitive model discover*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution))
```

## IEEE Xplore — Concept 3

[Open search](<https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText=%28%28%22cognitive+diagnostic+model%2A%22+OR+%22cognitive+diagnosis+model%2A%22+OR+%22diagnostic+classification+model%2A%22+OR+%22DINA+model%2A%22+OR+%22G-DINA%22+OR+%22cognitive+diagnostic+assessment%2A%22%29+AND+%28clinical+OR+psychiatr%2A+OR+psychopatholog%2A+OR+%22mental+health%22+OR+symptom%2A+OR+DSM+OR+personality+OR+disorder%2A+OR+depress%2A+OR+anxiety+OR+%22non-cognitive%22+OR+noncognitive+OR+%22socio-emotional%22+OR+%22social-emotional%22%29%29>)

Prefilled URL pattern; not browser-verified. Confirm All Metadata search, apply 2021–2027, and check English eligibility. If the link loses the query, paste it below.

```text
(("cognitive diagnostic model*" OR "cognitive diagnosis model*" OR "diagnostic classification model*" OR "DINA model*" OR "G-DINA" OR "cognitive diagnostic assessment*") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional"))
```

## ACM DL — Concept 1

[Open search](<https://dl.acm.org/search/advanced>)

Open Advanced Search and paste this concept query. Select metadata fields and the Full-Text Collection, then apply 2021–2027 and English. Repeat for all three concepts.

```text
((("Q-matrix" OR "Q-matrices") OR ("Q matrix" OR "Q matrices")) AND (("cognitive diagnosis" OR "cognitive diagnostic") OR "diagnostic classification" OR "diagnostic assessment" OR DINA OR attribute* OR skill* OR "knowledge component" OR assessment*))
```

## ACM DL — Concept 2

[Open search](<https://dl.acm.org/search/advanced>)

Open Advanced Search and paste this concept query. Select metadata fields and the Full-Text Collection, then apply 2021–2027 and English. Repeat for all three concepts.

```text
(("knowledge component" OR "skill model" OR "cognitive model discovery" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover* OR refin* OR generat* OR tagging OR "data driven" OR "learning factors analysis" OR automat* OR extract* OR attribution))
```

## ACM DL — Concept 3

[Open search](<https://dl.acm.org/search/advanced>)

Open Advanced Search and paste this concept query. Select metadata fields and the Full-Text Collection, then apply 2021–2027 and English. Repeat for all three concepts.

```text
(("cognitive diagnostic model" OR "cognitive diagnosis model" OR "diagnostic classification model" OR "DINA model" OR "G-DINA" OR "cognitive diagnostic assessment") AND (clinical OR psychiatr* OR psychopatholog* OR "mental health" OR symptom* OR DSM OR personality OR disorder* OR depress* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional"))
```
