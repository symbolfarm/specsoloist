# SpecSoloist — Product & Technical Improvement Notes

> Brainstorm document. Not a roadmap — just thinking out loud about where this could go.
> Last updated: 2026-02-19
>
> **v0.3.2 (2026-02-19):** All of Section 0 shipped. Also fix 1c (pytest warnings).

---

## 0. Bugs / Immediately Fixable

### 0a. Docs reference `sp lift` — command is `sp respec`

`docs/reference/cli.md:15` lists `sp lift` which was the old name. The rename to `sp respec`
happened in Phase 4 but the docs weren't updated. Anyone reading the docs and trying `sp lift`
gets a confusing error.

### 0b. `validate_inputs()` is a placeholder

`src/specsoloist/schema.py:139` — `InterfaceSchema.validate_inputs()` has a body of `pass`.
This is called at runtime during `sp perform` to validate workflow step inputs.
Either implement it or raise `NotImplementedError` so failures are explicit rather than silent.

### 0c. Rich ANSI codes break CI/CD pipelines

Spinners and Rich markup render as garbage in GitHub Actions logs. A simple `--no-color`
flag (or auto-detection of `NO_COLOR` env var, which Rich supports natively) would make
`sp build` and `sp conduct` usable in scripted/CI contexts without visual noise.
Rich already has `Console(force_terminal=False)` for this — it's a one-liner.

### 0d. Missing docs for Arrangement, Docker sandbox, and agents

Three shipped features with zero user documentation:
- Arrangement system — no guide in docs/
- Docker sandboxing (`SPECSOLOIST_SANDBOX=true`) — mentioned nowhere in docs/
- Agent integration (`.claude/agents/`, `.gemini/agents/`) — no guide explaining how to use them

### 0e. `setup_commands` is parsed but never executed

`Arrangement.environment.setup_commands` is a first-class field in the schema — users can
write `setup_commands: [uv sync, npm install]` in their `arrangement.yaml` and it will
validate cleanly. But `runner.py` never reads it. The field silently does nothing.

This is worse than a missing feature: it's a documented field that promises behaviour the
code doesn't deliver. If a user's environment isn't already set up and they rely on
`setup_commands` to do it, compilation fails with an opaque error and they have no idea why.
Either execute them before running tests, or remove the field from the schema.

### 0f. `--auto-accept` uses `bypassPermissions` too broadly

`_run_agent_oneshot()` in `cli.py` passes `--permission-mode bypassPermissions` to Claude
whenever `--auto-accept` is set. This is appropriate for a deliberately supervised quine run,
but `--auto-accept` is exposed on every agent command: `sp compose`, `sp fix`, `sp respec`,
`sp conduct`. So `sp fix myspec --auto-accept` gives Claude Code unrestricted file-write
access across the entire filesystem with no confirmation prompts.

There was already one incident in Phase 6 where a soloist ignored its output path and wrote
to `src/` instead of `build/quine/` — it was caught only because someone noticed the git diff.
With `bypassPermissions` that write went through silently.

Safer alternatives:
- Scope `bypassPermissions` only to the quine path (when `is_quine` is true)
- Use `--allowedTools` or `--allowed-paths` to restrict Claude to specific directories
- Default `--auto-accept` to `--dangerously-skip-permissions` only where strictly necessary

---

## 1. Quick Wins (Low effort, high value)

### 1a. `sp doctor` — Pre-flight diagnostic command

The most common failure mode for new users is a missing API key or no agent CLI installed.
A single command that checks everything would eliminate this entire class of support issues:

```
sp doctor

  ✓ ANTHROPIC_API_KEY set
  ✗ GEMINI_API_KEY not set
  ✓ claude CLI found (Claude Code 1.2.3)
  ✗ gemini CLI not found
  ✓ Docker available (will use sandbox mode)
  ✓ uv available
  ✓ Python 3.12 (meets >=3.10 requirement)
  ✓ 4 specs found in src/
```

### 1b. `sp status` — Show compilation state of each spec

Right now there's no way to see at a glance what's compiled, stale, or broken:

```
sp status

  Spec            Compiled    Tests    Last Built
  ─────────────────────────────────────────────
  config          ✓           ✓        2h ago
  resolver        ✓           ✗ FAIL   2h ago
  parser          stale        -        4d ago
  my_new_spec     never        -        -
```

This would just read the build manifest. The data is already there.

### 1c. Fix pytest collection warnings

Two known warnings in the test suite:
- `TestResult` class in `runner.py` confuses pytest collection
- `TestRunner` class in `runner.py` has `__init__` so pytest skips it

Neither is harmful but they're noise in every test run. Rename them to `_TestResult` / `_TestRunner`
or use a `# noqa` hint if renaming breaks the spec.

### 1d. Fix the quine naming mismatch

The quine generates `speccomposer.py` / `specconductor.py` but the originals are
`composer.py` / `conductor.py`. Either:
- Rename the originals to match what the quine produces (quine is the authority), or
- Update the score specs to instruct soloists to use the shorter names

This is a correctness issue for quine validation — right now the quine passes but produces
differently-named files, which makes semantic comparison harder.

### 1e. `sp init` — Scaffold a new project

```bash
sp init my-project
```

Creates:
```
my-project/
  src/            # where specs go
  arrangement.yaml
  .gitignore
```

Currently new users have to discover the directory convention by reading docs.

### 1f. Remove `sp perform` or finish it

`sp perform` executes workflow specs but the workflow spec type is not well-documented
and `perform()` in `conductor.py` has placeholder-quality implementation (including
`validate_inputs()` which is a `pass` stub). It either needs a proper spec, integration
tests, and documentation — or it should be removed before it creates support burden.
Half-finished features erode trust in the tool.

### 1g. `--quiet` / `--json` output flags for scripting

No way to suppress Rich terminal output or get machine-readable results.
Downstream tooling (Makefiles, CI scripts, editor integrations) needs clean output.

```bash
sp build --quiet       # only emit errors
sp status --json       # JSON-formatted state for editor extensions to parse
```

Rich has `Console(quiet=True)` and the data structures are already Pydantic models,
so JSON serialization is trivial.

---

## 2. Developer Experience

### 2a. Watch mode — `sp watch`

```bash
sp watch              # recompile any spec that changes
sp watch resolver     # watch a specific spec
```

Uses `watchdog` or `inotify`. Detects when a `.spec.md` changes and kicks off
`sp compile <name>` automatically. Essential for rapid iteration.

### 2b. Streaming compilation output

Right now compilation shows a spinner and then dumps the result. When you're paying
attention to what the agent is doing, seeing the output stream in real time is much better.
This is more of a UX polish item but the difference in feel is significant.

### 2c. `sp diff <name>` — Show what changed

After recompiling a spec, show a diff of the generated code vs the previous version.
Helps developers understand what the agent actually changed and catch regressions
before they hit tests.

### 2d. Better `--no-agent` first-run experience

The direct LLM path (`--no-agent`) is the fallback for users without Claude/Gemini CLI.
Currently it requires an API key but gives poor feedback if the key is wrong or the
model call fails. The error paths should be as polished as the happy path.

---

## 3. The Quine & Score (Self-Hosting)

### 3a. `quine_diff` — Semantic fidelity tool (spec exists, not implemented)

`score/quine_diff.spec.md` already exists. The spec is written; it just needs a soloist
to compile it. This is a great opportunity for SpecSoloist to eat its own cooking —
run `sp compile quine_diff`, then use the output. A natural first task for Phase 8.

After running `sp conduct score/`, compare the quine output against the original source:
- Function signatures match?
- Public API is a superset of the spec?
- Test count is reasonable?
- Any functions in the original that aren't in the quine?

This turns the quine from a binary pass/fail into a useful diagnostic tool.

### 3b. Quine CI — nightly self-hosting run

Add a scheduled GitHub Actions workflow that runs `sp conduct score/` nightly and
reports pass rate. If the quine degrades (specs drift from source), you know immediately.
This is the canary for spec quality.

### 3c. Score freshness check

When you modify `src/specsoloist/foo.py`, the corresponding `score/foo.spec.md`
may now be out of date. A `sp score check` command (or a hook in `sp build`) could
compare spec-described API against actual implementation and warn about drift.

This is the inverse of what soloists do: instead of spec → code, it's code → "does the
spec still describe this?"

---

## 4. Spec Format & Language

### 4a. Spec inheritance / extension

```yaml
---
name: authenticated_api
extends: base_api
type: bundle
---
```

Allows specs to inherit common patterns (auth, pagination, error handling) from a base spec.
Reduces duplication in large projects where every endpoint needs the same error contract.

### 4b. Spec versioning

Track which version of a spec produced the current compiled artifact. When a spec changes,
flag any downstream specs that might need recompilation (the dependency graph already knows
what depends on what).

Format: a `version` field in frontmatter, stored in the manifest.

### 4c. Better bundle format for large modules

Bundles are great for small groups of functions but get unwieldy at 15+ items.
Consider a `section` divider within bundles, or a size heuristic that suggests splitting.

### 4d. `sp validate` quality checks (beyond structure)

Currently validates spec *structure* (required fields, valid type, etc.).
Add quality hints:
- "No examples provided — soloists compile better with concrete examples"
- "Spec has no schema block — interface contract is underspecified"
- "Description is very short — consider expanding edge cases"

These are warnings, not errors. But they'd significantly improve compile quality.

---

## 5. Multi-Language

### 5a. TypeScript / Node.js

The runner already has TypeScript configured (via `tsx`), but there's no working
`arrangement.example.ts.yaml`, no integration tests, and no documentation. The pieces
are there but the path is unvalidated. A concrete TypeScript example project (with a
working arrangement file and a passing test run) would prove the system works and make
it accessible to a huge audience.

Note: the runner uses `tsx` not `jest` — this should be explicitly documented since
most TypeScript developers expect Jest.

### 5b. Multi-language quine

Run `sp conduct score/` with `target_language: typescript` and get working TypeScript.
This would prove the spec format is truly language-agnostic and is a strong marketing
narrative.

### 5c. Go and Rust

Longer-term. Both languages benefit enormously from correct-by-construction patterns
(strong typing, explicit error handling). Specs would map very naturally to Go interfaces
and Rust traits. But start with TypeScript first.

---

## 6. Agent & LLM Providers

### 6a. OpenAI / GPT provider

The `LLMProvider` abstraction exists. Adding OpenAI would make SpecSoloist accessible
to a much larger audience (many developers have OpenAI credits but not Anthropic/Google).

### 6b. Local LLMs via Ollama

`ollama run llama3` as a provider for:
- Privacy-sensitive projects (no data leaves the machine)
- Cost-conscious users
- Offline use

Quality will be lower but for simple specs it may be sufficient.

### 6c. Provider cost/token tracking

Show token usage after each compilation:
```
Compiled resolver in 12s  (2,847 tokens, est. $0.003)
```

Especially useful for `sp conduct` runs where you're compiling 15 specs in parallel
and costs add up. Log totals to the manifest.

### 6d. Model pinning in arrangement files

```yaml
model: claude-haiku-4-5-20251001  # fast/cheap for leaf specs
```

Combined with cost tracking, this lets teams make deliberate cost/quality tradeoffs
per-spec without using global config.

---

## 7. Testing & Quality

### 7a. Spec coverage metric

Analogous to test coverage: what % of the exported symbols in a compiled module
are described in its spec? Run via static analysis of the generated code.

```
sp coverage

  parser.py:       87% spec coverage (3 functions undocumented)
  resolver.py:    100% spec coverage
  compiler.py:     61% spec coverage  ← needs attention
```

### 7b. Snapshot testing for generated code

After successful compilation, store a hash of the generated code. On recompilation,
if the hash changes significantly (not just whitespace), prompt the developer to review
the diff before accepting. Prevents silent regressions where a spec is subtly mis-compiled.

### 7c. `sp test --all` with summary reporting

Run tests for every compiled spec and show a dashboard. Currently you'd have to
loop `sp test <name>` for each spec. A single command with a nice table output
would make quality checking feel much lighter.

---

## 8. Infrastructure & Distribution

### 8a. Homebrew formula

```bash
brew install specsoloist
```

Reaches developers who don't use pip. Homebrew is the first-class installation path
for many macOS/Linux developers for CLI tools. Low effort to maintain once set up.

### 8b. Official Docker image

```bash
docker run ghcr.io/symbolfarm/specsoloist sp conduct src/
```

Useful for CI pipelines where you don't want to install Python. The sandbox Dockerfile
already exists — a wrapper image for the CLI itself is a small step from there.

### 8c. `.specsoloist/` project directory

Currently build artifacts are scattered:
- `.specular-manifest.json` in project root
- `.spechestra/traces/` for workflow traces
- `build/quine/` for quine output

Consolidating under `.specsoloist/` makes the tool feel more intentional:
```
.specsoloist/
  manifest.json
  build/
  traces/
  cache/
```

A minor cleanup but it signals that the tool is mature and respects your project root.

### 8d. Windows support audit

Is `sp` tested on Windows? The path handling (`os.path.join`, etc.) should be fine,
but runner subprocess commands may not be. Worth a CI matrix run.

---

## 9. Collaboration & Ecosystem

### 9a. VS Code extension

The highest-leverage distribution play. An extension could provide:
- Syntax highlighting for `.spec.md` files
- Preview pane showing compiled code alongside spec
- "Compile Spec" code action
- Inline errors from `sp validate`
- Status bar showing compilation state

This lowers the barrier to entry significantly — you get the full experience without
knowing any CLI commands.

### 9b. Spec registry (longer term)

An npm-like registry where developers share reusable specs:
```bash
sp install specsoloist/rest-api-patterns
sp install specsoloist/auth-patterns
```

Shared specs for common patterns (pagination, authentication, error handling, CRUD).
This creates a community around the format and accelerates adoption.

### 9c. GitHub App / PR checks

A GitHub App that:
- Runs `sp validate` on changed specs in PRs
- Posts a comment if specs are structurally invalid
- (Optional) Runs `sp compile` in a sandbox and posts the diff

Makes spec quality a first-class part of code review without requiring team members
to run the tool locally.

### 9d. Example project gallery

A `specsoloist/examples` repo with 3-5 complete projects built with SpecSoloist:
- A REST API (Python + FastAPI)
- A CLI tool
- A data pipeline
- A TypeScript web service (once TS support is solid)

Nothing convinces developers like seeing a real working thing they can clone.

---

## 10. Strategic / Philosophical

### 10a. The "live spec" concept

Right now specs are compiled once. What if a running service could reflect on its own
spec at runtime? Error messages that reference the spec. Auto-generated API docs
that are always in sync because they come from the spec, not the code.

This is a bigger idea but it's the natural endpoint of "specs are the source of truth."

### 10b. Spec-first API design

Integration with OpenAPI/Swagger: convert an OpenAPI spec to SpecSoloist format,
then compile to a server implementation. Or vice versa — generate OpenAPI from
SpecSoloist specs. This bridges spec-driven development and API-first development.

### 10c. The "upgrade" workflow

When you upgrade a library (say, from FastAPI 0.100 to 0.115), the generated code
may be outdated. `sp upgrade` could:
1. Note which specs produce code using the old API
2. Recompile those specs with the new library version in the arrangement
3. Show the diff

This makes dependency upgrades much less painful in large spec-driven projects.

### 10d. Spec migration format versioning

The spec format itself may need to evolve. Adding a `spec_version: 1.0` field to
frontmatter now means we can write migrations later (like Rails migrations, but for
specs). Without this, future format changes will break existing spec files silently.

---

## Summary: What to Do Next

Rough priority ordering given current state of the project:

| Priority | Item | Why |
|----------|------|-----|
| ✅ done | Fix `sp lift` → `sp respec` in docs (0a) | Users reading docs hit a broken command |
| ✅ done | Execute `setup_commands` or remove the field (0e) | Silently broken contract |
| ✅ done | Scope `bypassPermissions` to quine only (0f) | Security/safety; one incident already |
| ✅ done | `NO_COLOR` / Rich CI fix (0c) | Spinners render as garbage in GitHub Actions |
| ✅ done | Fix pytest warnings in runner.py (1c) | Noise in every test run |
| ✅ done | `validate_inputs()` raises `NotImplementedError` (0b) | Silent broken promise |
| ✅ done | Write Arrangement + agents docs (0d) | Two shipped features with zero docs |
| ★★★ | Fix quine naming mismatch (1d) | Correctness; blocks quine_diff |
| ★★★ | `sp doctor` (1a) | #1 new-user pain point |
| ★★★ | TypeScript support end-to-end + validated example (5a) | Biggest audience expansion |
| ★★☆ | `sp status` (1b) | High utility, manifest data already exists |
| ★★☆ | `sp validate` quality hints (4d) | Improves compile quality significantly |
| ★★☆ | `quine_diff` — compile from existing spec (3a) | Spec already written, just needs `sp compile` |
| ★★☆ | Fix or remove `sp perform` (1f) | Placeholder code in production |
| ★★☆ | `--quiet` / `--json` output flags (1g) | Makes tool scriptable |
| ★★☆ | OpenAI provider (6a) | Unlocks a large existing user base |
| ★★☆ | Homebrew formula (8a) | Low effort, broad reach |
| ★☆☆ | Watch mode (2a) | Convenience; needs watchdog dep |
| ★☆☆ | VS Code extension (9a) | High impact but significant effort |
| ★☆☆ | Spec registry (9b) | Requires infrastructure; too early |
| ★☆☆ | Multi-language quine (5b) | Great story, not urgent |
