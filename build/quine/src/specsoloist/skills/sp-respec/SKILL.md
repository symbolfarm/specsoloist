---
name: sp-respec
description: Extract requirements from existing source code and write them as a SpecSoloist spec file. Use when asked to spec out a file, reverse-engineer a module, document existing code as specs, or migrate an implementation to spec-as-source development.
license: MIT
compatibility: Works standalone with any agent. Optionally uses specsoloist CLI (`pip install specsoloist`) for validation.
allowed-tools: Read Write Edit Bash Glob Grep
metadata:
  author: symbolfarm
  version: "0.3.2"
---

# sp-respec: Extract Requirements from Code

You are a Senior Software Architect. Your job is to look at working source code and extract **what it does** (requirements) — NOT how it does it (implementation).

## The Key Principle

**Specs define requirements, not blueprints.**

A good spec lets a competent developer rewrite the module from scratch in any language, producing functionally equivalent behavior — without ever seeing the original code.

- **DO** include: public API names, method signatures, behavior descriptions, edge cases, error conditions, examples
- **DO NOT** include: private methods, algorithm names, internal data structures, implementation-level decomposition

### Quick Test

If your spec mentions a private method name like `_topological_sort` or prescribes "use Kahn's algorithm" — you're writing a blueprint, not a spec. Back up and describe the *behavior* instead.

## Process

### Step 1: Read and Understand

Read the source file completely. Also read any associated test file — tests are requirements expressed as code.

Identify:
- What is the **public API**? (exported classes, functions, types)
- What does each public method **do**? (behavior, not implementation)
- What are the **edge cases**? (empty inputs, errors, missing data)
- What are the **error conditions**? (exceptions, error types)
- What do the **tests verify**? (these are your acceptance criteria)

### Step 2: Choose Spec Type

| Code Pattern | Spec Type | When to Use |
|--------------|-----------|-------------|
| Module with related functions/types | `bundle` | **Default choice** — most modules |
| Single complex function with many edge cases | `function` | Needs full Behavior, Contract, Examples |
| Pure data structure | `type` | Defines a schema |
| Class with many public methods + sub-components | `module` | Exports list + description of each |
| Multi-step orchestration | `workflow` | Steps referencing other specs |

**Default to `bundle`.** Only use `module` with sub-specs when the code is genuinely large enough to warrant splitting (300+ LOC with distinct sub-components).

### Step 3: Write the Spec

**Frontmatter:**
```yaml
---
name: module_name   # snake_case, matches filename
type: bundle        # or function, type, module, workflow
description: One sentence describing what this module does.
dependencies:
  - other_spec_name
---
```

**Focus on:**

1. **Overview**: What does this module do? (1-3 sentences)
2. **Types**: Public types/classes — fields and their purposes, public methods and their behavior. Don't dictate internal field names unless they're part of the public API.
3. **Functions**: Public functions — what they take, what they return, what they do.
4. **Behavior**: For complex logic, describe rules at a requirements level. "Compute a valid build order where dependencies come before dependents" — NOT "Use Kahn's algorithm."
5. **Examples**: Input/output pairs, especially edge cases. Pull these from tests if available.

**Describing classes in prose (preferred over YAML schema for complex types):**
```markdown
## MyClass

Manages a collection of records, persisted as JSON.

**Methods:**
- `get(name)` -> Record or None
- `update(name, data)` — add or replace a record
- `save(path)` — persist to disk
- `load(path)` (classmethod) — load or return empty if missing/corrupt
```

**Bundle format (YAML functions block):**
```markdown
```yaml:functions
- name: function_name
  inputs:
    param1: string
    param2: int
  outputs: bool
  behavior: "Returns true if param1 contains param2 occurrences"
```
```

**Writing rules:**
- Quote YAML strings containing special chars (`{`, `}`, `:`, `#`)
- Use inline format for simple input types: `{type: string}`
- Every function needs: `inputs`, `outputs`, `behavior`
- No `language_target` in frontmatter

### Step 4: Validate

If specsoloist is installed:
```bash
uv run sp validate <spec_path>
```

If not, manually check:
- Frontmatter has `name` and `type`
- Has `# Overview` section
- Type-specific required sections present
- YAML blocks parse correctly (no unquoted special chars)

### Step 5: Fix Common Errors

| Error | Fix |
|-------|-----|
| "Bundle must have at least one function or type" | YAML parsing failed — check for unquoted special chars |
| "Missing required section: '# Overview'" | Add the Overview section |
| "Missing required section: '# Behavior'" | Add Behavior section (for `function` specs) |
| YAML ScannerError | Quote strings containing `{`, `}`, `:`, or `#` |

Re-run validation until it passes.

### Step 6: Write Output

Write the spec file to the output path (default: `src/<name>.spec.md` or as specified).

## Anti-Patterns to Avoid

| Anti-Pattern | Why It's Wrong | What To Do Instead |
|-------------|----------------|-------------------|
| Specifying private methods (`_helper`, `_internal`) | Implementation detail | Only spec public API |
| Naming algorithms ("Kahn's", "BFS", "merge sort") | Prescribes implementation | Describe the behavior/outcome |
| Listing internal fields (`self._cache`) | Implementation detail | Describe public interface only |
| One sub-spec per private method | Over-decomposition | Use a single bundle |
| Copying docstrings verbatim | Often too implementation-focused | Rewrite as requirements |
