---
name: factorial
type: function
status: stable
tags:
  - math
  - pure
---

# 1. Overview
Computes the factorial of a non-negative integer. The factorial of n (written n!) is the product of all positive integers less than or equal to n.

# 2. Interface Specification

```yaml:schema
inputs:
  n:
    type: integer
    minimum: 0
    maximum: 20
    description: "The non-negative integer to compute factorial of"
outputs:
  result:
    type: integer
    minimum: 1
```

# 3. Functional Requirements (Behavior)
- **FR-01**: Return 1 when n is 0 (base case: 0! = 1).
- **FR-02**: Return the product of all positive integers from 1 up to n for n > 0.
- **FR-03**: Raise an error for negative inputs.
- **FR-04**: Raise an error for inputs exceeding 20 to prevent overflow in restricted environments.

# 4. Non-Functional Requirements (Constraints)
- **NFR-Purity**: Must be a pure function with no side effects.
- **NFR-Performance**: Implementation should favor iterative approach over deep recursion.

# 5. Design Contract
- **Pre-condition**: n is an integer where 0 <= n <= 20.
- **Post-condition**: result is equal to the mathematical factorial n!.

# 6. Test Scenarios
| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Base case | `n: 0` | `1` |
| Small integer | `n: 1` | `1` |
| Typical case | `n: 5` | `120` |
| Maximum supported | `n: 20` | `2432902008176640000` |
| Negative input | `n: -1` | `Error` |
| Out of range | `n: 21` | `Error` |
