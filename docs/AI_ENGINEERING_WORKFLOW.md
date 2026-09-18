# AI Engineering Workflow

This repository uses a simple evidence-driven loop for AI-assisted development:

**define the job → collect the evidence → parse the docs → save the memory → compress the context → run the code safely → watch what changes → ship the output**

It complements Spec Kit and Anti-Slop:

- **Spec Kit** defines the contract and development sequence: specify → clarify → plan → tasks → implement → converge, with optional checklist/analyze gates for higher-risk work.
- **Anti-Slop** is the quality filter: remove unnecessary complexity, generic boilerplate, decorative comments, duplicated logic, and work without a demonstrated purpose.
- **This workflow** controls the agent's evidence and execution loop so it does not jump from a vague request directly to code.

## Practical mapping

| Loop | Engineering action | Evidence/output |
|---|---|---|
| Define the job | Capture goal, constraints, non-goals, acceptance criteria | Spec or concise task statement |
| Collect the evidence | Inspect repo, tests, history, failures, tool behavior | Evidence notes |
| Parse the docs | Read constitution/spec/plan/tasks and relevant primary docs | Applicable constraints |
| Save the memory | Persist durable decisions and workflow rules | Repository docs/specs/agent instructions |
| Compress the context | Keep only relevant requirements, files, risks, and tests in the active context | Focused implementation context |
| Run the code safely | Branch, smallest coherent change, no weakened tests | Code + test output |
| Watch what changes | Inspect diff, generated artifacts, runtime behavior, and failures | Verification evidence |
| Ship the output | Converge, document limitations, open focused PR | Reviewable PR |

## When to use the full loop

Use the full loop for features, behavior changes, integrations, and non-trivial bug fixes.

For tiny documentation or configuration changes, use judgment and skip ceremony that adds no useful evidence. The goal is lower cognitive overhead, not more paperwork.

## Completion rule

Do not use "done" to mean "the code was edited." Use it only when the acceptance criteria have corresponding evidence, relevant tests/checks have been run, known limitations are documented, and the final diff contains no unrelated work.

For Windows/JOSM workflows, explicitly separate:

1. automated verification;
2. local/manual acceptance;
3. production or field evidence.

A successful automated test does not prove that a real JOSM GUI workflow works, and a successful manual run does not replace regression tests.
