# User Project Example

This example demonstrates Specular's multi-spec dependency system.

## Structure

```
src/
├── types.spec.md        # Shared type definitions (typedef)
├── validation.spec.md   # Validation utilities (depends on types)
└── user_service.spec.md # User service (depends on types + validation)
```

## Dependency Graph

```
types (typedef)
    ↓
validation ─────┐
    ↓           │
user_service ←──┘
```

## Building

```python
from specsoloist import SpecularCore

core = SpecularCore("examples/user_project")

# Preview build order
order = core.get_build_order()
print(order)  # ['types', 'validation', 'user_service']

# Build all specs in dependency order
result = core.compile_project()
print(f"Compiled: {result.specs_compiled}")
print(f"Failed: {result.specs_failed}")
```

## Key Features Demonstrated

1. **Typedef specs** - `types.spec.md` uses `type: typedef` and generates only dataclasses
2. **Dependency declarations** - Specs declare dependencies in YAML frontmatter
3. **Automatic build order** - Specular computes topological sort
4. **Import context** - Dependencies are passed to the LLM for correct imports
