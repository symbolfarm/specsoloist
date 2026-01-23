---
name: specular_core
type: class
language_target: python
status: draft
---

# 1. Overview
The `SpecularCore` class is the logic engine of the Specular framework. It manages the lifecycle of "Spec-as-Source" development, including creating specifications, compiling them to code, generating tests, executing tests, and performing agentic self-healing.

# 2. Interface Specification

## 2.1 Initialization
### `__init__(root_dir: str = ".", api_key: Optional[str] = None)`
*   Initializes the core with a project root and optional API key.
*   Sets up `src/` and `build/` directories if they don't exist.

## 2.2 Core Methods

### `create_spec(name: str, description: str, type: str = "function") -> str`
*   Creates a new `*.spec.md` file from the internal template.
*   **Returns**: Success message with path.

### `compile_spec(name: str, model: str = "gemini-2.0-flash") -> str`
*   Reads a spec file, strips frontmatter, and prompts the LLM to generate the implementation.
*   **Returns**: Success message with output path.

### `compile_tests(name: str, model: str = "gemini-2.0-flash") -> str`
*   Prompts the LLM (as a QA Engineer) to generate a `test_*.py` suite based on the spec's scenarios.
*   **Returns**: Success message with output path.

### `run_tests(name: str) -> Dict[str, Any]`
*   Executes the generated test suite using `pytest`.
*   **Returns**: Dictionary with `success` (bool) and `output` (str).

### `attempt_fix(name: str, model: str = "gemini-2.0-flash") -> str`
*   The "Self-Healing" loop. Runs tests; if they fail, sends logs + spec + code to LLM to generate a patch.
*   Parses LLM output for `### FILE: ...` blocks and applies changes.
*   **Returns**: Status message describing applied fixes.

# 3. Functional Requirements (Behavior)

## File Management
*   **FR-01**: The system shall enforce a directory structure where specs live in `src/` and generated code lives in `build/`.
*   **FR-02**: The system shall bundle default templates (`spec_template.md`, `global_context.md`) and load them via `importlib.resources` or local fallback.

## Compilation logic
*   **FR-03**: When compiling, the system shall strip YAML frontmatter from the spec before sending it to the LLM to prevent confusion.
*   **FR-04**: The system shall handle API errors (HTTP 400/404/500) by raising descriptive exceptions, not failing silently.

## Test Execution
*   **FR-05**: `run_tests` shall inject the `build/` directory into `PYTHONPATH` so generated tests can import generated modules.
*   **FR-06**: `run_tests` shall capture both `stdout` and `stderr` from the test runner.

## Self-Healing
*   **FR-07**: `attempt_fix` shall strip Markdown code fences (```python) from the LLM's response before writing files to disk to prevent SyntaxErrors.
*   **FR-08**: `attempt_fix` shall only overwrite files explicitly named in `### FILE:` blocks.

# 4. Non-Functional Requirements (Constraints)
*   **NFR-Dependencies**: The core must depend ONLY on the Python Standard Library (urllib, json, re, subprocess) for runtime execution. No `requests` or `openai` packages.
*   **NFR-Security**: The system must never write files outside of the configured `root_dir`.
*   **NFR-Robustness**: All API calls must include error handling for network issues.

# 5. Design Contract
*   **Invariant**: `api_key` must be present (either passed or in env `GEMINI_API_KEY`) for any LLM operation.
*   **Pre-condition**: `name` arguments for specs can be provided with or without the `.spec.md` extension (system normalizes).
