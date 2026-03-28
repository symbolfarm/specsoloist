# Task 36: External dependency declaration in spec frontmatter

**Effort**: Medium

**Depends on**: None

## Motivation

Specs can depend on external packages (Textual, FastHTML, etc.) but there's no structured
way to declare this. When `sp conduct` spawns soloists, they fail on `import textual` if
the package isn't installed — wasting tokens on a fix loop for an environment problem, not
a code problem.

The conductor should know about external dependencies *before* spawning soloists, so it
can fail fast with a clear message or ensure the environment is ready.

## Design

### New frontmatter field: `requires`

```yaml
---
name: tui
type: bundle
dependencies:
  - from: build_state.spec.md
requires:
  - textual>=1.0
---
```

`requires` is a list of PEP 508 dependency specifiers (same format as `pyproject.toml`
dependencies). This keeps the declaration close to the spec that needs it — the TUI spec
knows it needs Textual, not some distant config file.

### Conductor flow change

Current:
1. Parse specs, resolve dependency graph
2. Spawn soloists

Proposed:
1. Parse specs, resolve dependency graph
2. **Gather `requires:` from all specs, deduplicate**
3. **Check each requirement is satisfied (importable, version matches)**
4. **If missing: fail fast with a clear message listing what's needed**
5. Spawn soloists

### `sp doctor` integration

`sp doctor` already checks API keys, CLIs, and tools. Add a check for spec requirements:

```
$ sp doctor
...
✔ API keys configured
✔ CLI tools available
✖ Missing packages for specs:
    textual>=1.0 (required by: tui.spec.md)
    python-fasthtml>=0.12 (required by: fasthtml_interface.spec.md)
```

### Optional: auto-install

The arrangement could opt into auto-installation:

```yaml
environment:
  auto_install_requires: true  # default: false
```

When enabled, the conductor runs `pip install` (or `uv pip install`) for missing packages
before spawning soloists. When disabled (default), it just reports and exits.

## Relationship to reference specs

Reference specs document external APIs for soloist accuracy. `requires:` declares that a
package must be *installed*. These are complementary:

- A reference spec for FastHTML helps the soloist generate correct code
- `requires: python-fasthtml>=0.12` ensures the package is available at test time

Both can coexist on the same spec, or `requires:` can appear on non-reference specs that
simply use an external package.

## Files to Read

- `src/specsoloist/config.py` — arrangement parsing, environment config
- `src/specsoloist/parser.py` — frontmatter parsing
- `src/specsoloist/core.py` — `compile_project()` flow
- `src/specsoloist/cli.py` — `sp doctor` command

## Success Criteria

- `requires:` field parsed from spec frontmatter
- `sp validate` accepts specs with `requires:` (no structural error)
- Conductor checks requirements before spawning soloists
- Clear error message listing missing packages and which specs need them
- `sp doctor` reports missing spec requirements
- Existing specs without `requires:` are unaffected
