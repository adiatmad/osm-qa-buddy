# OSM QA Buddy — Agent Working Agreement

OSM QA Buddy is a Windows-first, human-reviewed third-pass QA helper for HOT Tasking Manager projects. JOSM remains the validation engine; QA Buddy prepares data, parses native validation output, attributes findings to tasks, and reports results.

## North-star workflow

For meaningful engineering work, use this loop:

> **define the job → collect the evidence → parse the docs → save the memory → compress the context → run the code safely → watch what changes → ship the output**

This is an execution discipline, not a replacement for the repository's Spec Kit workflow.

### 1. Define the job
- State the user-visible problem, desired outcome, constraints, and explicit non-goals.
- Do not invent material requirements. Ask when ambiguity changes behavior.
- Identify whether the work is a feature, bug fix, documentation/configuration change, or operational task.

### 2. Collect the evidence
- Inspect the current branch, relevant code, tests, specs, recent history, and actual failure/output before changing code.
- Prefer repository evidence and primary tool documentation over assumptions.
- Record important platform-specific limitations, especially Windows/JOSM behavior.

### 3. Parse the docs
- Treat the constitution, accepted specification, plan, task list, and tool/repository documentation as constraints.
- For feature work, use Spec Kit's specify → clarify → plan → checklist/tasks → analyze → implement → converge flow as appropriate.
- Keep the implementation faithful to the accepted specification rather than optimizing for what is easiest to code.

### 4. Save the memory
- Persist durable engineering decisions in the appropriate repository artifact: constitution, specification, plan, README, docs, or agent instructions.
- Do not rely on chat history for facts that future agents need.
- Keep durable memory concise and update it when behavior or constraints change.

### 5. Compress the context
Before implementation, reduce the working set to what is actually needed:
- relevant requirements and acceptance criteria;
- affected files/components;
- known constraints and dependencies;
- current failure or expected behavior;
- tests that prove the change.

Do not load or rewrite unrelated parts of the repository merely for context.

### 6. Run the code safely
- Work on a branch; keep `main` stable.
- Make the smallest coherent change.
- Never weaken or delete tests to obtain a green result.
- Never commit secrets, credentials, generated machine-local state, or unrelated edits.
- Preserve the human-in-the-loop QA boundary and JOSM-as-validation-engine architecture.

### 7. Watch what changes
- Inspect the diff, test results, generated artifacts, and runtime behavior.
- Diagnose failures at the cause rather than hiding symptoms.
- For Windows/JOSM-dependent behavior, distinguish CI verification from real local/manual acceptance.
- Use Spec Kit convergence to compare implementation against the specification, plan, and tasks.

### 8. Ship the output
Before a PR is considered ready, verify:
- the requested behavior is implemented;
- relevant automated/manual checks have evidence;
- the diff is focused and free of unrelated changes;
- documentation and durable memory match the implementation;
- known limitations are explicit;
- Anti-Slop quality review has passed.

AI may investigate, implement, test, commit, and open a PR. Human review and merge authority remain with the repository owner.

## Anti-Slop quality gate

Use Anti-Slop as a filter, not an architecture authority. Reject unnecessary boilerplate, speculative abstractions, duplicated logic, decorative comments, generic AI-sounding copy, and unrelated cleanup. Every significant addition should have a demonstrated purpose. For changed comments, follow `.gemini/skills/antislop-code/SKILL.md`.

## Evidence contract

Never claim a check passed unless it actually ran. If a check could not be performed, say exactly what remains unverified. A feature is complete when the evidence supports the acceptance criteria, not merely when the code compiles.


## Ponytail minimal-change discipline

Apply Ponytail's smallest-complete-change rule alongside this repository's existing workflow; it does not replace or weaken the repository-specific requirements above.

- Read the affected code and trace callers, tests, fixtures, configuration, and exports before editing.
- Prefer existing project helpers and patterns, then standard-library or native platform features, then already-installed dependencies. Add no abstraction, dependency, option, or configuration without a demonstrated need.
- Make the smallest complete change, not merely the smallest diff: preserve required validation, security, accessibility, error handling, and data-loss protections.
- Add a focused test or assert-based self-check for new non-trivial logic and bug fixes. Never weaken a valid test to make a change pass.
- Review the complete diff and verify the relevant behavior. Report what was not checked and any remaining risk.
- Mark deliberate shortcuts as `shortcut: <the limit>, <when to upgrade>`.

Use the full Ponytail Skill at `.agents/skills/ponytail/SKILL.md` when the active agent supports project Skills. Existing Spec Kit, Anti-Slop, Superpowers/Loop & Graph, and repository-specific rules remain in force.

## Modern Web Guidance — mandatory for relevant web work

Use [Google Chrome Modern Web Guidance](https://github.com/GoogleChrome/modern-web-guidance) as the source of current web-platform implementation guidance. This requirement applies to every coding agent working in this repository, including agents that do not have a dedicated plugin integration.

### When to use it
Before designing or changing browser-facing UI or client-side behavior, including HTML, CSS, DOM, browser APIs, responsive layout, animation, forms and validation, accessibility, performance/Core Web Vitals, web security, dates/time zones, and web components:
1. Search the relevant capability first:
   `npx -y modern-web-guidance@latest search "<focused 2–5 word action-oriented query>"`
2. Retrieve the best matching guide ID(s):
   `npx -y modern-web-guidance@latest retrieve "<guide-id>"`
3. Read and apply the relevant implementation rules, compatibility notes, and fallback requirements before coding.
4. Verify the changed implementation against the retrieved guidance and the repository's own acceptance criteria.

On Windows, use `npx.cmd` where required. If the environment blocks network access, request the necessary permission before execution. Do not claim the guidance was consulted if the commands did not run.

### Scope and guardrails
- Search first; never invent guide IDs or rely on remembered guide content. If the first search is weak, rephrase once; if no relevant guide exists, proceed without applying unrelated guidance.
- Follow the guide's browser-support and progressive-enhancement rules. Use required fallbacks for features that are not Baseline Widely available unless this project has an explicit browser-support policy.
- Do not adopt Origin Trial, volatile, or experimental features without explicit user approval.
- Adapt vanilla HTML/CSS/JS guidance to the repository's framework and architecture; do not add dependencies or refactor unrelated code merely to follow a guide.
- This is not required for backend-only work, SQL/ORM/API routes, Python/Go processing, GIS/data pipelines, CI/CD, Docker, Git operations, or trivial tooling/docs changes unless they affect browser-facing behavior.
- Preserve all existing repository instructions, specifications, security constraints, tests, and delivery gates. Modern Web Guidance supplements them; it does not override them.
- In the delivery response, include a concise **Modern Web Guidance** note naming the guide IDs actually retrieved and the material decisions they informed. If searched but no guide applied, say so briefly.
