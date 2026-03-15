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
- [x] **Build Caching**: Track file hashes and build manifest (`.specsoloist-manifest.json`).
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
- ~~[x] **Workflow Execution**: `perform()` - Run compiled workflows with checkpoints.~~ *(removed — see `decisions/01-sp-perform.md`)*
- ~~[x] **Execution Tracing**: Save traces to `.spechestra/traces/`.~~ *(removed with `perform`)*
- ~~[x] **Combined Flow**: `build_and_perform()` - Build then execute.~~ *(removed with `perform`)*

### 4e: CLI Integration
- [x] **`sp compose`**: Draft architecture and specs from natural language.
- [x] **`sp conduct`**: Orchestrate parallel builds.
- ~~[x] **`sp perform`**: Execute workflow specs.~~ *(removed — see `decisions/01-sp-perform.md`)*
- [x] **`sp respec`**: Reverse engineer code to specs (formerly `lift`).

---

## Phase 5: Agent-First Architecture (Completed)

The core insight: **complex operations should delegate to AI agents** (Claude, Gemini) rather than single-shot LLM API calls. Agents can read files, validate, iterate on errors, and make multi-step decisions.

### 5a: Agent-First Commands

| Command | Status | Description |
|---------|--------|-------------|
| `sp respec` | ✅ Done | Reverse engineer code → specs with validation loop |
| `sp compose` | ✅ Done | Architecture drafting with iterative refinement |
| `sp conduct` | ✅ Done | Conductor agent orchestrates spec compilation (Claude: spawns soloist subagents; Gemini: compiles directly) |
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

## Phase 7: Robustness & Polish (Completed)

- [x] **Agent-first `sp fix`**: Self-healing command using native subagents
- [x] **Fix agent**: `.claude/agents/fix.md` and `.gemini/agents/fix.md` — analyze test failures, patch code, re-test
- [x] **Naming consistency**: Align quine output names (`composer`, `conductor`)
- [x] **Arrangement System**: Implement the Arrangement (makefile) system to decouple build config from specs
- [x] **Sandboxed Execution**: Run generated code in Docker/Wasm containers for safety
- [x] **Drop MCP server**: `specsoloist-mcp` removed; agent-first CLI is the better abstraction

## Phase 8: Web-Dev Readiness (Completed 2026-03-14)

- [x] **`sp init`**: Scaffold a new project (`specs/`, `arrangement.yaml`, `.gitignore`)
- [x] **`type: reference` spec type**: Third-party API docs injected as soloist context; `# Verification` compiled to tests (task 04)
- [x] **FastHTML example validated**: `examples/fasthtml_app/` — 23 tests passing, `fasthtml_interface.spec.md` migrated to `type: reference`
- [x] **Arrangement `dependencies` field**: Machine-readable version constraints injected into soloist prompts (task 05)
- [x] **FastHTML app refactor**: Split `app.spec.md` into layout/routes/state; multi-spec web app pattern (task 06)
- [x] **Next.js AI chat example**: `vercel_ai_interface` as `type: reference`; 22 tests passing (task 07)
- [x] **Arrangement templates**: `sp init --template python-fasthtml/nextjs-vitest/nextjs-playwright` (task 08)
- [x] **E2E testing pattern**: Playwright arrangement, `data-testid` spec contract, FastHTML E2E example (task 09)
- [x] **`sp conduct --resume` / `--force`**: Skip already-compiled specs; cascade recompile on dep change (task 10)
- [x] **`env_vars` in Arrangement**: Declared env var names; `sp doctor` warns if unset (task 11)
- [x] **Nested session detection**: Friendly warning when running inside Claude Code or Gemini CLI (task 12)
- [x] **Incremental adoption guide**: `sp respec` workflow for existing FastHTML/Next.js projects (task 13)
- [x] **Database persistence patterns**: fastlite + Prisma reference specs; test fixture patterns (task 14)

270 tests passing at phase close.

## Phase 9: Distribution & Developer Experience (Planned)

- [ ] **Fix quine naming mismatch**: Score specs instruct soloists to use `composer.py`/`conductor.py` (not `speccomposer.py`)
- [ ] **`sp diff` — spec vs code drift detection**: Compare a compiled module against its spec; enumerate missing/extra symbols and behaviour gaps. Generalised from the quine_diff concept to work on any project.
- [ ] **Pydantic AI provider abstraction**: Replace bespoke `LLMProvider` with Pydantic AI; get most LLM providers (OpenAI, Gemini, Anthropic, Ollama) for free; opens path to custom agents independent of Claude/Gemini CLI
- [ ] **`--quiet` / `--json` output flags**: Scripting and CI-friendly output (1g)
- [ ] **Model pinning in arrangements**: `model:` field in arrangement YAML; cost/quality control per-spec (6d)
- [ ] **Quine CI**: Scheduled GitHub Actions workflow running `sp conduct score/` nightly; score freshness check (3c)
- [ ] **Watch mode `sp watch`**: Recompile specs on file change via `watchdog` (2a)
- [ ] **`.specsoloist/` directory consolidation**: Gather manifest, build artifacts, traces under one directory (8c)
- [ ] **VS Code extension**: Syntax highlighting, inline validation, compile action for `.spec.md` files (9a)

---

## Maintenance

- [x] Fix ruff lint errors as they arise
- [x] Keep self-hosting specs in sync with implementation
- [x] 242 original tests passing, 563 quine tests passing
- [x] **v0.3.2 patch** — fix setup_commands execution, bypassPermissions scope, NO_COLOR support, validate_inputs NotImplementedError, pytest warnings, stale CLI docs, new arrangement/agents guides
- [x] **TypeScript conduct validated** — `sp conduct examples/ts_demo/` with `arrangement.typescript.yaml` produces working code and passing tests via Gemini CLI

