# Task 25: `static` — verbatim artifacts in arrangements

**Effort**: Medium

## Motivation

The spec-as-source model has a gap: not everything in a real project is generated from specs.
Docs, templates, scripts, help files, and other hand-crafted assets are still part of the
project's output — but `sp conduct` currently ignores them. A clean-room regeneration of a
project from its specs + arrangement is therefore never complete.

The `static` field closes this gap. It declares files or directories that the conductor
copies verbatim from the project's source tree into the output. Together, specs + arrangement
+ static assets fully describe a reproducible project.

**SpecSoloist's own quine is the canonical example**: `src/specsoloist/help/` is a directory
of hand-written Markdown guides. They are not generated from specs, but they are part of the
package output. Declaring them as a static artifact means `sp conduct score/` can reproduce
the full `src/specsoloist/` package, not just the compiled Python modules.

## Design Decisions (locked)

- Field names: **`source`** and **`dest`** (not `from`/`to`). `source` avoids the Python
  keyword collision cleanly; `dest` is the Unix convention paired with `source`.
- Paths: both `source` and `dest` resolve **relative to the directory containing
  `arrangement.yaml`**. There is no separate "output root" — `dest` is just a path from
  the project root, the same as `source`.
- Copy behaviour: **always overwrite by default** (`overwrite: true`). Set `overwrite: false`
  to skip copying if the destination already exists (useful for generated-once files).
- Missing source: **warn but do not fail** — a missing doc is not a build error.
- The quine will have a `score/arrangement.yaml` that uses `static` to declare `help/`.

## Model (`src/specsoloist/schema.py`)

```python
class ArrangementStatic(BaseModel):
    """A verbatim file or directory to copy during sp conduct."""

    source: str = Field(description="Source path relative to the arrangement file.")
    dest: str = Field(description="Destination path relative to the arrangement file.")
    description: str = Field(default="", description="Human-readable note for agents.")
    overwrite: bool = Field(
        default=True,
        description="If False, skip copying when the destination already exists.",
    )
```

Add to `Arrangement`:

```python
static: list[ArrangementStatic] = Field(
    default_factory=list,
    description=(
        "Verbatim files or directories to copy into the output during sp conduct. "
        "Use for docs, templates, scripts, and other hand-crafted assets that are "
        "part of the project but not generated from specs."
    ),
)
```

## Arrangement YAML syntax

```yaml
static:
  - source: help/
    dest: src/myapp/help/
    description: "Bundled help files copied verbatim into the package"
  - source: templates/
    dest: src/myapp/templates/
  - source: scripts/seed.py
    dest: scripts/seed.py
  - source: ARRANGEMENT.md
    dest: ARRANGEMENT.md
    overwrite: false   # don't clobber user edits
```

## Conductor behaviour (`src/spechestra/conductor.py`)

After all specs have been compiled (the existing compilation loop), add a "copy static
artifacts" step:

```
for each entry in arrangement.static:
    src = arrangement_dir / entry.source
    dst = arrangement_dir / entry.dest
    if src does not exist:
        warn: "Static artifact not found: {entry.source}"
        continue
    if dst exists and not entry.overwrite:
        log: "Skipping static (overwrite=false): {entry.source}"
        continue
    if src is a directory:
        shutil.copytree(src, dst, dirs_exist_ok=True)
    if src is a file:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    log: "Copied static: {entry.source} → {entry.dest}"
```

## `sp doctor` warning

If any `static` entry's `source` path does not exist on disk, `sp doctor` should warn:

```
⚠ Static artifact not found: help/  (declared in arrangement.yaml)
```

## `sp schema` / `sp help`

- `sp schema` will automatically include the new `static` field (picked up from Pydantic
  field descriptions — no extra work needed once the model is in place).
- Update `src/specsoloist/help/arrangement.md` to document `static` with the YAML example
  above, including the `overwrite` flag.

## Score / Quine

Create `score/arrangement.yaml` — the quine's own arrangement file:

```yaml
target_language: python

specs_path: score/

output_paths:
  implementation: src/specsoloist/{name}.py
  tests: tests/test_{name}.py

static:
  - source: src/specsoloist/help/
    dest: src/specsoloist/help/
    description: "Bundled help guides — hand-written, not generated from specs"
  - source: src/specsoloist/skills/
    dest: src/specsoloist/skills/
    description: "Agent skill definitions — hand-written, not generated from specs"

environment:
  tools:
    - uv
    - pytest
  setup_commands:
    - uv sync

build_commands:
  test: uv run python -m pytest {file} -v
```

Note: `specs_path: score/` tells `sp conduct` to look in `score/` for specs, so the
command becomes `sp conduct --arrangement score/arrangement.yaml` (or auto-discovered
if run from the repo root with `arrangement.yaml` there). Double-check the right invocation
by reading how `sp conduct` resolves `src_dir` vs `arrangement.specs_path`.

## Tests

- **Unit** (`tests/test_arrangement.py`):
  - `ArrangementStatic` round-trips through YAML correctly
  - `source`/`dest`/`description`/`overwrite` fields parse correctly
  - `overwrite` defaults to `True`
  - `static` field defaults to empty list
- **Integration** (new `tests/test_static_artifacts.py`):
  - Conductor with a static directory entry copies it to the dest
  - Conductor with a static file entry copies it
  - Conductor with `overwrite=False` skips existing dest
  - Conductor with `overwrite=True` (default) overwrites existing dest
  - Conductor with a missing source path warns but does not fail
- **`sp schema`**: output includes `static` field and its sub-fields

## Files to Read

- `src/specsoloist/schema.py` — add `ArrangementStatic` and `static` field
- `src/spechestra/conductor.py` — add post-compilation copy step; understand how
  `arrangement_dir` is currently resolved for other path operations
- `src/specsoloist/cli.py` — `cmd_doctor` for the missing-source warning; understand
  how existing arrangement path warnings are structured
- `src/specsoloist/help/arrangement.md` — add `static` section
- `tests/test_arrangement.py` — add unit tests
