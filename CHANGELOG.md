# Changelog

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
