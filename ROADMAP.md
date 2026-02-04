# SpecSoloist Roadmap

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
- [x] **Configuration System**: `SpecSoloistConfig` with environment-based loading.
- [x] **Thin Orchestrator**: Refactor `SpecSoloistCore` to delegate to specialized modules.
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
- [x] **Human CLI**: `sp` command with list, create, compile, test, fix, build commands.
- [x] **PyPI Publication**: Released `specsoloist` to PyPI.

## Phase 3: Polish (Completed)
- [x] **CLI Polish**: Rich terminal output (spinners, tables, colored panels).
- [x] **Multi-Language Support**: Config-driven runner with TypeScript support (via `tsx` and `node:test`).
- [x] **Documentation Site**: MkDocs Material site with "Leaves-Up" workflow guide.
- [x] **Error Handling**: Friendly messages for circular dependencies and missing API keys.

## Phase 4: Spechestra Architecture (In Progress)

### 4a: Spec Format Revision (In Progress)
- [x] **Language-Agnostic Specs**: Remove `language_target` from specs; move to build config.
- [x] **Granular Specs**: One function = one spec for better modularity and parallelism.
- [x] **Bundle Type**: Compact format for grouping trivial functions/types.
- [x] **Schema-First Interface**: `yaml:schema` blocks as primary interface definition.
- [x] **Spec Format Spec**: Self-hosting spec defining the format itself.
- [ ] **New Parser**: Update parser to handle revised spec format.

### 4b: Package Separation (Planned)
- [ ] **Monorepo Structure**: Reorganize into `packages/specsoloist` and `packages/spechestra`.
- [ ] **SpecSoloist Core**: Individual spec compilation (current functionality).
- [ ] **Spechestra Package**: Orchestration layer depending on SpecSoloist.

### 4c: SpecComposer (Planned)
- [ ] **Architecture Drafting**: Plain English → component architecture with dependencies.
- [ ] **Spec Generation**: Auto-generate `*.spec.md` files from architecture.
- [ ] **Interactive Review**: Present architecture and specs for user approval/editing.
- [ ] **Auto-Accept Mode**: Skip reviews for automated pipelines.
- [ ] **Context Awareness**: Incorporate existing specs when drafting new architecture.

### 4d: SpecConductor (Planned)
- [ ] **Parallel Build**: Orchestrate multiple SpecSoloist instances for parallel compilation.
- [ ] **Build Verification**: `verify()` for schema compliance and interface compatibility.
- [ ] **Workflow Execution**: `perform()` to run compiled workflows with checkpoints.
- [ ] **Execution Tracing**: Save traces to `.spechestra/traces/` for debugging.

### 4e: Integration (Planned)
- [ ] **End-to-End Flow**: `compose() → build() → perform()` pipeline.
- [ ] **CLI Commands**: `sp compose`, `sp conduct`, `sp perform`.
- [ ] **Vibe-Coding Demo**: Plain English to working code demonstration.

## Phase 5: Developer Experience (Future)
- [ ] **Sandboxed Execution**: Run generated code in Docker containers for safety.
- [ ] **VS Code Extension**: Live preview of generated code/tests while editing specs.
- [ ] **Visual Spec Editor**: A GUI for defining Functional Requirements and Contracts.
- [ ] **Advanced Workflows**: Conditional branching, loops, fan-out/fan-in parallelism.
- [ ] **Streaming Compilation**: Real-time feedback as specs are compiled.

## Maintenance
- [ ] Fix any ruff lint errors as they arise.
- [ ] Keep self-hosting specs in sync with implementation.
- [ ] Add tests for new components (SpecComposer, SpecConductor).
