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
---

# Overview
SpecularCore: The main orchestrator for spec-driven development.
Provides the high-level API for coordinating spec parsing, code compilation, 
test generation, and the self-healing fix loop.

# Types
```yaml:types
build_result:
  properties:
    success: {type: boolean}
    specs_compiled: {type: array, items: {type: string}}
    specs_skipped: {type: array, items: {type: string}}
    specs_failed: {type: array, items: {type: string}}
    build_order: {type: array, items: {type: string}}
    errors: {type: object, description: "Map of spec name to error message"}
  required: [success, specs_compiled, specs_skipped, specs_failed, build_order, errors]

core_state:
  properties:
    root_dir: {type: string}
    config: {type: ref, ref: config/specsoloist_config}
    src_dir: {type: string}
    build_dir: {type: string}
    api_key: {type: optional, of: {type: string}}
    parser: {type: object, description: "SpecParser instance"}
    runner: {type: object, description: "TestRunner instance"}
    resolver: {type: object, description: "DependencyResolver instance"}
    compiler: {type: optional, of: {type: object}, description: "SpecCompiler instance"}
    provider: {type: optional, of: {type: object}, description: "LLMProvider instance"}
    manifest: {type: optional, of: {type: object}, description: "BuildManifest instance"}
  required: [root_dir, config, src_dir, build_dir, parser, runner, resolver]
```

# Functions
```yaml:functions
init_core:
  inputs:
    root_dir: {type: string, default: "."}
    api_key: {type: optional, of: {type: string}}
    config: {type: optional, of: {type: ref, ref: config/specsoloist_config}}
  outputs:
    core: {type: ref, ref: core_state}
  behavior: "Initialize the SpecSoloistCore orchestrator. If config is not provided, load it from environment. Ensures necessary directories exist and initializes parser, runner, and resolver."

list_specs:
  inputs: {core: {type: ref, ref: core_state}}
  outputs: {specs: {type: array, items: {type: string}}}
  behavior: List all available specification files in the project.

read_spec:
  inputs:
    core: {type: ref, ref: core_state}
    name: {type: string}
  outputs: {content: {type: string}}
  behavior: Read the content of a specification file.

create_spec:
  inputs:
    core: {type: ref, ref: core_state}
    name: {type: string}
    description: {type: string}
    type: {type: string, default: "function"}
  outputs: {message: {type: string}}
  behavior: Create a new specification file from the template and return a success message with the file path.

validate_spec:
  inputs:
    core: {type: ref, ref: core_state}
    name: {type: string}
  outputs:
    result:
      type: object
      properties:
        valid: {type: boolean}
        errors: {type: array, items: {type: string}}
  behavior: Validate a spec for basic structure and SRS compliance.

verify_project:
  inputs: {core: {type: ref, ref: core_state}}
  outputs:
    result:
      type: object
      properties:
        success: {type: boolean}
        results: {type: object}
  behavior: "Verifies all specs in the project for structural correctness, dependency integrity, and orchestrator data flow. Checks for circular dependencies, missing schemas, and validates that step inputs in orchestrators match available outputs and types."

compile_spec:
  inputs:
    core: {type: ref, ref: core_state}
    name: {type: string}
    model: {type: optional, of: {type: string}}
    skip_tests: {type: boolean, default: false}
  outputs: {message: {type: string}}
  behavior: "Compiles a spec to implementation code using the compiler, handling typedef, orchestrator, and regular specs appropriately, then writes the result to the build directory."

compile_tests:
  inputs:
    core: {type: ref, ref: core_state}
    name: {type: string}
    model: {type: optional, of: {type: string}}
  outputs: {message: {type: string}}
  behavior: "Generates a test suite for a spec and writes it to the build directory. Skips generation if the spec type is typedef."

compile_project:
  inputs:
    core: {type: ref, ref: core_state}
    specs: {type: optional, of: {type: array, items: {type: string}}}
    model: {type: optional, of: {type: string}}
    generate_tests: {type: boolean, default: true}
    incremental: {type: boolean, default: false}
    parallel: {type: boolean, default: false}
    max_workers: {type: integer, default: 4}
  outputs: {result: {type: ref, ref: build_result}}
  behavior: "Compiles multiple specs in dependency order. Supports sequential or parallel builds, incremental compilation based on content hashes, and optional test generation."

get_build_order:
  inputs:
    core: {type: ref, ref: core_state}
    specs: {type: optional, of: {type: array, items: {type: string}}}
  outputs: {order: {type: array, items: {type: string}}}
  behavior: Resolve and return the build order for specs based on their dependencies.

get_dependency_graph:
  inputs:
    core: {type: ref, ref: core_state}
    specs: {type: optional, of: {type: array, items: {type: string}}}
  outputs: {graph: {type: object}}
  behavior: Build and return the dependency graph for the project specs.

run_tests:
  inputs:
    core: {type: ref, ref: core_state}
    name: {type: string}
  outputs:
    result:
      type: object
      properties:
        success: {type: boolean}
        output: {type: string}
  behavior: Run the tests for a specific component and return the outcome.

run_all_tests:
  inputs: {core: {type: ref, ref: core_state}}
  outputs:
    result:
      type: object
      properties:
        success: {type: boolean}
        results: {type: object}
  behavior: Run tests for all compiled specs in the project, skipping those of type typedef or those without tests.

attempt_fix:
  inputs:
    core: {type: ref, ref: core_state}
    name: {type: string}
    model: {type: optional, of: {type: string}}
  outputs: {message: {type: string}}
  behavior: "Attempts to fix a failing component by running tests, analyzing the output with an LLM, and applying generated fixes to the code or tests."