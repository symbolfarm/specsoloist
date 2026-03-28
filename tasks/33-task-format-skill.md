# Task 33: Formalize task tracking as an agent skill

**Effort**: Medium

## Motivation

SpecSoloist's `tasks/` directory has organically evolved into a lightweight but effective
system for giving AI coders working context from a cold start. Each task file serves as a
prompt: motivation, design decisions, implementation steps, files to read, and success criteria.
This has worked well across many AI coding sessions, but the format is undocumented and
hand-maintained.

The gap this fills is distinct from specs: specs define *what code should do*; task files
define *what work needs doing and why*. Specs are the source of truth for code generation;
tasks are the source of truth for development context. Both are Markdown, both are structured,
but they serve different roles in the pipeline.

Other parallel AI agent frameworks are evolving similar concepts (issue-to-task bridges,
structured briefs), but most are heavyweight. The SpecSoloist approach — plain Markdown files
in a `tasks/` directory with a README index — has the virtue of simplicity.

## What to Formalize

### 1. Task file format specification

Document the implicit structure that has emerged:

```markdown
# Task {number}: {title}

**Effort**: Small | Medium | Large
**Depends on**: Task N (description)

## Motivation
Why this work matters. Context an AI coder needs to understand the "why".

## Design Decisions (locked)
Choices already made. The AI should not revisit these.

## Implementation
What to build, which files to create/modify.

## Files to Read Before Starting
Specific paths the AI should read to build context before writing code.

## Success Criteria
How to verify the task is done. Usually test commands + lint.
```

### 2. Task README index format

The `tasks/README.md` pattern: project state summary, task table with status, "how to pick
up a task" instructions, working principles.

### 3. Agent skill: `sp-task` or similar

A skill definition (like the existing `sp-compose`, `sp-conduct`, etc.) that:
- Lists available tasks (`sp task list`)
- Reads and summarizes a task (`sp task read 27`)
- Creates a new task from a brief description (`sp task create "Add retry budget"`)
- Marks a task complete and moves it to history (`sp task done 27`)

### 4. Potential standalone tool

Consider whether this should be a separate package (like the issue-to-task bridge in
IDEAS.md §11a) or stay within SpecSoloist. The format is generic enough to work outside
spec-driven projects.

## Open Questions (for design discussion)

- Should the task format be a formal spec (`task_format.spec.md`) like `spec_format.spec.md`?
- Should tasks support dependencies beyond the informal "Depends on" line?
- How does this relate to the issue-to-task bridge concept in IDEAS.md §11a?
- Is `sp task` a CLI command, an agent skill, or both?

## Files to Read Before Starting

- `tasks/README.md` — the current index format
- `tasks/25-static-artifacts.md` — example of a well-structured task
- `src/specsoloist/skills/` — existing skill definitions
- `IDEAS.md` §11a — issue-to-task bridge concept

## Success Criteria

- Task file format is documented (in docs/ or as a spec)
- At minimum: `sp task list` and `sp task read` work
- Existing tasks validate against the documented format
