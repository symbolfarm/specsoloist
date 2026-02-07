---
name: runner
type: bundle
dependencies:
  - config
tags:
  - test
  - execution
---

# Overview

Test execution and result handling for SpecSoloist. Provides functionality to manage implementation and test files within a build directory and execute tests according to language-specific configurations.

# Types

```yaml:types
test_result:
  description: Result of a test execution.
  properties:
    success: {type: boolean, description: "True if the test passed (exit code 0)"}
    output: {type: string, description: "Combined stdout and stderr from the test execution"}
    return_code: {type: integer, description: "Process exit code, or -1 for execution errors"}
  required: [success, output, return_code]
```

# Functions

```yaml:functions
test_runner_init:
  inputs:
    build_dir: {type: string, description: "Path to the build directory"}
    config: {type: optional, of: {type: ref, ref: config/specsoloist_config}, description: "Framework configuration"}
  outputs:
    runner: {type: object, description: "An initialized TestRunner instance"}
  behavior: "Initialize a TestRunner with an absolute build_dir path and optional config"

get_test_path:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    path: {type: string}
  behavior: "Compute the absolute path to the test file for a module using the language configuration's test_filename_pattern and test_extension"

get_code_path:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    path: {type: string}
  behavior: "Compute the absolute path to the implementation file for a module using the language configuration's extension"

test_exists:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    exists: {type: boolean}
  behavior: "Return True if the test file for the module exists in the build directory"

code_exists:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    exists: {type: boolean}
  behavior: "Return True if the implementation file for the module exists in the build directory"

read_code:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    content: {type: optional, of: {type: string}}
  behavior: "Read and return the content of the implementation file, or null if it does not exist"

read_tests:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    content: {type: optional, of: {type: string}}
  behavior: "Read and return the content of the test file, or null if it does not exist"

write_code:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    content: {type: string}
    language: {type: string, default: python}
  outputs:
    path: {type: string}
  behavior: "Write implementation content to the build directory and return the resulting file path"

write_tests:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    content: {type: string}
    language: {type: string, default: python}
  outputs:
    path: {type: string}
  behavior: "Write test content to the build directory and return the resulting file path"

write_file:
  inputs:
    runner: {type: object}
    filename: {type: string}
    content: {type: string}
  outputs:
    path: {type: string}
  behavior: "Write content to a file in the build directory using only the filename's basename to prevent path traversal"

run_tests:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    result: {type: ref, ref: test_result}
  behavior: |
    Execute tests for a module:
    1. Resolve language configuration (defaulting to Python if not configured).
    2. Verify test file existence; return failure if missing.
    3. Prepare environment: copy current env and prepend cfg.env_vars (formatting {build_dir}) to existing values using path separator.
    4. Prepare command: format cfg.test_command parts with {file} placeholder.
    5. Execute command, capture output, and return TestResult.
    6. Handle FileNotFoundError or other exceptions by returning a failure TestResult.
```
