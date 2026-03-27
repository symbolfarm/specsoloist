# Changelog

## [Unreleased]

## [0.7.0] - 2026-xx-xx

### Added
- `specs_path` field in `arrangement.yaml` — configures spec discovery directory
  (default: `src/`); `sp list`, `sp status`, `sp graph` now load the arrangement
  and use this field (HK-15)
- `--arrangement` flag on `sp list`, `sp status`, `sp graph` — explicit arrangement
  override for discovery commands (HK-15)
- `sp schema [topic]` — prints annotated JSON/text schema for `arrangement.yaml`;
  topic filter (e.g. `sp schema output_paths`) returns just that section (task 22)
- `sp help <topic>` — topic-based help with bundled spec content; `sp help arrangement`,
  `sp help spec-format`, `sp help conduct`, `sp help overrides`, `sp help specs-path`
  work from any PyPI install (task 23)
- `sp install-skills` now embeds a `<!-- sp-version: X.Y.Z -->` marker; `sp doctor`
  warns when installed skills are from an older package version (task 24)
- `--version` / `-V` flag — prints `specsoloist X.Y.Z` and exits 0 (HK-17)

### Changed
- `sp init` templates now include commented examples for `specs_path`, `output_paths.overrides`,
  `model`, and `env_vars` — all optional fields visible on first init (task 24)
- Skill and agent files updated with "Key Arrangement Fields" section covering
  `specs_path` and `output_paths.overrides` (task 24)

### Fixed
- `sp validate` no longer warns "No test scenarios found" for specs that use
  `yaml:test_scenarios` blocks; warning message now includes an inline example (HK-17)
- `output_paths.overrides` unit tests added; YAML round-trip confirmed (HK-16)
- Publish workflow reverted to trusted publishing — `PYPI_API_TOKEN` no longer required (HK-14)

## [0.5.0] - 2026-03-19

### Added
- `sp vibe` — single-command compose→conduct pipeline; reads a `.md` brief or plain string; `--pause-for-review` to inspect specs before building; `--resume` for addendum mode (task 19)
- `sp diff <name>` — spec-vs-code drift detection; compares spec-declared symbols against compiled Python using AST; reports MISSING/UNDOCUMENTED/TEST_GAP issues; `--json` flag (task 15)
- `sp init --template` — arrangement templates for `python-fasthtml`, `nextjs-vitest`, `nextjs-playwright`; `sp init --list-templates` to list all (task 08)
- `sp conduct --resume` / `--force` — incremental rebuilds; skips specs whose output already exists unless forced (task 10)
- `--quiet` global flag — silences Rich output; `--json` per-subcommand flag on `status`/`compile`/`validate` emits structured JSON (task 16)
- `env_vars` field in Arrangement — compiler injects "Environment Variables" section into prompts; `sp doctor --arrangement` warns on unset required vars (task 11)
- `model` field in Arrangement — optional model pinning with CLI > arrangement > env precedence (task 17)
- Pydantic AI provider — supports OpenAI, OpenRouter, and Ollama backends via `pydantic-ai-slim` (task 20)
- Nested session detection — warns when `sp conduct` is run inside an active Claude Code or Gemini CLI session (task 12)
- Weekly quine CI (`.github/workflows/quine.yaml`) — scheduled + `workflow_dispatch`; build artifact retained 30 days (task 18)
- Google-style docstrings across all modules; mkdocstrings API reference live at the docs site (HK-10)
- `docs/incremental-adoption.md` — 6-step guide for adding SpecSoloist to an existing project (task 13)
- `docs/database-patterns.md` — persistence patterns for FastHTML (fastlite) and Next.js (Prisma) (task 14)
- `docs/e2e-testing.md` — E2E testing guide with Playwright; `data-testid` spec contract (task 09)
- `score/spec_diff.spec.md` — spec for the drift-detection module; closes last quine hole (task 22)

### Changed
- Quine refreshed — `sp conduct score/` now generates 320 tests; score specs updated to cover all Phase 8/9 features (task 21)
- `score/` cleaned up — removed `arrangement.spec.md`, `specsoloist.spec.md`, `spechestra.spec.md` (non-code-generating overview specs) (HK-13)

### Fixed
- Hardcoded repo paths in tests replaced with `Path(__file__).parent.parent` — tests now pass when run from any directory (HK-09)
- `score/runner.spec.md` — added constraint preventing pytest `TestResult`/`TestRunner` collection warnings in quine output (HK-12)

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
