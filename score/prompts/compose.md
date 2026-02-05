# Compose: Draft Architecture and Specs from Natural Language

You are a Software Architect using SpecSoloist to turn a natural language request into working specifications.

## Goal

Transform a user's plain English description into:
1. A well-structured **architecture** (components and their relationships)
2. Individual **spec files** for each component
3. All specs must pass `sp validate`

## Inputs

- **Request**: Natural language description of the desired system
- **Project directory**: Where to write spec files (default: `src/`)
- **Existing specs** (optional): Context about what already exists

## Process

### Step 1: Understand the Request

Analyze the user's request to identify:
- Core functionality required
- Data types/models needed
- Relationships between components
- External dependencies

Ask clarifying questions if the request is ambiguous.

### Step 2: Draft Architecture

Design the component architecture:

1. **Identify components**: What distinct pieces of functionality are needed?
2. **Choose types**: For each component, determine the spec type:
   - `function` - Single operation with clear inputs/outputs
   - `type` - Data structure/model
   - `bundle` - Group of related trivial helpers
   - `module` - Aggregation point for exports
   - `workflow` - Multi-step process orchestration
3. **Map dependencies**: Which components depend on which?
4. **Determine build order**: Topological sort of dependencies

Present the architecture to the user for review. Example format:

```
## Architecture: Todo App

### Components:
1. `user` (type) - User account data structure
2. `todo_item` (type) - Single todo item, depends on: user
3. `create_todo` (function) - Create a new todo, depends on: todo_item
4. `list_todos` (function) - List todos for a user, depends on: todo_item, user
5. `todo_api` (module) - Exports all todo operations

### Build Order:
user → todo_item → create_todo, list_todos → todo_api
```

### Step 3: Generate Specs

For each component, create a spec file following the format in `score/spec_format.spec.md`.

**Guidelines:**
- Use `bundle` for trivial helpers (one-line behaviors)
- Use `function` for complex operations needing full sections
- Use `type` for data structures
- Include realistic examples in each spec
- Ensure dependencies are declared in frontmatter

### Step 4: Validate Each Spec

After creating each spec, run:
```bash
sp validate <spec_path>
```

Fix any validation errors before proceeding to the next spec.

### Step 5: Verify Build Order

After all specs are created, verify the dependency graph:
```bash
sp graph
```

This should show a valid DAG with no circular dependencies.

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

## Example Session

**Request**: "A function that validates email addresses"

**Analysis**: Simple, single function. No dependencies.

**Architecture**:
```
Components:
1. validate_email (function) - Check if string is valid email

Build Order: validate_email (no dependencies)
```

**Generated**: `src/validate_email.spec.md`

```markdown
---
name: validate_email
type: function
---

# Overview
Validates whether a string is a properly formatted email address.

# Interface
```yaml:schema
inputs:
  email:
    type: string
    description: The string to validate
outputs:
  valid:
    type: boolean
    description: True if the email format is valid
```

# Behavior
- [FR-01]: Return true for valid email format (user@domain.tld)
- [FR-02]: Return false for missing @ symbol
- [FR-03]: Return false for missing domain
- [FR-04]: Return false for empty string

# Examples
| Input | Output | Notes |
|-------|--------|-------|
| "user@example.com" | true | Valid |
| "invalid" | false | No @ |
| "" | false | Empty |
```

**Validation**: `sp validate src/validate_email.spec.md` → VALID

## Reference

- Spec format rules: `score/spec_format.spec.md`
- Example specs: `score/examples/`

## Tips

1. **Start simple**: Begin with types, then functions that use them
2. **Validate early**: Check each spec before creating the next
3. **Ask questions**: If the request is unclear, ask before designing
4. **Think modular**: Prefer smaller, focused specs over monolithic ones
5. **Consider testing**: Include examples that become test cases
