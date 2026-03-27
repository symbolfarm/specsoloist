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

## Design

New field on `Arrangement` in `schema.py`:

```python
static: list[ArrangementStatic] = Field(default_factory=list, description="...")
```

New model:

```python
class ArrangementStatic(BaseModel):
    from_: str = Field(alias="from", description="Source path relative to the arrangement file.")
    to: str = Field(description="Destination path relative to the output root.")
    description: str = Field(default="", description="Human-readable note for agents.")
```

Note: `from` is a Python keyword, so use `from_` with `alias="from"` and
`model_config = ConfigDict(populate_by_name=True)`.

### Arrangement YAML syntax

```yaml
static:
  - from: help/
    to: src/myapp/help/
    description: "Bundled help files copied verbatim into the package"
  - from: templates/
    to: src/myapp/templates/
  - from: scripts/seed.py
    to: scripts/seed.py
```

Paths are relative to the directory containing `arrangement.yaml`.

### Conductor behaviour (`src/spechestra/conductor.py`)

After all specs have been compiled (the existing compilation loop), add a "copy static
artifacts" step:

```
for each entry in arrangement.static:
    src = resolve relative to arrangement dir
    dst = resolve relative to output root (arrangement's output_paths base)
    if src is a directory: shutil.copytree(src, dst, dirs_exist_ok=True)
    if src is a file: shutil.copy2(src, dst), creating parent dirs as needed
    if src does not exist: warn (do not fail — missing doc is not a build error)
    log: "Copied static: {entry.from_} → {dst}"
```

The output root for `to` paths should be consistent with how `output_paths.implementation`
is resolved — i.e., relative to the arrangement file's directory.

### `sp doctor` warning

If any `static` entry's `from` path does not exist on disk, `sp doctor` should warn:
```
⚠ Static artifact not found: help/  (declared in arrangement.yaml)
```

### `sp schema` / `sp help`

- `sp schema` should include the new `static` field with its description.
- Update `src/specsoloist/help/arrangement.md` to document `static` with the YAML example above.

## Score / Quine

Add `static` to SpecSoloist's own `score/arrangement.yaml` (once it exists — currently the
quine uses no arrangement file for the score itself, so this may need a `score/arrangement.yaml`
to be created first):

```yaml
static:
  - from: src/specsoloist/help/
    to: src/specsoloist/help/
    description: "Bundled help guides — hand-written, not generated"
```

Update `score/arrangement.spec.md` if it is recreated, or update
`src/specsoloist/help/arrangement.md` to document the new field.

## Tests

- **Unit**: `ArrangementStatic` round-trips through YAML correctly
- **Unit**: `from` alias works (`{"from": "help/", "to": "src/help/"}` parses correctly)
- **Unit**: `static` field defaults to empty list
- **Integration**: conductor with a static directory entry copies it to the output
- **Integration**: conductor with a static file entry copies it
- **Integration**: conductor with a missing static path warns but does not fail
- **`sp schema`**: output includes `static` field

## Files to Read

- `src/specsoloist/schema.py` — add `ArrangementStatic` and `static` field
- `src/spechestra/conductor.py` — add post-compilation copy step
- `src/specsoloist/cli.py` — `cmd_doctor` for the missing-path warning
- `src/specsoloist/help/arrangement.md` — add `static` section
- `tests/test_arrangement.py` — add new unit tests
