# Classifying included studies by what they contribute to the research questions

Version of 2026-10-26. This is a sorting pass, not a screening decision. Its output helps the team
decide whether to add exclusion criteria. It removes nothing.

## Background

The review studies how **Q-matrices** are generated, validated, and refined. A Q-matrix maps
assessment items to the skills or attributes they measure; knowledge-component models and skill
tags on exercises count too. Every study you will see has already been included at full text.

The research questions are:

- **RQ1:** the distribution of Q-matrix generation, validation and refinement studies across method
  families and domains;
- **RQ2:** the conditions under which Q-matrix *methods are tested*: data, sample size, numbers of
  items and attributes, response type, attribute structure, diagnostic model, misspecification,
  item quality;
- **RQ3:** the *evaluation criteria* applied to Q-matrix methods: recovery, classification
  accuracy or reliability, validation-test power, model fit, prediction, agreement with expert
  Q-matrices, expert or think-aloud review, computational cost;
- **RQ4:** author-reported *limitations of Q-matrix methods*.

RQ2–RQ4 only have something to work with when a study **evaluates** its mapping, or the method
that produced it. Your job is to say, for each study, which of these it does.

## What you get for each study

Each record contains:

- title, abstract, venue, year, document type;
- the full-text screener's reasoning and quoted evidence (`ft_reasoning`, `ft_evidence`);
- its provisional codes: task, family, domain, data.

The screener read the whole paper, so its reasoning is your main source. Judge each study on its
own record only.

## The groups

Assign exactly one group.

**A. Method study.** The paper's contribution is a method for generating, validating or refining
the mapping, and the method itself is evaluated. Examples:

- a new Q-matrix estimation or validation method;
- a comparison of methods;
- a tagging or KC-extraction method scored against expert labels;
- a neural model whose stated aim is learning or refining the mapping;
- a method for choosing the number of attributes;
- an LLM generation pipeline;
- a software or tutorial paper that evaluates methods.

**B. Instrument or application study with an evaluated Q-matrix.** The paper builds or adopts a
mapping for a particular test, and then checks the mapping itself against evidence from outside
its own construction. Evidence that counts:

- comparing candidate Q-matrices by fit;
- an empirical validation method (GDI or PVAF, Wald, Hull, mesa plots, stepwise or iterative
  refinement) whose result is reported;
- think-aloud or verbal-report checks of the item-attribute mapping;
- review of the finished Q-matrix by an independent expert panel;
- attribute-hierarchy-method consistency checks;
- learning-curve validation;
- revising entries in light of data.

**C. Application where the Q-matrix is only a preparatory step.** A mapping is built, often by a
described expert process, and then used. The paper reports no evidence about the mapping's own
quality beyond the construction itself. The contribution lies elsewhere: profiles of learners, a
new test's psychometrics, DIF, an intervention, a substantive finding. Count as C:

- inter-coder agreement *during construction* is part of construction, not an evaluation;
- fitting one or several diagnostic models with the Q-matrix held fixed, only to choose a model or
  report classifications, is not an evaluation of the Q-matrix.

**H. Hierarchy-only.** The Q-matrix itself is taken as given, from earlier work, a framework or a
test blueprint. The study's own mapping work concerns only the attribute hierarchy or attribute
structure, whether estimating, validating or comparing it.

**U. Can't tell.** The record does not settle whether the mapping is evaluated. Say what is
missing; the full text will be checked.

**Telling B from C.** Ask: *if the Q-matrix were wrong, would anything reported in this paper have
shown it?* If yes, it's B. If no, it's C.

## Output

Write one JSON object per study, on one line, with exactly these keys:

```json
{"id": "F0000", "group": "C", "study_type": "application", "evaluation": [], "confidence": "high", "reasoning": "..."}
```

- `group`: "A", "B", "C", "H" or "U".
- `study_type`: what the paper is.
  - "method_new": proposes a new method;
  - "method_comparison": compares existing methods;
  - "application": applies methods to a particular test or setting;
  - "tool": a software or tutorial paper.
- `evaluation`: the evaluation criteria applied to the **mapping or the method that produced it**,
  from this list. Use an empty list for C and, usually, for H.
  - "Q_recovery": recovery of known entries, in simulation;
  - "classification_accuracy"
  - "classification_reliability"
  - "validation_power_type1"
  - "model_fit_comparison": candidate Q-matrices compared by fit;
  - "validation_index": GDI, PVAF, Wald, Hull, mesa plots, item-level misfit used to revise
    entries;
  - "prediction_heldout": prediction of held-out responses, including AUC in knowledge tracing;
  - "agreement_with_expert": agreement with an expert or gold-standard mapping;
  - "expert_or_thinkaloud_review": independent review, think-aloud or verbal reports;
  - "learning_curves"
  - "hierarchy_consistency"
  - "computational_cost"
- `confidence`: "high", "medium" or "low".
- `reasoning`: one or two sentences. For B, name the evidence that checks the mapping. For C, say
  what the paper's contribution is instead.
