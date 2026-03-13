# SpecSoloist Ralph Loop Prompt

Use this prompt to run autonomous task iteration, with or without the ralph-loop plugin.

**With the plugin:**
```bash
/ralph-loop "$(cat tasks/ralph-prompt.md)" --completion-promise "ALL_TASKS_DONE" --max-iterations 20
```

**Without the plugin:** paste the contents of this file into a new Claude Code session and
re-paste after each iteration if needed.

---

## Your Task

You are working through the SpecSoloist task backlog autonomously. Each iteration you will:
1. Do pre-task housekeeping
2. Complete one task
3. Do post-task reflection

Read `tasks/README.md` now to orient yourself.

---

## Pre-Task Housekeeping

Before picking up a task, do a quick health check:

```bash
uv run python -m pytest tests/ -q
uv run ruff check src/
git status
```

If tests are red or lint fails and it's not caused by your own previous work this session,
add a housekeeping entry to the Housekeeping table in `tasks/README.md` describing the issue,
then fix it before proceeding to the feature task. Commit the fix separately.

---

## Picking a Task

Pick the **lowest-numbered active task** from the To Do table in `tasks/README.md`.

If all tasks are complete, output:
```
ALL_TASKS_DONE
```
and stop.

If the next task requires human input (design decision, credentials, external service, or
the task file says "discuss with user first"), output:
```
NEEDS_HUMAN: <one sentence describing what's needed>
```
and stop.

---

## Doing the Task

1. Read the task file in full (`tasks/<N>-<name>.md`)
2. Read every source file the task references before writing any code
3. Implement the changes
4. Verify:
   ```bash
   uv run python -m pytest tests/ -q
   uv run ruff check src/
   ```
5. Fix any failures before committing (up to 3 attempts; if still failing, output `NEEDS_HUMAN`)

**Nested session note:** If the task requires `sp conduct`, do NOT shell out — use the
`Agent` tool with `subagent_type="conductor"` instead.

---

## Committing

```bash
git add <changed files>
git commit -m "<type>: <description>"
```

Use conventional commit style (`feat:`, `fix:`, `docs:`, `chore:`, `test:`).

---

## Post-Task Reflection

After committing, do the following:

**1. Move the completed task to `tasks/HISTORY.md`:**
- Remove the row from the To Do table in `tasks/README.md`
- Append a row to the relevant table in `tasks/HISTORY.md` with today's date and a brief note

**2. Note any observations:**
- If you noticed something that should be fixed (doc drift, a stale reference, a missing test),
  add a row to the Housekeeping table in `tasks/README.md`:
  `| HK-XX | <title> | Tiny/Small | <one-line description> |`
  Use the next available HK number.
- If you made a significant implementation decision not covered by the task file, add it to
  the Key Architectural Decisions section of `tasks/README.md`.

**3. Update Current State** in `tasks/README.md` if the task changes a layer's status.

**4. Commit housekeeping changes:**
```bash
git add tasks/README.md tasks/HISTORY.md
git commit -m "chore: post-task notes after task <N>"
```

Then loop back to Pre-Task Housekeeping for the next task.

---

## Completion Signals

| Signal | Meaning |
|--------|---------|
| `ALL_TASKS_DONE` | No active tasks remain in README |
| `NEEDS_HUMAN: <reason>` | Blocked — human input required before continuing |
