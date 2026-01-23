# Global Project Context

## Project Philosophy
This project adheres to the "Spec-as-Source" methodology. The source of truth is strictly the `*.spec.md` files. Code is a build artifact.

## Coding Standards (Generated)
- **Error Handling**: Prefer explicit error returns (Result types) over exceptions where possible, or use standard idiomatic exception handling for the target language.
- **Comments**: Generated code should include docstrings derived from the Spec Objective.
- **Naming**: Use snake_case for functions and variables, PascalCase for types (or idiomatic conventions for the target language).

## Security Constraints
- Input validation must occur at the boundary of every public function.
- No secrets hardcoded.

## Testing Strategy
- Every component must have unit tests generated based on the "Test Plan" section of the spec.
