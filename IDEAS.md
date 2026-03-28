# SpecSoloist — Ideas & Future Directions

> Brainstorm document. Not a roadmap — just thinking out loud about where this could go.
> Last updated: 2026-03-19
>
> Consolidated from IMPROVEMENTS.md and PROPOSALS.md.
> Actionable tasks live in `tasks/README.md`. Completed work in `tasks/HISTORY.md`.

---

## 1. Full Autonomous Workflow ("sp vibe")

The primary use-case SpecSoloist is moving towards: give a high-level natural language brief,
get a working application. The pipeline already exists in pieces — this is about stitching
them into a single command with good UX.

### 1a. `sp vibe` — single-command pipeline

```bash
sp vibe "A Tamagotchi-style pet game with a local LLM personality"
sp vibe brief.md --template python-fasthtml --pause-for-review
```

Internally: `sp compose` → optional pause → `sp conduct` → test report → fix loop.

**Pause modes:**
- `--pause-for-review` — stop after specs are written; user edits specs, then presses enter to continue
- `--interactive` — pause after each spec is written for incremental approval
- `--auto` — no pauses (current default behaviour, just compose then conduct)

The pause is a simple "press enter to continue" at the terminal for now. A dashboard
(see §3) is the eventual UX for this.

### 1b. Brief file format

A structured Markdown prompt file that `sp vibe` accepts:

```markdown
# Project Brief

## What
A Tamagotchi-style pet game where the pet has a persistent mood and talks via a local LLM.

## Stack
FastHTML + fastlite + Ollama

## Must Have
- Pet state: hunger, mood, energy, last interaction time
- Mood decays over time without interaction
- Pet speaks using Ollama (llama3)
- Persistent state across browser sessions

## Nice to Have
- Animations (CSS)
- Multiple pets
```

The brief file becomes the input to `sp compose`, with the stack hints informing which
arrangement template to use.

---

## 2. Spec Quality & Drift Detection

### 2a. `sp diff` — spec vs code drift

```bash
sp diff parser           # compare spec to compiled implementation
sp diff src/ score/      # compare all modules
sp diff --runs 2         # diff last two quine runs (regression detection)
```

For each spec, report:
- Symbols in spec but missing from code
- Symbols in code not documented in spec
- Behaviour described in spec with no corresponding test

This is a generalisation of the quine_diff concept — useful for any project, not just
the quine. See `score/build_diff.spec.md` for the existing spec (needs `sp compile`).

### 2b. Run archives & regression detection

When `sp conduct` completes, archive the output with a timestamp:

```
build/
  runs/
    2026-03-15T14:30:00/
      run_meta.json    # arrangement, test results, model, duration, token cost
      src/...
      tests/...
  quine/               # symlink to latest run
```

`sp diff --runs 2` then compares the last two runs. A consistently green diff means
the spec is stable and generation is deterministic. High variance → spec needs tightening.

### 2c. Flakiness score

Over N runs of the same spec, measure how often the generated code is identical.
High-flakiness specs have ambiguous requirements. Surface via `sp diff --flakiness`.

### 2d. Spec coverage

```bash
sp coverage src/specsoloist/core.py score/core.spec.md
# Coverage: 12/15 functions (80%)
# Missing: _load_manifest, get_build_status, delete_spec
```

What fraction of the exported symbols in a compiled module are described in its spec?

### 2e. Score freshness check

When `src/specsoloist/foo.py` changes, `score/foo.spec.md` may be out of date.
A `sp score check` command (or hook in `sp build`) compares spec-described API against
actual implementation and warns about drift. Inverse of what soloists do.

---

## 3. Observability & Dashboard

The key architectural insight: **structured events are the product**. The dashboard,
CI integration, cost tracking, and commercial tier are all consumers of the same event stream.

### 3a. Structured build log (foundation)

Emit structured JSON events during `sp conduct`:

```json
{"event": "spec_start",    "spec": "config", "level": 0, "ts": "..."}
{"event": "spec_complete", "spec": "config", "tests": 46, "pass": true, "duration": 42.3, "tokens": 1840}
{"event": "build_complete","total": 13, "passed": 13, "failed": 0, "duration": 780.1}
```

Written to `--log-file` or stdout with `--json`. Tools like Datadog, Grafana, or
a simple `jq` pipeline can then analyse build performance over time.

### 3b. Localhost SSE/WebSocket endpoint

`sp conduct --serve` starts a lightweight local server that pushes events as SSE or
WebSocket messages. A browser dashboard (`sp dashboard`) connects and shows live progress.

This is the foundation for the `sp vibe` review UX — the pause-for-review could be
handled as a message to the dashboard rather than blocking the terminal.

### 3c. Commercial dashboard layer

The events API (§3a/3b) is the natural commercial product:
- Self-hosted: open-source event emitter + open-source dashboard
- Cloud tier: hosted dashboard with team features (shared build history, cost tracking,
  spec library, PR integration)

Other commercial possibilities:
- **GitHub App**: posts spec validation + diff summary on PRs
- **Cost reports**: token usage per spec, per run, per team member
- **Spec library**: shared reference specs across projects (like npm for specs)

### 3d. Token usage tracking

Track input/output tokens per spec compilation. Store in run archive and manifest.
Answers: which specs are most expensive? Which need many retries (multiplying cost)?

---

## 4. LLM Provider Independence (Pydantic AI)

Replace the hand-rolled `LLMProvider` abstraction with Pydantic AI:
- Most providers (OpenAI, Gemini, Anthropic, Ollama, Mistral) for free
- Structured outputs via Pydantic models rather than prompt-parsed JSON
- Path to writing custom agents in pure Python — not dependent on Claude Code or Gemini CLI
- `--no-agent` mode becomes much more capable

This is the most important architectural change for long-term independence from
third-party CLI tools. The `LLMProvider` abstraction already exists; it's a bounded
replacement rather than a rewrite.

**Ollama support** (via Pydantic AI) also enables the TamaTalky use case — fully local,
zero API cost, privacy-preserving.

---

## 5. Multi-Language

### 5a. TypeScript quine

Run `sp conduct score/` with `arrangements/quine-typescript.yaml` and produce
working TypeScript. Proves specs are truly language-agnostic.

```yaml
target_language: typescript
output_paths:
  implementation: build/quine-ts/src/{name}.ts
  tests: build/quine-ts/tests/{name}.test.ts
environment:
  tools: [node, npm, tsx, vitest]
  setup_commands: [npm install]
```

Deliverable: `QUINE_RESULTS_TS.md` parallel to `QUINE_RESULTS.md`.

### 5b. TypeScript port + NPM distribution

A full TypeScript port of the `sp` CLI published to NPM. Opens up the Node ecosystem
without requiring Python. Maintenance burden is real — any new feature must ship twice
until one implementation is deprecated — so this is a Phase 11+ project, not Phase 10.

`npm info specsoloist` — reserve the name with a placeholder package before someone
else does. The placeholder README should link to the PyPI package and note the TS port
is planned.

The TypeScript quine (§5a) is a prerequisite: if the score can't generate working
TypeScript, the port isn't ready.

### 5c. Arrangement-level reference spec abstraction

Reference specs are necessarily language-specific (import paths, API shapes, package
names are all stack-tied). This conflicts with the language-agnostic spec goal.

**The idea:** specs declare abstract dependency names; the arrangement resolves them to
concrete reference specs for the target stack.

```
project/
  specs/
    state.spec.md       # depends on: db_interface  (abstract name)
    routes.spec.md      # depends on: ui_framework, db_interface  (abstract)
  arrangements/
    python-fasthtml/
      arrangement.yaml  # maps ui_framework → ./ui_framework.spec.md
      ui_framework.spec.md   # FastHTML reference spec
      db_interface.spec.md   # fastlite reference spec
    nextjs/
      arrangement.yaml  # maps ui_framework → ./ui_framework.spec.md
      ui_framework.spec.md   # React/Next.js reference spec
      db_interface.spec.md   # Prisma reference spec
```

The arrangement adds a `reference_specs` mapping block:
```yaml
reference_specs:
  ui_framework: ui_framework.spec.md   # relative to arrangements/ subdir
  db_interface: db_interface.spec.md
```

The resolver maps abstract dependency names to concrete reference spec paths at build
time. Specs themselves stay language-agnostic. Swapping stacks = pointing to a different
arrangements/ subdirectory.

**Implementation scope:** Arrangement schema change + resolver lookup extension. Spec
format unchanged. Validate by building the same `state.spec.md` against two different
arrangements and confirming both compile correctly.

**When to build:** After at least two real multi-stack projects demonstrate where the
natural seams are. Don't design the abstraction in the abstract.

### 5d. Go and Rust

Longer-term. Both languages benefit from correct-by-construction patterns. Specs map
naturally to Go interfaces and Rust traits.

### 5c. Cross-language diff

Once two language runs exist, `sp diff build/quine-py/ build/quine-ts/ --vs-source`
surfaces which functions translated cleanly vs needed language-specific workarounds.

---

## 6. CI/CD & Quine Automation

### 6a. Quine CI — scheduled GitHub Actions workflow

Run `sp conduct score/` on a schedule (weekly rather than nightly to manage costs).
Report pass rate and diff vs source. Fail if any spec regresses.

**Cost management:**
- Use `--model haiku` in CI (cheapest capable model)
- Scope the API key to a monthly spend cap at provider level
- Use `--resume` to skip specs that haven't changed
- Weekly schedule (not nightly) keeps costs to ~$2-8/month at haiku rates

**Key security:** GitHub encrypted secrets keep the API key safe. The workflow runs
only on `schedule:`, not on `push:` or `pull_request:`, preventing external forks
from triggering it.

### 6b. quine_diff CI step

After `sp conduct score/`, run `sp diff src/ build/quine/src/ --report diff.json`
and post the summary as a PR comment. Makes spec changes reviewable — you see how
a spec edit affects generated code.

### 6c. `conduct_quine.sh` convenience script

A `scripts/conduct_quine.sh` wrapper that runs the quine with the right flags and
arrangement, so `sp conduct score/` is fully reproducible without remembering flags.

---

## 7. Developer Experience

### 7a. `--quiet` / `--json` output flags

```bash
sp build --quiet       # only emit errors
sp status --json       # JSON-formatted state for editor extensions
```

Rich has `Console(quiet=True)`. Data structures are already Pydantic models.
Makes SpecSoloist scriptable from Makefiles, CI, and editor integrations.

### 7b. Model pinning in arrangements

```yaml
model: claude-haiku-4-5-20251001   # fast/cheap for leaf specs
```

Combined with token tracking, enables deliberate cost/quality tradeoffs per-spec.

### 7c. `sp watch` — live recompilation

```bash
sp watch              # recompile any spec that changes
sp watch resolver     # watch a specific spec
```

Uses `watchdog`. Detects `.spec.md` changes and kicks off `sp compile` automatically.
Essential for rapid iteration when editing specs.

### 7d. `.specsoloist/` directory consolidation

Currently build artifacts are scattered. Consolidate:

```
.specsoloist/
  manifest.json      # was .specsoloist-manifest.json
  build/             # was build/quine/
  traces/            # was .spechestra/traces/
  runs/              # new: archived build runs
```

A minor cleanup but it signals maturity and respects the project root.

### 7e. Retry budget configuration

Soloists currently have up to 3 retries on test failure. Make this configurable
in arrangement files. Failed soloists should produce a `*.failed.md` with the last
error, enabling `sp fix` to pick up where they left off.

### 7f. Per-soloist timeout

Configurable per-soloist timeout (default: 5 minutes) that marks the spec as failed
and continues the build rather than blocking indefinitely.

### 7g. `sp draft` — low-commitment spec-to-code preview

```bash
sp draft score/tui.spec.md             # generate code to stdout, don't write to output path
sp draft score/tui.spec.md -o /tmp     # write to temp directory for review
sp draft score/tui.spec.md --model haiku  # use a cheap model for fast iteration
```

The spec-first workflow has a gap: after writing a spec, the only way to see what a
soloist produces is `sp compile`, which writes to the real output path. `sp draft`
would generate code without side effects — letting you iterate on the spec before
committing to the output.

**Model considerations:** drafting benefits from a lightweight/fast model since you're
iterating, not producing final output. Pydantic AI's provider abstraction supports
OpenRouter and others, so cheap models (Haiku, local Ollama) could be used for drafting
while expensive models handle final compilation. Need to verify that provider selection
is fine-grained enough to support this (per-command model override vs arrangement-level).

**Inside Claude Code:** this is especially valuable when you can't shell out to
`sp compile` (subprocess restriction). An `sp draft --dry-run` that just emits the
prompt would let the agent itself do the generation step.

### 7h. Cross-spec type validation

Specs declare dependencies and reference types/functions from other specs. Currently
`sp validate` checks structure but not cross-references — if `tui.spec.md` references
`BuildState` from `build_state.spec.md`, nothing verifies that `BuildState` actually
exists in the dependency.

**Implementation sketch:**

1. During validation, extract "defined symbols" from each spec — class names from
   `## TypeName` headings, function names from `## func_name()` headings
2. Extract "referenced symbols" by scanning prose for names that match defined symbols
   in declared dependencies
3. Report unresolved references (symbol used but not found in any dependency)

The `yaml:schema` blocks would make this more reliable (structured type definitions),
but even heuristic extraction from Markdown headings would catch most renames and
deletions. Could surface as `sp validate --check-refs` or a flag on `sp diff`.

**Open questions:**
- How to distinguish a prose mention of a type from an actual code dependency?
- Should this be a warning (likely references) or an error (definite references)?
- Could the `# Verification` snippets provide ground truth — if an import in a
  verification block fails, that's a definitive broken reference.

### 7i. Environment readiness for external dependencies

Specs can depend on external packages (e.g., `textual`, `fasthtml`). Currently there's
no structured way to declare this — constraints mention it in prose, but nothing machine-
readable tells `sp doctor` or `sp conduct` that a package needs to be installed.

**Relationship to reference specs:** Reference specs already document external APIs for
soloist accuracy. They could grow a `package:` frontmatter field that serves double duty:

```yaml
---
name: textual_interface
type: reference
package: textual>=1.0
---
```

This enables:
1. `sp doctor` checks the package is installed (and version satisfies the constraint)
2. `sp conduct` could auto-install missing packages (or warn before proceeding)
3. The reference spec body still provides API docs to soloists — same as today

**Alternative: arrangement-level declaration.** Instead of (or in addition to) the
reference spec field, arrangements could list required packages:

```yaml
dependencies:
  - textual>=1.0
  - python-fasthtml>=0.12
```

This is simpler but decoupled from the spec that actually needs the package. The
reference spec approach keeps the "why this package" and "what version" together.

**Open questions:**
- Should `sp conduct` auto-install, or just fail fast with a clear message?
- How does this interact with arrangement `environment.tools` (which is for CLIs, not packages)?
- For the quine, external deps are already in `pyproject.toml` — is this only useful for
  fresh project bootstrapping?

---

## 8. Auth & Production Patterns

### 8a. Auth reference spec

Document session-based auth (FastHTML) and JWT auth (Next.js) as reference specs.
This is the most common gap when building real web apps with SpecSoloist.

### 8b. Multi-page shared state pattern

How session/user state flows across routes in a multi-spec app. Needs a documented
pattern + example.

### 8c. OpenAPI integration

Convert an OpenAPI spec to SpecSoloist format, or generate OpenAPI from SpecSoloist
specs. Bridges spec-driven development and API-first development.

### 8d. The "upgrade" workflow

When upgrading a library (FastAPI 0.100 → 0.115), `sp upgrade` could:
1. Note which specs produce code using the old API
2. Recompile those specs with the new version in the arrangement
3. Show the diff

Makes dependency upgrades less painful in large spec-driven projects.

---

## 9. Distribution & Ecosystem

### 9a. VS Code extension

- Syntax highlighting for `.spec.md`
- "Compile Spec" code action
- Inline errors from `sp validate`
- Status bar showing compilation state
- Preview pane showing compiled code alongside spec

### 9b. Docker image on GHCR

```bash
docker run --rm -v $(pwd):/workspace ghcr.io/symbolfarm/specsoloist:latest sp conduct score/
```

Lets users try the quine without installing Python.

### 9c. Homebrew formula

Reaches developers who don't use pip. Requires someone with a Mac to verify.

### 9d. Spec registry

```bash
sp install specsoloist/auth-patterns
sp install specsoloist/rest-api-patterns
```

Shared specs for common patterns. Requires infrastructure — too early, but worth
keeping in mind when designing the `sp init` experience.

### 9f. NPM placeholder

Reserve `specsoloist` on NPM with a minimal placeholder package pointing to the PyPI
package. Do this before anyone else does. Publish once, then replace with the real
TypeScript port (§5b) when it's ready.

### 9e. GitHub App / PR checks

Runs `sp validate` on changed specs in PRs. Posts a comment if specs are structurally
invalid. Optional: runs `sp diff` and posts the diff summary.

---

## 10. Spec Format Evolution

### 10a. Spec inheritance / extension

```yaml
extends: base_api
```

Inherit common patterns (auth, pagination, error handling) from a base spec.

### 10b. `spec_version` field

Add `spec_version: 1.0` to frontmatter now so format migrations can be written later,
like Rails migrations for specs.

### 10c. The "live spec" concept

A running service that reflects on its own spec at runtime. Error messages that
reference the spec. Auto-generated API docs always in sync because they come from
the spec, not the code. Long-term vision for what "specs as source of truth" means
at runtime.

### 10d. Spec specificity tiers

Specs sit on a continuum of language/framework specificity. Recognizing the tiers
helps spec authors make deliberate choices about what's agnostic and what isn't:

**Tier 1 — Fully agnostic.** Describes behavior independent of language or framework.
"When a `build.started` event arrives, status becomes `building`." Implementable in
any language. This is the ideal for `# Overview`, `# Behavior`, and `# Examples`.

**Tier 2 — Framework-coupled, language-agnostic.** Tied to a specific framework but
not to language syntax. "The app must work in headless mode for CI testing" — this
presumes Textual's architecture but could be stated in any language. Common for UI
specs, web framework specs, and anything with external dependencies. Acceptable and
often unavoidable in `# Constraints` and `# Overview`.

**Tier 3 — Implementation-leaking.** Specific API calls, import paths, test assertions.
`app.query_one("StatusBar").renderable_text` is Python-Textual test code, not a
requirement. This belongs only in `# Verification` (which is explicitly language-specific)
and should be avoided in `# Examples`.

**Guidance for spec authors:**
- `# Overview`, `# Behavior`, `# Examples` → aim for tier 1, accept tier 2 when necessary
- `# Constraints` → tier 2 is fine (framework requirements are real constraints)
- `# Verification` → tier 3 is expected (it compiles to a real test file)
- If you find tier 3 creeping into `# Examples`, rewrite as prose: "the list displays
  both spec names in dependency order" rather than `assert spec_list.spec_names == [...]`

---

## 11. Adjacent Tooling & Ecosystem Ideas

### 11a. Issue-to-Task Bridge ("briefer")

**The gap:** GitHub Issues (and equivalents) are where communities raise problems.
Agent task files (like SpecSoloist's `tasks/` format) are where AI agents get their
working context. No mature tool bridges these two worlds.

**The insight:** A raw issue ("fix login bug") is too sparse for an agent to act on.
The value isn't syncing — it's *enriching*: turning a sparse human issue into a
structured, agent-readable task brief with steps, success criteria, and context.

**The pipeline:**

```
Issue Source        Enrichment              Output
──────────────      ──────────────────      ──────────────────────────
GitHub Issues  →                       →   tasks/42-fix-login.md
GitLab Issues  →   LLM briefer         →   (agent-readable task brief)
Linear         →   (like sp compose    →
Jira           →    but for issues)    →
Plain markdown →   (pass-through)      →   (no enrichment needed)
```

**Provider strategy:** Provider-agnostic core with thin adapters. The issue data
model is just `{id, title, body, labels, url}` — any tracker can supply this.
GitHub is the pragmatic starting point (80% of open source) but should never
leak into the core format. The task file stands alone without provider context.

**The loop:**
1. Community member opens a GitHub Issue
2. Briefer fetches it and runs it through an LLM to produce a structured task file
3. Maintainer reviews/edits the brief (same as reviewing a spec)
4. Agent executes the task, opens a PR
5. PR merge closes the Issue (cheap to add as a provider-specific step)

**Self-hosting opportunity:** This could be built *with* SpecSoloist — the briefer
is essentially a `sp compose`-style agent that takes an issue body as input instead
of a feature description. A strong proof-of-concept for the framework.

**Prior art to study:**
- **Beads / bd** (Steve Yegge) — Dolt-backed local issue tracker with hash-based
  IDs; Molecules/Wisps pattern. Local-first, not provider-integrated. Key insight:
  issues as structured local data for agent consumption. Originally noted in
  IMPROVEMENTS.md §11a before consolidation.
- **git-bug** — stores issues in git objects (not browsable files)
- **gh CLI** — pull-on-demand JSON export, not a live mirror

**Open questions:**
- Should the brief format be SpecSoloist's `tasks/` style, or a more general standard?
- Bidirectional sync (local edits → update Issue) or one-way pull only?
- Where does the enrichment LLM call live — local CLI, CI action, or GitHub App?
- Could this be a `sp issues` subcommand, or a standalone tool?

### 11b. User Acceptance Stories / "Did it meet requirements?"

**The gap:** The spec-as-source model verifies that generated code matches specs, and that
tests pass. But it doesn't verify that the specs themselves match what the *user actually
wanted*. There's a missing feedback loop: the user described something in plain English,
specs were generated, code was generated — but did the result deliver the original intent?

**The insight:** Unit tests verify correctness against the spec. User acceptance verifies the
spec was the *right spec*. These are different validation layers. You can have 100% test
coverage and completely miss what the user needed.

**Possible approaches:**

*Scenario / story specs* — a first-class spec type (`type: story`) written from the user's
perspective in plain language. Before the quine, but after compose:
```
"As a user, I can add a todo item and see it appear in the list."
```
Stories get compiled into E2E / acceptance tests rather than unit tests. The soloist for a
story reads the scenario and writes a playwright/cypress test. The presence of a failing story
test is a signal the specs didn't capture the requirement.

*Acceptance criteria in the brief* — `sp vibe` could prompt for acceptance criteria alongside
the brief. These get passed into the compose step so specs are shaped around verifiable
outcomes from the start.

*Post-build review loop* — after `sp conduct`, a "did this work?" step where the user runs
the app and confirms or rejects user stories. Rejections feed back as updated briefs.

**Relationship to spec format:** Stories would complement, not replace, existing spec types.
The spec-as-source model stays intact — stories just add the user's perspective as a
validation layer on top of the generated specs.

**Open questions:**
- Should stories be in the score (framework validates itself via stories) or only in user projects?
- Is `type: story` a new spec type, or are E2E specs (§6.7) sufficient?
- How does `sp vibe --pause-for-review` fit here — is that already the acceptance gate?
