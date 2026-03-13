# SpecSoloist — Task History

Append-only log of completed tasks, in order of completion.

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

## Housekeeping Tasks

| # | Task | Completed | Notes |
|---|------|-----------|-------|
| HK-01 | Consolidate IMPROVEMENTS + ROADMAP | 2026-02-18 | Trimmed §0 done-items from IMPROVEMENTS.md; fixed §0g (`_compile_single_spec` reference spec guard) and §0h (dep key normalised to `"from"` in core.py) |
| HK-02 | Small fixes | 2026-03-11 | Fixed `Optional[ArrangementEnvironment]` type hint; added comment on reference spec early return; moved dependency warning to `_resolve_arrangement()` |
| HK-03 | Remove `sp perform` | 2026-03-11 | Removed `cmd_perform`, `SpecConductor.perform/build_and_perform/_execute_step`, `PerformResult`, `StepResult` |
| HK-04 | Conductor writes `config_files` | 2026-03-13 | Always overwrite from arrangement (was skipping existing files); fixed typo in log message |
| HK-05 | Bundle spec docs vs parser | 2026-03-13 | Validator now accepts prose `##` headings in addition to `yaml:functions` blocks; all score specs now pass `sp validate` |
| HK-06 | Release v0.4.0 | 2026-03-13 | Released as v0.4.1 (README fix caught post-tag); publish workflow now auto-creates GitHub releases; release checklist added to CONTRIBUTING.md |

## Decisions

| File | Topic | Decision | Date |
|------|-------|----------|------|
| `decisions/01-sp-perform.md` | Keep / fix / remove `sp perform` | Option A — remove | 2026-03-11 |
