---
name: specular_core
type: module
language_target: python
status: stable
---

# 1. Overview
The `specular` module is the core of the Specular framework—a "Spec-as-Source" AI coding system that treats rigorous SRS-style Markdown specifications as the single source of truth and uses LLMs to compile them into executable code.

The module is organized into specialized components:
- **SpecularCore**: The main orchestrator that coordinates all operations
- **SpecParser**: Handles spec file discovery, parsing, and validation
- **SpecCompiler**: Manages prompt construction and LLM code generation
- **TestRunner**: Executes tests and manages build artifacts
- **SpecularConfig**: Configuration management with environment-based loading
- **LLMProvider**: Protocol for pluggable LLM backends (Gemini, Anthropic)

# 2. Interface Specification

## 2.1 SpecularCore (Orchestrator)

### `__init__(root_dir: str = ".", api_key: Optional[str] = None, config: Optional[SpecularConfig] = None)`
*   Initializes the framework with a project root directory.
*   If `config` is provided, uses it directly; otherwise loads from environment.
*   Sets up `src/` and `build/` directories if they don't exist.
*   Lazily initializes the LLM provider and compiler on first use.

### `list_specs() -> List[str]`
*   Returns a list of all `*.spec.md` files in the source directory.

### `read_spec(name: str) -> str`
*   Returns the raw content of a specification file.

### `create_spec(name: str, description: str, type: str = "function") -> str`
*   Creates a new `*.spec.md` file from the internal template.
*   **Returns**: Success message with path.

### `validate_spec(name: str) -> Dict[str, Any]`
*   Validates spec structure for SRS compliance.
*   **Returns**: Dict with `valid` (bool) and `errors` (list).

### `compile_spec(name: str, model: Optional[str] = None) -> str`
*   Compiles a spec to implementation code via the LLM.
*   **Returns**: Success message with output path.

### `compile_tests(name: str, model: Optional[str] = None) -> str`
*   Generates a pytest suite based on the spec's test scenarios.
*   **Returns**: Success message with output path.

### `run_tests(name: str) -> Dict[str, Any]`
*   Executes the generated test suite using `pytest`.
*   **Returns**: Dict with `success` (bool) and `output` (str).

### `attempt_fix(name: str, model: Optional[str] = None) -> str`
*   The "Self-Healing" loop. Analyzes test failures and patches code/tests.
*   **Returns**: Status message describing applied fixes.

## 2.2 SpecParser

### `__init__(src_dir: str)`
*   Initializes with the source directory path.

### `list_specs() -> List[str]`
*   Walks the source directory and returns all `*.spec.md` filenames.

### `read_spec(name: str) -> str`
*   Reads and returns raw spec content.

### `parse_spec(name: str) -> ParsedSpec`
*   Parses a spec into structured data: `ParsedSpec(metadata, content, body, path)`.

### `validate_spec(name: str) -> Dict[str, Any]`
*   Checks for required sections (Overview, Interface, FRs, NFRs, Design Contract).

### `get_module_name(name: str) -> str`
*   Extracts the module name from a spec filename (strips `.spec.md`).

## 2.3 SpecCompiler

### `__init__(provider: LLMProvider, global_context: str = "")`
*   Initializes with an LLM provider and optional global context.

### `compile_code(spec: ParsedSpec) -> str`
*   Generates implementation code from a parsed spec.

### `compile_tests(spec: ParsedSpec) -> str`
*   Generates a pytest test suite from a parsed spec.

### `generate_fix(spec: ParsedSpec, code_content: str, test_content: str, error_log: str) -> str`
*   Generates a fix response for failing tests.

### `parse_fix_response(response: str) -> Dict[str, str]`
*   Parses `### FILE: ...` blocks from the LLM response.

## 2.4 TestRunner

### `__init__(build_dir: str)`
*   Initializes with the build directory path.

### `run_tests(module_name: str) -> TestResult`
*   Executes pytest and returns `TestResult(success, output, return_code)`.

### `write_code(module_name: str, content: str) -> str`
*   Writes implementation code to build directory.

### `write_tests(module_name: str, content: str) -> str`
*   Writes test code to build directory.

### `write_file(filename: str, content: str) -> str`
*   Writes a file securely (basename only, no path traversal).

## 2.5 SpecularConfig

### `__init__(llm_provider: str = "gemini", llm_model: Optional[str] = None, api_key: Optional[str] = None, root_dir: str = ".", ...)`
*   Configuration dataclass with all framework settings.

### `from_env(root_dir: str = ".") -> SpecularConfig`
*   Class method to load config from environment variables:
    - `SPECULAR_LLM_PROVIDER`: "gemini" or "anthropic"
    - `SPECULAR_LLM_MODEL`: Model identifier
    - `GEMINI_API_KEY` / `ANTHROPIC_API_KEY`: API keys

### `create_provider() -> LLMProvider`
*   Factory method to instantiate the configured LLM provider.

### `ensure_directories()`
*   Creates `src/` and `build/` directories if they don't exist.

## 2.6 LLMProvider Protocol

### `generate(prompt: str, temperature: float = 0.1) -> str`
*   Sends a prompt to the LLM and returns the generated text.
*   Implementations: `GeminiProvider`, `AnthropicProvider`

# 3. Functional Requirements (Behavior)

## Module Organization
*   **FR-01**: The system shall be organized into specialized modules (parser, compiler, runner, config, providers) with SpecularCore as the thin orchestrator.
*   **FR-02**: Each module shall have a single responsibility and be independently testable.

## File Management
*   **FR-03**: The system shall enforce a directory structure where specs live in `src/` and generated code lives in `build/`.
*   **FR-04**: The system shall bundle default templates (`spec_template.md`, `global_context.md`) and load them via `importlib.resources` or local fallback.

## Compilation
*   **FR-05**: When compiling, the system shall strip YAML frontmatter from the spec before sending it to the LLM.
*   **FR-06**: The system shall strip Markdown code fences from LLM responses before writing files.
*   **FR-07**: The system shall validate specs before compilation, rejecting invalid specs with descriptive errors.

## Test Execution
*   **FR-08**: `run_tests` shall inject the `build/` directory into `PYTHONPATH` so generated tests can import generated modules.
*   **FR-09**: `run_tests` shall capture both `stdout` and `stderr` from pytest.

## Self-Healing
*   **FR-10**: `attempt_fix` shall analyze test failures using the spec as source of truth.
*   **FR-11**: `attempt_fix` shall only overwrite files explicitly named in `### FILE:` blocks.
*   **FR-12**: `attempt_fix` shall strip Markdown fences from fix content before writing.

## Provider Abstraction
*   **FR-13**: The system shall support multiple LLM providers via a common `LLMProvider` protocol.
*   **FR-14**: Provider selection shall be configurable via environment variables or explicit config.
*   **FR-15**: The LLM provider shall be lazily initialized on first use.

# 4. Non-Functional Requirements (Constraints)

*   **NFR-Dependencies**: Runtime dependencies limited to Python Standard Library (urllib, json, os, subprocess, dataclasses). No `requests`, `openai`, or `anthropic` packages.
*   **NFR-Security**: File writes constrained to configured directories (no path traversal). API keys never logged or exposed.
*   **NFR-Robustness**: All API calls include error handling with descriptive exceptions.
*   **NFR-Testability**: All components support dependency injection for testing (mock providers).
*   **NFR-Extensibility**: New LLM providers can be added by implementing the `LLMProvider` protocol.

# 5. Design Contract

*   **Invariant**: An API key must be available (via config or environment) before any LLM operation.
*   **Invariant**: The `build/` directory is the only location where generated code is written.
*   **Pre-condition**: Spec names can be provided with or without `.spec.md` extension (system normalizes).
*   **Pre-condition**: Specs must pass validation before compilation.
*   **Post-condition**: After `compile_spec`, a `.py` file exists in `build/` with the module name.
*   **Post-condition**: After `compile_tests`, a `test_*.py` file exists in `build/`.

# 6. Test Scenarios
| Scenario | Input | Expected Output | Notes |
|----------|-------|-----------------|-------|
| Create valid spec | `create_spec("auth", "Auth module")` | File created at `src/auth.spec.md` | Template populated |
| Create duplicate spec | `create_spec("auth", ...)` twice | `FileExistsError` | Prevents overwrites |
| Validate missing sections | Spec without Overview | `{"valid": False, "errors": [...]}` | Lists missing sections |
| Compile valid spec | Valid spec + mock provider | Code written to `build/` | Provider called once |
| Compile invalid spec | Spec missing frontmatter | `ValueError` | Descriptive error |
| Run passing tests | Valid code + tests | `{"success": True, ...}` | Output contains "passed" |
| Run failing tests | Buggy code | `{"success": False, ...}` | Output contains error |
| Attempt fix | Failing tests | Files patched, status message | Only named files changed |
| Config from env | `SPECULAR_LLM_PROVIDER=anthropic` | Config with anthropic provider | Env override works |
| Provider injection | Mock provider assigned | Mock used for generation | Supports testing |
