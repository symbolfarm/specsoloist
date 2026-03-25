# Task 23: `sp help <topic>` — Topic-Based Help with Bundled Specs

## Why

`sp --help` prints a full command listing that agents read but often don't absorb
completely. Agents calling `sp help` mid-session want a short, focused answer to a
specific question, not a wall of text.

Additionally, agents working on integrations (like definitree) need access to
SpecSoloist's canonical spec format and arrangement documentation from within the
installed package — not from the source repo, which they don't have.

`sp help <topic>` solves both: short per-topic output, bundled spec content available
from any PyPI install.

## Behaviour

```bash
sp help                    # List available topics
sp help arrangement        # Return bundled arrangement.spec.md
sp help spec-format        # Return bundled spec_format.spec.md
sp help conduct            # Return a curated conduct reference
sp help overrides          # Return focused section on output_paths.overrides
sp help specs-path         # Return focused section on specs_path
```

`sp help` (no topic) prints:

```
Available help topics:

  arrangement    Full arrangement.yaml reference (all fields, examples)
  spec-format    Spec file format (.spec.md structure, types, blocks)
  conduct        Running sp conduct: arguments, arrangement, agent mode
  overrides      Per-spec output path overrides (output_paths.overrides)
  specs-path     Configuring the spec discovery directory

Run: sp help <topic>
```

## Bundled Spec Files

Key specs are bundled inside the package so they work from any PyPI install.

### Where to store them

Create `src/specsoloist/help/` with markdown files built from the score specs:

```
src/specsoloist/help/
  arrangement.md       # Auto-generated from score/arrangement.spec.md
  spec-format.md       # Auto-generated from score/spec_format.spec.md
  conduct.md           # Auto-generated from src/specsoloist/skills/sp-conduct/SKILL.md
  overrides.md         # Extracted section from arrangement.md
  specs-path.md        # Extracted section from arrangement.md
```

They are included in the wheel automatically because they live under `src/specsoloist/`.

### Auto-generation from score specs (investigate first)

**Before implementing**, investigate whether auto-generation is feasible and flag
any issues to the developer before proceeding:

The preferred approach is to generate these files at build time from their score
sources so that `sp help arrangement` always reflects the current spec, not a stale
hand-written copy. The ideal mechanism is a script or Makefile target that runs before
`uv build`, reading the source files from `score/` and `src/specsoloist/skills/` and
writing the output into `src/specsoloist/help/`.

**Questions to investigate:**

1. **Build integration**: Does the project use a `Makefile`, `scripts/`, or hatch
   build hooks? Check `pyproject.toml` for `[tool.hatch.build.hooks.*]` sections and
   look for any `Makefile` or `scripts/` directory. The right home for the generation
   script depends on what's already there.

2. **Score spec availability**: The `score/` directory lives at the repo root and is
   not included in the installed package. Generation must happen at build time (before
   `uv build`), not at runtime. Confirm this is workable — if score specs change
   frequently between releases, the workflow is: edit score → run generation script →
   commit the generated files → build wheel.

3. **Section extraction**: `overrides.md` and `specs-path.md` are focused excerpts,
   not whole spec files. The generation script needs to extract the relevant section
   from `score/arrangement.spec.md` by heading. Check whether the arrangement spec
   has clear `## Output Path Overrides` / `## specs_path` headings to split on, or
   whether this extraction is fragile. If extraction is unreliable, these two topics
   can fall back to hand-written files while the others are auto-generated.

4. **conduct.md source**: The conduct reference comes from
   `src/specsoloist/skills/sp-conduct/SKILL.md`, which is already inside the package.
   **Try this approach first**: serve it directly at runtime via `importlib.resources`
   rather than pre-building a copy, since the file is already bundled and always
   up-to-date. If this works cleanly, it's the right solution for this topic and
   avoids any build step for conduct help entirely.

**If any of these questions reveal a significant obstacle** (e.g. no suitable build
hook mechanism, score specs structured in a way that makes extraction unreliable),
stop and ask the developer how to proceed before writing any code. Do not silently
fall back to hand-written files without flagging it.

### Reading bundled files at runtime

Use `importlib.resources`:

```python
import importlib.resources as pkg_resources

def _read_help_file(topic: str) -> str | None:
    try:
        ref = pkg_resources.files("specsoloist.help").joinpath(f"{topic}.md")
        return ref.read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError):
        return None
```

This works correctly whether the package is installed from PyPI, run from a venv, or
run directly from the source tree.

## CLI Wiring

`sp help` should be handled **before** `SpecSoloistCore` initialisation (it needs no
project context):

```python
help_parser = subparsers.add_parser(
    "help",
    help="Get help on a specific topic (arrangement, spec-format, conduct, ...)"
)
help_parser.add_argument(
    "topic", nargs="?", default=None,
    help="Topic to look up"
)
```

In `main()`, handle `args.command == "help"` before the `SpecSoloistCore(os.getcwd())`
call. If no topic, print the topic list. If topic found, print the bundled markdown
(using `ui.console.print(Markdown(content))` for Rich rendering, or plain print for
`--quiet`/`--json` mode). If topic not found, print "Unknown topic" and list valid ones.

## Help File Content

`arrangement.md` and `spec-format.md` are generated from their score sources and should
not be edited by hand. `overrides.md` and `specs-path.md` may be generated (extracted
sections) or hand-written depending on what the investigation above finds.

If any help files must be hand-written (e.g. `conduct.md` if the skill file isn't a
suitable direct source), write them as clean practical references — not exhaustive, not
terse, ~50–100 lines. Confirm with the developer before writing hand-maintained files.

## Relationship to `sp schema`

`sp schema` (task 22) gives a machine-readable schema dump. `sp help arrangement` gives
a human/agent-readable narrative with YAML examples. Both are useful; they complement
rather than replace each other.

## Files to Read

- `src/specsoloist/cli.py` — `main()`, how `init` and `doctor` are handled without
  core initialisation, how `ui.console.print` is used
- `score/arrangement.spec.md` — source material for arrangement.md
- `score/spec_format.spec.md` — source material for spec-format.md
- `src/specsoloist/skills/sp-conduct/SKILL.md` — source material for conduct.md

## Update `score/cli.spec.md`

Add `sp help` to the CLI spec so the next quine run produces a CLI that includes this
command. Document: the `topic` argument, that it requires no project context, and the
list of built-in topics.

## Success Criteria

- `sp help` lists available topics without error, no project context needed
- `sp help arrangement` prints the arrangement reference, including overrides and
  specs_path fields added in HK-15/HK-16
- `sp help spec-format` prints the spec format reference
- `sp help bogus` prints "Unknown topic" and lists valid topics, exits non-zero
- Works from a directory with no `arrangement.yaml` and no `src/` directory
- All 355 tests pass; `uv run ruff check src/` clean

## Tests

Add `tests/test_cli_help.py`:
- `sp help` exits 0 and output lists at least `arrangement`, `spec-format`, `conduct`
- `sp help arrangement` exits 0 and output contains `output_paths` and `overrides`
- `sp help bogus` exits non-zero
- `_read_help_file("arrangement")` returns non-empty string (tests bundling works)
