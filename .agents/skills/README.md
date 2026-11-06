# Engineering skills

This repository's `AGENTS.md` and `.specify/memory/constitution.md` remain authoritative. The Anti-Slop core is included at `/antislop.md`.

Upstream sources:
- Matt Pocock engineering skills: https://github.com/mattpocock/skills
- Anti-Slop: https://github.com/miqdadbadjuber/anti-slop
- GitHub Spec Kit: https://github.com/github/spec-kit

Install selected Matt Pocock skills into the Codex project with `npx skills@latest add mattpocock/skills -a codex`. Select TDD, diagnosing-bugs, codebase-design, and code-review.

The Anti-Slop core is already vendored. To install the modular skills, use `npx skills@latest add miqdadbadjuber/anti-slop --all -a codex`.

Spec Kit is already represented by the existing `.specify/` constitution and `specs/` feature artifacts. If the CLI is missing, install it with `uv tool install specify-cli` and verify using `specify version`. Follow the official existing-project adoption guidance before adding or migrating generated files.

UI/UX Pro Max is intentionally omitted: the repository's core workflow is JOSM-assisted validation, task attribution, and reporting rather than a first-party interface.

Review installer changes before accepting updates. Do not force-overwrite customized files or commit machine-specific global settings.
