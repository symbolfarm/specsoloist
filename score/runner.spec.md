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

Test execution and file management for SpecSoloist builds. Manages implementation and test files within a build directory, and executes tests according to language-specific configurations.

# Types

## TestResult

Result of a test execution. **Fields:** `success` (bool), `output` (string — combined stdout/stderr), `return_code` (int, default 0).

## TestRunner

Manages the build directory and runs tests. Constructed with `build_dir` (string) and optional `config` (SpecSoloistConfig).

**File management methods:**
- `get_code_path(module_name, language="python")` -> string: absolute path to implementation file
- `get_test_path(module_name, language="python")` -> string: absolute path to test file
- `code_exists(module_name, language)` -> bool
- `test_exists(module_name, language)` -> bool
- `read_code(module_name, language)` -> string or None
- `read_tests(module_name, language)` -> string or None
- `write_code(module_name, content, language)` -> string (path written)
- `write_tests(module_name, content, language)` -> string (path written)
- `write_file(filename, content)` -> string: write to build dir using basename only (prevents path traversal)

**Test execution:**
- `run_tests(module_name, language="python")` -> TestResult

# Behavior

## File path resolution

File paths are computed from the language configuration:
- Code path: `{build_dir}/{module_name}{extension}`
- Test path: `{build_dir}/{test_filename_pattern}{test_extension}` where pattern substitutes `{name}` with module_name

Default language is Python if not specified or not in config.

## Test execution

When running tests:
1. Verify the test file exists; return failure TestResult if missing
2. Set up environment variables from language config, formatting `{build_dir}` placeholders and prepending to existing values using path separator
3. Format the test command with `{file}` placeholder
4. If sandboxing is enabled in config:
    - Wrap the test command in a `docker run --rm` call
    - Mount the build directory to `/app/build`
    - Set working directory to `/app`
    - Pass environment variables to the container
    - Use the configured `sandbox_image`
5. Execute the command and capture output
6. Return TestResult with success based on exit code 0
7. Handle execution errors (missing command, other exceptions) by returning failure TestResult
