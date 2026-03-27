# HK-20: Update docs for v0.6.0

**Effort**: Small–Medium (1–2 hours)

## Problem

The docs site and README were not updated when v0.6.0 features shipped. Three pages have
missing commands or fields; users and agents consulting the docs will not find them.

## Missing items

### `docs/reference/cli.md`

1. **`sp schema [topic] [--json]`** — not documented at all. Add a section covering:
   - Basic usage: `sp schema` (full schema), `sp schema <topic>` (filtered), `sp schema --json`
   - Available topics mirror the top-level Arrangement fields (`output_paths`, `environment`, etc.)
   - Can be run without a project (no arrangement required)

2. **`sp help <topic>`** — not documented at all. Add a section covering:
   - `sp help` lists available topics
   - Available topics: `arrangement`, `spec-format`, `conduct`, `overrides`, `specs-path`
   - Works from any PyPI install (guides are bundled)

3. **`--version` / `-V` global flag** — missing from the Global Flags section. One line: prints
   `specsoloist X.Y.Z` and exits 0.

4. **`--arrangement <file>` on `sp list`, `sp status`, `sp graph`** — these commands gained this
   flag in HK-15 but the docs don't mention it. Add to each command's flag table.

### `docs/guide/arrangement.md`

5. **`specs_path` field** — not in the Fields table. Add it with description and example:
   ```yaml
   specs_path: specs/   # default is src/
   ```

6. **`output_paths.overrides`** — not documented. Add a subsection under `output_paths`
   explaining the nested syntax and when to use it. The canonical form is:
   ```yaml
   output_paths:
     implementation: src/{name}.py
     tests: tests/test_{name}.py
     overrides:
       my_module:
         implementation: src/mypackage/my_module.py
         tests: tests/mypackage/test_my_module.py
   ```

### `README.md`

7. Add `sp schema`, `sp help`, and `--version` to the CLI reference table/section. These are
   the most discoverable entry point for new users.

## Verification

- `uv run mkdocs build --strict` passes cleanly
- `uv run mkdocs serve` — manually verify the three affected pages look correct
- All six new items appear in the rendered docs

## Files to Read

- `docs/reference/cli.md` — add items 1–4
- `docs/guide/arrangement.md` — add items 5–6
- `README.md` — add item 7
- `src/specsoloist/cli.py` — search for `cmd_schema`, `cmd_help` for accurate descriptions
- `src/specsoloist/schema.py` — for accurate `specs_path` and `overrides` field descriptions
