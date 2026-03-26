# specs_path Reference

`specs_path` configures where SpecSoloist looks for spec files (`.spec.md`). It affects
`sp list`, `sp status`, `sp graph`, and `sp conduct` (when no positional directory is
given). The default is `src/`.

---

## Why it exists

SpecSoloist's default spec directory is `src/`, which is correct for projects that
store only specs there. Projects that use `src/` for application code alongside specs —
or that prefer a separate `specs/` directory — need a different path.

Without `specs_path`, these commands print:

```
⚠ No specs found in src/
```

even when specs exist in another directory.

---

## Setting specs_path

In `arrangement.yaml`:

```yaml
target_language: python
specs_path: specs/           # all sp list/status/graph/conduct calls use specs/
output_paths:
  implementation: src/{name}.py
  tests: tests/test_{name}.py
build_commands:
  test: uv run pytest tests/
```

`sp conduct`, `sp list`, `sp status`, and `sp graph` all auto-discover `arrangement.yaml`
in the current directory and read `specs_path` from it automatically.

---

## Overriding per-command

For one-off use, pass `--arrangement` explicitly:

```bash
sp list --arrangement path/to/other.yaml
sp status --arrangement staging.yaml
```

`sp conduct` also accepts a positional directory argument that takes precedence over
`specs_path`:

```bash
sp conduct specs/             # uses specs/ regardless of specs_path in arrangement
sp conduct                    # uses specs_path from arrangement (or src/ if none)
```

---

## Common patterns

| Project layout | specs_path setting |
|---------------|-------------------|
| Specs in `src/` (default) | omit or `specs_path: src/` |
| Specs in `specs/` | `specs_path: specs/` |
| Specs in `score/` (SpecSoloist quine) | `specs_path: score/` |
| Specs nested under `src/specs/` | `specs_path: src/specs/` |

---

## See also

- `sp help arrangement` — full arrangement.yaml reference
- `sp schema` — annotated arrangement schema
