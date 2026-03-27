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
persistence patterns.

## Phase 9: Distribution & Developer Experience (Completed 2026-03-27)

`sp diff`, `sp vibe`, `sp schema`, `sp help`, Pydantic AI provider, model pinning,
`--quiet`/`--json` flags, quine CI, `specs_path` and `output_paths.overrides` in arrangements,
richer `sp init` templates, skill version staleness detection.

## Phase 10: Full Project Reproducibility (Current)

Goal: a `sp conduct` run can reproduce *all* project artifacts, not just compiled code.

- [ ] **`static` artifacts** — declare files/directories to copy verbatim into the output; closes the reproducibility gap for docs, templates, scripts, and help files

## Phase 11: Ecosystem (Future)

- [ ] **Live dashboard** — localhost SSE/WebSocket; browser UI for `sp vibe` review flow
- [ ] **VS Code extension** — syntax highlighting, inline validation, compile action
- [ ] **Docker image on GHCR** — try the quine without installing Python
- [ ] **Multi-language quine** — TypeScript, then Go/Rust; prove language-agnosticism
- [ ] **Commercial layer** — hosted dashboard, team cost tracking, shared spec library

## Maintenance

- Keep `uv run python -m pytest tests/` green
- Keep `uv run ruff check src/` clean
- Keep score specs in sync with implementation (`sp respec` on changed modules)
- Release checklist in `CONTRIBUTING.md`
