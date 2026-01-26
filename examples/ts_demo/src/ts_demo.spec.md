---
name: ts_demo
type: module
language_target: typescript
status: draft
---

# 1. Overview
A simple TypeScript demonstration module that provides basic string manipulation utilities.

# 2. Interface Specification

## 2.1 Inputs

### `reverseString(input: string): string`
*   `input`: The string to reverse.

### `toCapitalCase(input: string): string`
*   `input`: The string to capitalize.

## 2.2 Outputs
*   `reverseString`: Returns the reversed string.
*   `toCapitalCase`: Returns the string with the first letter of each word capitalized.

# 3. Functional Requirements (Behavior)
*   **FR-01**: `reverseString` shall return the input string in reverse order.
*   **FR-02**: `toCapitalCase` shall convert the first character of every word (separated by spaces) to uppercase and the rest to lowercase.

# 4. Non-Functional Requirements (Constraints)
*   **NFR-TypeSafety**: Must use explicit TypeScript types.
*   **NFR-Style**: Use standard Prettier formatting.

# 5. Design Contract
*   **Pre-condition**: Inputs are non-null strings.
*   **Post-condition**: Returns a new string (immutability).

# 6. Test Scenarios
| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Reverse Word | `reverseString("hello")` | `"olleh"` |
| Capitalize Single | `toCapitalCase("hello")` | `"Hello"` |
| Capitalize Sentence | `toCapitalCase("hello world")` | `"Hello World"` |
| Mixed Case | `toCapitalCase("hElLo")` | `"Hello"` |
