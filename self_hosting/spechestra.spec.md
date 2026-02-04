---
name: spechestra
type: module
language_target: python
status: draft
dependencies:
  - {name: SpecSoloist, from: specsoloist.spec.md}
---

# 1. Overview

**Spechestra** is the orchestration layer for spec-driven development. It sits above SpecSoloist and provides high-level workflows for turning plain English requests into working software.

Spechestra introduces two key components:
- **SpecComposer**: Takes natural language input and drafts an architecture with specs
- **SpecConductor**: Manages parallel builds and workflow execution

Together they enable "vibe-coding" - users describe what they want, review the generated specs, and watch the system build it.

```
User (plain English)
        │
        ▼
┌──────────────────┐
│   SpecComposer   │  "Build me a todo app with auth"
│   (Architect)    │           │
└──────────────────┘           ▼
        │            ┌─────────────────────┐
        │            │ Architecture + Specs │
        │            │ - auth.spec.md       │
        │            │ - todo.spec.md       │
        │            │ - api.spec.md        │
        │            └─────────────────────┘
        │                      │
        ▼              [User review/edit]
┌──────────────────┐           │
│  SpecConductor   │◄──────────┘
│   (Manager)      │
└──────────────────┘
        │
        ├──────────────┬──────────────┐
        ▼              ▼              ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │SpecSolo-│   │SpecSolo-│   │SpecSolo-│
   │ist(auth)│   │ist(todo)│   │ist(api) │
   └─────────┘   └─────────┘   └─────────┘
        │              │              │
        └──────────────┴──────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ SpecConductor   │
              │   .perform()    │
              └─────────────────┘
```

# 2. Interface Specification

## 2.1 Package Structure

```
spechestra/
  __init__.py           # Exports SpecComposer, SpecConductor
  composer.py           # SpecComposer implementation
  conductor.py          # SpecConductor implementation
  blackboard.py         # Shared state for workflows
  schema.py             # Interface validation (Pydantic models)
```

## 2.2 SpecComposer

See `speccomposer.spec.md` for detailed specification.

## 2.3 SpecConductor

See `specconductor.spec.md` for detailed specification.

## 2.4 Blackboard

A shared state store for workflow execution. Allows steps to share data without direct coupling.

### `Blackboard(storage_path: str)`
*   Initializes with a path for persistence.

### `set(key: str, value: Any, scope: str = "shared")`
*   Stores a value under a scoped key.

### `get(key: str, scope: str = "shared") -> Optional[Any]`
*   Retrieves a value by key and scope.

### `clear()`
*   Removes all data.

# 3. Functional Requirements

*   **FR-01**: Spechestra shall depend on SpecSoloist for individual spec compilation.
*   **FR-02**: Spechestra shall provide a high-level API for end-to-end workflows (compose → build → perform).
*   **FR-03**: Each component (Composer, Conductor) shall be usable independently.
*   **FR-04**: Spechestra shall support both interactive (review/approve) and automated (auto-accept) modes.

# 4. Non-Functional Requirements

*   **NFR-Separation**: Spechestra shall be installable as a separate package (`pip install spechestra`).
*   **NFR-Backwards-Compatible**: Existing SpecSoloist users shall not need Spechestra.
*   **NFR-Extensibility**: Custom Composers and Conductors can be implemented by extending base classes.

# 5. Design Contract

*   **Pre-condition**: SpecSoloist must be installed and configured with an LLM provider.
*   **Invariant**: Spechestra never modifies SpecSoloist internals; it only uses public APIs.
*   **Post-condition**: After a successful compose→build→perform cycle, compiled code exists in `build/` and workflow results are available.

# 6. Test Scenarios

| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Import package | `from spechestra import SpecComposer` | No error |
| Compose + Build | Natural language request | Specs created, code compiled |
| Perform workflow | Compiled workflow | Execution trace returned |
| Composer standalone | Request + no auto-build | Specs created, no compilation |
| Conductor standalone | Pre-written specs | Code compiled |
