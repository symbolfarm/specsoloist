# Task 35: Directory-based spec discovery

**Effort**: Medium

**Depends on**: None (can be done independently)

## Motivation

The current arrangement maps spec names to output paths via a flat pattern:
`src/specsoloist/{name}.py`. Any module in a subdirectory (e.g., `subscribers/build_state.py`)
needs an explicit `output_paths.overrides` entry. This doesn't scale — a moderately complex
app with `models/`, `routes/`, `services/` directories would need an override for every spec.

Directory-based spec discovery makes the score directory mirror the source directory, so the
path structure is implicit rather than requiring per-spec overrides.

## Design

Allow specs to be organized in subdirectories under `specs_path`:

```
score/
  config.spec.md              -> src/specsoloist/config.py
  parser.spec.md              -> src/specsoloist/parser.py
  subscribers/
    build_state.spec.md       -> src/specsoloist/subscribers/build_state.py
    ndjson.spec.md            -> src/specsoloist/subscribers/ndjson.py
    tui.spec.md               -> src/specsoloist/subscribers/tui.py
```

The arrangement pattern uses `{path}` (includes subdirectories) instead of `{name}` (flat):

```yaml
specs_path: score/
output_paths:
  implementation: src/specsoloist/{path}.py    # {path} = subscribers/build_state
  tests: tests/test_{name}.py                  # {name} = build_state (leaf only)
```

Both `{name}` (leaf filename without extension) and `{path}` (relative directory + name)
should be supported as pattern variables. `{name}` remains the default for backward
compatibility.

## Files to Read

- `src/specsoloist/config.py` — `OutputPaths`, arrangement parsing, `resolve_implementation()`
- `src/specsoloist/parser.py` — `list_specs()`, spec discovery logic
- `src/specsoloist/resolver.py` — dependency resolution (uses spec names)
- `score/arrangement.yaml` — current overrides pattern

## Key Decisions

- **Backward compatible**: `{name}` keeps working as-is. `{path}` is opt-in.
- **Dependency references**: Specs in subdirectories can be referenced by path
  (`from: subscribers/build_state.spec.md`) or by name (`from: build_state.spec.md`)
  if unambiguous. Ambiguous names (same leaf name in different directories) require
  the full path.
- **Flat score still works**: A flat `score/` directory with `{name}` patterns is
  unchanged. Directory nesting is additive.

## Success Criteria

- Specs in subdirectories are discovered by `sp list`, `sp validate`, `sp conduct`
- `{path}` pattern variable resolves correctly in `output_paths`
- Existing flat scores (including the quine) continue working unchanged
- Dependencies can reference specs by path or unambiguous name
- Tests cover: nested discovery, path pattern resolution, ambiguous name detection,
  backward compatibility with flat layouts
