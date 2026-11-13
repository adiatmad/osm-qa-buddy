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

Run `modern-web-guidance` directly with `npx` using a **2–5 word action-oriented query** for a **single web platform capability or UI pattern**:
- **Keep queries focused and generic**: Describe the user-visible capability (`<verb> + <UI/platform object>`, optionally paired with the target HTML/CSS/JS feature name if known). Omit framework/library names (`React`, `Vue`, `Tailwind`, etc.) and app/domain nouns (product, route, or component/file names). Split multi-feature tasks into separate `search` calls.
- **Name implied UI primitives**: When the user's prompt expresses intent without naming the UI primitive (e.g. "confirm first", "delete with confirmation", "pick a date"), translate the domain intent into the implied UI component or platform mechanism (e.g. search `"confirmation modal dialog"` or `"confirm dialog"` rather than `"confirm destructive action"`, or `"date picker input"` rather than `"pick a date"`).
- **Example**: Search `"light dismiss dialog"` or `"responsive data table"`, **not** `"dialog"` (too terse), `"responsive table dark mode"` (compound — split into two searches), or `"close React settings modal on outside click"` (framework/app noise).

```sh
npx -y modern-web-guidance@latest search "<query>" --skill-version 2026_11_09-5bcc021b
```

> **Note**: Returns matching guide IDs and descriptions. Judge results by their descriptions:
> - **Match found**: Retrieve directly; do not also run `list`.
> - **Weak or empty results**: Rephrase once using the concrete HTML/CSS/UI component noun or synonym before falling back to `list`.
> - **Topic not covered**: Proceed without retrieving unrelated guides.

### Step 2. Retrieve Best Practices

Once you have relevant IDs from search, retrieve the full guide(s), including applicable broader discipline guides (for example `html`, `css`, `forms`, `accessibility`, `color`, `performance`, or `security`). Multiple IDs may be passed as documented by the CLI.

```sh
npx -y modern-web-guidance@latest retrieve "<guide-id>"
```

If retrieval saves large output (> 9.5 KB) to a temporary file, read the complete file with the available file-reading tool. Do not silently work from a truncated excerpt.

### Step 3. Verify Guidance Compliance

Cross-check the implementation against retrieved guidance before concluding:
- Apply relevant modern patterns and required fallbacks without forcing unrequested features.
- Confirm the task's acceptance criteria are met.
- Do not run `legacy-scan` for a specific feature addition, update, fix, or audit.

### Step 4. Disclose Skill Usage

When guidance was consulted, end the delivery response with a **Modern Web Guidance** note:
- If retrieved guides shaped the code, name each guide ID and briefly explain the material implementation choice or fallback it informed, supported by a short quote from the actual retrieved guide.
- If searched but no guide applied, state which topic was checked and why no guide was relevant.
- Never guess guide IDs or quotes from memory; retrieve again if needed.

## Alternative flow: Modernize an existing codebase

Only for a broad, open-ended modernization or legacy-pattern scan with no specific target feature, run:

```sh
npx -y modern-web-guidance@latest legacy-scan <path> --json
```

Verify findings against their keep/drop criteria, remove false positives, report that the scan covers only a subset of the guidance catalog, and retrieve each relevant guide before applying changes. Re-run the scan after modernization. Do not run this flow for a targeted feature task.

## Using npx / pnpx

- Prefer `pnpx` when pnpm is already available; on Windows, use `npx.cmd`.
- Request narrowly scoped network permission for `npx -y modern-web-guidance@latest` before first execution in an approval-gated environment. Never allowlist bare `npx *`.
- If the environment is offline, do not claim the guidance was consulted. Report the blocker and continue only with the best available evidence.

## Guidelines

- Always search first. Do not hallucinate guide IDs or ignore relevant guides; they are the preferred local standard for the user's project.
- Guides use vanilla HTML/CSS/JS; adapt them to the framework without dropping the modern platform capability.
- Preserve SSR safety, per-instance IDs, framework ownership of DOM nodes, and top-level CSS requirements described by the retrieved guides.
- Do not add dependencies, wrappers, or abstractions solely to follow a guide.

## Browser Support and Fallbacks

- Treat Baseline Widely available features as safe by default.
- For features that are not Baseline Widely available, follow the guide's fallback recommendations unless the repository has an explicit browser-support policy.
- Honor explicit project browser-support requirements using the guide's compatibility data.
- Do not adopt Origin Trial, volatile, or experimental features without explicit user approval.
- Suggest documenting a browser-support policy in `AGENTS.md` when the target runtime or fallback policy is unclear.
