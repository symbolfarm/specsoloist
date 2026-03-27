# HK-22: Release v0.7.0

## Prerequisites

All of the following must be complete before running this checklist:

- [x] HK-14 — Revert publish workflow to trusted publishing
- [x] HK-15 — `specs_path` arrangement field + discovery commands
- [x] HK-16 — `output_paths.overrides` tests + score spec docs
- [x] HK-17 — `yaml:test_scenarios` validator fix + `--version` flag
- [x] Task 22 — `sp schema [topic]`
- [x] Task 23 — `sp help <topic>` with bundled specs
- [x] Task 24 — Richer init templates + skill updates + staleness detection
- [ ] HK-19 — Fix `score/cli.spec.md` quine correctness
- [ ] HK-20 — Update docs for v0.7.0 features
- [ ] HK-21 — Trim stale dynamic facts from AGENTS.md and ROADMAP.md
- [ ] Task 25 — `static` artifacts in arrangements

## Release Narrative

> **"Real-world readiness + full project reproducibility."** SpecSoloist now works
> correctly for projects that don't match its default layout. Agents can discover the
> full arrangement schema without reading source code. And for the first time, a
> `sp conduct` run can reproduce *all* project artifacts — not just compiled code —
> by declaring static assets in the arrangement.

## Pre-flight Checks

- [ ] `uv run python -m pytest tests/` — all passing (note count)
- [ ] `uv run ruff check src/` — 0 errors
- [ ] `uv run mkdocs build --strict` — clean (0 warnings)
- [ ] `sp schema` — runs without error, lists key fields including `static`
- [ ] `sp help arrangement` — runs without error, shows `static` section
- [ ] `sp --version` — prints `specsoloist 0.7.0` and exits 0
- [ ] No uncommitted changes: `git status`

## CHANGELOG

Update `CHANGELOG.md` — rename `[0.7.0] - 2026-xx-xx` to use today's date, and ensure
the following entries are present (add any that are missing):

```markdown
## [0.7.0] - 2026-xx-xx

### Added
- `static:` field in `arrangement.yaml` — declares files/directories to copy verbatim
  into the output during `sp conduct`; closes the full-project-reproducibility gap (task 25)
- `specs_path` field in `arrangement.yaml` — configures spec discovery directory
  (default: `src/`); `sp list`, `sp status`, `sp graph` now load the arrangement
  and use this field (HK-15)
- `--arrangement` flag on `sp list`, `sp status`, `sp graph` (HK-15)
- `sp schema [topic] [--json]` — annotated schema for `arrangement.yaml` (task 22)
- `sp help <topic>` — bundled Markdown guides: arrangement, spec-format, conduct,
  overrides, specs-path (task 23)
- `sp install-skills` embeds `<!-- sp-version: X.Y.Z -->` marker; `sp doctor` warns
  when installed skills are from an older package version (task 24)
- `--version` / `-V` global flag (HK-17)

### Changed
- `sp init` templates include commented examples for all optional fields (task 24)
- Skill and agent files updated with "Key Arrangement Fields" section (task 24)
- `AGENTS.md` and `ROADMAP.md` no longer embed stale test counts or phase snapshots;
  current state lives in `tasks/README.md` (HK-21)

### Fixed
- `sp validate` no longer warns for specs using `yaml:test_scenarios` blocks (HK-17)
- `score/cli.spec.md` corrected — removed `sp perform`, added `--version` and
  `--arrangement` entries (HK-19)
- `output_paths.overrides` unit tests added; YAML round-trip confirmed (HK-16)
- Publish workflow reverted to trusted publishing (HK-14)
```

## Version Bump

Already done — `pyproject.toml` is at `0.7.0`. Confirm with:
```bash
grep '^version' pyproject.toml
```

## Commit & Tag

```bash
git add -p   # review and stage all changes
git commit -m "chore: release v0.7.0"
git tag v0.7.0
git push origin main --tags
```

## GitHub Release

- [ ] Create a GitHub release from tag `v0.7.0`
- [ ] Title: `v0.7.0 — Real-world readiness`
- [ ] Copy the `[0.7.0]` section from CHANGELOG as release notes

## Post-release

- [ ] Add a new `[Unreleased]` section at the top of `CHANGELOG.md`
- [ ] Move this task to `tasks/HISTORY.md`
