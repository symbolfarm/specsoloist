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

### 4a: Spec Format Revision (Completed)
- [x] **Language-Agnostic Specs**: Remove `language_target` from specs; move to build config.
- [x] **Granular Specs**: One function = one spec for better modularity and parallelism.
- [x] **Bundle Type**: Compact format for grouping trivial functions/types.
- [x] **Schema-First Interface**: `yaml:schema` blocks as primary interface definition.
- [x] **Spec Format Spec**: Self-hosting spec defining the format itself.
- [x] **New Parser**: Parser handles function, type, bundle, module, workflow spec types.

### 4b: Package Separation (Completed)
- [x] **Spechestra Package**: Created `src/spechestra/` alongside `src/specsoloist/`.
- [x] **SpecSoloist Core**: Individual spec compilation (existing functionality preserved).
- [ ] **Optional**: Full monorepo structure with separate pyproject.toml files (deferred).

### 4c: SpecComposer (Implemented)
- [x] **Architecture Drafting**: `draft_architecture()` - Plain English → component graph.
- [x] **Spec Generation**: `generate_specs()` - Auto-generate `*.spec.md` files.
- [x] **Compose Workflow**: `compose()` - Full pipeline with auto-accept option.
- [ ] **Interactive Review**: Present architecture and specs for user approval/editing.
- [x] **Context Awareness**: Incorporate existing specs when drafting new architecture.

### 4d: SpecConductor (Implemented)
- [x] **Parallel Build**: `build()` - Orchestrate SpecSoloistCore for parallel compilation.
- [x] **Build Verification**: `verify()` - Schema compliance and interface compatibility.
- [x] **Workflow Execution**: `perform()` - Run compiled workflows with checkpoints.
- [x] **Execution Tracing**: Save traces to `.spechestra/traces/`.
- [x] **Combined Flow**: `build_and_perform()` - Build then execute.

### 4e: Integration (Next Up)
- [ ] **CLI Commands**: Add `sp compose`, `sp conduct`, `sp perform` commands.
- [ ] **Vibe-Coding Demo**: End-to-end demo from plain English to working code.
- [ ] **Interactive Mode**: Terminal UI for reviewing/approving architecture and specs.
- [ ] **Deprecate Old Modules**: Remove `agent.py`, `orchestrator.py`, `state.py` from specsoloist.

## Phase 5: Self-Hosting & Fidelity (New)

The goal is to achieve full "Quine" status: `sp conduct self_hosting/` should be able to regenerate the entire `src/` directory with high fidelity.

### 5a: Spec Lifter (`sp lift`)
- [ ] **Reverse Engineering**: `sp lift <file>` - Generate a spec from existing source code.
- [ ] **Test Awareness**: ingest existing `tests/test_*.py` to populate spec "Test Scenarios".
- [ ] **Decomposition**: Intelligent refactoring - suggest breaking monolithic files into granular specs.
- [ ] **Fidelity Checking**: Compare generated code against original to verify spec accuracy.

### 5b: Full Spec Suite
- [ ] **Leaf Modules**: Lift `config.py`, `ui.py`, `schema.py`.
- [ ] **Core Logic**: Lift `parser.py`, `compiler.py`, `resolver.py`.
- [ ] **Application**: Lift `cli.py` and entry points.

## Phase 6: Developer Experience (Future)
- [ ] **Sandboxed Execution**: Run generated code in Docker containers for safety.
- [ ] **VS Code Extension**: Live preview of generated code/tests while editing specs.
- [ ] **Visual Spec Editor**: A GUI for defining Functional Requirements and Contracts.
- [ ] **Advanced Workflows**: Conditional branching, loops, fan-out/fan-in parallelism.
- [ ] **Streaming Compilation**: Real-time feedback as specs are compiled.

---

## Next Steps (Detailed)

The following tasks are ready for the next contributor:

### CLI Integration (Priority: High)
- [x] **Add `sp compose` command** in `cli.py`:
   - Accept natural language request as argument
   - Call `SpecComposer.compose()`
   - Display generated architecture and spec paths
   - Add `--auto-accept` flag to skip prompts

- [x] **Add `sp conduct` command** (or integrate into `sp build`):
   - Use `SpecConductor.build()` instead of `SpecSoloistCore.compile_project()`
   - Show parallel build progress

- [x] **Add `sp perform` command**:
   - Execute workflow with `SpecConductor.perform()`
   - Display step-by-step execution
   - Show trace path on completion

### Interactive Review (Priority: Medium)
- [x] **Architecture Review UI**:
   - Use Rich to display component table
   - Prompt for approval/modifications
   - Allow adding/removing components (via YAML editor)

- [ ] **Spec Review UI**:
   - Display generated spec content
   - Open in $EDITOR if user wants to modify
   - Confirm before proceeding

### Cleanup (Priority: Low)
- [x] **Deprecate old orchestration modules**:
   - `src/specsoloist/agent.py` → replaced by `SpecConductor.perform()`
   - `src/specsoloist/orchestrator.py` → replaced by `SpecConductor`
   - `src/specsoloist/state.py` → Blackboard logic in conductor

- [ ] **Update self-hosting specs**:
   - Ensure `self_hosting/specsoloist.spec.md` reflects current implementation
   - Add tests that verify specs match implementation

## Maintenance
- [x] Fix ruff lint errors as they arise.
- [x] Keep self-hosting specs in sync with implementation.
- [x] Add tests for new components (52 tests total).
