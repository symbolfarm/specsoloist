---
name: math_demo
type: module
language_target: python
status: draft
---

# 1. Overview
A library for mathematical operations including factorial calculation and primality testing.

# 2. Interface Specification

## 2.1 Inputs
### `factorial(n: int) -> int`
*   `n`: The non-negative integer to calculate the factorial of.

### `is_prime(n: int) -> bool`
*   `n`: The integer to check for primality.

## 2.2 Outputs
*   `factorial`: Returns the factorial as an integer.
*   `is_prime`: Returns True if n is prime, False otherwise.

# 3. Functional Requirements (Behavior)
*   **FR-01**: `factorial` shall return 1 for input 0.
*   **FR-02**: `factorial` shall return the product of all positive integers less than or equal to n.
*   **FR-03**: `is_prime` shall return False for numbers less than or equal to 1.
*   **FR-04**: `is_prime` shall return True for 2 and 3.
*   **FR-05**: `is_prime` shall use an efficient primality test (e.g., trial division up to sqrt(n)).

# 4. Non-Functional Requirements (Constraints)
*   **NFR-Purity**: Both functions must be pure.
*   **NFR-Robustness**: `factorial` should raise a ValueError for negative inputs.

# 5. Design Contract
*   **Pre-condition**: `factorial` input `n >= 0`.
*   **Post-condition**: `is_prime` output is always boolean.

# 6. Test Scenarios
| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Factorial 0 | `factorial(0)` | `1` |
| Factorial 5 | `factorial(5)` | `120` |
| Prime 7 | `is_prime(7)` | `True` |
| Not Prime 10 | `is_prime(10)` | `False` |
| Negative Factorial | `factorial(-1)` | `ValueError` |