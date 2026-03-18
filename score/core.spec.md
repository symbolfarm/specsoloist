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

- `compile_spec(name, model=None, skip_tests=False, arrangement=None)` -> string: Compile one spec to code, using appropriate method based on spec type (typedef, orchestrator, or regular). For `type: reference` specs, returns immediately without generating code.
- `compile_tests(name, model=None, arrangement=None)` -> string: Generate test suite for a spec. Skips typedef specs. For `type: reference` specs, extracts the `# Verification` snippet and wraps it in a test function (skips if no snippet).
- `compile_project(specs=None, model=None, generate_tests=True, incremental=False, parallel=False, max_workers=4, arrangement=None)` -> BuildResult: Compile multiple specs in dependency order, with optional incremental and parallel modes

## Build Order

- `get_build_order(specs=None)` -> list of strings: Preview build order without compiling
- `get_dependency_graph(specs=None)` -> DependencyGraph: Get the dependency graph

## Testing

- `run_tests(name)` -> dict with `success` and `output`: Run tests for one spec
- `run_all_tests()` -> dict with `success` and per-spec `results`: Run tests for all compiled specs

## Self-Healing

- `attempt_fix(name, model=None, arrangement=None)` -> string: Run tests, analyze failures with LLM, apply generated fixes

# Behavior

## Compilation dispatch

`compile_spec` dispatches to the appropriate compiler method based on spec type:
- `reference` specs: return early with a "no code generated" message (documentation only)
- `typedef` specs use `compile_typedef`
- `orchestrator`/`workflow` specs use `compile_orchestrator`
- All others use `compile_code`

Before calling `compile_code`, `compile_spec` collects any `type: reference` deps into a `reference_specs` dict, which is forwarded to `compile_code` and `compile_tests` so the soloist has accurate third-party API context.

## Reference spec test generation

For `type: reference` specs, `compile_tests` extracts the `# Verification` snippet from the spec body via `parser.extract_verification_snippet()`. If a snippet exists, it wraps it in a `test_verify()` function and writes it as the test file. If no snippet, the method returns without creating a test file.

## Parallel builds

`compile_project` with `parallel=True` groups specs into parallelizable levels (using `get_parallel_build_order`) and compiles each level concurrently. Specs within a level have no mutual dependencies.

## Incremental builds

With `incremental=True`, `compile_project` checks each spec's content hash and dependencies against the build manifest. Only specs that changed (or whose dependencies were rebuilt) are recompiled.

## Self-healing loop

`attempt_fix` runs tests, and if they fail, sends the spec (source of truth), current code, current tests, and error output to the LLM. The LLM response contains corrected files which are applied to the build directory.
