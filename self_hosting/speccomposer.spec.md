---
name: speccomposer
type: class
language_target: python
status: draft
dependencies:
  - {name: SpecSoloist, from: specsoloist.spec.md}
---

# 1. Overview

**SpecComposer** is the architect component of Spechestra. It takes plain English requests and drafts a complete spec architecture - the dependency graph and individual `*.spec.md` files for each component.

This is the "vibe-coding" entry point: users describe what they want, and SpecComposer figures out the architecture.

**Key workflow:**
1. User provides natural language request
2. SpecComposer drafts an architecture (components + dependencies)
3. User reviews/edits the architecture (optional)
4. SpecComposer generates individual specs
5. User reviews/edits specs (optional)
6. Hand off to SpecConductor for building

# 2. Interface Specification

```yaml:schema
inputs:
  request:
    type: string
    description: Natural language description of desired software
  context:
    type: object
    description: Optional existing specs/code context
    required: false
outputs:
  architecture:
    type: object
    description: Component graph with dependencies
  specs:
    type: array
    description: List of generated spec file paths
```

## 2.1 Constructor

### `SpecComposer(project_dir: str, provider: Optional[LLMProvider] = None)`
*   Initializes with a project directory.
*   If `provider` is not given, loads from environment configuration.

## 2.2 Core Methods

### `draft_architecture(request: str, context: Optional[Dict] = None) -> Architecture`
*   Takes a natural language request and produces an architecture plan.
*   Returns an `Architecture` object containing:
    - `components`: List of component definitions (name, type, description)
    - `dependencies`: Dependency graph between components
    - `build_order`: Suggested compilation order
*   Does NOT create files yet.

### `review_architecture(architecture: Architecture) -> Architecture`
*   Presents the architecture for user review in interactive mode.
*   Returns potentially modified architecture.
*   In auto-accept mode, returns unchanged.

### `generate_specs(architecture: Architecture) -> List[str]`
*   Creates `*.spec.md` files in `src/` for each component.
*   Returns list of created file paths.
*   Uses the spec template and fills in based on architecture.

### `review_specs(spec_paths: List[str]) -> List[str]`
*   Presents generated specs for user review.
*   User can edit specs directly.
*   Returns final list of spec paths.

### `compose(request: str, auto_accept: bool = False) -> CompositionResult`
*   High-level method that runs the full workflow:
    1. `draft_architecture(request)`
    2. `review_architecture()` (if not auto_accept)
    3. `generate_specs()`
    4. `review_specs()` (if not auto_accept)
*   Returns `CompositionResult(architecture, spec_paths, ready_for_build)`.

## 2.3 Data Classes

### `Architecture`
```python
@dataclass
class Architecture:
    components: List[ComponentDef]
    dependencies: Dict[str, List[str]]  # component -> [dependencies]
    build_order: List[str]

@dataclass
class ComponentDef:
    name: str
    type: str  # "function", "class", "module", "typedef"
    description: str
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
```

### `CompositionResult`
```python
@dataclass
class CompositionResult:
    architecture: Architecture
    spec_paths: List[str]
    ready_for_build: bool
```

# 3. Functional Requirements

## Architecture Drafting
*   **FR-01**: Given a plain English request, SpecComposer shall produce a component architecture.
*   **FR-02**: The architecture shall identify component types (function, class, module, typedef).
*   **FR-03**: The architecture shall infer dependencies between components.
*   **FR-04**: The architecture shall suggest a build order (topological sort).

## Spec Generation
*   **FR-05**: Generated specs shall follow the standard SRS template (Overview, Interface, FRs, NFRs, Contract, Tests).
*   **FR-06**: Generated specs shall include `yaml:schema` blocks for interface definitions.
*   **FR-07**: Specs shall be placed in the project's `src/` directory.
*   **FR-08**: Existing specs with the same name shall NOT be overwritten without confirmation.

## Review Flow
*   **FR-09**: In interactive mode, the architecture shall be presented for review before spec generation.
*   **FR-10**: In interactive mode, generated specs shall be presented for review/editing.
*   **FR-11**: In auto-accept mode (`auto_accept=True`), all reviews are skipped.
*   **FR-12**: The review interface shall support terminal-based display (using Rich).

## Context Awareness
*   **FR-13**: If existing specs are provided as context, SpecComposer shall incorporate them into the architecture.
*   **FR-14**: SpecComposer shall detect and avoid duplicate component names.

# 4. Non-Functional Requirements

*   **NFR-LLM**: Architecture drafting and spec generation use LLM calls; results may vary.
*   **NFR-Idempotent**: Running compose twice with the same input should produce similar (not necessarily identical) architectures.
*   **NFR-Transparent**: The user should be able to see and understand the generated architecture before committing.
*   **NFR-Editable**: All generated artifacts (architecture, specs) should be human-editable.

# 5. Design Contract

*   **Pre-condition**: `request` must be a non-empty string describing desired functionality.
*   **Pre-condition**: Project directory must exist and be writable.
*   **Invariant**: SpecComposer never compiles specs; that's SpecConductor's job.
*   **Post-condition**: After `compose()`, all spec files exist in `src/` (if not cancelled).
*   **Post-condition**: Generated specs are valid according to `validate_spec()`.

# 6. Test Scenarios

| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Simple request | "A function that adds two numbers" | Architecture with 1 component |
| Multi-component | "A REST API with auth and user CRUD" | Architecture with 3+ components |
| With dependencies | "A service using a shared User type" | Architecture shows User as dependency |
| Auto-accept mode | Request + `auto_accept=True` | Specs created without prompts |
| Existing context | Request + existing specs | New specs integrate with existing |
| Duplicate name | Request creating "auth" when exists | Confirmation prompt or rename |
| Invalid request | Empty string | `ValueError` raised |
| Review and cancel | User cancels during review | No specs created, returns early |
