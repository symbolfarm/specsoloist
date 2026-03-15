# SpecSoloist Roadmap

Completed phases are summarised in `tasks/HISTORY.md`. Ideas and future directions in `IDEAS.md`.

---

## Phases 1–7: Foundation (Completed)

Core framework, multi-spec builds, CLI, Spechestra (composer/conductor), agent-first commands,
native subagents, the Quine, arrangement system. See `tasks/HISTORY.md` for details.

## Phase 8: Web-Dev Readiness (Completed 2026-03-14)

`type: reference` spec type, arrangement templates (`sp init --template`), FastHTML + Next.js
examples validated end-to-end, E2E testing pattern, `sp conduct --resume`/`--force`,
`env_vars` in arrangements, nested session detection, incremental adoption guide, database
persistence patterns. 270 tests passing.

## Phase 9: Distribution & Developer Experience (Planned)

Goal: make SpecSoloist production-grade for real commercial web applications.

- [ ] **Fix quine naming mismatch** — score specs use `composer.py`/`conductor.py` consistently
- [ ] **`sp vibe`** — single-command pipeline: compose → pause-for-review → conduct → test
- [ ] **`sp diff`** — generalised spec vs code drift detection; run-over-run regression
- [ ] **Auth patterns** — session auth (FastHTML) + JWT (Next.js) reference specs
- [ ] **Pydantic AI provider** — replace hand-rolled `LLMProvider`; get most providers free; path to CLI independence
- [ ] **`--quiet` / `--json` output flags** — scripting and CI-friendly output
- [ ] **Model pinning in arrangements** — `model:` field; cost/quality control per-spec
- [ ] **Structured build events** — JSON event log; foundation for dashboard and CI integration
- [ ] **Quine CI** — scheduled GitHub Actions workflow; score freshness check
- [ ] **Watch mode `sp watch`** — recompile on spec file change
- [ ] **`.specsoloist/` directory** — consolidate manifest, build artifacts, traces

## Phase 10: Ecosystem (Future)

- [ ] **Live dashboard** — localhost SSE/WebSocket; browser UI for `sp vibe` review flow
- [ ] **VS Code extension** — syntax highlighting, inline validation, compile action
- [ ] **Docker image on GHCR** — try the quine without installing Python
- [ ] **Multi-language quine** — TypeScript, then Go/Rust; prove language-agnosticism
- [ ] **Commercial layer** — hosted dashboard, team cost tracking, shared spec library

## Maintenance

- Keep `uv run python -m pytest tests/` green (270 tests)
- Keep `uv run ruff check src/` clean
- Keep score specs in sync with implementation (`sp respec` on changed modules)
- Release checklist in `CONTRIBUTING.md`
