**Revised Research Questions**

RQ1. How does the distribution of Q-matrix generation, validation, and refinement studies (2021–2026) across four method families (expert-driven, statistical, machine learning, and LLM-based) differ between educational measurement, intelligent tutoring systems and learning analytics, and psychological and clinical assessment?

RQ2. How do the following conditions under which Q-matrix methods are tested vary across method families and domains: simulated or empirical data, sample size, numbers of items and attributes, response type (dichotomous or polytomous), attribute structure, diagnostic model, and, in simulations, the proportion of misspecified Q-matrix entries and item quality? 

RQ3. How do the following evaluation criteria, and the benchmark datasets used to apply them, vary across method families and domains: Q-matrix recovery, attribute classification accuracy, classification reliability, power and Type I error of validation tests, model fit, prediction of held-out responses, agreement with expert-specified Q-matrices, expert or think-aloud review, and computational cost? 

RQ4. Which author-reported limitations of Q-matrix methods recur across method families and domains?

**Revised Inclusion/Exclusion Criteria**

2.3 Inclusion and Exclusion  
2.3.1 Inclusion Criteria. Studies were included if they were published in peer-reviewed English conferences, journals or peer-reviewed edited volumes between January 2021 and the search date (October 8, 2026), as measured by first online publication date, and addressed the generation, validation, or refinement of a Q-matrix used to diagnose the skills or attributes that assessment items measure. Because intelligent tutoring research rarely uses the term “Q-matrix,” studies using equivalent terms more common to the field (e.g., knowledge-component models and skill tags) were included. To be eligible, a study was required to propose, compare, or apply such a method, using empirical data from one of our three domains (educational measurement, intelligent tutoring systems and learning analytics, and psychological and clinical assessment) or simulated data. Further, it had to describe how the Q-matrix was generated, validated, or refined in sufficient detail to assign it to one of our pre-defined method families and contribute to at least one of our pre-defined research questions. Studies that omitted an extracted data item were included, and the missing item was recorded as not reported.

2.3.2 Exclusion Criteria. Studies were excluded if they used the term Q-matrix in an unrelated context (for example, in encryption), or used “cognitive diagnosis” in the sense of cognitive impairment, were published before our pre-defined review period, had not yet received successful peer review, or were not available in full text in English. Dissertations were excluded. We also excluded duplicates of the same publications, counting each study only once, and any studies that did not contribute to our research questions, which we defined as studies reporting no Q-matrix method of their own. We also excluded studies using models that estimate continuous traits rather than diagnose attributes. Lastly, we did not include any publications that exclusively took advantage of pre-existing Q-matrices and did not contribute to their generation, validation, or refinement in any way, as our review is specifically about how Q-matrices are produced. 

We deployed these criteria both for the initial abstract-level screening and for the subsequent paper-level screening. Any records identified as failing a criterion either in abstract-level or paper-level screening were excluded.

**Revised Search Terms and Results**  
An initial scoping search was conducted across the following databases to develop a general sense of literature in the field, with 963 results found after deduplication was applied: Scopus, Web  
of Science Core Collection, APA PsycInfo, ERIC, ACM Digital Library, IEEE Xplore, and OpenAlex. Claude Opus 5.5 was used to assess the abstracts of scoping results to refine the search terms in order to achieve more relevant results, resulting in the following query (Scopus version):

( TITLE-ABS-KEY( ("Q-matri\*" OR "Q matri\*") AND ("cognitive diagnos\*" OR "diagnostic classification\*" OR "diagnostic assessment\*" OR DINA OR attribute\* OR skill\* OR "knowledge component\*" OR assessment\*) ) OR TITLE-ABS-KEY( ("knowledge component\*" OR "skill model\*" OR "cognitive model discover\*" OR "knowledge concept tagging" OR "skill tagging" OR "knowledge tagging" OR "item-skill") AND (discover\* OR refin\* OR generat\* OR tagging OR "data driven" OR "learning factors analysis" OR automat\* OR extract\* OR attribution) ) OR TITLE-ABS-KEY( ("cognitive diagnostic model\*" OR "cognitive diagnosis model\*" OR "diagnostic classification model\*" OR "DINA model\*" OR "G-DINA" OR "cognitive diagnostic assessment\*") AND (clinical OR psychiatr\* OR psychopatholog\* OR "mental health" OR symptom\* OR DSM OR personality OR disorder\* OR depress\* OR anxiety OR "non-cognitive" OR noncognitive OR "socio-emotional" OR "social-emotional") ) ) AND PUBYEAR \> 2020 AND PUBYEAR \< 2028 AND LANGUAGE(english)

The above query combines three main search concepts with OR. Within each concept, synonyms were joined with OR and paired with context terms using AND, with quotation marks for phrases and wildcards for word endings. Concept 1 targeted studies that use the term “Q-matrix,” with context terms (e.g., cognitive diagnosis, attribute, skill) to exclude unrelated uses of the term in fields like encryption. Concept 2 targeted intelligent tutoring research, which typically describes equivalent mapping as knowledge-component or skill models; we required action terms (e.g., discover\*, generat\*, refin\*) so that studies merely using these models were not returned. We added “attribution” after the scoping search missed a known relevant study. Concept 3 targeted psychological and clinical studies by pairing diagnostic model names (e.g., “G-DINA”) with clinical terms; we used model names rather than “cognitive diagnos\*” because the broader term mostly returned studies of cognitive impairment. We did not include method-specific terms, so the search would not favor any of the method families compared in RQ1.

We validated the search string against a test set of 20 known relevant studies, selected in part to cover all four method families and all three domains, including studies that do not use the term “Q-matrix.” In Scopus, which indexes all 20, a query for the test set’s DOIs combined with “AND NOT” the final string returned no records, confirming that the string retrieves every test study; Web of Science, which indexes 17, gave the same result. One seed study (Shi et al., 2024\) had been missed by the scoping string; adding “attribution” to the second search concept corrected this. Because fifteen test studies came from the scoping results, the test mainly confirms that refining the string lost no relevant records; the five seed studies provide the independent check.

The final search query was run on Scopus,Web of Science Core Collection, APA PsycInfo, ERIC, PubMed, ACM Digital Library, and IEEE Xplore, except for database-specific revisions tied to specific search syntax. Where a database’s syntax requirements didn’t permit a date range filtering as part of the query, the platform’s date filter was applied to limit to publications occurring between 2021-2027.

In some cases, the search had to be broken up into segments due to length constraints (i.e., IEEE Xplore and ACM Digital Library). Here are examples of the syntax differences:

| Database | Scoping Syntax | Wildcards | Quoted phrases | Query structure |
| ----- | ----- | ----- | ----- | ----- |
| **Scopus** | `TITLE-ABS-KEY( … )` around each concept | `*` anywhere, including inside phrases | Double quotes \= loose phrase; punctuation ignored, so `"Q-matri*"` ≈ `"Q matri*"` | One query; three concepts joined by OR |
| **Web of Science** | `TS=( … )` around each concept | `*` anywhere, including inside phrases | Hyphen treated like a space | One query; three concepts joined by OR |
| **PsycInfo / ERIC (EBSCOhost)** | `TI ( … ) OR AB ( … ) OR KW ( … )` around each term block | `*` anywhere, including inside phrases | Standard phrase search | One query; three concepts joined by OR |
| **PubMed** | `[tiab]` after every term | `*` at the end of a word; needs at least 4 characters before it | Quoted phrase \+ `[tiab]` allows truncation | One query; three concepts joined by OR |
| **IEEE Xplore** | None (defaults to All Metadata) | `*` allowed, including inside phrases; maximum 10 per search | Standard phrase search | Three searches, one per concept |
| **ACM DL** | Set by the dropdown, not in the query | `*` on single words only; ignored inside quotes | Phrases spelled out (`"Q-matrix" OR "Q-matrices"`); plurals and stems matched automatically | Three searches, one per concept |

The final searches yielded 836 unique records, as follows:

| Database | Dates of Coverage | Records Found |
| ----- | :---- | ----- |
| Scopus (Elsevier) | Records back to 1788; comprehensive from 1970 | 621 |
| Web of Science Core Collection (Clarivate) | unavailable | 411 |
| APA PsycInfo (EBSCOhost) | 1887 to present, with abstracts from 1995 onward | 125 |
| ERIC (EBSCOhost) | 1966–present  | 72 |
| PubMed (NLM) | 1946–present, with selected older citations back to 1781 | 119 |
| IEEE Xplore | 1872–present for selected content; full text mainly from 1988 | 252 |
| ACM Digital Library (Full-Text Collection) | Full-Text Collection from 1951 | 26 |
| **Total** |  | **1,626** |
| Duplicates removed |  | 790 |
| **Unique records** |  | **836** |

All databases were searched on October 8, 2026\. 

Citation search was not used. 

An initial calibration batch of papers was screened and the extraction methodology tested by two team members. Final screening \[still to be done\] was divided approximately evenly among all five team members, with each member processing approximately 167 papers and no duplicate processing of papers.

The 20 test documents included:

| Paper | Family / domain | DOI |
| :---- | :---- | :---- |
| Qin & Guo (2024), machine learning for Q-matrix validation | ML  · ed. measurement | 10.3758/s13428-023-02126-0 |
| Fu et al. (2024/25), regularized Q-matrix validation | Statistical · ed. measurement | 10.3102/10769986241240084 |
| Shi et al. (2024), KC attribution problem for programming, *JEDM*  | ML · ITS | 10.5281/zenodo.10844782 |
| Moore et al. (2024), generating and tagging KCs from MCQs, L@S | LLM · ITS | 10.1145/3657604.3662030 |
| Tan et al. (2022/23), CDM tutorial for mental-health symptom profiles | Statistical · clinical | 10.1007/s11121-022-01346-8 |
| Qin, Bao & Guo (2026), Q-matrix validation toolkit | Statistical · ed. measurement | 10.3758/s13428-026-02991-5 |
| Wang et al. (2026), Bayesian Q-matrix and hierarchy estimation | Statistical · ed. measurement | 10.1017/psy.2026.10093 |
| Wang et al. (2026), Bayesian network structure learning for the Q-matrix | Statistical · ed. measurement | 10.3102/10769986251334789 |
| Sun et al. (2025), regularization \+ logistic regression validation | Statistical · ed. measurement | 10.1111/bmsp.12346 |
| Cai & Min (2025), EFA to inform Q-matrix specification | Expert-driven \+ Statistical · ed. measurement | 10.1080/15434303.2025.2536838 |
| Lin et al. (2025), Q-matrix revision in chemistry via SEM | Expert-driven \+ Statistical · ed. measurement (applied) | 10.3389/fpsyg.2025.1647968 |
| Xiong et al. (2024), sparse NMF Q-matrix estimation | Statistical · ed. measurement | 10.3758/s13428-024-02442-z |
| Demirtaş (2024), novel KC models for programming (EDM) | Statistical (LFA-style) · ITS | 10.5281/zenodo.12730015 |
| Zhang et al. (2026), residual Q-matrix refinement for neural CD | ML · ITS | 10.1109/icaisisas68969.2026.11567788 |
| Lopes et al. (2026), LLM Q-matrix generation | LLM · ed. measurement | 10.1109/access.2026.3683811 |
| Amoruso & Demara (2025), zero-shot LLM skill classification | LLM · ITS | 10.1145/3716368.3735218 |
| Rezazadeh et al. (2026), DCMs for emotional-behavioral diagnosis | Expert-driven · clinical | 10.1007/s10578-026-01972-1 |
| Jia & Liu (2026), CD-CAT for internet gaming disorder | Expert-driven · clinical | 10.3390/bs16040558 |
| Nájera et al. (2021), number of attributes in CDMs | Statistical · ed. measurement | 10.3389/fpsyg.2021.614470 |
| Zhang et al. (2026), human-AI Q-matrix refinement | LLM-based \+ ML · ITS | 10.1007/978-3-032-29760-0\_30 |

***Internal Team Only Notes:***  
Here are the revisions to the milestone 1 search query and their reasoning:

| Change | Evidence |
| ----- | ----- |
| Concept 2: added `attribution` and `"item-skill"` | September’s recall check missed Shi et al. (2024), which talks about knowledge-component “attribution.” The final Scopus search now finds it. |
| Concept 3: `"cognitive diagnos*" OR "diagnostic classification*"` became model names (`"cognitive diagnostic model*"`, `"DINA model*"`, `"G-DINA"`, `"cognitive diagnostic assessment*"`, and so on) | This was the refinement I mentioned in our meeting. In Scopus, the original wording found 1,292 more records; 1,290 were medical or dementia papers, and the 2 relevant ones are now recovered by `"cognitive diagnostic assessment*"`. |
| Concept 3: added `disorder*`, `depress*`, `anxiety`, `"non-cognitive"` and the socio-emotional terms | They widen coverage of the thinnest domain. This found new relevant studies on social anxiety, eating-disorder screening and forced-choice personality assessment. |
| Tested and **not** added: `"knowledge point*"`, `"skill map*"`, `label*`, `mapping`, `DINO`, `LCDM`, bare `DINA` | Each added mostly noise, or nothing new. |

Files containing the exported search results are here: [https\://drive.google.com/drive/folders/1YtyfmFBGlJ8mWDM4m2XBVrQgKizok8j9?usp=drive\_link](https://drive.google.com/drive/folders/1YtyfmFBGlJ8mWDM4m2XBVrQgKizok8j9?usp=drive_link) 

The combined, de-duplicated list for the 836 final candidates is here: [https\://docs.google.com/spreadsheets/d/1QmpbiOujV1agWkQK5SMCzPoCl9nZM-Zm/edit?usp=drive\_link\&ouid=110706820617788411165\&rtpof=true\&sd=true](https://docs.google.com/spreadsheets/d/1QmpbiOujV1agWkQK5SMCzPoCl9nZM-Zm/edit?usp=drive_link&ouid=110706820617788411165&rtpof=true&sd=true)

