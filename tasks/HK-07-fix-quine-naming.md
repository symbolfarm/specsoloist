# HK-07: Fix Quine Naming Mismatch

## Problem

The quine generates `speccomposer.py` / `specconductor.py` but the originals are
`composer.py` / `conductor.py`. This means a quine run produces differently-named files,
making semantic comparison harder and `sp diff` less useful.

## Decision

Update the score specs to instruct soloists to use the shorter names (`composer.py`,
`conductor.py`). The specs are the source of truth — the names they specify are canonical.

Do NOT rename the originals. The quine should converge to match the source, not vice versa.

## Files to Read

- `score/composer.spec.md` (or `speccomposer.spec.md` — check which exists)
- `score/conductor.spec.md` (or `specconductor.spec.md`)
- `src/spechestra/composer.py` — the original
- `src/spechestra/conductor.py` — the original

## Steps

1. Check which score spec filenames exist: `ls score/*.spec.md`
2. In the relevant score specs, find where the output filename is implied (usually in the
   spec name/frontmatter or any output path references)
3. Rename spec files if needed (e.g. `score/speccomposer.spec.md` → `score/composer.spec.md`)
4. Update any `depends_on` references in other specs that reference the old names
5. Verify with `uv run sp validate score/composer.spec.md` (and conductor)
6. Run `uv run python -m pytest tests/ -q` and `uv run ruff check src/`

## Success Criteria

- `ls score/*.spec.md` shows `composer.spec.md` and `conductor.spec.md` (not `speccomposer*`)
- All score specs pass `sp validate`
- All 270 tests still pass
- No references to `speccomposer` / `specconductor` remain in score specs
