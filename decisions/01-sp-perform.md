# Decision: What to do with `sp perform`

**Status:** Open
**Raised:** 2026-03-11

---

## What is `sp perform`?

`sp perform <workflow> --inputs '{...}'` executes a compiled workflow: it reads a
`type: workflow` spec, resolves the step order, loads each compiled module from the
build directory via `importlib`, calls its entry point (`run`/`main`/`execute`), and
passes outputs between steps. Execution traces are saved to `.spechestra/traces/`.

The implementation lives in `src/spechestra/conductor.py:SpecConductor.perform()`.
It is not a stub — it has real logic: checkpoint callbacks, input resolution, step
sequencing, trace saving. `_execute_step()` loads compiled Python modules at runtime
and calls their entry points.

The CLI command is `src/specsoloist/cli.py:cmd_perform()`.

---

## The Problem

**`validate_inputs()` raises `NotImplementedError`** — but checking the call graph,
this is only reachable via `InterfaceSchema.validate_inputs()`, which is not called by
`SpecConductor.perform()`. So `sp perform` doesn't actually crash at runtime from this
alone. The real issues are:

1. **No workflow specs exist in the wild.** There are no `type: workflow` specs in the
   codebase, no examples, and no documentation for users. The format is defined in
   `score/spec_format.spec.md` but never demonstrated.

2. **Steps depend on the compiled build directory.** `_execute_step()` looks for
   `{build_path}/{spec_name}.py`. This only works with the legacy `sp build` path, not
   the agent-first `sp conduct` path (which writes to arrangement-defined output paths).
   In practice, anyone using `sp conduct` — which is the default recommended path —
   can't use `sp perform` at all.

3. **`validate_inputs()` is a `NotImplementedError`.** Even if not on the hot path
   today, it signals that runtime input validation was planned and never delivered.
   It is called at runtime in `sp perform` once that path is fully wired.

4. **The step input mapping is fragile.** Steps refer to outputs of prior steps via
   string paths like `"step1.outputs.result"`. There is no schema enforcement at
   compile time (beyond the `_verify_orchestrator_steps()` check, which only validates
   structure, not types end-to-end). A typo silently fails at runtime.

---

## Option A: Remove `sp perform`

Remove the `sp perform` CLI command and `SpecConductor.perform()`. Keep the `type:
workflow` spec type for forward compatibility (it parses fine; soloists can compile
it to whatever orchestration code they like). Remove `validate_inputs()` or leave it
as `NotImplementedError` since it becomes unreachable.

**Pros:**
- Eliminates a command that doesn't work with the current agent-first architecture
- Removes the expectation that SpecSoloist is a workflow *runtime* (it's a code
  generator — the generated code runs workflows, not SpecSoloist itself)
- Smaller surface area to document, test, and maintain
- Honest: doesn't promise behaviour the tool can't deliver in its current state
- The agent-first paradigm (`sp conduct`) is a better answer to multi-step
  orchestration: the conductor agent *is* the orchestrator, and the generated code
  handles runtime logic

**Cons:**
- Removes a real (if fragile) capability: executing a chain of compiled modules with
  data flow, checkpoints, and execution traces
- Traces (`.spechestra/traces/`) become orphaned — no command writes them
- Breaks the `build_and_perform()` combined flow in `SpecConductor`
- Someone may have been using this (unlikely given no docs, but possible)

---

## Option B: Fix and finish `sp perform`

Implement `validate_inputs()`, update `_execute_step()` to respect arrangement output
paths, write at least one real workflow spec example, add integration tests, and
document the command.

**Pros:**
- Completes a genuinely useful feature: spec-defined pipelines with typed data flow
  and execution tracing
- The trace format and checkpoint callback design are already solid
- Differentiates SpecSoloist from "just another code generator" — you can define,
  build, *and run* a pipeline from a spec

**Cons:**
- Significant work: `validate_inputs()`, arrangement-aware step execution, a real
  workflow example, integration tests, and documentation
- The use case overlaps heavily with what modern AI agents do natively: you can
  orchestrate a multi-step AI workflow by describing it in a spec and conducting it
  — the generated code handles the runtime, no `sp perform` needed
- Adds a runtime dependency that doesn't fit the "build artifact" mental model:
  specs → code → *you run the code*. `sp perform` blurs this by making SpecSoloist
  the runtime itself
- Harder to maintain: the step execution engine needs to stay in sync with how soloists
  generate entry points

---

## Option C: Keep the code, add a deprecation warning

Print a `[deprecated]` banner when `sp perform` is invoked, pointing users toward
writing a workflow spec and conducting it. Don't invest in fixes but don't delete
it either.

**Pros:**
- Zero work
- Signals intent without breaking anything

**Cons:**
- The "just conduct a workflow spec" alternative doesn't actually exist as a documented
  pattern yet. The deprecation notice points to a gap, not a solution.
- Deferred clutter.

---

## Instinct

Option A (remove) is probably right, but with a prerequisite: before removing `sp
perform`, it's worth establishing the recommended alternative pattern. The question
"how do I run a multi-step pipeline with SpecSoloist?" needs a good answer that isn't
just "write Python". One path: document that a `type: workflow` spec, when conducted,
produces a standalone executable module — and show an example. That gives users a
real answer before the escape hatch is closed.

Option B is appealing if there's a concrete use case that `sp conduct` can't serve.
The most plausible one: a user wants to chain together SpecSoloist-compiled functions
*at dev time* (e.g. a data pipeline) without writing any glue code. Whether that
warrants a full runtime engine, or whether "conduct a workflow spec that generates
a runner script" covers it, is the crux.

Option C is a cop-out.

---

## Historical Context

`sp perform` was built during the early direct-LLM-call era of SpecSoloist, before
Claude Code / Gemini CLI integration existed. At that time, SpecSoloist needed its own
orchestration layer to chain compiled modules together — there was no external agent to
do that job. `sp perform` was the runtime that executed those chains.

That need is now gone. `sp conduct` (with a native subagent as the conductor) is the
orchestration layer. The workflow has become well-defined and intentional rather than
pluggable.

There is a longer-term interest in integrating SpecSoloist with platform-agnostic
agentic frameworks (e.g. Pydantic AI) as an alternative to Claude Code / Gemini CLI.
That is a separate story — and even in that world, SpecSoloist would act as a *build
tool* consumed by an agent framework, not as an orchestration runtime itself.

## Decision

**Option A — Remove `sp perform`.**

SpecSoloist is a spec-driven build tool with a well-defined workflow (`sp conduct`).
It is not, and will not become, a multi-agent orchestration runtime. Removing `sp
perform` and `SpecConductor.perform()` eliminates a misleading surface area and
sharpens the tool's identity.

The `type: workflow` spec type and `yaml:steps` format can remain valid for now —
they are parsed cleanly and could be useful for describing orchestration requirements
that a soloist compiles into a standalone runner script. But the `sp perform` runtime
that executes those steps is out of scope.

**Implementation notes for whoever does the removal:**
- Remove `cmd_perform` from `cli.py` and its `perform` subparser entry
- Remove `SpecConductor.perform()`, `build_and_perform()`, `_execute_step()`,
  `_resolve_step_inputs()`, `_save_trace()`, `get_trace()` from `conductor.py`
- Remove `PerformResult` and `StepResult` dataclasses from `conductor.py`
- Remove or stub out `validate_inputs()` in `schema.py` (keep raising
  `NotImplementedError` with an updated message, or delete if `InterfaceSchema`
  is otherwise clean)
- Check `tests/` for any `sp perform` / `SpecConductor.perform` test coverage
  to remove
- Update `ROADMAP.md` to reflect that `sp perform` is removed (it is listed as
  ✅ Done in Phase 4d)
- Keep `.spechestra/traces/` directory convention documented in case traces are
  useful for a future agent-framework integration
