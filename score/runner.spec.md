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

Test execution and result handling for SpecSoloist. Provides functionality to run tests, manage code and test files in a build directory, and return structured results.

# Types

```yaml:types
test_result:
  description: Result of a test run
  properties:
    success: {type: boolean, description: Whether the test passed}
    output: {type: string, description: Combined stdout and stderr from test run}
    return_code: {type: integer, description: Process exit code (0 for success, -1 for errors)}
  required: [success, output]
```

# Functions

```yaml:functions
test_runner_init:
  inputs:
    build_dir: {type: string, description: Directory where code and tests are built}
    config: {type: optional, of: {type: ref, ref: config/specsoloist_config}, description: SpecSoloist configuration}
  outputs:
    runner: {type: object, description: Initialized TestRunner instance}
  behavior: "Initialize runner with absolute build_dir path and optional config"

get_lang_config:
  inputs:
    runner: {type: object}
    language: {type: optional, of: {type: string}}
  outputs:
    config: {type: ref, ref: config/language_config}
  behavior: "Return language config from runner config, defaulting to python if not specified"

get_test_path:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    path: {type: string}
  behavior: "Return path to test file using language config's test_filename_pattern and test_extension"

get_code_path:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    path: {type: string}
  behavior: "Return path to implementation file using language config's extension"

test_exists:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    exists: {type: boolean}
  behavior: "Check if test file exists at the computed path"

code_exists:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    exists: {type: boolean}
  behavior: "Check if implementation file exists at the computed path"

read_code:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    content: {type: optional, of: {type: string}}
  behavior: "Read and return implementation file content, or None if file does not exist"

read_tests:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    content: {type: optional, of: {type: string}}
  behavior: "Read and return test file content, or None if file does not exist"

write_code:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    content: {type: string}
    language: {type: string, default: python}
  outputs:
    path: {type: string}
  behavior: "Write implementation code to build directory and return the file path"

write_tests:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    content: {type: string}
    language: {type: string, default: python}
  outputs:
    path: {type: string}
  behavior: "Write test code to build directory and return the file path"

write_file:
  inputs:
    runner: {type: object}
    filename: {type: string}
    content: {type: string}
  outputs:
    path: {type: string}
  behavior: "Write file to build directory using basename only (prevents path traversal)"
  contract:
    pre: filename is not empty
    post: file exists at build_dir/basename(filename)

run_tests:
  inputs:
    runner: {type: object}
    module_name: {type: string}
    language: {type: string, default: python}
  outputs:
    result: {type: ref, ref: runner/test_result}
  behavior: "Execute test command for module using language config, return TestResult with success, output, and return_code"
  contract:
    pre: build_dir exists
  examples:
    - input: {module_name: factorial, language: python}
      output: {success: true, output: "...", return_code: 0}
      notes: Successful test run
    - input: {module_name: missing_module, language: python}
      output: {success: false, output: "Test file not found...", return_code: -1}
      notes: Test file does not exist
```
