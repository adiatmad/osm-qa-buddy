---
name: modern-web-guidance
description: |
  Search tool for modern web development best practices. MANDATORY: Execute FIRST for all HTML/CSS and clientside JS tasks. Do NOT skip — web APIs evolve rapidly and training weights contain obsolete patterns.
  Trigger immediately for: modals/dialogs/popovers, tables, dark mode, anchor positioning, container queries, view transitions, scroll-driven animations, parallax/reveals, forms, validation, autofill, accessibility, custom selects, scrollbars, CWV (LCP, INP, CLS), content-visibility, fetch priority, image optimization, security, passkeys, HTML sanitization, web components, dates/timezones, built-in AI, WebAssembly, standard HTML/CSS/DOM in frameworks, etc.
  DO NOT trigger for: backend (SQL, ORMs, API routes), infra/scripts (CI/CD, Docker, Actions, Python/Go, Git), or tooling/trivial (Vite, tsconfig, ESLint, tests, copy/renames, 3P docs), etc.
---

# Modern Web Guidance

Search and retrieve standardized modern web best practices at the **start** of implementing or updating any web UI, CSS layout/animation, or client-side JS logic (dates/timezones, sanitization, performance, accessibility, UX fixes) before writing ad-hoc solutions or adding dependencies.

## Primary Workflow

### Step 1. Search Use Cases

Run `modern-web-guidance` directly with `npx` using a **2–5 word action-oriented query** for a **single web platform capability or UI pattern`:
- **Keep queries focused and generic**: Describe the user-visible capability (`<verb> + <UI/platform object>`, optionally paired with the target HTML/CSS/JS feature name if known). Omit framework/library names and app/domain nouns. Split multi-feature tasks into separate searches.
- **Name implied UI primitives**: Translate user intent into the implied UI component or platform mechanism (for example, search `"confirmation modal dialog"` rather than `"confirm destructive action"`).
- Search first:
  ```sh
  npx -y modern-web-guidance@latest search "<query>"
  ```
- If results are weak, rephrase once. If no relevant guide exists, proceed without retrieving unrelated guides.

### Step 2. Retrieve Best Practices

Retrieve the matching guide IDs and applicable broader discipline guides (such as `html`, `css`, `forms`, `accessibility`, `performance`, or `security`):
```sh
npx -y modern-web-guidance@latest retrieve "<guide-id>"
```
Read complete output, including any temporary file used for long results.

### Step 3. Verify Guidance Compliance

Cross-check the implementation against retrieved rules, compatibility notes, and required fallbacks. Confirm task acceptance criteria. Do not run `legacy-scan` for a targeted feature task.

### Step 4. Disclose Skill Usage

End the delivery response with a **Modern Web Guidance** note. Name guide IDs actually retrieved and the material decisions they informed, supported by a short quote from the retrieved guide. If searched but no guide applied, state why. Never invent IDs or quotes.

## Broad modernization only

For a broad, open-ended modernization request with no specific target feature, use:
```sh
npx -y modern-web-guidance@latest legacy-scan <path> --json
```
Verify findings against keep/drop criteria, report scan coverage limitations, retrieve relevant guides before edits, and re-scan after changes. Do not use this for targeted feature work.

## Execution and compatibility

- Prefer `pnpx` when pnpm is already available; on Windows use `npx.cmd`.
- Request narrowly scoped network permission before first execution in approval-gated environments. Never allowlist bare `npx *`.
- If offline or blocked, disclose that guidance was not retrieved; do not claim otherwise.
- Adapt vanilla HTML/CSS/JS guidance to the project's framework without dropping the modern platform capability or adding unnecessary dependencies.
- Baseline Widely available features are safe by default. For features below that level, follow guide fallback recommendations unless the repository defines a browser-support policy.
- Do not adopt Origin Trial, volatile, or experimental features without explicit user approval.
- Do not invoke for backend-only, SQL/ORM/API routes, Python/Go processing, GIS/data pipelines, CI/CD, Docker, Git, or trivial tooling/docs changes unless browser-facing behavior is affected.
- This skill supplements and never overrides repository specifications, architecture, security constraints, tests, or other agent instructions.
