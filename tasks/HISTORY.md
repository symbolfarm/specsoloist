# SpecSoloist — Task History

Append-only log of completed tasks and roadmap phases, in order of completion.

---

## Feature Tasks

| # | Task | Completed | Notes |
|---|------|-----------|-------|
| 01 | Fix `--auto-accept` scoping | 2026-02-18 | `bypassPermissions` now scoped to quine runs only |
| 02 | Implement `sp test --all` | 2026-02-18 | Runs tests for every compiled spec, shows summary table |
| 03 | Validate FastHTML example | 2026-02-18 | `examples/fasthtml_app/` — 23 tests passing, README written |
| 04 | `reference` spec type | 2026-03-11 | Parser validation, compiler injection, no code gen, verification tests, `sp validate`/`sp status` display |
| 05 | Arrangement `dependencies` field | 2026-03-11 | `ArrangementEnvironment.dependencies: dict[str, str]`; injected as "Dependency Versions" table in soloist prompts; `sp validate --arrangement` warns if no install command; FastHTML arrangement and score spec updated |
| 06 | FastHTML app refactor | 2026-03-11 | Split `app.spec.md` into layout/routes/state; add delete button; migrate `fasthtml_interface` to `type: reference` |
| 07 | Validate Next.js AI chat | 2026-03-13 | `vercel_ai_interface` reference spec written; `@ai-sdk/openai` pinned to `^0.0.9`; 22 tests passing across 4 files; README written |
| 08 | Arrangement templates | 2026-03-13 | `sp init --template python-fasthtml/nextjs-vitest/nextjs-playwright`; templates bundled in `src/specsoloist/arrangements/`; `sp init --list-templates` lists all with descriptions |
| 09 | E2E testing pattern | 2026-03-13 | `docs/e2e-testing.md` guide; `e2e_todos.spec.md` FastHTML example; `data-testid` added to layout spec; `pytest-playwright` added to pyproject.toml; §6.7 added to spec_format.spec.md |
| 10 | `sp conduct --resume` | 2026-03-13 | `--resume` and `--force` flags; `IncrementalBuilder.needs_rebuild()` checks output file existence; pre-flight SKIPPED/COMPILING plan display; 6 new tests in `test_conduct_resume.py` |
| 11 | Arrangement `env_vars` field | 2026-03-13 | `ArrangementEnvVar` model; compiler injects "Environment Variables" section into prompts; `sp doctor --arrangement` checks unset required vars; `sp validate` warns; nextjs arrangement updated; score spec updated; 8 new tests |
| 12 | Nested session warning | 2026-03-13 | `_detect_nested_session()` checks `CLAUDECODE`/`CLAUDE_CODE_ENTRYPOINT` env vars; "Heads Up" warning panel; friendly failure message; README note; 8 new tests |
| 13 | Incremental adoption guide | 2026-03-13 | `docs/incremental-adoption.md` (6-step guide); `examples/fasthtml_incremental/` with `original/app.py`, three hand-reviewed specs, `arrangement.yaml`, `README.md`; README link added |
| 14 | Database persistence patterns | 2026-03-13 | `fastlite_interface.spec.md` + `db.spec.md` + `routes_db.spec.md` for FastHTML; `prisma_interface.spec.md` for Next.js; `docs/database-patterns.md` (5 patterns); arrangement updated with fastlite note |
| 15 | `sp diff` spec-drift mode | 2026-03-15 | `sp diff <name>` compares spec symbols vs compiled Python using AST; reports MISSING/UNDOCUMENTED/TEST_GAP; `--json` flag; 22 new tests in `test_spec_diff.py`; backward-compatible (two-arg build-diff mode preserved) |
| 16 | `--quiet` / `--json` flags | 2026-03-15 | `--quiet` global flag (sp --quiet <cmd>) silences Rich output; `--json` per-subcommand flag on status/compile/validate emits structured JSON; `ui.configure()` reinitialises console; 13 new tests |
| 17 | Model pinning in arrangements | 2026-03-15 | Optional `model` field in Arrangement; `_resolve_model()` applies CLI > arrangement > env precedence; conductor.build passes model through; score/arrangement.spec.md updated; 12 new tests |
| 18 | Quine CI | 2026-03-15 | `.github/workflows/quine.yaml` — weekly schedule + workflow_dispatch; claude-haiku + --auto-accept + --resume; quine tests run; artifact uploaded 30 days; CONTRIBUTING.md note added |

## Housekeeping Tasks

| # | Task | Completed | Notes |
|---|------|-----------|-------|
| HK-01 | Consolidate IMPROVEMENTS + ROADMAP | 2026-02-18 | Trimmed §0 done-items from IMPROVEMENTS.md; fixed §0g (`_compile_single_spec` reference spec guard) and §0h (dep key normalised to `"from"` in core.py) |
| HK-02 | Small fixes | 2026-03-11 | Fixed `Optional[ArrangementEnvironment]` type hint; added comment on reference spec early return; moved dependency warning to `_resolve_arrangement()` |
| HK-03 | Remove `sp perform` | 2026-03-11 | Removed `cmd_perform`, `SpecConductor.perform/build_and_perform/_execute_step`, `PerformResult`, `StepResult` |
| HK-04 | Conductor writes `config_files` | 2026-03-13 | Always overwrite from arrangement (was skipping existing files); fixed typo in log message |
| HK-05 | Bundle spec docs vs parser | 2026-03-13 | Validator now accepts prose `##` headings in addition to `yaml:functions` blocks; all score specs now pass `sp validate` |
| HK-06 | Release v0.4.0 | 2026-03-13 | Released as v0.4.1 (README fix caught post-tag); publish workflow now auto-creates GitHub releases; release checklist added to CONTRIBUTING.md |

## Completed Roadmap Phases

| Phase | Completed | Summary |
|-------|-----------|---------|
| 1: Core Framework | 2025 | Spec-as-Source, LLM compilation, test generation, self-healing fix loop, MCP server |
| 1.5: Foundation Hardening | 2025 | Modular architecture (parser/compiler/runner), LLM provider abstraction, config system |
| 2a: Multi-Spec Architecture | 2025 | Dependency syntax, dependency graph, type specs, multi-spec builds |
| 2b: Build Optimization | 2025 | Incremental builds, build caching, parallel compilation |
| 2c: Release Prep | 2025 | `sp` CLI, PyPI publication |
| 3: Polish | 2025 | Rich terminal output, multi-language config, MkDocs docs site |
| 4: Spechestra Architecture | 2026-02 | Language-agnostic specs, bundle type, SpecComposer, SpecConductor, `sp compose`/`conduct`/`respec` |
| 5: Agent-First Architecture | 2026-02 | Agent-first commands, native subagents (`.claude/agents/`, `.gemini/agents/`), requirements-oriented specs |
| 6: The Quine | 2026-02 | `sp conduct score/` regenerates `src/` — 563 generated tests passing |
| 7: Robustness & Polish | 2026-02 | `sp fix` agent, arrangement system, sandboxed execution, MCP server removed |
| 8: Web-Dev Readiness | 2026-03-14 | `type: reference`, arrangement templates, FastHTML + Next.js examples, E2E pattern, `--resume`/`--force`, `env_vars`, nested session detection, incremental adoption guide, database patterns. 270 tests. |

## Decisions

| File | Topic | Decision | Date |
|------|-------|----------|------|
| `decisions/01-sp-perform.md` | Keep / fix / remove `sp perform` | Option A — remove | 2026-03-11 |
