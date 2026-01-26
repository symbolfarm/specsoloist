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
- **DependencyResolver**: Resolves spec dependencies and computes build order
- **BuildManifest**: Tracks file hashes for incremental builds
- **UI**: Provides rich terminal output and progress indicators

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

### `compile_project(specs: List[str] = None, model: Optional[str] = None, generate_tests: bool = True, incremental: bool = False, parallel: bool = False, max_workers: int = 4) -> BuildResult`
*   Compiles multiple specs in dependency order.
*   If `incremental=True`, only recompiles specs that have changed.
*   If `parallel=True`, compiles independent specs concurrently.
*   **Returns**: `BuildResult(success, specs_compiled, specs_skipped, specs_failed, build_order, errors)`.

### `get_build_order(specs: List[str] = None) -> List[str]`
*   Returns specs in topological order (dependencies before dependents).

### `get_dependency_graph(specs: List[str] = None) -> DependencyGraph`
*   Returns the dependency graph for inspection.

### `run_all_tests() -> Dict[str, Any]`
*   Runs tests for all compiled specs.
*   **Returns**: Dict with overall `success` and per-spec results.

## 2.2 SpecParser

### `__init__(src_dir: str)`
*   Initializes with the source directory path.

### `list_specs() -> List[str]`
*   Walks the source directory and returns all `*.spec.md` filenames.

### `read_spec(name: str) -> str`
*   Reads and returns raw spec content.

### `parse_spec(name: str) -> ParsedSpec`
*   Parses a spec into structured data: `ParsedSpec(metadata, content, body, path)`.
*   **Behavior**: If `description` is missing from frontmatter, extracts the first non-empty line from the "# 1. Overview" section.

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

### `__init__(build_dir: str, config: Optional[SpecularConfig] = None)`
*   Initializes with build directory and optional configuration.

### `run_tests(module_name: str, language: str = "python") -> TestResult`
*   Executes the test command defined in the language configuration.
*   Resolves placeholders like `{file}` and `{build_dir}` in commands and environment variables.

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

### `languages: Dict[str, LanguageConfig]`
*   A mapping of language names to their execution configurations (extensions, commands, env vars).

## 2.6 LLMProvider Protocol

### `generate(prompt: str, temperature: float = 0.1, model: Optional[str] = None) -> str`
*   Sends a prompt to the LLM and returns the generated text.
*   If `model` is provided, overrides the default model for this call.
*   Implementations: `GeminiProvider`, `AnthropicProvider`

## 2.7 DependencyResolver

### `__init__(parser: SpecParser)`
*   Initializes with a parser for reading spec files.

### `build_graph(spec_names: List[str] = None) -> DependencyGraph`
*   Builds a dependency graph from spec files.
*   Raises `MissingDependencyError` if a dependency doesn't exist.

### `resolve_build_order(spec_names: List[str] = None) -> List[str]`
*   Returns specs in topological order via Kahn's algorithm.
*   Raises `CircularDependencyError` if a cycle is detected.

### `get_parallel_build_order(spec_names: List[str] = None) -> List[List[str]]`
*   Returns specs grouped into parallelizable levels.
*   Specs within a level can be compiled concurrently.

### `get_affected_specs(changed_spec: str, graph: DependencyGraph = None) -> List[str]`
*   Returns all specs that need rebuilding when a spec changes.

## 2.8 BuildManifest

### `__init__()`
*   Initializes an empty manifest.

### `load(build_dir: str) -> BuildManifest`
*   Class method to load manifest from `.specular-manifest.json`.
*   Returns empty manifest if file doesn't exist or is corrupted.

### `save(build_dir: str)`
*   Saves manifest to the build directory.

### `update_spec(name: str, spec_hash: str, dependencies: List[str], output_files: List[str])`
*   Updates build info for a spec after successful compilation.

### `get_spec_info(name: str) -> Optional[SpecBuildInfo]`
*   Returns build info for a spec, or None if never built.

## 2.9 IncrementalBuilder

### `__init__(manifest: BuildManifest, src_dir: str)`
*   Initializes with a manifest and source directory.

### `needs_rebuild(spec_name: str, current_hash: str, current_deps: List[str], rebuilt_specs: set) -> bool`
*   Determines if a spec needs rebuilding based on hash, deps, or cascade.

### `get_rebuild_plan(build_order: List[str], spec_hashes: Dict, spec_deps: Dict) -> List[str]`
*   Returns which specs in the build order need rebuilding.

## 2.10 UI (Terminal Output)

### `print_header(title: str, subtitle: str = "")`
*   Displays a styled panel with a blue title.

### `print_success(message: str) / print_error(message: str) / print_warning(message: str)`
*   Displays themed status messages with icons.

### `create_table(columns: List[str], title: Optional[str] = None) -> Table`
*   Returns a Rich Table object with standard styling.

### `spinner(message: str) -> Status`
*   Returns a context manager for a "dots" spinner.

# 3. Functional Requirements (Behavior)

## Module Organization
*   **FR-01**: The system shall be organized into specialized modules (parser, compiler, runner, config, providers, ui) with SpecularCore as the thin orchestrator.
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

## Multi-Spec Builds
*   **FR-16**: Specs may declare dependencies in YAML frontmatter using `dependencies: [{name: X, from: y.spec.md}]` syntax.
*   **FR-17**: The system shall resolve dependencies using topological sort (Kahn's algorithm).
*   **FR-18**: The system shall detect and report circular dependencies with the cycle path.
*   **FR-19**: The system shall support `type: typedef` specs for shared data structures.
*   **FR-20**: `compile_project` shall compile all specs in dependency order, passing import context.

## Incremental Builds
*   **FR-21**: The system shall track spec content hashes and build metadata in `.specular-manifest.json`.
*   **FR-22**: When `incremental=True`, only specs with changed content, changed deps, or rebuilt deps shall be recompiled.
*   **FR-23**: The manifest shall persist across builds and recover gracefully from corruption.

## Parallel Compilation
*   **FR-24**: When `parallel=True`, specs at the same dependency level shall be compiled concurrently.
*   **FR-25**: Parallel compilation shall respect dependency order (level N completes before level N+1).

## UI and Feedback
*   **FR-26**: The CLI shall use the `rich` library to provide formatted tables, colored output, and spinners for asynchronous operations.
*   **FR-27**: Tables for `list` and `build` commands shall include metadata like type, status, and description.

# 4. Non-Functional Requirements (Constraints)

*   **NFR-Dependencies**: Runtime dependencies limited to Python Standard Library plus `pyyaml`, `rich`, and `mcp`.
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
| Build order | A depends on B | `["B", "A"]` | Dependencies first |
| Circular dependency | A -> B -> C -> A | `CircularDependencyError` | Reports cycle path |
| Diamond dependency | A -> B,C -> D | All built, D last | No duplicate builds |
| Incremental build | Unchanged spec | `specs_skipped` includes spec | Hash unchanged |
| Incremental cascade | Dependency changed | Dependents rebuilt | Cascade to dependents |
| Parallel levels | A,B independent | Both in level 0 | Can compile together |
| Manifest persistence | Build, reload | Same spec info | Survives restarts |
