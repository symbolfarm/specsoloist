---
name: dependency_resolver
type: module
---

# Overview
This module provides functionality for resolving dependencies between specs, building a dependency graph, and computing a build order that respects those dependencies. It includes classes for representing the dependency graph and handling circular and missing dependencies. The module can be used to determine the order in which specs should be compiled, as well as to identify which specs need to be rebuilt when a spec changes.

# Exports
- `CircularDependencyError`: Exception raised when a circular dependency is detected.
- `MissingDependencyError`: Exception raised when a dependency references a non-existent spec.
- `DependencyGraph`: Represents the dependency relationships between specs.
- `DependencyResolver`: Resolves dependencies between specs and computes build order.

---
name: circular_dependency_error
type: type
---

# Overview
Represents an error raised when a circular dependency is detected between specs.

# Schema
```yaml:schema
properties:
  cycle:
    type: array
    items:
      type: string
    description: The cycle of dependencies that caused the error.
required:
  - cycle
```

# Examples
| Valid | Invalid | Why |
|---|---|---|
| `{'cycle': ['a', 'b', 'c']}` |  | Valid cycle |
| `{'cycle': []}` |  | Valid, though unlikely |

---
name: missing_dependency_error
type: type
---

# Overview
Represents an error raised when a spec depends on another spec that does not exist.

# Schema
```yaml:schema
properties:
  spec:
    type: string
    description: The name of the spec that has the missing dependency.
  missing:
    type: string
    description: The name of the missing dependency.
required:
  - spec
  - missing
```

# Examples
| Valid | Invalid | Why |
|---|---|---|
| `{'spec': 'a', 'missing': 'b'}` |  | Valid missing dependency |

---
name: dependency_graph
type: type
---

# Overview
Represents the dependency relationships between specs.

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
    description: All spec names in the graph.
required: []
```

# Examples
| Valid | Invalid | Why |
|---|---|---|
| `{'dependencies': {'a': ['b']}, 'dependents': {'b': ['a']}, 'specs': ['a', 'b']}` |  | Valid dependency graph |
| `{'dependencies': {}, 'dependents': {}, 'specs': []}` |  | Valid empty dependency graph |

---
name: dependency_graph/add_spec
type: function
---

# Overview
Adds a spec and its dependencies to the dependency graph.

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
    description: List of spec names that the spec depends on.  Defaults to empty list.
outputs:
  None:
    type: null
```

# Behavior
- [FR-01]: Adds the spec name to the set of specs in the graph.
- [FR-02]: Adds the dependencies to the `dependencies` dictionary, mapping the spec name to the list of dependencies.
- [FR-03]: Updates the `dependents` dictionary to reflect the reverse dependencies.
- [FR-04]: If `depends_on` is None, it defaults to an empty list.

# Examples
| Input | Output | Notes |
|---|---|---|
| `name: 'a', depends_on: ['b']` |  | Adds spec 'a' with dependency 'b' |
| `name: 'a', depends_on: None` |  | Adds spec 'a' with no dependencies |

---
name: dependency_graph/get_dependencies
type: function
---

# Overview
Gets the direct dependencies of a spec.

# Interface
```yaml:schema
inputs:
  name:
    type: string
    description: The name of the spec to get dependencies for.
outputs:
  dependencies:
    type: array
    items:
      type: string
    description: List of spec names that the spec depends on.  Returns an empty list if the spec is not in the graph.
```

# Behavior
- [FR-01]: Returns the list of dependencies for the given spec name from the `dependencies` dictionary.
- [FR-02]: Returns an empty list if the spec name is not found in the `dependencies` dictionary.

# Examples
| Input | Output | Notes |
|---|---|---|
| `name: 'a'` (where 'a' depends on 'b') | `['b']` | Returns the dependency 'b' |
| `name: 'c'` (where 'c' has no dependencies) | `[]` | Returns an empty list |
| `name: 'd'` (where 'd' is not in the graph) | `[]` | Returns an empty list |

---
name: dependency_graph/get_dependents
type: function
---

# Overview
Gets the specs that directly depend on a given spec.

# Interface
```yaml:schema
inputs:
  name:
    type: string
    description: The name of the spec to get dependents for.
outputs:
  dependents:
    type: array
    items:
      type: string
    description: List of spec names that depend on the spec. Returns an empty list if the spec is not in the graph.
```

# Behavior
- [FR-01]: Returns the list of dependents for the given spec name from the `dependents` dictionary.
- [FR-02]: Returns an empty list if the spec name is not found in the `dependents` dictionary.

# Examples
| Input | Output | Notes |
|---|---|---|
| `name: 'b'` (where 'a' depends on 'b') | `['a']` | Returns the dependent 'a' |
| `name: 'c'` (where no specs depend on 'c') | `[]` | Returns an empty list |
| `name: 'd'` (where 'd' is not in the graph) | `[]` | Returns an empty list |

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
    description: A SpecParser instance used to parse spec files.
required:
  - parser
```

---
name: dependency_resolver/build_graph
type: function
---

# Overview
Builds a dependency graph from specs.

# Interface
```yaml:schema
inputs:
  spec_names:
    type: array
    items:
      type: string
    description: List of spec names to include. If None, includes all specs.
    optional: true
outputs:
  graph:
    type: ref
    ref: dependency_graph
    description: A DependencyGraph representing the relationships.
```

# Behavior
- [FR-01]: If `spec_names` is None, it defaults to a list of all specs found by the parser.
- [FR-02]: Creates a `DependencyGraph` instance.
- [FR-03]: Iterates through the `spec_names`, parses each spec using the parser, extracts dependencies, and adds the spec and its dependencies to the graph.
- [FR-04]: Validates that all dependencies exist within the provided `spec_names` or as existing specs in the parser.
- [FR-05]: Raises a `MissingDependencyError` if a dependency references a non-existent spec.

# Examples
| Input | Output | Notes |
|---|---|---|
| `spec_names: ['a', 'b']` (where 'a' depends on 'b') | `DependencyGraph(dependencies={'a': ['b'], 'b': []}, dependents={'b': ['a'], 'a': []}, specs={'a', 'b'})` | Builds a graph with two specs and one dependency |
| `spec_names: None` | `DependencyGraph(...)` | Builds a graph with all specs found by the parser |

# Error Handling
- Raises `MissingDependencyError` if a spec depends on a non-existent spec.

---
name: dependency_resolver/_extract_dependencies
type: function
---

# Overview
Extracts dependency spec names from a parsed spec.

# Interface
```yaml:schema
inputs:
  spec:
    type: object
    description: A ParsedSpec instance.
outputs:
  dependencies:
    type: array
    items:
      type: string
    description: List of dependency spec names.
```

# Behavior
- [FR-01]: Extracts dependencies from the spec's metadata.dependencies field.
- [FR-02]: Handles both string and dictionary formats for dependencies in the metadata.
- [FR-03]: Extracts dependencies from the spec's schema.steps (for workflow specs).
- [FR-04]: Removes the ".spec.md" extension from dependency names.
- [FR-05]: Ensures that dependencies are not added multiple times.

# Examples
| Input | Output | Notes |
|---|---|---|
| `spec: ParsedSpec(metadata=Metadata(dependencies=['a.spec.md']))` | `['a']` | Extracts dependency from metadata |
| `spec: ParsedSpec(schema=Schema(steps=[Step(spec='b.spec.md')]))` | `['b']` | Extracts dependency from schema steps |
| `spec: ParsedSpec(metadata=Metadata(dependencies=['a']), schema=Schema(steps=[Step(spec='a')]))` | `['a']` | Extracts dependency only once |

---
name: dependency_resolver/resolve_build_order
type: function
---

# Overview
Computes the build order for specs using topological sort.

# Interface
```yaml:schema
inputs:
  spec_names:
    type: array
    items:
      type: string
    description: List of spec names to build. If None, includes all specs.
    optional: true
outputs:
  build_order:
    type: array
    items:
      type: string
    description: List of spec names in build order.
```

# Behavior
- [FR-01]: Builds a dependency graph using `build_graph`.
- [FR-02]: Performs a topological sort on the graph using `_topological_sort`.
- [FR-03]: Returns the list of spec names in build order.

# Examples
| Input | Output | Notes |
|---|---|---|
| `spec_names: ['a', 'b']` (where 'a' depends on 'b') | `['b', 'a']` | Returns the correct build order |
| `spec_names: None` | `[...]` | Returns the build order for all specs |

# Error Handling
- Raises `CircularDependencyError` if a circular dependency is detected.
- Raises `MissingDependencyError` if a dependency references a non-existent spec.

---
name: dependency_resolver/_topological_sort
type: function
---

# Overview
Performs topological sort on a dependency graph using Kahn's algorithm.

# Interface
```yaml:schema
inputs:
  graph:
    type: ref
    ref: dependency_graph
    description: The dependency graph to sort.
outputs:
  build_order:
    type: array
    items:
      type: string
    description: List of spec names in build order.
```

# Behavior
- [FR-01]: Calculates the in-degree (number of dependencies) for each spec in the graph.
- [FR-02]: Initializes a queue with specs that have no dependencies (in-degree of 0).
- [FR-03]: Iteratively removes specs from the queue, adds them to the result, and reduces the in-degree of their dependents.
- [FR-04]: Sorts the queue at each iteration for deterministic output.
- [FR-05]: Checks for cycles by verifying that all specs have been processed.
- [FR-06]: Raises a `CircularDependencyError` if a cycle is detected.

# Examples
| Input | Output | Notes |
|---|---|---|
| `graph: DependencyGraph(dependencies={'a': ['b'], 'b': []}, dependents={'b': ['a'], 'a': []}, specs={'a', 'b'})` | `['b', 'a']` | Returns the correct build order |
| `graph: DependencyGraph(dependencies={'a': [], 'b': []}, dependents={'a': [], 'b': []}, specs={'a', 'b'})` | `['a', 'b']` | Returns a valid build order for independent specs |

# Error Handling
- Raises `CircularDependencyError` if a circular dependency is detected.

---
name: dependency_resolver/_find_cycle
type: function
---

# Overview
Finds a cycle in the remaining nodes of a dependency graph for error reporting.

# Interface
```yaml:schema
inputs:
  graph:
    type: ref
    ref: dependency_graph
    description: The dependency graph to search for a cycle.
  remaining:
    type: array
    items:
      type: string
    description: List of spec names that are suspected to be part of a cycle.
outputs:
  cycle:
    type: array
    items:
      type: string
    description: List of spec names that form a cycle.
```

# Behavior
- [FR-01]: Performs a Depth-First Search (DFS) to detect cycles.
- [FR-02]: Returns the cycle as a list of spec names.
- [FR-03]: If no cycle is found, returns the input `remaining` list.

# Examples
| Input | Output | Notes |
|---|---|---|
| `graph: DependencyGraph(dependencies={'a': ['b'], 'b': ['a']}, dependents={'b': ['a'], 'a': ['b']}, specs={'a', 'b'}), remaining: ['a', 'b']` | `['a', 'b']` | Returns the cycle ['a', 'b'] |
| `graph: DependencyGraph(dependencies={'a': ['b'], 'b': []}, dependents={'b': ['a'], 'a': []}, specs={'a', 'b'}), remaining: ['a']` | `['a']` | Returns ['a'] as no cycle is found |

---
name: dependency_resolver/get_parallel_build_order
type: function
---

# Overview
Computes build order grouped into parallelizable levels.

# Interface
```yaml:schema
inputs:
  spec_names:
    type: array
    items:
      type: string
    description: List of spec names to build. If None, includes all specs.
    optional: true
outputs:
  levels:
    type: array
    items:
      type: array
      items:
        type: string
    description: List of levels, where each level is a list of spec names that can be compiled in parallel.
```

# Behavior
- [FR-01]: Builds a dependency graph using `build_graph`.
- [FR-02]: Performs a topological sort to group specs into levels using `_topological_sort_levels`.
- [FR-03]: Returns the list of levels.

# Examples
| Input | Output | Notes |
|---|---|---|
| `spec_names: ['a', 'b', 'c']` (where 'a' depends on 'b', 'b' depends on 'c') | `[['c'], ['b'], ['a']]` | Returns the correct parallel build order |
| `spec_names: ['a', 'b']` (where 'a' and 'b' are independent) | `[['a', 'b']]` | Returns a single level with both specs |

# Error Handling
- Raises `CircularDependencyError` if a circular dependency is detected.
- Raises `MissingDependencyError` if a dependency references a non-existent spec.

---
name: dependency_resolver/_topological_sort_levels
type: function
---

# Overview
Modified Kahn's algorithm that returns specs grouped by levels for parallel builds.

# Interface
```yaml:schema
inputs:
  graph:
    type: ref
    ref: dependency_graph
    description: The dependency graph to sort.
outputs:
  levels:
    type: array
    items:
      type: array
      items:
        type: string
    description: List of levels, where each level is a list of spec names that can be compiled in parallel.
```

# Behavior
- [FR-01]: Calculates the in-degree (number of dependencies) for each spec in the graph.
- [FR-02]: Initializes the first level with specs that have no dependencies (in-degree of 0).
- [FR-03]: Iteratively processes each level, reduces the in-degree of dependents, and adds dependents with in-degree 0 to the next level.
- [FR-04]: Checks for cycles by verifying that all specs have been processed.
- [FR-05]: Raises a `CircularDependencyError` if a cycle is detected.

# Examples
| Input | Output | Notes |
|---|---|---|
| `graph: DependencyGraph(dependencies={'a': ['b'], 'b': ['c'], 'c': []}, dependents={'b': ['a'], 'c': ['b']}, specs={'a', 'b', 'c'})` | `[['c'], ['b'], ['a']]` | Returns the correct parallel build order |
| `graph: DependencyGraph(dependencies={'a': [], 'b': []}, dependents={'a': [], 'b': []}, specs={'a', 'b'})` | `[['a', 'b']]` | Returns a single level with both specs |

# Error Handling
- Raises `CircularDependencyError` if a circular dependency is detected.

---
name: dependency_resolver/get_affected_specs
type: function
---

# Overview
Gets all specs that need to be rebuilt when a spec changes.

# Interface
```yaml:schema
inputs:
  changed_spec:
    type: string
    description: The spec that changed.
  graph:
    type: ref
    ref: dependency_graph
    description: Pre-built graph, or None to build a new one.
    optional: true
outputs:
  affected_specs:
    type: array
    items:
      type: string
    description: List of spec names that need rebuilding, in build order.
```

# Behavior
- [FR-01]: Builds a dependency graph if one is not provided.
- [FR-02]: Identifies all specs that depend on the changed spec (transitively).
- [FR-03]: Returns the list of affected specs in build order.

# Examples
| Input | Output | Notes |
|---|---|---|
| `changed_spec: 'b', graph: DependencyGraph(dependencies={'a': ['b'], 'b': ['c'], 'c': []}, dependents={'b': ['a'], 'c': ['b']}, specs={'a', 'b', 'c'})` | `['c', 'b', 'a']` | Returns the correct affected specs in build order |
| `changed_spec: 'a'` | `[...]` | Returns the affected specs based on a newly built graph |