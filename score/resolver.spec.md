---
name: resolver
type: module
status: draft
---

# Overview
This module provides functionality for resolving dependencies between specs, building a dependency graph, and computing a build order that respects those dependencies. It handles the extraction of dependencies from spec metadata and workflow steps, supports parallel build order computation, and identifies transitive dependents for incremental builds.

# Exports
- `CircularDependencyError`: Raised when a circular dependency is detected.
- `MissingDependencyError`: Raised when a dependency references a non-existent spec.
- `DependencyGraph`: Manages the graph of dependencies and dependents.
- `DependencyResolver`: Main orchestrator for dependency resolution and build order computation.

---
name: circular_dependency_error
type: type
---

# Overview
Exception raised when a circular dependency is detected between specs.

# Schema
```yaml:schema
properties:
  cycle:
    type: array
    items:
      type: string
    description: The cycle of spec names detected (e.g., ['A', 'B', 'A']).
required:
  - cycle
```

---
name: missing_dependency_error
type: type
---

# Overview
Exception raised when a spec depends on another spec that does not exist.

# Schema
```yaml:schema
properties:
  spec:
    type: string
    description: The name of the spec that has the missing dependency.
  missing:
    type: string
    description: The name of the missing dependency spec.
required:
  - spec
  - missing
```

---
name: dependency_graph
type: type
---

# Overview
Represents the dependency relationships between specs, tracking both forward dependencies and reverse dependents.

# Schema
```yaml:schema
properties:
  dependencies:
    type: object
    additionalProperties:
      type: array
      items:
        type: string
    description: Map of spec name to list of specs it depends on.
  dependents:
    type: object
    additionalProperties:
      type: array
      items:
        type: string
    description: Map of spec name to list of specs that depend on it.
  specs:
    type: array
    items:
      type: string
    description: All spec names present in the graph.
```

---
name: dependency_graph/add_spec
type: function
---

# Overview
Adds a spec and its dependencies to the graph.

# Interface
```yaml:schema
inputs:
  name:
    type: string
    description: The name of the spec to add.
  depends_on:
    type: array
    items:
      type: string
    optional: true
    description: List of spec names that this spec depends on.
outputs:
  None:
    type: null
```

# Behavior
- [FR-01]: Add `name` to the set of specs.
- [FR-02]: Store the list of `depends_on` (defaulting to empty) for the given `name`.
- [FR-03]: For each dependency in `depends_on`, add `name` to its list of dependents.
- [FR-04]: Ensure all mentioned specs are added to the general `specs` list.

---
name: dependency_graph/get_dependencies
type: function
---

# Overview
Returns the list of direct dependencies for a spec.

# Interface
```yaml:schema
inputs:
  name:
    type: string
outputs:
  result:
    type: array
    items:
      type: string
```

# Behavior
- [FR-01]: Return the list of dependencies for `name`, or an empty list if not found.

---
name: dependency_graph/get_dependents
type: function
---

# Overview
Returns the list of specs that directly depend on the given spec.

# Interface
```yaml:schema
inputs:
  name:
    type: string
outputs:
  result:
    type: array
    items:
      type: string
```

# Behavior
- [FR-01]: Return the list of dependents for `name`, or an empty list if not found.

---
name: dependency_resolver
type: type
---

# Overview
Resolves dependencies between specs and computes build order.

# Schema
```yaml:schema
properties:
  parser:
    type: object
    description: An instance of SpecParser used to load and parse specs.
required:
  - parser
```

---
name: dependency_resolver/build_graph
type: function
---

# Overview
Builds a DependencyGraph from a list of specs or all available specs.

# Interface
```yaml:schema
inputs:
  spec_names:
    type: array
    items:
      type: string
    optional: true
    description: List of spec names to include. Defaults to all available specs.
outputs:
  graph:
    type: ref
    ref: dependency_graph
```

# Behavior
- [FR-01]: If `spec_names` is not provided, list all specs from the parser.
- [FR-02]: For each spec, parse it and extract dependencies.
- [FR-03]: Add each spec and its dependencies to a new `DependencyGraph`.
- [FR-04]: Validate that every dependency mentioned exists either in the input list or in the parser's storage.
- [FR-05]: Raise `MissingDependencyError` if a dependency is missing.

---
name: dependency_resolver/_extract_dependencies
type: function
---

# Overview
Extracts dependency names from a parsed spec, looking in both metadata and workflow steps.

# Interface
```yaml:schema
inputs:
  spec:
    type: object
    description: The ParsedSpec object to examine.
outputs:
  deps:
    type: array
    items:
      type: string
```

# Behavior
- [FR-01]: Extract dependencies from `metadata.dependencies`.
- [FR-02]: Support both string names and dictionary descriptors (using the `from` field) in metadata.
- [FR-03]: If the spec has a `schema.steps` (workflow), extract the `spec` name from each step.
- [FR-04]: Strip `.spec.md` extensions from all names and ensure the result list is unique.

---
name: dependency_resolver/resolve_build_order
type: function
---

# Overview
Computes a linear build order for the given specs.

# Interface
```yaml:schema
inputs:
  spec_names:
    type: array
    items:
      type: string
    optional: true
outputs:
  order:
    type: array
    items:
      type: string
```

# Behavior
- [FR-01]: Build the dependency graph.
- [FR-02]: Perform a topological sort on the graph.
- [FR-03]: Raise `CircularDependencyError` if a cycle is detected.

---
name: dependency_resolver/_topological_sort
type: function
---

# Overview
Implements Kahn's algorithm for topological sorting.

# Interface
```yaml:schema
inputs:
  graph:
    type: ref
    ref: dependency_graph
outputs:
  result:
    type: array
    items:
      type: string
```

# Behavior
- [FR-01]: Calculate in-degrees for all specs.
- [FR-02]: Initialize a queue with specs having 0 in-degree.
- [FR-03]: While the queue is not empty: sort it (for determinism), pop the first spec, add to result, and decrement in-degrees of its dependents.
- [FR-04]: If result length != total specs, find and raise circular dependency.

---
name: dependency_resolver/get_parallel_build_order
type: function
---

# Overview
Computes a build order grouped into parallelizable levels.

# Interface
```yaml:schema
inputs:
  spec_names:
    type: array
    items:
      type: string
    optional: true
outputs:
  levels:
    type: array
    items:
      type: array
      items:
        type: string
```

# Behavior
- [FR-01]: Build the dependency graph.
- [FR-02]: Group specs into levels where Level N only depends on specs in Levels 0 to N-1.
- [FR-03]: Raise `CircularDependencyError` if a cycle is detected.

---
name: dependency_resolver/get_affected_specs
type: function
---

# Overview
Determines which specs need rebuilding when a specific spec changes.

# Interface
```yaml:schema
inputs:
  changed_spec:
    type: string
    description: Name of the spec that was modified.
  graph:
    type: ref
    ref: dependency_graph
    optional: true
outputs:
  affected:
    type: array
    items:
      type: string
    description: List of affected specs in build order.
```

# Behavior
- [FR-01]: If no graph is provided, build one for all specs.
- [FR-02]: Use BFS/DFS to find all transitive dependents of `changed_spec`.
- [FR-03]: Compute the full topological build order and filter it to include only the affected specs.

# Examples
| Input | Output | Notes |
|-------|--------|-------|
| `changed_spec: "types", graph: {deps: {"auth": ["types"], "app": ["auth"]}, ...}` | `["types", "auth", "app"]` | Transitive dependents in order |
| `changed_spec: "util", graph: {deps: {"app": ["auth"]}, "util": []}` | `["util"]` | No dependents affected |
