---
name: antislop-code
description: "Code comment hygiene for AI coding agents: remove generic AI-slop comments, keep valuable comments, never change executable code merely to satisfy this skill."
allowed-tools: Read Write Edit Glob Grep
---
# Anti-Slop Code Comments

Use this skill whenever code comments are added or changed.

## Scope

This skill is a comment-quality filter. It must never be used as a reason to modify executable logic, identifiers, imports, formatting, indentation, control flow, or behavior.

## Remove

- Decorative separator banners or box-drawn section headers.
- Comments that simply restate the next line, declaration, or function name.
- Step-by-step narration of obvious control flow.
- Empty labels such as `Main logic`, `Helper`, or `Entry point` when they add no information.
- Vague TODOs that do not identify an actionable task.
- Decorative emoji in comments.
- End-of-block comments that merely repeat a closing brace or block boundary.
- Long, stiff explanations when a short statement of the actual constraint is sufficient.

## Preserve

Keep comments that explain information the code does not make obvious, including:

- business intent
- architectural decisions
- security constraints
- performance trade-offs
- concurrency behavior
- protocol or API contracts
- workarounds
- edge cases and assumptions
- licensing or legal requirements

## Final check

Before delivery, ask of every changed comment: does it tell the next maintainer something the code itself does not already show? If not, remove it.
