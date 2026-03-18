# HK-13: Remove non-code overview specs from score/

## Why

Three specs in `score/` are now `type: specification` (documentation only, no code generated):
- `arrangement.spec.md` — arrangement schema docs; content now covered by `schema.spec.md`
- `specsoloist.spec.md` — package overview in old numbered-sections format
- `spechestra.spec.md` — package overview in old numbered-sections format

They serve no purpose in the quine: they generate no code, their content is redundant with other
specs or with `docs/`, and they add noise to `sp list` and `sp validate` when run against `score/`.
The canonical documentation lives in `docs/` and in the living code-generating specs.

## Fix

Delete all three files:
```bash
rm score/arrangement.spec.md
rm score/specsoloist.spec.md
rm score/spechestra.spec.md
```

Verify the quine still works:
```bash
sp conduct score/ --model claude-haiku-4-5-20251001 --auto-accept --resume
PYTHONPATH=build/quine/src uv run python -m pytest build/quine/tests/ -q
```

## Success Criteria

- `ls score/*.spec.md` shows only code-generating specs (15 files: 14 code-gen + spec_format)
- Quine tests still pass
- `sp validate score/` reports no errors
