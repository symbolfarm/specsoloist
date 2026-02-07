---
name: resolver
type: module
tags:
  - core
  - dependencies
---

# Overview

Dependency resolution for multi-spec builds. Given a set of specs that declare dependencies on each other, this module can:

- Build a dependency graph
- Compute a valid build order (dependencies before dependents)
- Group specs into parallelizable levels
- Determine which specs are affected when one changes
- Detect and report circular dependencies and missing dependencies

# Exports

- `CircularDependencyError`: Exception raised when specs form a dependency cycle.
- `MissingDependencyError`: Exception raised when a spec depends on one that doesn't exist.
- `DependencyGraph`: A dependency graph with methods to query relationships.
- `DependencyResolver`: The main resolver that builds graphs and computes build orders.

# Error Types

## CircularDependencyError

An exception with a `cycle` attribute (list of spec names forming the cycle). The error message should describe the cycle clearly.

### Examples

| Scenario | cycle attribute | Message includes |
|----------|----------------|-----------------|
| A depends on B, B depends on A | `["a", "b"]` or similar | "a", "b", and "circular" |

## MissingDependencyError

An exception with `spec` and `missing` attributes. `spec` is the name of the spec that declared the dependency; `missing` is the name of the dependency that doesn't exist.

### Examples

| Scenario | spec | missing |
|----------|------|---------|
| "auth" depends on "users" but "users" doesn't exist | `"auth"` | `"users"` |

# DependencyGraph

A data structure representing dependency relationships between specs.

## Interface

```yaml:schema
inputs: {}
outputs: {}
```

## Methods

### add_spec(name, depends_on)

Add a spec and its dependencies to the graph.

- `name`: string, the spec name
- `depends_on`: optional list of strings, names of specs this one depends on

**Behavior:**
- Records that `name` exists in the graph
- Records its dependencies
- Updates reverse mappings so dependents can be looked up

### get_dependencies(name) -> list of strings

Returns the direct dependencies of the named spec. Returns empty list if the name is not in the graph.

### get_dependents(name) -> list of strings

Returns the specs that directly depend on the named spec. Returns empty list if the name is not in the graph.

# DependencyResolver

The main resolver. Requires a `SpecParser` instance (from `specsoloist.parser`) to load and inspect specs.

## Constructor

Takes a `parser` argument (a `SpecParser` instance).

## Methods

### build_graph(spec_names=None) -> DependencyGraph

Build a dependency graph from specs.

**Behavior:**
- If `spec_names` is None, discover all available specs from the parser.
- For each spec, parse it and extract its declared dependencies.
- Dependencies come from two sources in a parsed spec:
  - `metadata.dependencies`: a list where each entry is either a string (spec name) or a dict with a `"from"` key containing the spec filename.
  - `schema.steps`: if present (workflow specs), each step has a `spec` attribute naming a dependency.
- Strip `.spec.md` extensions from dependency names.
- Validate that every referenced dependency actually exists (in the input list or in the parser's storage).

**Errors:**
- Raises `MissingDependencyError` if a dependency doesn't exist.

### resolve_build_order(spec_names=None) -> list of strings

Compute a linear build order for the given specs (or all specs if None).

**Behavior:**
- Dependencies appear before their dependents in the result.
- When multiple specs have no dependency ordering between them, sort alphabetically for determinism.
- Detects cycles.

**Errors:**
- Raises `CircularDependencyError` if a cycle exists.
- Raises `MissingDependencyError` if a dependency doesn't exist.

### get_parallel_build_order(spec_names=None) -> list of lists of strings

Compute build order grouped into parallelizable levels.

**Behavior:**
- Level 0 contains specs with no dependencies.
- Level N contains specs whose dependencies all appear in levels 0 through N-1.
- Within each level, specs are sorted alphabetically for determinism.
- All specs in the same level can be built concurrently.

**Errors:**
- Raises `CircularDependencyError` if a cycle exists.
- Raises `MissingDependencyError` if a dependency doesn't exist.

### get_affected_specs(changed_spec, graph=None) -> list of strings

Determine which specs need rebuilding when a specific spec changes.

**Behavior:**
- Includes the changed spec itself.
- Includes all transitive dependents (specs that depend on it, and specs that depend on those, etc.).
- Returns results in valid build order.
- If `graph` is not provided, builds one for all specs.

### Examples

Given specs: types (no deps), auth (depends on types), users (depends on types), api (depends on auth and users), unrelated (no deps):

| Method | Input | Expected Output |
|--------|-------|----------------|
| `resolve_build_order()` | all specs | types before auth, types before users, auth and users before api |
| `get_parallel_build_order()` | all specs | Level 0: [types, unrelated], Level 1: [auth, users], Level 2: [api] |
| `get_affected_specs("types")` | "types" changed | ["types", "auth", "users", "api"] (not "unrelated") |
| `get_affected_specs("api")` | "api" changed | ["api"] only |

Given specs: a -> b -> c -> a (circular):

| Method | Input | Expected |
|--------|-------|----------|
| `resolve_build_order()` | all specs | Raises `CircularDependencyError` with non-empty cycle |
