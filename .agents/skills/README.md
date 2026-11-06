# ChatGPT-first engineering toolkit

This repository is prepared for work with **ChatGPT as the primary coding assistant**. These files are reference material for ChatGPT; they are not automatically loaded into every ChatGPT conversation.

## Read these project files before making changes

At the start of each substantial task, ChatGPT should inspect and read:

1. `/AGENTS.md` — repository-specific engineering rules and product constraints.
2. `/antislop.md` — the vendored Anti-Slop core rules and delivery gate.
3. `.specify/memory/constitution.md` — the project constitution, when present.
4. The relevant feature specification, README, implementation, configuration, and tests.
5. Only the upstream skill material relevant to the task (links below).

Do not assume that the existence of these files means ChatGPT has already read or applied them. Explicitly load the relevant content in the current conversation.

## What is actually present in this repository

- **Anti-Slop core:** `/antislop.md` is vendored in this repository. Read it for substantial implementation, UI, and writing work.
- **Project rules:** `/AGENTS.md` contains repository-specific constraints and the required engineering workflow.
- **Spec Kit principles:** use the existing constitution and feature-spec structure. Preserve existing specifications and decisions.
- **Additional upstream skills:** Matt Pocock's skills and Anti-Slop's modular skills are linked below for selective, task-specific consultation. They are not all vendored here.

## Upstream references — consult selectively

- Matt Pocock engineering skills: https://github.com/mattpocock/skills
- Anti-Slop modular skills: https://github.com/miqdadbadjuber/anti-slop
- GitHub Spec Kit: https://github.com/github/spec-kit
- UI/UX Pro Max is intentionally not included: this repository's core workflow is JOSM-assisted validation, task attribution, and reporting rather than a first-party user interface.

Do not bulk-copy every upstream skill or generated design dataset into this repository by default. First identify a concrete task that needs a specific skill, read its current upstream instructions, and explain why it applies. Avoid duplicate skill bundles and unnecessary repository growth.

## ChatGPT-first task procedure

For each task:

1. **Inspect first.** Confirm the repository, branch, working tree context available through GitHub, existing files, relevant code, specs, tests, and recent changes.
2. **Define the change.** For non-trivial work, state the user outcome, scope, non-goals, constraints, risks, and testable acceptance criteria before editing.
3. **Plan minimally.** Prefer the smallest maintainable change. Reuse existing architecture and conventions; do not introduce dependencies or abstractions without evidence.
4. **Edit narrowly.** Work on a dedicated review branch or the explicitly selected PR branch. Change only necessary files. Preserve existing user-authored configuration, specifications, data, and project rules. Never replace a file just because an installer expects a conventional path.
5. **Verify honestly.** Inspect the diff. Run tests only when an actual execution environment is available. GitHub file operations do not execute the application, shell commands, or test suites. If tests cannot be run in this session, mark them **NOT RUN**, provide exact Windows PowerShell commands for local execution, and wait for the results before claiming success.
6. **Close the loop.** Report files changed, evidence gathered, tests run/not run, known risks, and remaining work. Do not merge a PR or perform destructive/irreversible actions without explicit approval.

## Reusable instruction to give ChatGPT

> Before changing this repository, read `AGENTS.md`, this guide, `antislop.md`, the existing Spec Kit constitution and relevant feature specs, plus the relevant code, tests, and configuration. Consult upstream skill documentation only when it materially applies. Summarize the constraints and acceptance criteria first. Make the smallest safe change, preserve existing project files, inspect the diff, and distinguish executed tests from tests that could not be run. Do not overwrite, initialize, migrate, or delete existing project files without inspecting the exact impact and getting my approval where the change is consequential.

## Installation policy for this ChatGPT-only setup

No agent-specific CLI installation is required for ChatGPT to use these repository documents. In particular, do **not** run `specify init --force`, `uipro init`, or an agent-specific `npx skills add` command merely to make ChatGPT recognize this repository. Those commands target supported local coding-agent environments and may generate or modify project files. Use them only if a separate compatible coding agent is deliberately introduced later.

The Spec Kit CLI may be installed locally for a human-operated workflow, but it is not required to use the existing constitution and specifications with ChatGPT.
