# Changelog

## [Unreleased]

## [0.4.1] - 2026-03-13

### Fixed
- `sp perform` removed from README (command was removed in HK-03)

## [0.4.0] - 2026-03-13

### Added
- `type: reference` spec type — documents third-party APIs without generating code; body injected into dependent soloists' prompts; `# Verification` section compiled to a test file (task 04)
- `ArrangementEnvironment.dependencies: dict[str, str]` — version pins injected as "Dependency Versions" table in soloist prompts; `sp validate --arrangement` warns if no install command (task 05)
- `examples/nextjs_ai_chat/` — Next.js App Router + Vercel AI SDK chat app validated end-to-end; 22 tests passing; `vercel_ai_interface.spec.md` reference spec documents the v3 API (task 07)
- `examples/fasthtml_app/` refactored into three-spec decomposition (layout/routes/state); added Pico CSS, empty state, input reset, styled delete button (task 06)

### Changed
- `fasthtml_interface.spec.md` migrated from `type: bundle` to `type: reference` (task 04)

### Fixed
- `Optional[ArrangementEnvironment]` type hint corrected — field is never `None` (HK-02)
- Arrangement dependency warning moved to `_resolve_arrangement()` so it fires on all commands, not just `sp validate` (HK-02)
- `_compile_single_spec()` reference spec early return now has explanatory comment (HK-02)
- `_provision_environment()` now always writes config_files from the arrangement (was skipping if file existed); fixed typo in log message (HK-04)
- Bundle spec validator now accepts prose-style `##` headings as well as `yaml:functions` blocks — all score specs now pass `sp validate` (HK-05)

### Removed
- `sp perform` command and `SpecConductor.perform/build_and_perform/_execute_step` — placeholder-quality implementation removed (HK-03, decision 01)

## [0.3.2] - 2026-02-18

### Fixed
- `setup_commands` in Arrangement now executed before running tests (was silently ignored)
- `validate_inputs()` now raises `NotImplementedError` instead of silently doing nothing
- `--permission-mode bypassPermissions` scoped to quine runs only (was applied to all `--auto-accept` commands)
- `NO_COLOR` env var now respected by Rich console output
- Pytest collection warnings for `TestResult`/`TestRunner` classes suppressed via `__test__ = False`
- `sp lift` corrected to `sp respec` in CLI reference docs
- `docs/guide/workflow.md` updated from old "Specular"/"specular" naming

### Added
- `docs/guide/arrangement.md` — guide for the Arrangement system (previously undocumented)
- `docs/guide/agents.md` — guide for native subagents (previously undocumented)
- `sp test` now auto-discovers `arrangement.yaml` and respects its `setup_commands`

## [0.3.1] - 2026-02-18

### Fixed
- Updated keywords (removed `mcp`, added `agents`, `claude`, `gemini`)
- Removed misleading "(used with --no-agent)" from `sp conduct --arrangement` help text

## [0.3.0] - 2026-02-18

### Added
- Agent-first commands (`compose`, `conduct`, `fix`, `respec`) — delegate to Claude/Gemini CLI agents by default; `--no-agent` for direct LLM fallback
- Native subagent definitions (`.claude/agents/`, `.gemini/agents/`) for Claude Code and Gemini CLI
- The Quine: `sp conduct score/` regenerates full source with 563 generated tests passing
- Arrangement system: `--arrangement` flag on `compile`/`build`/`conduct`, auto-discovery of `arrangement.yaml`, `arrangement.example.yaml`
- Sandboxed execution via Docker (`SPECSOLOIST_SANDBOX=true`)
- `sp fix` command with agent-first self-healing loop
- Integration tests for full arrangement pipeline (`tests/test_arrangement.py`)

### Changed
- Specs are now requirements-oriented (define what, not how)
- Aligned composer/conductor naming between `score/` and `src/`
- Hardened quine prompts to prevent accidental source overwrites
- `_discover_arrangement` now logs a warning instead of silently swallowing parse errors
- Removed MCP server (`specsoloist-mcp`) — superseded by agent-first CLI

### Fixed
- `_conduct_with_llm` referenced nonexistent `core.project_dir` — now uses `core.root_dir`

### Dependencies
- Removed: `mcp` (MCP server dropped)
- `cryptography` bumped 46.0.4 → 46.0.5

## [0.2.0] - 2026-02-04

Initial spechestra integration: `SpecComposer`, `SpecConductor`, multi-spec builds, incremental builds, parallel compilation, Rich terminal UI.

## [0.1.0] - 2025-xx-xx

Initial release: spec parsing, LLM compilation, test generation, self-healing fix loop, MCP server.
