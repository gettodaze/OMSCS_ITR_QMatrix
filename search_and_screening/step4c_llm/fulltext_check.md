# Full-text check for studies left as U

Addendum to `classification_prompt.md`, used for the studies the summary-based pass could not
place (group U). Everything in that prompt applies, with these changes:

- Read the study's full text, `step4_llm/text/<ID>.txt` (one `[[page N]]` marker per page), as
  well as its record in `batches/fulltext_U.jsonl`. The full text is now your main source.
- U is no longer available. Assign A, B, C or H, and use `confidence` to say how sure you are.
- Apply the B/C test to what the paper actually reports: *if the Q-matrix were wrong, would
  anything reported here have shown it?*
- Add a key `evidence`: one or two short quotations, each with its page (`p. 7`), that settle
  the group.
