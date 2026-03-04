# Production Readiness Proposals

Proposals for moving SpecSoloist from "proven concept" to "reliable tool" that developers reach for in real projects. Organised by theme, roughly in priority order within each section.

---

## 1. Multi-Language Quine

**The big proof point.** The claim "specs are language-agnostic" is currently validated only in Python. The most compelling demonstration is running `sp conduct score/` with a different arrangement and producing working TypeScript (or Go, or Rust) code that passes its own test suite.

### 1a. TypeScript Arrangement

Write `score/arrangements/typescript.arrangement.yaml`:
```yaml
target_language: typescript
output_paths:
  implementation: build/quine-ts/src/{name}.ts
  tests: build/quine-ts/tests/{name}.test.ts
environment:
  tools: [node, npm, tsx, vitest]
  setup_commands: [npm install]
build_commands:
  compile: npx tsc --noEmit
  lint: npx eslint src/**/*.ts
  test: npx vitest run
constraints:
  - Use strict TypeScript
  - Use ES modules (import/export)
  - Use vitest for testing
```

Then run:
```bash
sp conduct score/ --arrangement score/arrangements/typescript.arrangement.yaml --auto-accept
```

Expected deliverable: a `QUINE_RESULTS_TS.md` parallel to `QUINE_RESULTS.md`.

**Why this matters:** Proves specs really are the source of truth and not secretly Python-flavoured.

### 1b. Go Arrangement

Longer-term. Go has a different module system and idioms (interfaces vs inheritance, error tuples vs exceptions). If the same specs compile to idiomatic Go, the framework's language-agnosticism is beyond doubt.

```yaml
target_language: go
output_paths:
  implementation: build/quine-go/{name}.go
  tests: build/quine-go/{name}_test.go
environment:
  tools: [go]
  setup_commands: [go mod download]
build_commands:
  compile: go build ./...
  lint: go vet ./...
  test: go test ./...
constraints:
  - Use idiomatic Go (snake_case for file names, CamelCase for exported symbols)
  - Return errors as (result, error) tuples
  - Use interfaces for dependency injection
```

### 1c. Diff Report for Cross-Language Runs

Once two language runs exist, use `sp diff` to compare them semantically:
```bash
sp diff build/quine-py/src/ build/quine-ts/src/ --report reports/cross-lang-diff.json
```

This surfaces which functions "translated" cleanly and which needed language-specific workarounds.

---

## 2. Build Run History & Regression Detection

Currently each `sp conduct` run overwrites the previous output. We lose the ability to ask "did the quine get better or worse?"

### 2a. Timestamped Run Archives

When `sp conduct score/` completes, automatically archive the output:
```
build/
  runs/
    2026-03-01T14:30:00/
      run_meta.json          # arrangement, test results, model, duration
      src/specsoloist/*.py
      tests/test_*.py
    2026-03-01T16:45:00/
      ...
  quine/                     # symlink or copy of the latest run
```

The `record_build_run` function in `build_diff` already provides the scaffolding for this.

### 2b. `sp diff` Run-Over-Run Comparison

After the archive structure exists:
```bash
sp diff --runs 2     # diff last two runs
sp diff runs/2026-03-01T14:30:00/ runs/2026-03-01T16:45:00/
```

A green diff means the spec is stable and the AI generates consistent code. A red diff means the generation is non-deterministic and the spec may need more precision.

### 2c. Flakiness Score

Over N runs of the same spec with the same model, measure how often the generated code for a given function is identical. A "flakiness score" per spec surfaces which requirements are ambiguous. High-flakiness specs should be investigated and tightened.

---

## 3. Spec Quality Metrics

### 3a. Spec Coverage

Similar to code coverage: what fraction of the public API (functions, types, error conditions) has a corresponding spec? Build a tool that cross-references spec function names against the actual implementation's exported symbols and reports gaps.

```bash
sp coverage src/specsoloist/core.py score/core.spec.md
# Coverage: 12/15 functions (80%)
# Missing: _load_manifest, get_build_status, delete_spec
```

### 3b. Example Density

Specs without examples are harder for soloists to interpret correctly. A linter check that warns when a function spec has zero examples in its Examples table, or when an edge case mentioned in Behavior has no corresponding example.

### 3c. Scenario Completeness

Parse the Examples table and check that all scenario paths in the Behavior section have at least one example. This is automatable: Behavior bullet points mentioning "if X" or "when Y" should have a row in Examples where X is true/false.

---

## 4. CI/CD Integration

### 4a. GitHub Actions: Quine Validation Workflow

A workflow that runs on every change to `score/`:
1. Run `sp conduct score/ --auto-accept --no-agent` (direct LLM mode for reproducibility in CI)
2. Run `sp diff src/ build/quine/src/ --report build/diff-report.json`
3. Fail the build if `diff-report.json` has any `FAIL` status entries
4. Comment the report on the PR (diff summary as a PR comment)

This makes spec changes reviewable: you see not just the spec diff but how it affects generated code.

### 4b. Test Artifact Upload

Upload `build/quine/` as a GitHub Actions artifact so every CI run has a downloadable copy of the generated code. Essential for debugging flaky quine runs.

### 4c. Model Pinning

CI should pin the model version to prevent regressions caused by model updates. Add `SPECSOLOIST_LLM_MODEL` to the CI environment. When a model is upgraded, run the quine validation and update the pin deliberately.

---

## 5. Robustness & Error Recovery

### 5a. Retry Budget for Soloists

Soloists currently have up to 3 retries on test failure. The retry logic should be configurable and should log each attempt with the error that triggered it. Failed soloists should produce a `*.failed.md` file with the last error, enabling `sp fix` to pick up where they left off.

### 5b. Partial Build Resume

If `sp conduct` is interrupted mid-run (e.g. API rate limit, network error), restarting from scratch wastes time. The build manifest already tracks completed specs. Add a `--resume` flag that skips already-compiled specs and continues from the last completed level.

### 5c. Arrangement Validation at Start

Before spawning a single soloist, validate that all tools listed in the arrangement's `environment.tools` are available on PATH. Fail fast with a clear message rather than failing in the middle of a build.

### 5d. Timeout per Soloist

Long-running soloists can block a level indefinitely. Add a configurable per-soloist timeout (default: 5 minutes) that marks the spec as failed and continues the build.

---

## 6. Observability

### 6a. Structured Build Log

Emit structured JSON events during `sp conduct`:
```json
{"event": "spec_start", "spec": "config", "level": 0, "ts": "2026-03-01T14:30:01Z"}
{"event": "spec_complete", "spec": "config", "tests": 46, "pass": true, "duration": 42.3}
{"event": "build_complete", "total": 13, "passed": 13, "failed": 0, "duration": 780.1}
```

Tools like Datadog, Grafana, or a simple `jq` pipeline can then analyse build performance over time.

### 6b. Build Dashboard

A simple `sp status` command (or HTML report generated alongside the JSON report) showing:
- Which specs were compiled in the last run
- Pass/fail per spec with test count
- Diff summary vs original source
- Model and arrangement used

### 6c. Token Usage Tracking

Track input/output tokens per spec compilation. Over time this answers: which specs are most expensive to compile? Are there specs that consistently need many retries (token cost × retries)?

---

## 7. Developer Experience

### 7a. `sp diff` as a First-Class CLI Command

See `score/build_diff.spec.md` for the full spec. The short version:

```bash
sp diff src/ build/quine/src/         # quine fidelity check
sp diff build/run1/ build/run2/       # run-over-run regression
sp diff --vs-source build/quine-ts/   # cross-language fidelity
```

Outputs a coloured summary to terminal + a JSON report.

### 7b. SKILLS.md & Slash Commands

Define user-invocable slash commands (distinct from native subagents):
- `/quine` — run the quine and diff against source
- `/diff` — compare latest two build runs
- `/coverage` — run spec coverage report

These complement the `.claude/agents/` subagents which are for delegation, not user invocation.

### 7c. VS Code Extension Prototype

A minimal extension that:
- Displays a "Compile" button when a `.spec.md` file is open
- Shows inline test pass/fail indicators next to spec function names
- Highlights spec/code drift (when source has changed since last compile)

A full GUI editor is Phase 8 material; this prototype just needs `sp compile` and `sp test` wired to VS Code commands.

### 7d. `sp watch` — Live Recompilation

Watch `score/` for changes and automatically recompile changed specs (and their dependents) in the background. Like `webpack --watch` for specs. Useful during active spec development.

---

## 8. Packaging & Distribution

### 8a. PyPI Release Automation

Add a GitHub Actions release workflow:
1. On `git tag v*`, build and publish to PyPI automatically
2. Include a CHANGELOG entry (can be generated from conventional commit messages)
3. Pin `build_requires` versions to ensure reproducible sdist builds

### 8b. Docker Image on GHCR

Publish the `specsoloist.Dockerfile` image to GitHub Container Registry on each release:
```bash
docker run --rm -v $(pwd):/workspace ghcr.io/symbolfarm/specsoloist:latest sp conduct score/
```

This lets users try the quine without installing anything locally.

### 8c. `arrangement.yaml` Templates

Ship a `score/arrangements/` directory with ready-to-use arrangement templates:
- `python-uv.arrangement.yaml` — Python with uv, ruff, pytest
- `typescript-vitest.arrangement.yaml` — TypeScript with vitest
- `go.arrangement.yaml` — Go modules
- `rust.arrangement.yaml` — Rust with cargo

Users copy and customise. This lowers the barrier to multi-language experiments.

---

## Priority Summary

| # | Proposal | Impact | Effort | Do Next? |
|---|----------|--------|--------|----------|
| 1a | TypeScript quine | Very High | Medium | Yes |
| 2a | Run archives | High | Low | Yes |
| 2b | `sp diff` run-over-run | High | Low | Yes (blocked by 7a) |
| 4a | GitHub Actions CI | High | Low | Yes |
| 3a | Spec coverage | Medium | Medium | Soon |
| 5b | Partial build resume | Medium | Medium | Soon |
| 6a | Structured build log | Medium | Low | Soon |
| 7b | SKILLS.md | Low | Low | Yes |
| 1b | Go quine | High | High | Later |
| 7c | VS Code extension | Medium | High | Later |
| 7d | `sp watch` | Medium | Medium | Later |
