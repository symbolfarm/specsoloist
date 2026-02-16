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

## Phase 4: Spechestra Architecture (Completed)

### 4a: Spec Format Revision
- [x] **Language-Agnostic Specs**: Remove `language_target` from specs; move to build config.
- [x] **Granular Specs**: One function = one spec for better modularity and parallelism.
- [x] **Bundle Type**: Compact format for grouping trivial functions/types.
- [x] **Schema-First Interface**: `yaml:schema` blocks as primary interface definition.
- [x] **Spec Format Spec**: Self-hosting spec defining the format itself.
- [x] **New Parser**: Parser handles function, type, bundle, module, workflow spec types.

### 4b: Package Separation
- [x] **Spechestra Package**: Created `src/spechestra/` alongside `src/specsoloist/`.
- [x] **SpecSoloist Core**: Individual spec compilation (existing functionality preserved).

### 4c: SpecComposer
- [x] **Architecture Drafting**: `draft_architecture()` - Plain English → component graph.
- [x] **Spec Generation**: `generate_specs()` - Auto-generate `*.spec.md` files.
- [x] **Compose Workflow**: `compose()` - Full pipeline with auto-accept option.
- [x] **Context Awareness**: Incorporate existing specs when drafting new architecture.

### 4d: SpecConductor
- [x] **Parallel Build**: `build()` - Orchestrate SpecSoloistCore for parallel compilation.
- [x] **Build Verification**: `verify()` - Schema compliance and interface compatibility.
- [x] **Workflow Execution**: `perform()` - Run compiled workflows with checkpoints.
- [x] **Execution Tracing**: Save traces to `.spechestra/traces/`.
- [x] **Combined Flow**: `build_and_perform()` - Build then execute.

### 4e: CLI Integration
- [x] **`sp compose`**: Draft architecture and specs from natural language.
- [x] **`sp conduct`**: Orchestrate parallel builds.
- [x] **`sp perform`**: Execute workflow specs.
- [x] **`sp respec`**: Reverse engineer code to specs (formerly `lift`).

---

## Phase 5: Agent-First Architecture (Completed)

The core insight: **complex operations should delegate to AI agents** (Claude, Gemini) rather than single-shot LLM API calls. Agents can read files, validate, iterate on errors, and make multi-step decisions.

### 5a: Agent-First Commands

| Command | Status | Description |
|---------|--------|-------------|
| `sp respec` | ✅ Done | Reverse engineer code → specs with validation loop |
| `sp compose` | ✅ Done | Architecture drafting with iterative refinement |
| `sp conduct` | ✅ Done | Conductor agent spawns soloist subagents per spec |
| `sp fix` | ✅ Done | Self-healing with error analysis and re-testing |

**Implementation pattern:**
- Commands default to agent mode (detect claude/gemini CLI)
- `--no-agent` flag for direct LLM API fallback
- Agent handles file I/O, validation, iteration

### 5b: Native Subagents

| Agent | Status | Role |
|-------|--------|------|
| `respec` | ✅ Done | Extract requirements from code → spec |
| `compose` | ✅ Done | Draft architecture from natural language |
| `conductor` | ✅ Done | Orchestrate builds, spawn soloists per dependency level |
| `soloist` | ✅ Done | Read spec, write code directly (agent IS the compiler) |
| `fix` | ✅ Done | Self-healing: analyze test failures, patch code |

### 5c: Requirements-Oriented Specs

Key philosophical shift: specs define **requirements and public API**, not implementation blueprints.

- [x] **Validated round-trip** on 3 modules (resolver, config, manifest)
- [x] **Updated spec_format.spec.md** with "Requirements, Not Blueprints" philosophy
- [x] **Updated respec agents** to extract requirements, not implementation details
- [x] **Updated parser templates** for requirements-oriented output
- [x] **Respecced all modules** — every module in score/ now has a requirements-oriented spec

---

## Phase 6: The Quine (Self-Hosting)

Goal: `sp conduct score/` regenerates `src/` with passing tests.

### 6a: Score Status

All modules have requirements-oriented specs in `score/`. All validated via quine.

| Spec | Type | Dependencies | Round-trip Validated |
|------|------|-------------|---------------------|
| `config.spec.md` | bundle | — | ✅ Yes |
| `manifest.spec.md` | bundle | config | ✅ Yes |
| `resolver.spec.md` | bundle | — | ✅ Yes |
| `ui.spec.md` | bundle | — | ✅ Yes |
| `schema.spec.md` | bundle | — | ✅ Yes |
| `runner.spec.md` | bundle | config | ✅ Yes |
| `compiler.spec.md` | bundle | — | ✅ Yes |
| `parser.spec.md` | module | schema | ✅ Yes |
| `respec.spec.md` | bundle | config | ✅ Yes |
| `core.spec.md` | bundle | config, parser, compiler, runner, resolver, manifest | ✅ Yes |
| `cli.spec.md` | bundle | core, resolver, ui | ✅ Yes |
| `speccomposer.spec.md` | bundle | core | ✅ Yes |
| `specconductor.spec.md` | bundle | core | ✅ Yes |

### 6b: Quine Attempt — Completed ✅

- [x] Run `sp conduct score/ --model haiku --auto-accept` end-to-end
- [x] 563 generated tests passing (100% pass rate)
- [x] Output to `build/quine/` — full regeneration from specs alone
- [x] Document results in `QUINE_RESULTS.md`
- [x] Harden output path prompts to prevent soloists overwriting original source

**Known issues:**
- Naming mismatch: quine generates `speccomposer.py`/`specconductor.py` vs original `composer.py`/`conductor.py`
- `server.py` has no spec — not regenerated
- One soloist (resolver) ignored output path and wrote to `src/` — mitigated by prompt hardening

---

## Phase 7: Robustness & Polish (Next)

- [x] **Agent-first `sp fix`**: Self-healing command using native subagents
- [x] **Fix agent**: `.claude/agents/fix.md` and `.gemini/agents/fix.md` — analyze test failures, patch code, re-test
- [x] **`server.py` spec**: Add spec for the MCP server so the quine is fully complete
- [x] **Naming consistency**: Align quine output names (`composer`, `conductor`)
- [ ] **Arrangement System**: Implement the Arrangement (makefile) system to decouple build config from specs
- [x] **Sandboxed Execution**: Run generated code in Docker/Wasm containers for safety
- [ ] **Quine diff report**: Implement the quine_diff tool for semantic fidelity analysis

## Phase 8: Developer Experience (Future)

- [ ] **Interactive Mode**: Terminal UI for reviewing/approving specs and architecture
- [ ] **VS Code Extension**: Live preview while editing specs
- [ ] **Visual Spec Editor**: GUI for defining requirements
- [ ] **Advanced Workflows**: Conditional branching, loops, fan-out/fan-in
- [ ] **Streaming Compilation**: Real-time feedback during compilation
- [ ] **Multi-language quine**: Prove specs can compile to TypeScript/Go/Rust, not just Python
- [ ] **Spec coverage**: Tooling to measure how much of the public API is covered by specs

---

## Maintenance

- [x] Fix ruff lint errors as they arise
- [x] Keep self-hosting specs in sync with implementation
- [x] 52 original tests passing, 563 quine tests passing
