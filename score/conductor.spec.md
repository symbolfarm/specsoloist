---
name: conductor
type: bundle
status: draft
dependencies:
  - config
  - core
  - resolver
  - parser
  - schema
---

# Overview

SpecConductor is the build manager of Spechestra. It takes a set of specs and orchestrates parallel compilation via SpecSoloistCore. It also provisions the build environment (config files, setup commands) when an arrangement is provided.

# Types

## VerifyResult

Result of project verification.

**Fields:** `success` (bool), `results` (dict mapping spec name to verification details dict).

# Functions

## SpecConductor (class)

The main conductor class. Constructed with a project directory path and an optional `SpecSoloistConfig`. If config is not provided, loads from environment. Creates an internal `SpecSoloistCore` instance for compilation and exposes its `parser` and `resolver` as public attributes.

### verify() -> VerifyResult

Verify all specs for schema compliance and interface compatibility.

**Behavior:**
- Delegates to SpecSoloistCore's project verification.
- Returns a VerifyResult summarizing per-spec verification status.
- An empty project (no specs) is considered valid.

### build(specs=None, parallel=True, incremental=True, max_workers=4, arrangement=None, model=None) -> BuildResult

Build specs in dependency order.

- `specs`: optional list of spec name strings; if null, builds all specs
- `parallel`: bool, compile independent specs concurrently (default true)
- `incremental`: bool, only recompile changed specs (default true)
- `max_workers`: int, maximum parallel workers (default 4)
- `arrangement`: optional Arrangement; if provided, `_provision_environment` is called first
- `model`: optional LLM model override applied to all compilations

**Behavior:**
- If an arrangement is provided, provisions the build environment (writes config files, runs setup commands) before delegating to SpecSoloistCore.
- Delegates actual compilation to SpecSoloistCore's `compile_project`, including test generation.
- After compilation, if the arrangement declares any `static` entries, copies them with `_copy_static_artifacts`.
- Returns a BuildResult (from specsoloist.core) with compiled, skipped, and failed spec lists.

### get_build_order(specs=None) -> list of strings

Return specs in build order without actually building.

- `specs`: optional list of spec names; if null, includes all specs

**Behavior:**
- Returns an empty list for an empty project.
- Dependencies appear before dependents in the result.

### get_dependency_graph(specs=None) -> DependencyGraph

Return the dependency graph for the given specs (or all specs).

**Behavior:**
- Delegates to SpecSoloistCore's dependency graph construction.
- Returns a DependencyGraph object (from specsoloist.resolver).

# Behavior

## Environment provisioning

When an arrangement is provided to `build()`, the conductor writes any declared `config_files` to the build directory and runs `setup_commands` before compilation begins. This ensures the build environment is ready (e.g., package.json exists before npm install runs).

## Static artifact copying

After compilation, the conductor copies each entry in `arrangement.static` verbatim from `source` to `dest`. Both paths resolve relative to the conductor's `project_dir`. Directories are copied with `dirs_exist_ok=True`; files create parent directories as needed. If the source does not exist, a warning is printed and the entry is skipped. If `overwrite=False` and the destination already exists, the copy is skipped silently.

## Separation of concerns

SpecConductor delegates all compilation to SpecSoloistCore. It does not contain compilation logic itself. Its role is orchestration: environment setup, dependency ordering, and parallelism.

# Examples

| Scenario | Input | Expected |
|----------|-------|----------|
| Initialize conductor | `SpecConductor("/path/to/project")` | `project_dir` is set to the absolute path |
| Verify empty project | No specs in project | `result.success == True` |
| Build order empty project | No specs | Returns `[]` |
| VerifyResult defaults | `VerifyResult(success=True, results={})` | `results` is empty dict |
