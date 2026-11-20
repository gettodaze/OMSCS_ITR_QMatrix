# Full-text screening instructions

Version of 2026-10-23, revised after the pilot. The rules marked **[team default]** encode the
defaults proposed in `../Step 4 - Full-text screening plan.md`; they were adopted without change.

You are making the final eligibility decision for a systematic literature review titled "Recent
Advancements in Q-Matrix Generation Across Application Domains." Each record already passed
title/abstract screening. You now have its full text.

**Judge each paper on its own, from its own text only.**
- Don't let other papers in your batch shift your judgment.
- Don't use outside knowledge of the paper or its authors.
- Don't look anything up.

## What the review is about

The review maps how **Q-matrices** are generated, validated, and refined. A Q-matrix specifies which
skills or attributes each assessment item measures. Equivalent item-to-skill mappings count too:
knowledge-component (KC) models, skill models, and skill or knowledge-concept tags on exercises.

The review compares four **method families**, defined by what sets the mapping's entries:
- **expert:** content experts assign the entries;
- **statistical:** entries are estimated or revised from response data with a measurement model;
- **ML:** non-LLM machine-learning models trained on response data or item text;
- **LLM:** generative language models applied to item content.

It compares them across three **domains**:
- **education:** educational measurement, covering tests in any subject, including medical,
  physical and language education;
- **ITS/LA:** intelligent tutoring systems and learning analytics;
- **psych/clinical:** psychological and clinical assessment, covering non-cognitive constructs such
  as symptoms, personality, emotion, teamwork or self-regulation, in any setting.

Studies with only simulated data are coded **simulation**.

## The decision

At full text there is no Maybe. Decide **Include** or **Exclude** with a code.

- **Include** only if the paper meets every criterion below.
- **Exclude** with the code of the **first** criterion it fails, in the order listed.
- **Confidence:** high, medium or low.
  - Use low when the paper is genuinely borderline on what the criteria mean, not merely on
    detail.
  - When you use low, also fill `rule_question` (see Output).

**Errors are not symmetric.** Every included paper is read again in full during data extraction,
where a wrong Include can still be caught. A wrong Exclude is never seen again. So:
- Exclude on a clear failure you can show with a quote.
- When the text leaves an eligibility point truly undecidable, Include and say why in `flags`.

## Criteria, in order

**1. Full text in English (E8).**
- The main body (methods and results) must be in English.
- An English abstract or title with the body in another language is E8.
- A PDF that contains a complete English article plus pages in another language passes.
- If the paper is E8, stop: don't assess the other criteria.

**2. Eligible publication type (E6).**
- **Eligible:** peer-reviewed journal articles; peer-reviewed conference papers, full or short;
  chapters reporting original research in a peer-reviewed volume.
- **E6:**
  - conference abstracts, posters and extended abstracts;
  - doctoral-consortium papers and research plans, as a class, even when they report preliminary
    results;
  - editorials and errata;
  - dissertations.
- **[team default] Two pages or fewer is E6.** A paper of two pages or fewer, excluding
  references, is a conference abstract or poster summary.
- **[team default] Book chapters.** A chapter counts as peer-reviewed if any of these holds:
  - the volume is a conference-proceedings series;
  - the text or front matter says the chapters were refereed;
  - the volume is a series known for refereed research volumes, such as Springer Proceedings or
    Lecture Notes.

  Otherwise it is E6.
- **Preprints.** A full text that is an arXiv or other preprint copy of a published paper is
  judged as that published paper. Set the flag `preprint_version`.

**3. Date (E7).** E7 only if the full text states the paper was first published online before
1 January 2021. Otherwise pass.

**4. Item-to-attribute mapping (E1).** A Q-matrix or equivalent whose rows are assessment items,
exercises or practice problems that people answer. E1 if:
- there is no such mapping;
- or its rows are something else: instructional content, textbook sections, code submissions,
  worked examples.

**5. The study builds, estimates, validates, refines or designs the mapping (E2).**
- **Passes:**
  - generating, estimating or validating Q-matrix entries;
  - correcting misspecified entries;
  - choosing the number of attributes;
  - calibrating rows for new items;
  - tagging exercises with skills or concepts;
  - estimating an attribute hierarchy jointly with the Q-matrix;
  - developing a new diagnostic instrument for which the attributes and Q-matrix are built;
  - comparing candidate Q-matrices or item-attribute structures against data to choose one (by
    fit, CFA or a validation index), even when the candidates come from published frameworks;
  - building the study's own mapping by a described process, even when the paper's main
    contribution is something done afterwards with that mapping.
- **E2:**
  - the mapping is taken as given: from experts without a described process, from a framework or
    test blueprint, from an earlier paper (a citation for the Q-matrix), or from a benchmark
    dataset;
  - the contribution is something else done with a fixed mapping: adaptive-testing item selection,
    an estimation algorithm, reliability, DIF, model comparison, missing data, recommendation, or a
    substantive finding about learners.
- **Neural cognitive diagnosis and knowledge tracing.** Pass only if learning, refining,
  calibrating or completing the exercise–concept mapping is a stated aim **and** the learned or
  refined mapping is reported or evaluated: shown, compared with an expert mapping, or scored. A
  mapping used only internally is E2.
- **[team default] Attribute hierarchies.** Pass when the study specifies, compares or validates
  the attribute structure of a diagnostic instrument, by experts or from data. E2 when a given
  hierarchy is only used, or for prerequisite discovery among concepts with no item mapping.

**6. The model diagnoses discrete attributes (E3).** E3 if the model estimates only continuous
traits: multidimensional IRT, linear logistic test models. Cognitive and diagnostic
classification models, neural cognitive diagnosis, knowledge tracing, knowledge space theory,
Bayesian networks, and skill-tagging work all pass.

**7. Human respondents or psychometric simulation (E4).** E4 if AI systems or LLM-simulated
students are the ones being diagnosed.

**8. A primary study in scope (E5).** It proposes, compares or applies a mapping method, with data
from one of the three domains or simulated data.
- **Software and tutorial papers pass** when they evaluate or demonstrate a mapping method on
  simulated or real data, even if the journal labels them a review.
- **E5:**
  - reviews and surveys;
  - datasets or benchmarks with no method;
  - pure identifiability or completeness proofs with no method evaluated on data;
  - studies only of the effects of a misspecified Q-matrix;
  - data from outside the three domains, such as game players or workforce settings.
- **[team default] Expert-built Q-matrix without response data.** This passes if the paper
  actually specifies the mapping for items or criteria in one of the domains. Illustrative example
  items for a proposed instrument count. An example is a Q-matrix built from DSM-5 criteria for a
  proposed assessment. A conceptual framework that never specifies a mapping is E5.

**9. The procedure is described (E10).** The paper must describe how the mapping was built,
validated or refined in enough detail to name the method family: who or what set the entries, and
how.
- **E10:** "A Q-matrix was developed by content experts" with no account of the process.
- **Passes:** a short but concrete account, such as "three experts coded each item independently;
  disagreements were resolved by discussion; the Q-matrix was then validated with the GDI
  method".

## Output

Write one JSON object per paper, on one line, with exactly these keys:

```json
{"id": "F0000", "decision": "Exclude", "code": "E10", "confidence": "high", "reasoning": "...", "evidence": [{"page": 4, "quote": "..."}], "task": null, "family": null, "domain": null, "data": null, "flags": [], "rule_question": null}
```

- `decision`: "Include" or "Exclude".
- `code`: for Exclude, "E1" to "E10" (first failed criterion); for Include, null.
- `confidence`: "high", "medium" or "low".
- `reasoning`: two to four sentences.
  - **For Exclude:** name the criterion and explain the failure.
  - **For Include:** say what the paper does to the mapping, and how.
- `evidence`: one or two quotes from the text, each under 40 words, with the page number (from the
  `[[page N]]` markers). For Exclude, the quote shows the failure. For Include, it shows the mapping
  method.
- **For Include only** (null for Exclude). These are provisional codes for planning extraction;
  extraction may override them.
  - `task`: "generation", "validation", "refinement", or a combination joined with "+".
  - `family`: "expert", "statistical", "ML", "LLM", or a combination joined with "+".
  - `domain`: "education", "ITS/LA", "psych/clinical", "simulation", or a combination.
  - `data`: "simulated", "empirical" or "both".
- `flags`: a list, possibly empty, from this vocabulary:
  - `"preprint_version"`: the full text is a preprint copy;
  - `"extends_prior_version: <citation>"`: the paper says it extends an earlier conference or
    journal version of the same study;
  - `"text_problem"`: parts of the text were unreadable;
  - `"other_language_pages"`: the PDF also contains non-English pages;
  - `"undecidable: <criterion>"`: you included because the text could not settle that criterion.
- `rule_question`: null, or one sentence describing a gap in the criteria that this paper
  exposes. Fill it whenever confidence is low.

## Reading the text

- The text has `[[page N]]` markers. Cite those page numbers.
- If the text is garbled (shifted letters, symbols instead of words), read the PDF at the path
  given for that paper instead. Set the flag `text_problem` if any part stays unreadable.
- Long papers: the methods section and any section describing the Q-matrix, attributes or
  knowledge components carry the decision. Read them closely. Skim related work.
