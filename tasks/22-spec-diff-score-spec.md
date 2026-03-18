# Task 22: Add spec_diff to score

## Why

`src/specsoloist/spec_diff.py` powers `sp diff <spec_name>` (spec-drift detection mode — compares
spec-declared symbols against the compiled implementation). It has no score spec, so `sp conduct
score/` never regenerates it. This is a quine hole: the quine output is missing one module.

## What

Use `sp respec` to extract a requirements-oriented spec from the source, review it, place it in
`score/spec_diff.spec.md`, and verify the quine regenerates the module with passing tests.

## Steps

1. **Respec the module**:
   ```bash
   sp respec src/specsoloist/spec_diff.py \
     --test tests/test_spec_diff.py \
     --out score/spec_diff.spec.md
   ```

2. **Review the generated spec.** Key things to check against `src/specsoloist/spec_diff.py`
   and `tests/test_spec_diff.py`:
   - Public types: `SpecDiffIssue` (kind, symbol, detail), `SpecDiffResult` (spec_name, code_path,
     test_path, issues; issue_count property; to_dict method)
   - Public functions: `diff_spec(spec, code_path, test_path) -> SpecDiffResult` — uses AST to
     extract public names from the compiled Python file and compares against spec-declared symbols;
     reports MISSING (in spec, not in code), UNDOCUMENTED (in code, not in spec), TEST_GAP (in
     spec, no matching test function)
   - The spec should be requirements-oriented — describe what each function does, not how

3. **Wire the dependency**: `spec_diff` depends on nothing outside stdlib/ast. Add it to score/ with
   no dependencies.

4. **Verify**:
   ```bash
   sp validate score/spec_diff.spec.md
   ```
   Then do a spot quine compile:
   ```bash
   # From a terminal (outside Claude Code), or use Agent tool:
   sp conduct score/spec_diff.spec.md --model claude-haiku-4-5-20251001 --auto-accept
   PYTHONPATH=build/quine/src uv run python -m pytest build/quine/tests/test_spec_diff.py -v
   ```

## Files to Read

- `src/specsoloist/spec_diff.py` — source of truth
- `tests/test_spec_diff.py` — existing tests (guide for what the spec should cover)

## Success Criteria

- `score/spec_diff.spec.md` exists and passes `sp validate`
- A full quine run includes `spec_diff` in its compiled output
- `build/quine/tests/test_spec_diff.py` passes
