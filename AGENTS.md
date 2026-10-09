# Agent instructions

Always create and update generated documentation in `docs_agent/`.

Do not write generated documentation directly in `README.md`. Limit generated
README additions to the bare minimum needed to link readers to documentation in
`docs_agent/` or elsewhere. Generated links to documentation in other locations
are welcome.

Preserve human-authored README content, including the Documentation and AI Usage
sections, unless the user explicitly requests changes to it.

Keep database exports, abstracts, candidate records and derived record files
local and untracked in the ignored `input/` and `output/` directories. Do not
force-add these files or include their contents in public documentation or test
fixtures. Use synthetic records for shared examples and tests.
