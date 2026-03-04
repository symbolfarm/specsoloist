---
name: sp-compose
description: Draft architecture and spec files from a plain English description using SpecSoloist. Use when asked to design a system, create specs for a new feature, architect a project, or turn a natural language request into working specifications.
license: MIT
compatibility: Works standalone with any agent. Optionally uses specsoloist CLI (`pip install specsoloist`) for validation.
allowed-tools: Read Write Edit Bash Glob Grep
metadata:
  author: symbolfarm
  version: "0.3.2"
---

# sp-compose: Draft Architecture and Specs from Natural Language

You are a Software Architect using SpecSoloist to turn natural language requests into working specifications.

## Goal

Transform a plain English description into:
1. A well-structured **architecture** (components and their relationships)
2. Individual **spec files** for each component
3. A valid dependency graph with no circular dependencies

## Process

### Step 1: Understand the Request

Analyze the request to identify:
- Core functionality required
- Data types/models needed
- Relationships between components
- External dependencies

Ask clarifying questions if the request is ambiguous.

### Step 2: Draft Architecture

Design the component architecture:

1. **Identify components**: What distinct pieces of functionality are needed?
2. **Choose types**: For each component, determine the spec type:
   - `function` — Single operation with clear inputs/outputs
   - `type` — Data structure/model
   - `bundle` — Group of related functions/types (default for most modules)
   - `module` — Aggregation point for exports
   - `workflow` — Multi-step process orchestration
3. **Map dependencies**: Which components depend on which?
4. **Determine build order**: Topological sort of dependencies

Present the architecture for review before writing specs. Example format:

```
## Architecture: Todo App

### Components:
1. `user` (type) — User account data structure
2. `todo_item` (type) — Single todo item, depends on: user
3. `create_todo` (function) — Create a new todo, depends on: todo_item
4. `list_todos` (function) — List todos for a user, depends on: todo_item, user
5. `todo_api` (module) — Exports all todo operations

### Build Order:
user -> todo_item -> create_todo, list_todos -> todo_api
```

### Step 3: Write Spec Files

For each component, create a `.spec.md` file. Each spec must have:

**Frontmatter (required):**
```yaml
---
name: component_name
type: bundle  # or function, type, module, workflow
description: One sentence describing what this component does.
dependencies:
  - other_spec_name
---
```

**Required section for all specs:**
```markdown
# Overview

What this module does in 1-3 sentences.
```

**Type-specific required sections:**

| Type | Required sections |
|------|------------------|
| `bundle` | `# Overview` + at least one function/type defined in YAML |
| `function` | `# Overview`, `# Behavior`, `# Examples` |
| `type` | `# Overview`, `# Fields` |
| `module` | `# Overview`, `# Exports` |
| `workflow` | `# Overview`, `# Steps` |

**Bundle format example:**
```markdown
---
name: math_utils
type: bundle
description: Basic math utility functions.
---

# Overview

Utility functions for common math operations.

```yaml:functions
- name: clamp
  inputs:
    value: float
    min_val: float
    max_val: float
  outputs: float
  behavior: "Returns value clamped to [min_val, max_val]"
- name: lerp
  inputs: {a: float, b: float, t: float}
  outputs: float
  behavior: "Linear interpolation between a and b by factor t"
```
```

**Spec writing rules:**
- `name` must be `snake_case` and match the filename (without `.spec.md`)
- No `language_target` in frontmatter
- Specs define **what**, not **how** — no algorithm names or implementation details
- Include realistic examples with inputs and expected outputs
- Quote YAML strings containing special chars (`{`, `}`, `:`, `#`)

### Step 4: Validate Each Spec

If specsoloist is installed:
```bash
uv run sp validate <spec_path>
```

If not installed, manually check:
- Frontmatter has `name` and `type`
- Has `# Overview` section
- Type-specific required sections are present
- No circular dependencies in the declared `dependencies`

Fix any issues before moving to the next spec.

### Step 5: Verify Build Order

If specsoloist is installed:
```bash
uv run sp graph
```

Otherwise, manually verify the dependency graph is a valid DAG (no cycles).

## Output Structure

```
src/
  <project_name>/
    types/
      user.spec.md
      todo_item.spec.md
    functions/
      create_todo.spec.md
      list_todos.spec.md
    mod.spec.md          # Module aggregating exports
```

Or for simpler projects:
```
src/
  <name>.spec.md         # Single spec if only one component
```

## Spawning Sub-Composers

For complex systems with multiple independent subsystems, spawn additional `sp-compose` subagents to work on each subsystem in parallel. Each sub-composer should:
1. Focus on one coherent subsystem
2. Declare any cross-subsystem dependencies

## Tips

- **Start simple**: Begin with types, then functions that use them
- **Validate early**: Check each spec before creating the next
- **Think modular**: Prefer smaller, focused specs over monolithic ones
- **Consider testing**: Examples in specs become test cases

**Next step:** Use `sp-conduct` to compile specs into working code.
