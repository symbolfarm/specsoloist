---
name: sp-compose
description: Draft architecture and spec files from a plain English description using SpecSoloist. Use when asked to design a system, create specs for a new feature, architect a project, or turn a natural language request into working specifications.
license: MIT
compatibility: Requires specsoloist CLI (`pip install specsoloist` or `uv add specsoloist`). Designed for Claude Code and compatible agents.
metadata:
  author: symbolfarm
  version: "0.3.2"
---

# sp-compose: Compose Specs from Natural Language

## When to use this skill

- User wants to design a new system or application from scratch
- User asks to "spec out" a feature or component
- User describes what they want to build in plain English
- User wants an architecture drafted before writing any code

## How to compose

### With the CLI (recommended)

```bash
sp compose "<description of what you want to build>"
```

This launches an interactive agent that:
1. Analyzes the request and identifies components (types, functions, modules)
2. Drafts an architecture and presents it for review
3. Generates `.spec.md` files in `src/`
4. Validates each spec with `sp validate`

**Example:**
```bash
sp compose "a REST API for managing user todos with authentication"
```

### Without the CLI

If `sp` is not installed, follow the compose workflow manually:

1. Identify the components (data types, functions, modules)
2. Map dependencies between them
3. Create a `.spec.md` file for each component using the SpecSoloist spec format
4. Each spec needs: YAML frontmatter (`name`, `type`, `description`), an `# Overview` section, and type-appropriate sections (`# Behavior`, `# Examples`, etc.)

## Output

- `src/` populated with `.spec.md` files for each component
- Valid dependency graph (no circular dependencies)
- All specs passing `sp validate`

**Next step:** Run `sp conduct` to compile specs into working code.

## Tips

- Be descriptive: more detail in your request → better specs
- Review and edit the generated specs before conducting
- Run `sp graph` to visualize the dependency order
