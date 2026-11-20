# Title/abstract screening instructions

You are screening records for a systematic literature review titled "Recent Advancements in Q-Matrix
Generation Across Application Domains." Each record is a title, abstract, keywords, venue, year and
document type. Judge each record **on its own**, from its own title and abstract only. Do not let
earlier records in a batch shift your judgment, and do not use outside knowledge of the paper.

## What the review is about

The review maps how **Q-matrices** are generated, validated, and refined, 2021–2026. A Q-matrix
specifies which skills or attributes each assessment item measures. The review compares four
method families (expert-driven, statistical, machine learning, LLM-based) across three domains:

- educational measurement, covering tests and assessments in any subject, including medical,
  physical and language education;
- intelligent tutoring systems and learning analytics;
- psychological and clinical assessment, covering non-cognitive constructs such as symptoms,
  personality, emotion, teamwork and self-regulation, in any setting.

Studies using only simulated data are eligible too.

Intelligent tutoring research rarely says "Q-matrix". **Equivalent item-to-skill mappings count:**
knowledge-component (KC) models, skill models, skill or knowledge-concept tags on exercises, and
attribute specifications.

Publication type and date have already been screened. Language and the detail of the construction
procedure are checked later at full text, so ignore them here.

## The three decisions

- **Include:** the title and abstract show that every question below is answered "yes".
- **Maybe:** no question is clearly "no", but at least one can't be settled from the title and
  abstract. Maybe goes to full-text review.
- **Exclude:** at least one question is **clearly "no"**, and you can point to the words in the
  title or abstract that show it.

**Errors are not symmetric.** A wrong Exclude loses a study permanently. A wrong Maybe costs one
full-text read. When in doubt, choose Maybe. Never Exclude with low confidence.

## Decision sequence

Ask these questions in order. If you exclude, the code is that of the **first** question answered
"no".

1. **Is there an item-to-attribute mapping (E1)?** That means a Q-matrix or equivalent whose rows
   are assessment items, exercises or practice problems that learners or respondents answer, and
   whose columns are skills, attributes, knowledge components or concepts.
   - "No" means "Q matrix" in another sense: encryption, Fibonacci or Kalman matrices, MRI or SAR
     safety, population genetics (STRUCTURE plots), Q-learning, Markov chains, Q methodology.
   - "No" also means "cognitive diagnosis" meaning diagnosis of cognitive impairment or dementia.
   - "No" also means "skills" or "knowledge components" in robotics, manufacturing, software
     engineering, workforce or job matching, or health-behavior models such as
     Information-Motivation-Behavioral Skills.
   - "No" also means mappings whose rows are not items: concepts extracted from textbooks or
     instructional units without linking them to exercises, worked examples, or code submissions.
2. **Does the study build, estimate, validate, refine or design that mapping (E2)?** Examples:
   proposing or applying a method that generates or estimates Q-matrix entries from data, item
   text or experts; validating or correcting a Q-matrix; choosing the number of attributes;
   calibrating Q-matrix rows for new items; estimating an attribute hierarchy *jointly* with the Q-matrix;
   tagging exercises with skills or concepts; building a diagnostic instrument for which attributes
   were identified and a Q-matrix developed; evaluating a Q-matrix with learning curves or fit.
   - **"No"** when the mapping is only used as given: adaptive-testing item selection, estimation
     algorithms, reliability, DIF, model comparison or missing-data methods with a fixed
     Q-matrix, hierarchy or prerequisite learning without the Q-matrix, recommendation or
     learning-path systems, and substantive studies reporting who masters what.
   - **Neural cognitive diagnosis and knowledge tracing:** answer "no" when the Q-matrix or
     exercise–concept relation is only an input or an embedding. Answer "yes" (or "unclear") only
     when learning, refining, calibrating, completing or discovering the exercise–concept mapping
     is a **stated aim**.
   - **Applied diagnostic-model studies:** ask what the paper contributes. Answer "yes" or
     "unclear" when it is a new instrument, attribute model, or retrofit, and the abstract
     mentions identifying attributes or developing or validating a Q-matrix. Answer "unclear" when
     it develops a new diagnostic test without saying how the attributes were set. Answer "no"
     when the contribution is a finding about learners or teachers and the abstract says nothing
     about building the mapping, or when the Q-matrix is taken from a framework or earlier study.
   - **Attribute hierarchies:** answer "unclear" when a study specifies, compares or validates the
     attribute structure (hierarchy) of a diagnostic instrument, by experts or from data. Part of
     the attribute specification may come with it. Answer "no" only for prerequisite or relation
     discovery among concepts with no item mapping, or when a given hierarchy is just used.
3. **Does the model diagnose discrete attributes (E3)?** "No" means the model estimates continuous
   traits only: multidimensional IRT, linear logistic test models. ("LLM" sometimes means a
   linear logistic model, not a large language model.) Diagnostic classification and cognitive
   diagnosis models, neural cognitive diagnosis, knowledge tracing, knowledge space theory and
   Bayesian networks all count as "yes". A skill-tagging or KC-mapping study that names no model
   at all is also "yes": the mapping is the object, and this question only screens out
   continuous-trait models.
4. **Are the respondents human, or simulated from a psychometric or learner model (E4)?** "No"
   means AI systems or LLM-simulated students are the ones being diagnosed.
5. **Is it a primary study in scope (E5)?** That means it proposes, compares or applies a method,
   using data from one of the three domains or simulated data. Software or tutorial papers that
   evaluate a method count. "No" means any of these:
   - reviews and surveys, commentaries and editorials;
   - datasets or benchmarks only;
   - purely theoretical work, such as identifiability or completeness proofs with no estimation
     method evaluated on data. This does not cover a paper that specifies a Q-matrix or attribute
     set itself, for example derived by experts from diagnostic criteria or a curriculum for a
     proposed instrument or framework. That is expert-driven construction and is at least Maybe,
     even without data and even if the paper calls itself a review;
   - studies only of the *effects* of a misspecified Q-matrix, with no method proposed;
   - empirical data from outside the three domains, such as game players, military or workforce
     settings;
   - a whole book or textbook rather than one study.

## Data quirks

- Scopus sometimes replaces symbols with "(Formula presented)". "The (Formula presented)-matrix"
  is a Q-matrix.
- If the abstract is missing, judge from the title, keywords and venue. A plausibly relevant title
  is Maybe.
- An abstract may describe a dissertation-style or multi-part study. Judge the whole.

## Output

For each record, produce one JSON object on one line with exactly these keys:

```json
{"id": "F0000", "decision": "Exclude", "code": "E2", "confidence": "high", "reasoning": "...", "family": null, "domain": null}
```

- `decision`: "Include", "Maybe" or "Exclude".
- `code`: for Exclude, the code of the first failed question ("E1" to "E5"); otherwise null.
- `confidence`: "high" or "medium". An Exclude must be high or medium; if you would rate it low,
  the decision is Maybe.
- `reasoning`: one to three sentences.
  - **For Exclude:** name the criterion and point to what the title or abstract says that fails
    it. Quote a short phrase where you can.
  - **For Include:** say what mapping work the study does.
  - **For Maybe:** say which question is unclear and why.
- `family`: for Include and Maybe, the provisional method family or families that set the
  mapping's entries: "expert", "statistical", "ML", "LLM", or a combination joined with "+",
  or "unclear". For Exclude, null.
- `domain`: for Include and Maybe: "education", "ITS/LA", "psych/clinical", "simulation",
  a combination joined with "+", or "unclear". For Exclude, null.
