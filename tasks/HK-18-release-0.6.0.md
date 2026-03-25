# HK-18: Release v0.6.0

## Prerequisites

All of the following must be complete before running this checklist:

- [ ] HK-14 — Revert publish workflow to trusted publishing
- [ ] HK-15 — `specs_path` arrangement field + discovery commands
- [ ] HK-16 — `output_paths.overrides` tests + score spec docs
- [ ] HK-17 — `yaml:test_scenarios` validator fix + `--version` flag
- [ ] Task 22 — `sp schema [topic]`
- [ ] Task 23 — `sp help <topic>` with bundled specs
- [ ] Task 24 — Richer init templates + skill updates + staleness detection

## Release Narrative

> **"Real-world readiness."** SpecSoloist now works correctly for projects that don't
> match its default layout: specs outside `src/`, modules in subdirectories, any
> project structure. Agents can discover the full arrangement schema without reading
> source code — `sp schema`, `sp help <topic>`, richer init templates, and updated
> skill files close the discoverability gap that blocked real integrations.

## Pre-flight Checks

- [ ] `uv run python -m pytest tests/` — all passing (note count)
- [ ] `uv run ruff check src/` — 0 errors
- [ ] `uv run mkdocs build --strict` — clean (0 warnings)
- [ ] `sp schema` — runs without error, lists key fields
- [ ] `sp help arrangement` — runs without error, shows overrides and specs_path
- [ ] `sp --version` — prints `specsoloist 0.6.0` and exits 0
- [ ] No uncommitted changes: `git status`

## CHANGELOG

Update `CHANGELOG.md` — rename `[Unreleased]` to `[0.6.0] - 2026-xx-xx` and add:

```markdown
## [0.6.0] - 2026-xx-xx

### Added
- `specs_path` field in `arrangement.yaml` — configures spec discovery directory
  (default: `src/`); `sp list`, `sp status`, `sp graph` now load the arrangement
  and use this field (HK-15)
- `--arrangement` flag on `sp list`, `sp status`, `sp graph` — explicit arrangement
  override for discovery commands (HK-15)
- `sp schema [topic]` — prints annotated JSON/text schema for `arrangement.yaml`;
  topic filter (e.g. `sp schema output_paths`) returns just that section (task 22)
- `sp help <topic>` — topic-based help with bundled spec content; `sp help arrangement`,
  `sp help spec-format`, `sp help conduct`, `sp help overrides`, `sp help specs-path`
  work from any PyPI install (task 23)
- `sp install-skills` now embeds a `<!-- sp-version: X.Y.Z -->` marker; `sp doctor`
  warns when installed skills are from an older package version (task 24)
- `--version` / `-V` flag — prints `specsoloist X.Y.Z` and exits 0 (HK-17)

### Changed
- `sp init` templates now include commented examples for `specs_path`, `output_paths.overrides`,
  `model`, and `env_vars` — all optional fields visible on first init (task 24)
- Skill and agent files updated with "Key Arrangement Fields" section covering
  `specs_path` and `output_paths.overrides` (task 24)

### Fixed
- `sp validate` no longer warns "No test scenarios found" for specs that use
  `yaml:test_scenarios` blocks; warning message now includes an inline example (HK-17)
- `output_paths.overrides` unit tests added; YAML round-trip confirmed (HK-16)
- `score/arrangement.spec.md` documents the nested `overrides` syntax (HK-16)
```

## Version Bump

```bash
grep 'version' pyproject.toml   # confirm current is 0.5.0
```

- [ ] Bump `version = "0.5.0"` → `"0.6.0"` in `pyproject.toml`
- [ ] Check for version in `src/specsoloist/__init__.py` if it exists:
  ```bash
  grep -r '__version__' src/specsoloist/__init__.py 2>/dev/null
  ```

## Commit & Tag

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v0.6.0"
git tag v0.6.0
git push origin main --tags
```

## GitHub Release

- [ ] Create a GitHub release from tag `v0.6.0`
- [ ] Title: `v0.6.0 — Real-world readiness`
- [ ] Copy the `[0.6.0]` section from CHANGELOG as release notes

## Post-release

- [ ] Add a new `[Unreleased]` section at the top of `CHANGELOG.md`
- [ ] Move this task to `tasks/HISTORY.md`
- [ ] Update `tasks/README.md` Current State table (test count, phase description)
