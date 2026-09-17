# OSM QA Buddy Constitution

## Core Principles

### I. Human-in-the-Loop QA
OSM QA Buddy identifies candidates for review; a human makes the final mapping/QA decision. Automated output must not be presented as authoritative mapping truth.

### II. JOSM as the Validation Engine
For the JOSM GUI Validation Bridge, JOSM remains the source of validation rules and validation execution. QA Buddy is responsible for preparation, parsing, task attribution, and reporting. Do not silently reimplement JOSM validation rules when the workflow calls for native JOSM validation.

### III. Windows-First Reproducibility
The supported user workflow is Windows-first. Changes must preserve reproducible setup and execution with the repository's documented Python, Java, JOSM, Osmium, and Git requirements unless a specification explicitly changes them.

### IV. Small, Testable Changes
Prefer the smallest coherent implementation that satisfies the accepted specification. Keep orchestration and parsing logic testable. Avoid unrelated refactors, speculative abstractions, and dependency growth without demonstrated need.

### V. Evidence Before Completion
A feature is not complete merely because the code was changed. Relevant tests, syntax checks, validation checks, or documented manual verification must be run. Failures must be investigated rather than hidden or weakened.

### VI. Spec-Driven Changes
Feature and behavior changes use the repository's Spec Kit workflow: specify the behavior, clarify material ambiguity, plan, task, analyze when warranted, implement, and converge. Existing `specs/<NNN-feature-name>/` artifacts are part of the engineering record.

### VII. AI Quality Gate
AI-generated work must be reviewed for unnecessary complexity, generic boilerplate, duplicated logic, irrelevant comments, speculative behavior, and unrelated edits. Use the repository's Anti-Slop guidance as a quality filter, not as an architecture or product-design authority.

### VIII. Human Review and Merge Authority
AI may investigate, implement, test, commit, and open a pull request. AI must not merge its own pull request or change repository governance settings. The repository owner remains the final reviewer and merger.

## Change Rules

- Do not invent requirements when a material decision is missing.
- Preserve established behavior unless the specification explicitly changes it.
- Add regression coverage for changed behavior where practical.
- Never commit secrets, API keys, credentials, or machine-local state.
- Keep pull requests focused and reviewable.
- Document limitations when platform-specific or external-tool behavior could not be verified.
