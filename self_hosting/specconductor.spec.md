---
name: specconductor
type: class
language_target: python
status: draft
dependencies:
  - {name: SpecSoloist, from: specsoloist.spec.md}
---

# 1. Overview

**SpecConductor** is the build and execution manager of Spechestra. It takes a spec architecture (from SpecComposer or manually written specs) and:

1. **Builds** - Orchestrates parallel SpecSoloist instances to compile specs into code
2. **Performs** - Executes workflows defined by orchestrator/workflow specs

The Conductor is responsible for the entire "concert" - preparing the orchestra (build) and leading the performance (run).

# 2. Interface Specification

```yaml:schema
inputs:
  project_dir:
    type: string
    description: Path to project root
  specs:
    type: array
    description: Optional list of spec names to build (default: all)
    required: false
outputs:
  build_result:
    type: object
    description: Results of compilation
  perform_result:
    type: object
    description: Results of workflow execution
```

## 2.1 Constructor

### `SpecConductor(project_dir: str, config: Optional[SpecSoloistConfig] = None)`
*   Initializes with a project directory.
*   If `config` is not given, loads from environment.
*   Creates an internal `SpecSoloistCore` instance for compilation.

## 2.2 Build Methods

### `build(specs: List[str] = None, parallel: bool = True, incremental: bool = True, max_workers: int = 4) -> BuildResult`
*   Compiles specs in dependency order.
*   Uses multiple SpecSoloist instances in parallel when `parallel=True`.
*   With `incremental=True`, only recompiles changed specs.
*   Returns `BuildResult` with compilation status.

### `verify() -> VerifyResult`
*   Validates all specs for schema compliance and interface compatibility.
*   Checks that dependencies exist and types match.
*   Returns `VerifyResult` with per-spec status.

### `get_build_order(specs: List[str] = None) -> List[str]`
*   Returns specs in topological order without building.
*   Useful for previewing what will be built.

### `get_dependency_graph(specs: List[str] = None) -> DependencyGraph`
*   Returns the full dependency graph for visualization.

## 2.3 Perform Methods

### `perform(workflow: str, inputs: Dict[str, Any], checkpoint_callback: Callable = None) -> PerformResult`
*   Executes a workflow defined by an orchestrator/workflow spec.
*   Loads compiled modules and runs them in sequence.
*   With `checkpoint_callback`, pauses at checkpoints for approval.
*   Returns `PerformResult` with step outputs and execution trace.

### `get_trace(workflow: str) -> List[ExecutionTrace]`
*   Returns execution traces for a workflow.
*   Traces are saved to `.spechestra/traces/`.

## 2.4 Convenience Methods

### `build_and_perform(workflow: str, inputs: Dict[str, Any]) -> Tuple[BuildResult, PerformResult]`
*   Builds all required specs, then performs the workflow.
*   Convenience method for the common case.

## 2.5 Data Classes

### `BuildResult`
```python
@dataclass
class BuildResult:
    success: bool
    specs_compiled: List[str]
    specs_skipped: List[str]  # Unchanged in incremental mode
    specs_failed: List[str]
    build_order: List[str]
    errors: Dict[str, str]
    duration: float  # seconds
```

### `PerformResult`
```python
@dataclass
class PerformResult:
    success: bool
    workflow: str
    steps: List[StepResult]
    outputs: Dict[str, Any]  # Final outputs
    trace_path: str  # Path to saved trace
    duration: float

@dataclass
class StepResult:
    name: str
    spec: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    success: bool
    error: Optional[str]
    duration: float
```

### `VerifyResult`
```python
@dataclass
class VerifyResult:
    success: bool
    results: Dict[str, SpecVerification]

@dataclass
class SpecVerification:
    status: str  # "valid", "warning", "invalid", "error"
    schema_defined: bool
    errors: List[str]
    message: str
```

# 3. Functional Requirements

## Build Orchestration
*   **FR-01**: SpecConductor shall resolve dependencies and determine build order.
*   **FR-02**: Independent specs (no mutual dependencies) shall be compiled in parallel.
*   **FR-03**: Specs at level N must complete before level N+1 begins.
*   **FR-04**: Build failures shall be captured and reported per-spec.
*   **FR-05**: With `incremental=True`, unchanged specs shall be skipped.
*   **FR-06**: Each spec compilation shall use a separate SpecSoloist instance.

## Verification
*   **FR-07**: `verify()` shall check all specs for valid structure.
*   **FR-08**: `verify()` shall check schema compatibility between connected specs.
*   **FR-09**: Verification failures shall not prevent build (warning mode).

## Workflow Execution (Perform)
*   **FR-10**: `perform()` shall load compiled modules dynamically.
*   **FR-11**: `perform()` shall execute steps in the order defined by the workflow spec.
*   **FR-12**: Inputs shall be resolved from previous step outputs or initial inputs.
*   **FR-13**: Step results shall be stored in a Blackboard for subsequent steps.
*   **FR-14**: With `checkpoint_callback`, execution shall pause at checkpoint steps.
*   **FR-15**: Execution traces shall be saved to `.spechestra/traces/`.

## Error Handling
*   **FR-16**: If a step fails during perform, execution shall stop and return partial results.
*   **FR-17**: Build errors shall not affect unrelated specs (fail-fast per spec, not globally).
*   **FR-18**: Self-healing (`attempt_fix`) can be triggered on build failures (optional).

# 4. Non-Functional Requirements

*   **NFR-Performance**: Parallel builds shall use a configurable thread pool (default 4 workers).
*   **NFR-Observability**: Build progress shall be reportable (for UI integration).
*   **NFR-Isolation**: Each SpecSoloist runs independently; one failure doesn't corrupt others.
*   **NFR-Resumable**: Failed builds can be resumed with `incremental=True`.
*   **NFR-Traceable**: All perform executions save traces for debugging.

# 5. Design Contract

*   **Pre-condition**: Specs to build must exist in `src/` directory.
*   **Pre-condition**: For `perform()`, workflow spec must be of type "orchestrator" or "workflow".
*   **Pre-condition**: For `perform()`, all referenced specs must be compiled.
*   **Invariant**: SpecConductor uses SpecSoloist's public API only.
*   **Post-condition**: After successful `build()`, compiled code exists in `build/`.
*   **Post-condition**: After `perform()`, trace file exists in `.spechestra/traces/`.

# 6. Test Scenarios

| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Build single spec | One spec, no deps | `specs_compiled: [spec]` |
| Build with deps | A depends on B | B compiled before A |
| Parallel build | 3 independent specs | All in `specs_compiled`, faster than sequential |
| Incremental build | Unchanged spec | `specs_skipped: [spec]` |
| Build failure | Spec with syntax error | `specs_failed: [spec]`, others still compile |
| Verify valid | All specs with schemas | `success: True` |
| Verify missing schema | Spec without schema | `status: "warning"` |
| Perform simple | 2-step workflow | Both steps in results |
| Perform with checkpoint | Workflow with checkpoint | Callback invoked |
| Perform failure | Step throws exception | `success: False`, partial results |
| Build and perform | Workflow + inputs | Build succeeds, then perform runs |
| Get trace | After perform | Trace file contents returned |
