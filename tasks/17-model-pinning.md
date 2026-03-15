# Task 17: Model Pinning in Arrangements

## Why

Currently the model is either set globally via `SPECSOLOIST_LLM_MODEL` env var or passed
as `--model` on the CLI. There is no way to pin different models per-spec or per-project
in the arrangement file. This matters for cost/quality tradeoffs: leaf specs (config, utils)
can use a cheap fast model; core specs (parser, compiler) deserve a more capable one.

## Files to Read

- `src/specsoloist/schema.py` — `Arrangement` model; add `model` field here
- `src/specsoloist/compiler.py` — where the model is selected for compilation
- `src/specsoloist/cli.py` — `--model` flag; arrangement resolution
- `score/arrangement.spec.md` — update to document the new field
- `examples/fasthtml_app/arrangement.yaml` — example to update

## Behaviour

Add a `model` field to the arrangement YAML:

```yaml
model: claude-haiku-4-5-20251001   # used for all specs unless overridden
```

Precedence (highest to lowest):
1. `--model` CLI flag
2. `model` field in arrangement file
3. `SPECSOLOIST_LLM_MODEL` environment variable
4. Provider default

## Implementation Notes

- Add `model: str | None = None` to the `Arrangement` Pydantic model in `schema.py`
- In `_resolve_arrangement()` (or wherever the model is selected), apply the precedence
  order above
- The `--model` CLI flag already exists on `sp conduct` and `sp compile` — just wire
  the arrangement value into the fallback chain
- Do NOT add per-spec model overrides in this task (that's more complex; arrangement-level
  pinning covers the main use case)

## Success Criteria

- `arrangement.yaml` with `model: claude-haiku-4-5-20251001` uses haiku when `--model`
  is not passed on CLI
- `--model` CLI flag still overrides the arrangement value
- `sp validate --arrangement` reports the pinned model in output
- `score/arrangement.spec.md` documents the `model` field
- All 270 tests pass, ruff clean

## Tests

Add to `tests/test_arrangement.py` or a new `tests/test_model_pinning.py`:
- Arrangement with `model` field parses correctly
- Model precedence: CLI flag > arrangement > env var
- Arrangement without `model` field still works (backward compat)
