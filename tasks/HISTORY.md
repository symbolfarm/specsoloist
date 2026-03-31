# SpecSoloist — Task History

Append-only log of completed tasks and roadmap phases, in order of completion.

---

## Feature Tasks (v0.6.0 additions)

| # | Task | Completed | Notes |
|---|------|-----------|-------|
| 22 | `sp schema [topic]` | 2026-03-27 | Field descriptions added to all Arrangement sub-models; `_format_schema_text` walks Pydantic v2 model_fields recursively; `sp schema`, `sp schema <topic>`, `sp schema --json` all work; 10 new tests; `score/cli.spec.md` updated |
| 23 | `sp help <topic>` | 2026-03-27 | `src/specsoloist/help/` package with 5 hand-written Markdown guides (arrangement, spec-format, conduct, overrides, specs-path); `_read_help_file` via `importlib.resources`; `sp help` lists topics; `sp help <topic>` prints guide; 17 new tests; `score/cli.spec.md` updated |

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
| 19 | `sp vibe` | 2026-03-15 | Single-command compose→conduct pipeline; reads .md brief or plain string; --pause-for-review; --resume for addendum mode; README updated; 11 new tests |
| 20 | Pydantic AI provider | 2026-03-15 | PydanticAIProvider added alongside existing gemini/anthropic providers; supports openai/openrouter/ollama via pydantic-ai-slim; sp doctor updated; backward compat preserved; 27 new tests |
| 21 | Quine refresh | 2026-03-19 | Updated 10 score specs to cover ~20 Phase 8/9 features; deleted stale `quine_diff.spec.md`; added `build_diff.spec.md` as code-gen spec; marked 3 overview specs as `type: specification`; 320 quine tests pass (was 563 but structure changed) |
| 22 | Add spec_diff to score | 2026-03-19 | `score/spec_diff.spec.md` written from source; documents all public types and functions; 18 test scenarios; passes `sp validate` |

## Housekeeping Tasks

| # | Task | Completed | Notes |
|---|------|-----------|-------|
| HK-01 | Consolidate IMPROVEMENTS + ROADMAP | 2026-02-18 | Trimmed §0 done-items from IMPROVEMENTS.md; fixed §0g (`_compile_single_spec` reference spec guard) and §0h (dep key normalised to `"from"` in core.py) |
| HK-02 | Small fixes | 2026-03-11 | Fixed `Optional[ArrangementEnvironment]` type hint; added comment on reference spec early return; moved dependency warning to `_resolve_arrangement()` |
| HK-03 | Remove `sp perform` | 2026-03-11 | Removed `cmd_perform`, `SpecConductor.perform/build_and_perform/_execute_step`, `PerformResult`, `StepResult` |
| HK-04 | Conductor writes `config_files` | 2026-03-13 | Always overwrite from arrangement (was skipping existing files); fixed typo in log message |
| HK-05 | Bundle spec docs vs parser | 2026-03-13 | Validator now accepts prose `##` headings in addition to `yaml:functions` blocks; all score specs now pass `sp validate` |
| HK-06 | Release v0.4.0 | 2026-03-13 | Released as v0.4.1 (README fix caught post-tag); publish workflow now auto-creates GitHub releases; release checklist added to CONTRIBUTING.md |
| HK-08 | Review and update docs/ content | 2026-03-18 | Updated cli.md (all 18 commands + flags), getting_started.md (sp command, vibe-coding intro), workflow.md (sp vibe, --resume/--force, sp diff, sp status), arrangement.md (env_vars, dependencies, model, sp init templates), agents.md (nested session warning) |
| HK-10 | Add mkdocstrings + Google docstrings | 2026-03-18 | mkdocstrings[python] + ruff D/Google convention in pyproject.toml; docs/reference/api.md (public API) + internals.md (contributors); Google-style docstrings across all 20 modules (63 violations fixed); site/ added to .gitignore; broken nav links fixed; mkdocs build --strict passes | Updated cli.md (all 18 commands + flags), getting_started.md (sp command, vibe-coding intro), workflow.md (sp vibe, --resume/--force, sp diff, sp status), arrangement.md (env_vars, dependencies, model, sp init templates), agents.md (nested session warning) |
| HK-07 | Fix quine naming mismatch | 2026-03-18 | Score specs already used `composer`/`conductor` names correctly; stale `test_examples_build.py` (referenced deleted examples + old `sp build` API) deleted |
| HK-09 | Ban hardcoded paths in tests | 2026-03-18 | Working Principles note added to tasks/README.md; `test_examples_build.py` deleted (contained the violations); quine.yaml `--all-extras` flag removed |
| HK-11 | Spec type examples in docs | 2026-03-18 | New `docs/reference/spec-types.md` (replaces `template.md`) with one real embedded example per type using MkDocs snippets; `reference` type conventions documented; example docs rewritten for fasthtml_app + nextjs_ai_chat + math; stale examples removed (demo.py, user_project/, ml_demo/, ts_demo/) |
| HK-12 | Fix pytest TestResult/TestRunner warnings | 2026-03-19 | Added `# Constraints` to `score/runner.spec.md` — test files must not import TestResult/TestRunner at module scope |
| HK-13 | Remove non-code overview specs from score/ | 2026-03-19 | Deleted `arrangement.spec.md`, `specsoloist.spec.md`, `spechestra.spec.md`; score/ now has 15 specs (14 code-gen + spec_format) |
| HK-14 | Revert publish workflow to trusted publishing | 2026-03-26 | Removed `password: ${{ secrets.PYPI_API_TOKEN }}` and `attestations: false` from publish.yaml; root cause of v0.5.0 failures was duplicate ZIP entries, not auth |
| HK-15 | `specs_path` arrangement field + discovery commands | 2026-03-26 | Added `specs_path: str = "src/"` to `Arrangement`; `--arrangement` flag on `sp list/status/graph`; all three commands apply `specs_path` from arrangement before listing; 6 new tests |
| HK-16 | Verify and test `output_paths.overrides` | 2026-03-26 | Confirmed `resolve_implementation/tests` uses `.format(name=name)`; all override scenarios already covered in `test_arrangement.py` (impl-only, tests-only, both, no-override, YAML round-trip, compile integration); `score/arrangement.spec.md` n/a (deleted in HK-13) |
| HK-17 | `yaml:test_scenarios` validator fix + `--version` flag | 2026-03-26 | `_check_spec_quality` now recognises `` ```yaml:test_scenarios `` blocks; warning for missing scenarios includes example snippet; `--version`/`-V` added to argparse using `importlib.metadata`; 6 new tests |
| HK-19 | Fix `score/cli.spec.md` quine correctness | 2026-03-27 | Removed `sp perform` (deleted in HK-03 but still in spec); added `--version`/`-V` to Global Flags; added `--arrangement` flag to `sp list`, `sp status`, `sp graph` entries |
| HK-20 | Update docs for v0.7.0 | 2026-03-27 | cli.md: added `sp schema`, `sp help`, `--version`, `--arrangement` flags; arrangement.md: added `specs_path` and `output_paths.overrides` sections; README.md: updated CLI reference table |
| HK-21 | Trim stale dynamic facts from orientation files | 2026-03-27 | Removed test counts from AGENTS.md (3 places) and ROADMAP.md (2 places); replaced stale "Current State" section in AGENTS.md with pointer to `tasks/README.md`; marked Phase 9 complete in ROADMAP.md; added Phase 10 (current) and renumbered Ecosystem to Phase 11 | Removed `sp perform` (deleted in HK-03 but still in spec); added `--version`/`-V` to Global Flags; added `--arrangement` flag to `sp list`, `sp status`, `sp graph` entries |
| 24 | Init templates + skill updates + staleness detection | 2026-03-27 | Annotated init templates (python, typescript, fasthtml, nextjs) with commented `specs_path`, `overrides`, `dependencies`, `model`, `env_vars` examples; added "Key Arrangement Fields" section to `sp-conduct/SKILL.md` and `sp-soloist/SKILL.md` and native conductor/soloist agent files; `cmd_install_skills` prepends `<!-- sp-version: X.Y.Z -->` marker to each installed SKILL.md; `sp doctor` warns when installed skills have a different version; `sp schema` and `sp help` commands implemented; `score/cli.spec.md` updated; 4 new init tests, 5 new doctor/install-skills tests |
| 25 | `static` artifacts in arrangements | 2026-03-27 | `ArrangementStatic` model (`source`, `dest`, `description`, `overwrite`); `static` list field on `Arrangement`; `SpecConductor._copy_static_artifacts()` copies dirs/files after compilation; `sp doctor` warns on missing static sources; `src/specsoloist/help/arrangement.md` updated; `score/arrangement.yaml` created (quine arrangement with `help/` and `skills/` static entries); `score/schema.spec.md` and `score/conductor.spec.md` updated; 9 new tests |
| HK-22 | Release v0.7.0 | 2026-03-27 | CHANGELOG dated and task 25 entry added; all preflight checks green (411 tests, ruff, mkdocs --strict, uv build); tagged v0.7.0; pushed to trigger PyPI publish + GitHub release |
| HK-23 | `sp doctor` static path base dir | 2026-03-27 | Fixed: static source paths now resolve relative to the arrangement file's directory (`arr_base = os.path.dirname(os.path.abspath(arr_path))`), not `os.getcwd()` |
| UA-01 | Add `ANTHROPIC_API_KEY` to GitHub repo secrets | 2026-03-27 | Done by Toby |
| UA-02 | Delete `PYPI_API_TOKEN` from GitHub release environment secrets | 2026-03-27 | Done by Toby |
| 26 | Run quine with `score/arrangement.yaml` | 2026-03-27 | 584/584 tests pass; conductor/composer in `build/quine/src/spechestra/` ✓; help/ and skills/ static artifacts copied ✓; quine generated 584 tests vs 411 in original suite (specs prompt more thorough generation) |
| HK-25 | Integrate `score/arrangement.yaml` with quine mode | 2026-03-27 | Quine agent prompt now injects per-spec output overrides (prefixed with `build/quine/`) and static artifact copy instructions from the arrangement; also reverted HK-23's arrangement-file-dir change back to `os.getcwd()` (consistent with conductor's `project_dir` approach; arrangement-file-dir was wrong for `score/arrangement.yaml` which lives in a subdirectory with repo-root-relative paths) |
| 27 | Event bus and BuildEvent model | 2026-03-29 | `EventBus` (queue.Queue-based), `BuildEvent` dataclass, `EventType` enum, `EventSubscriber` protocol; thread-safe subscriber notification; drain helper for tests |
| 28 | Wire event emission into core/runner/compiler | 2026-03-29 | `event_bus` parameter threaded through `SpecSoloistCore`, `compile_code()`, `_generate()`; emits build/spec/test/fix events at all lifecycle points |
| 29 | Provider token tracking | 2026-03-29 | `LLMResponse` dataclass with `input_tokens`/`output_tokens`; providers return it; `llm.response` events emitted by compiler |
| 30 | NDJSON subscriber + `--log-file` | 2026-03-29 | `NdjsonSubscriber` writes one JSON line per event to a file; `--log-file` flag on `sp conduct`/`sp build` |
| 31a | BuildState model + TuiSubscriber | 2026-03-29 | `BuildState`/`SpecState` dataclasses; `.apply(event)` state machine; `TuiSubscriber` bridges events to Textual via `call_from_thread` |
| 31b | Textual app skeleton + spec list | 2026-03-29 | `DashboardApp`, `SpecListWidget`, `StatusBar`; navigable spec list with status icons; headless testing via `run_test()` |
| 31c | Spec detail panel (LogPanel) | 2026-03-29 | `SpecInfoWidget` (metadata), `LogPanel` (RichLog), `SpecDetailWidget` (container); `SpecState.log` field for accumulated event log lines; 8 new tests |
| 31d | CLI integration (`--tui`, `sp dashboard`) | 2026-03-29 | `--tui` flag on conduct/build; `_run_with_tui()` runs build in bg thread, Textual in fg; `sp dashboard` placeholder for SSE (task 32); requires `--no-agent` (agent subprocess can't share event bus) |
| 35 | Directory-based spec discovery (`{path}` pattern) | 2026-03-29 | `{path}` variable in `output_paths` includes subdirectory prefix; resolver leaf-name index for unambiguous dep resolution; `score/` reorganized with `subscribers/` subdir; `sp init` templates default to `{path}`; 4 arrangement + 4 resolver tests |
| HK-26 | Update score specs for event bus integration | 2026-03-29 | Added `events.spec.md`, `subscribers/ndjson.spec.md`, `subscribers/tui.spec.md`; updated `core.spec.md`, `compiler.spec.md`, `subscribers/build_state.spec.md`, `tui.spec.md`; score now 21 specs |
| HK-28 | Apply `specs_path` from arrangement in `sp validate` | 2026-03-29 | 4-line fix in `cmd_validate()` — resolves arrangement and sets `parser.src_dir` before validation; fixes "Spec file not found" for nested specs like `subscribers/build_state` |
| 37 | `sp diff` defaults to all-specs + daily CI drift check | 2026-03-30 | `sp diff` with no args checks all specs for drift (AST-based, no LLM); `--arrangement` flag for path resolution; `.github/workflows/spec-drift.yaml` runs daily + on PR; reference specs skipped; JSON array output in all-specs mode; 2 new tests |
| 38 | TUI startup feedback + error handling | 2026-03-29 | Pre-build events (build.init, build.specs.discovered, build.deps.resolved); preflight validation; build.error event; "Press q to exit" hints; Rich markup escaping; event bus threading to conductor; 10 new tests |
| 32 | SSE server (`sp conduct --serve`) | 2026-03-30 | `SSEServer` (stdlib `ThreadingHTTPServer`), `SSESubscriber`, `SSEHandler` (GET /events SSE stream, GET /status JSON snapshot, CORS); `--serve`/`--port`/`--keep-alive` flags on conduct/build; `sp dashboard` connects to SSE stream and displays in existing TUI; `score/subscribers/sse.spec.md`; 10 new tests; 555 total |
| 34 | `sp dashboard --replay` / `--follow` | 2026-03-30 | `--replay FILE` plays back NDJSON log at configurable `--speed` (default 10x, 0=instant); `--follow FILE` tails a growing log in real time (`tail -f` style); shared `_parse_ndjson_event`/`_parse_ndjson_timestamp` helpers; 16 new tests; 571 total |
| HK-27 | README refresh | 2026-03-31 | Badges, placeholder logo/demo, absolute URLs for PyPI rendering, trim to elevator pitch; detailed CLI/config/Docker moved to docs; `Documentation`/`Changelog` URLs in pyproject.toml |
| 36 | External dependency declaration (`requires:`) | 2026-03-31 | `requires:` PEP 508 list in spec frontmatter; `check_requirements()` on core; pre-flight fail-fast in `sp build`/`sp conduct --no-agent`; `sp doctor` reports missing; 14 new tests; 585 total |
| 39 | TUI file viewer (spec, code, tests) | 2026-03-31 | `s/c/t/l` keybindings on DashboardApp; `file_resolver` callback; `LogPanel.set_file_content()` with Rich Syntax; SSE `GET /files?path=` with path traversal guard; local + HTTP resolvers wired in CLI; 12 new tests; 597 total |

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
