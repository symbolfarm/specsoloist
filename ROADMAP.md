# Specular Roadmap

## Phase 1: Core Framework & Self-Healing (Completed)
- [x] **Spec-as-Source**: Define components using rigorous SRS-style Markdown.
- [x] **LLM Compilation**: Compile specs to Python code using Google Gemini.
- [x] **Test Generation**: Automatically generate `pytest` suites from spec scenarios.
- [x] **Integrated Runner**: Run tests in isolated environments.
- [x] **Agentic Self-Healing**: `attempt_fix` loop that analyzes failures and patches code/tests.
- [x] **MCP Server**: Expose all tools via the Model Context Protocol.

## Phase 1.5: Foundation Hardening (Completed)
- [x] **Code Separation**: Extract specialized modules (parser, compiler, runner, config).
- [x] **LLM Provider Abstraction**: `LLMProvider` protocol with Gemini and Anthropic implementations.
- [x] **Configuration System**: `SpecularConfig` with environment-based loading.
- [x] **Thin Orchestrator**: Refactor `SpecularCore` to delegate to specialized modules.
- [x] **Updated Self-Hosting Spec**: The Quine updated to reflect new architecture.

## Phase 2a: Multi-Spec Architecture (Completed)
- [x] **Dependency Syntax**: YAML frontmatter syntax for declaring spec dependencies.
- [x] **Dependency Graph**: `DependencyResolver` with topological sort for build order.
- [x] **Type Specs**: Support `type: typedef` specs with specialized compilation.
- [x] **Multi-Spec Builds**: `compile_project()` compiles all specs in dependency order.
- [x] **Affected Specs**: Track which specs need rebuilding when a dependency changes.

## Phase 2b: Build Optimization (Completed)
- [x] **Incremental Builds**: Only recompile specs that have changed.
- [x] **Build Caching**: Track file hashes and build manifest (`.specular-manifest.json`).
- [x] **Parallel Compilation**: Compile independent specs concurrently using `ThreadPoolExecutor`.

## Phase 2c: Release Prep (Completed)
- [x] **Human CLI**: `specular` command with list, create, compile, test, fix, build commands.
- [x] **PyPI Publication**: Released `specular-ai` v0.1.0 to PyPI.

## Phase 3: Polish (v1.0)
- [ ] **CLI Polish**: Rich terminal output (spinners, colored diffs).
- [ ] **Multi-Language Support**: Verify and template support for TypeScript and Go.
- [ ] **Documentation Site**: Examples and API reference.
- [ ] **Error Messages**: Improve user-facing error messages and edge case handling.

## Phase 4: Developer Experience
- [ ] **VS Code Extension**: Live preview of generated code/tests while editing specs.
- [ ] **Visual Spec Editor**: A GUI for defining Functional Requirements and Contracts.
- [ ] **Sandboxed Execution**: Run generated code in Docker containers for safety.
