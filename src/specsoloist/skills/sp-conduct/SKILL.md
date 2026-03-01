---
name: sp-conduct
description: Compile all SpecSoloist specs into working code by orchestrating soloist agents in dependency order. Use when asked to build a project, compile specs, conduct the build, or generate code from existing spec files.
license: MIT
compatibility: Requires specsoloist CLI (`pip install specsoloist` or `uv add specsoloist`). Designed for Claude Code and compatible agents.
metadata:
  author: symbolfarm
  version: "0.3.2"
---

# sp-conduct: Orchestrate Spec Compilation

## When to use this skill

- User wants to compile all specs in a project into working code
- User says "build the project", "conduct", or "compile the specs"
- User has finished reviewing specs and is ready to generate code
- User wants to run a quine validation (`sp conduct score/`)

## How to conduct

### With the CLI (recommended)

```bash
sp conduct [spec-dir]
```

**Examples:**
```bash
sp conduct              # Compile all specs in src/
sp conduct src/         # Explicitly specify spec directory
sp conduct score/       # Quine: regenerate SpecSoloist itself
```

The conductor:
1. Reads all `*.spec.md` files in the directory
2. Resolves the dependency graph (topological order)
3. Spawns soloist subagents to compile each spec
4. Runs the full test suite on completion

### Options

```bash
sp conduct --parallel --workers 4    # Compile independent specs in parallel
sp conduct --incremental             # Only recompile changed specs
sp conduct --arrangement arr.yaml    # Use a custom arrangement file
```

## Output

- Implementation files written to `src/`
- Tests written to `tests/`
- Full test suite run and results reported

## Tips

- Review specs before conducting — the spec is the source of truth
- Use `sp compile <name>` to test a single spec first
- Use `sp diff` to compare builds run-over-run
- If tests fail after conducting, use `sp fix <name>` to auto-heal
