---
name: sp-soloist
description: >
  Compile a single SpecSoloist spec into working code and tests. Use when asked to
  compile one specific spec, implement a single component, or test whether a spec is
  complete enough to generate code from. Runs `sp compile <name>`.
---

# sp-soloist: Compile a Single Spec

## When to use this skill

- User wants to compile one specific spec (not the whole project)
- User wants to test whether a spec is implementable
- User is iterating on a spec + implementation cycle for a single component
- User has just composed a spec and wants to see it compiled

## How to compile

### With the CLI (recommended)

```bash
sp compile <spec-name>
```

**Examples:**
```bash
sp compile resolver          # Compile the resolver spec
sp compile auth --no-tests   # Compile without generating tests
sp compile parser --model claude-opus-4-6  # Use a specific model
```

### What it does

1. Reads the spec file (`src/<name>.spec.md` or the path provided)
2. Validates the spec structure
3. Generates an implementation file
4. Generates a test file
5. Reports the output paths

### Typical workflow

```bash
sp compile <name>    # Compile implementation + tests
sp test <name>       # Run the tests
sp fix <name>        # Fix if tests fail
```

## Tips

- Validate first: `sp validate <name>` before compiling
- Check dependencies are compiled: `sp graph` to see the build order
- The spec is the source of truth — if output isn't right, improve the spec
- For the full project, use `sp conduct` instead of compiling one-by-one
