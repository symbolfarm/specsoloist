---
name: sp-respec
description: >
  Extract requirements from existing source code and express them as SpecSoloist
  spec files. Use when asked to spec out existing code, reverse-engineer a module,
  or migrate an implementation to spec-as-source. Runs `sp respec <file>`.
---

# sp-respec: Extract Requirements from Code

## When to use this skill

- User wants to document existing code as specs
- User asks to "respec" a file or module
- User wants to migrate an existing project to spec-as-source development
- User wants to extract a spec before refactoring

## How to respec

### With the CLI (recommended)

```bash
sp respec <source-file> [--test <test-file>] [--out <spec-path>]
```

**Examples:**
```bash
sp respec src/auth.py                              # Respec a module
sp respec src/auth.py --test tests/test_auth.py   # Include tests for context
sp respec src/auth.py --out score/auth.spec.md    # Save to specific path
```

### What it does

1. Reads the source file (and test file if provided)
2. Identifies the public API (exported classes, functions, types)
3. Extracts requirements: what each method does, edge cases, error conditions
4. Writes a `.spec.md` file describing the module's behavior
5. Validates the spec with `sp validate`

## The key principle

A good respec extracts **what** the code does, not **how** it does it.

- **DO** include: public API names, signatures, behavior descriptions, examples
- **DO NOT** include: private methods, algorithm names, internal data structures

A well-written spec lets a competent developer reimplement the module from scratch in any language, producing equivalent behavior — without seeing the original code.

## Output

A validated `.spec.md` file that:
- Passes `sp validate`
- Captures the public API and behavioral requirements
- Could be used to regenerate the module

## Tips

- Include the test file — tests are requirements expressed as code
- Review the generated spec to ensure it captures intent, not implementation
- Use `sp compile` on the result to verify it's complete enough to regenerate code
