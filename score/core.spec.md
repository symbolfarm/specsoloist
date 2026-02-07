---
name: core
type: bundle
dependencies:
  - config
  - parser
  - compiler
  - runner
  - resolver
  - manifest
tags:
  - core
  - orchestration
---

# Overview

The main orchestrator for SpecSoloist. Coordinates spec parsing, code compilation, test generation, and the self-healing fix loop. Provides the high-level API that the CLI and other tools consume.

# Types

## BuildResult

Result of a multi-spec build operation.

**Fields:** `success` (bool), `specs_compiled` (list of strings), `specs_skipped` (list of strings), `specs_failed` (list of strings), `build_order` (list of strings), `errors` (dict mapping spec name to error message).

## SpecSoloistCore

Main orchestrator class. Constructed with `root_dir` (string, default "."), optional `api_key`, and optional `config` (SpecSoloistConfig). If config is not provided, loads from environment.

On initialization:
- Sets up config, ensures directories exist
- Creates parser, runner, and resolver instances
- Lazily creates compiler, LLM provider, and build manifest on first use

Exposes `project_dir`, `config`, `parser`, `runner`, `resolver` as public attributes.

# Public API

## Spec Management

- `list_specs()` -> list of strings: List all available spec files
- `read_spec(name)` -> string: Read spec file content
- `create_spec(name, description, type="function")` -> string: Create from template, return success message
- `validate_spec(name)` -> dict with `valid` (bool) and `errors` (list): Validate spec structure

## Verification

- `verify_project()` -> dict with `success` and `results`: Verify all specs for structure, dependency integrity, and orchestrator data flow

## Compilation

- `compile_spec(name, model=None, skip_tests=False)` -> string: Compile one spec to code, using appropriate method based on spec type (typedef, orchestrator, or regular)
- `compile_tests(name, model=None)` -> string: Generate test suite for a spec (skips typedef specs)
- `compile_project(specs=None, model=None, generate_tests=True, incremental=False, parallel=False, max_workers=4)` -> BuildResult: Compile multiple specs in dependency order, with optional incremental and parallel modes

## Build Order

- `get_build_order(specs=None)` -> list of strings: Preview build order without compiling
- `get_dependency_graph(specs=None)` -> DependencyGraph: Get the dependency graph

## Testing

- `run_tests(name)` -> dict with `success` and `output`: Run tests for one spec
- `run_all_tests()` -> dict with `success` and per-spec `results`: Run tests for all compiled specs

## Self-Healing

- `attempt_fix(name, model=None)` -> string: Run tests, analyze failures with LLM, apply generated fixes

# Behavior

## Compilation dispatch

`compile_spec` dispatches to the appropriate compiler method based on spec type:
- `typedef` specs use `compile_typedef`
- `orchestrator`/`workflow` specs use `compile_orchestrator`
- All others use `compile_code`

## Parallel builds

`compile_project` with `parallel=True` groups specs into parallelizable levels (using `get_parallel_build_order`) and compiles each level concurrently. Specs within a level have no mutual dependencies.

## Incremental builds

With `incremental=True`, `compile_project` checks each spec's content hash and dependencies against the build manifest. Only specs that changed (or whose dependencies were rebuilt) are recompiled.

## Self-healing loop

`attempt_fix` runs tests, and if they fail, sends the spec (source of truth), current code, current tests, and error output to the LLM. The LLM response contains corrected files which are applied to the build directory.
