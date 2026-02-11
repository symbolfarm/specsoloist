---
name: conductor
type: bundle
status: draft
dependencies:
  - config
  - core
  - resolver
  - parser
---

# Overview

Conductor is the build and execution manager of Spechestra. It takes a spec architecture (from Composer or manually written specs) and orchestrates parallel compilation via SpecSoloistCore, then optionally executes workflows defined by workflow specs. The Conductor is responsible for the entire "concert" -- preparing the orchestra (build) and leading the performance (run).

# Types

## StepResult

Result of a single workflow step execution.

**Fields:** `name` (string), `spec` (string -- the spec that was executed), `inputs` (dict), `outputs` (dict), `success` (bool), `error` (string or null, default null), `duration` (float seconds, default 0.0).

## PerformResult

Result of a complete workflow execution.

**Fields:** `success` (bool), `workflow` (string -- name of the workflow spec), `steps` (list of StepResult), `outputs` (dict -- final outputs from the last step), `trace_path` (string, default empty), `duration` (float seconds, default 0.0).

## VerifyResult

Result of project verification.

**Fields:** `success` (bool), `results` (dict mapping spec name to verification details dict).

# Functions

## Conductor (class)

The main conductor class. Constructed with a project directory path and an optional `SpecSoloistConfig`. If config is not provided, loads from environment. Creates an internal `SpecSoloistCore` instance for compilation and exposes its parser and resolver.

### verify() -> VerifyResult

Verify all specs for schema compliance and interface compatibility.

**Behavior:**
- Delegates to SpecSoloistCore's project verification.
- Returns a VerifyResult summarizing per-spec verification status.
- An empty project (no specs) is considered valid.

### build(specs=None, parallel=True, incremental=True, max_workers=4) -> BuildResult

Build specs in dependency order.

- `specs`: optional list of spec name strings; if null, builds all specs
- `parallel`: bool, compile independent specs concurrently (default true)
- `incremental`: bool, only recompile changed specs (default true)
- `max_workers`: int, maximum parallel workers (default 4)

**Behavior:**
- Resolves dependencies and determines build order.
- Independent specs (no mutual dependencies) are compiled concurrently when parallel is enabled.
- With incremental enabled, unchanged specs are skipped.
- Build failures are captured per-spec; one spec failing does not prevent other independent specs from building.
- Delegates actual compilation to SpecSoloistCore, including test generation.
- Returns a BuildResult (from specsoloist.core) with compiled, skipped, and failed spec lists.

### get_build_order(specs=None) -> list of strings

Return specs in build order without actually building.

- `specs`: optional list of spec names; if null, includes all specs

**Behavior:**
- Returns an empty list for an empty project.
- Dependencies appear before dependents in the result.

### get_dependency_graph(specs=None) -> DependencyGraph

Return the dependency graph for the given specs (or all specs).

**Behavior:**
- Delegates to SpecSoloistCore's dependency graph construction.
- Returns a DependencyGraph object (from specsoloist.resolver).

### perform(workflow, inputs, checkpoint_callback=None) -> PerformResult

Execute a workflow defined by a workflow spec.

- `workflow`: string, name of the workflow spec
- `inputs`: dict, input values for the workflow
- `checkpoint_callback`: optional callable that takes a step name string and returns bool (true to continue, false to abort)

**Behavior:**
- Parses the named workflow spec and validates it is of type "workflow" or "orchestrator". Raises ValueError if not.
- Raises ValueError if the workflow has no steps defined.
- Executes steps in the order defined by the workflow spec.
- For each step, resolves input values from previous step outputs or initial workflow inputs using dot-notation references (e.g., `inputs.field` or `step_name.outputs.field`).
- Loads compiled modules dynamically from the build directory and calls a standard entry point (run, main, execute, or handler).
- If a checkpoint_callback is provided and a step has `checkpoint: true`, calls the callback before that step. If the callback returns false, execution stops and returns a failed result with partial steps.
- If any step fails with an exception, execution stops immediately and returns a failed result with all completed steps plus the failed step.
- On success, final outputs come from the last step's outputs.
- Saves an execution trace to disk after successful completion.

### build_and_perform(workflow, inputs, checkpoint_callback=None) -> tuple of (BuildResult, PerformResult)

Build all specs, then execute the workflow.

**Behavior:**
- Calls `build()` first. If the build fails, returns the failed BuildResult paired with an empty failed PerformResult (no steps executed).
- If the build succeeds, calls `perform()` with the given workflow and inputs.
- Returns both results as a tuple.

### get_trace(workflow) -> list of dicts

Retrieve saved execution traces for a workflow.

- `workflow`: string, name of the workflow

**Behavior:**
- Looks for trace files in the build directory under `.spechestra/traces/`.
- Returns traces as a list of dicts, sorted newest first by timestamp.
- Returns an empty list if no traces exist.

# Behavior

## Step input resolution

Workflow step inputs are resolved from dot-notation reference strings:
- `inputs.field` resolves to the workflow's initial input value for `field`.
- `step_name.outputs.field` resolves to a previous step's output value for `field`.
- Strings without dots are treated as literal values.

## Trace persistence

After a successful workflow execution, a JSON trace file is saved containing the workflow name, timestamp, inputs, and per-step details (name, spec, inputs, outputs, success, error, duration). Trace files are named with the workflow name and a timestamp for uniqueness.

## Separation of concerns

Conductor delegates compilation to SpecSoloistCore. It does not contain compilation logic itself. Its role is orchestration: ordering, parallelism, workflow execution, and trace management.

# Examples

| Scenario | Input | Expected |
|----------|-------|----------|
| Initialize conductor | `Conductor("/path/to/project")` | `project_dir` is set to the absolute path |
| Verify empty project | No specs in project | `result.success == True` |
| Build order empty project | No specs | Returns `[]` |
| StepResult defaults | `StepResult(name="s1", spec="f", inputs={}, outputs={}, success=True)` | `error` is null, `duration` is 0.0 |
| PerformResult | `PerformResult(success=True, workflow="w", steps=[], outputs={"result": 42})` | `outputs == {"result": 42}` |
| Build then perform | Build fails | PerformResult has `success=False`, empty steps |
| Perform non-workflow | Spec type is "function" | Raises ValueError |
| Step failure | Step raises exception | Returns partial results, `success=False` |
| Checkpoint abort | Callback returns false | Execution stops, returns partial results |
