# HK-06: Release v0.4.0

This is a checklist for cutting the 0.4.0 release. All code changes are complete —
this is purely the release process.

## Why 0.4.0?

- `type: reference` is a new spec format value (minor addition)
- `sp perform` removal is a breaking change for anyone using it
- Both justify a minor version bump over a patch

## Release Narrative

> **"Web app readiness."** SpecSoloist now works well for web applications, not just
> Python scripts. Two validated examples (FastHTML + Next.js AI chat), a `reference`
> spec type for third-party API documentation, and cleaned-up internals.

## Pre-flight Checks

- [ ] `uv run python -m pytest tests/` — all passing (247 tests, 4 skipped expected)
- [ ] `uv run ruff check src/` — 0 errors
- [ ] `uv run sp validate score/*.spec.md` — all valid (or note known exceptions)
- [ ] No uncommitted changes: `git status`

## CHANGELOG

- [ ] Rename `[Unreleased]` section in `CHANGELOG.md` to `[0.4.0] - YYYY-MM-DD`

## Version Bump

The version lives in `pyproject.toml`. Check where it is:

```bash
grep 'version' pyproject.toml
```

- [ ] Bump `version = "0.3.x"` → `"0.4.0"` in `pyproject.toml`
- [ ] Check if version is also in `src/specsoloist/__init__.py` or `src/specsoloist/cli.py`
  and bump there too if so:
  ```bash
  grep -r '__version__\|version' src/specsoloist/__init__.py src/specsoloist/cli.py 2>/dev/null
  ```

## Commit & Tag

```bash
git add pyproject.toml CHANGELOG.md   # (and any __init__.py / cli.py if changed)
git commit -m "chore: release v0.4.0"
git tag v0.4.0
git push origin main --tags
```

## PyPI Release (if publishing)

```bash
uv build
uv publish
```

Or check if there's a `Makefile` / `scripts/` entry for this.

## GitHub Release

- [ ] Create a GitHub release from tag `v0.4.0`
- [ ] Copy the `[0.4.0]` section from CHANGELOG as the release notes
- [ ] Title: `v0.4.0 — Web app readiness`

## Post-release

- [ ] Add a new `[Unreleased]` section at the top of CHANGELOG.md for the next batch
- [ ] Update `IMPROVEMENTS.md` header note with the release version and date
