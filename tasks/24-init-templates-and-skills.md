# Task 24: Richer Init Templates, Skill/Agent Updates, and Skill Version Staleness

## Why

Three discoverability gaps that each require a small, targeted fix:

1. **Init templates** don't show optional arrangement fields — a new project never
   sees `specs_path` or `overrides` unless they know to look for them.
2. **Skill and agent files** don't mention key arrangement fields — the conductor
   skill tells agents about `output_paths` templates but not `overrides` or `specs_path`.
3. **Installed skills go stale** — when a project installs skills via `sp install-skills`
   and then upgrades specsoloist, the installed copies don't update automatically. There
   is no signal that they are out of date.

## Part A: Richer Init Templates

### Python default template

The generated `arrangement.yaml` from `sp init` (and `sp init --arrangement python`)
should include all optional fields as commented-out examples. Edit the template source
(check `src/specsoloist/templates/` or `src/specsoloist/arrangements/` — find where
`sp init` reads from).

Target output for `arrangement.yaml`:

```yaml
target_language: python

# Directory where your .spec.md files live (default: src/).
# Change this if your specs are in a different location, e.g. specs/
# specs_path: specs/

output_paths:
  implementation: "src/{name}.py"
  tests: "tests/test_{name}.py"
  # Per-spec overrides for modules in subdirectories:
  # overrides:
  #   data:
  #     implementation: myapp/data/postgres/data.py
  #   components:
  #     implementation: myapp/html/components.py

environment:
  tools: []
  setup_commands:
    - uv sync
  # dependencies:
  #   some-package: ">=1.0,<2.0"

build_commands:
  test: uv run python -m pytest tests/ -q

# Pin the LLM model for this project (optional).
# Overridden by --model flag. Falls back to SPECSOLOIST_LLM_MODEL env var.
# model: claude-sonnet-4-5

# Declare environment variables your project needs:
# env_vars:
#   DATABASE_URL:
#     description: "PostgreSQL connection string"
#     required: true
#     example: "postgresql://user:pass@localhost/mydb"
```

Apply the same treatment to the `python-fasthtml`, `nextjs-vitest`, and
`nextjs-playwright` templates — each should include the `specs_path` and `overrides`
comments even if the rest differs.

### Files to modify

Find where templates are defined:
```bash
grep -r "arrangement.yaml\|specs_path\|output_paths" src/specsoloist/arrangements/ src/specsoloist/templates/ src/specsoloist/cli.py | grep -v ".pyc"
```

The `sp init` command likely reads from YAML files in `src/specsoloist/arrangements/`
or generates content inline in `cli.py`. Update whichever is the actual source.

---

## Part B: Skill and Agent File Updates

### What to add

In each of these files, add a short "Key Arrangement Fields" section or paragraph
that covers the two fields agents most commonly miss:

**Files to update:**
- `src/specsoloist/skills/sp-conduct/SKILL.md`
- `src/specsoloist/skills/sp-soloist/SKILL.md`
- `.claude/agents/conductor.md`
- `.claude/agents/soloist.md`
- `.gemini/agents/conductor.md` (if it exists)

**Content to add** (adapt tone per file):

```markdown
### Key Arrangement Fields

Two fields agents commonly miss:

**`specs_path`** (default: `"src/"`) — the directory where `.spec.md` files live.
If the project stores specs in `specs/` or another location, this must be set.
`sp list`, `sp status`, and `sp graph` use this field.

**`output_paths.overrides`** — per-spec path overrides for modules in subdirectories.
Use when a spec's output should go to a path that doesn't match the template:
```yaml
output_paths:
  implementation: "myapp/{name}.py"
  overrides:
    data:
      implementation: myapp/data/postgres/data.py
```
Before writing an arrangement, run `sp schema` to see all available fields.
Run `sp help arrangement` for a full narrative reference with examples.
```

Keep additions concise — the goal is awareness, not exhaustive docs. Each file
addition should be 10–20 lines.

---

## Part C: Skill Version Staleness Detection

### Problem

`sp install-skills` copies skill files from the package into the project's
`.claude/agents/` (or `--target` directory). When specsoloist is upgraded, those
copies are stale but nothing signals this.

### Fix

**Step 1**: Embed a version marker in installed files.

In `cmd_install_skills` (in `cli.py`), when writing each skill file, prepend a
comment line with the current package version:

```python
import importlib.metadata
_version = importlib.metadata.version("specsoloist")
version_marker = f"<!-- sp-version: {_version} -->\n"
content = version_marker + original_content
```

**Step 2**: Add a staleness check to `sp doctor`.

In `cmd_doctor` (or the doctor helper functions), scan the installed skills directory
(`.claude/agents/`, `.claude/skills/`, or wherever `sp install-skills` wrote to) for
files containing an `<!-- sp-version: ... -->` marker. Compare against the current
package version. Warn if mismatched:

```
⚠ Installed skills are from specsoloist 0.5.0 — current version is 0.6.0.
  Run: sp install-skills
```

The check should be a soft warning (not a failure), and should only run if installed
skill files are actually found. If no skills are installed, skip silently.

### Discovery: where are skills installed?

`sp install-skills` defaults to `--target .claude/skills`. The version check should
look in:
1. The `--target` path if passed
2. `.claude/agents/` (native agent directory)
3. `.claude/skills/` (default install target)

Only warn if at least one versioned file is found and its version doesn't match.

---

## Files to Read

- `src/specsoloist/cli.py` — `cmd_install_skills`, `cmd_doctor`, the init command
  and how it reads arrangement templates
- `src/specsoloist/arrangements/` — arrangement YAML template files
- `src/specsoloist/skills/sp-conduct/SKILL.md` — current content to understand
  what a "short addition" looks like in context
- `.claude/agents/conductor.md` — current content

## Success Criteria

- `sp init myproject` generates an `arrangement.yaml` with commented `specs_path`
  and `overrides` examples
- All four named arrangement templates include these comments
- Skill/agent files contain the "Key Arrangement Fields" addition
- `sp install-skills` writes a `<!-- sp-version: X.Y.Z -->` marker in each installed file
- `sp doctor` warns when installed skill files are from an older version
- `sp doctor` does not warn if no versioned skill files are found
- All 355 tests pass; `uv run ruff check src/` clean

## Tests

- `cmd_install_skills` test: installed file starts with `<!-- sp-version: ... -->`
- `cmd_doctor` test: mock an installed skill file with old version → warning emitted
- `cmd_doctor` test: mock an installed skill file with current version → no warning
- `sp init` template test: generated `arrangement.yaml` contains `# specs_path`
