---
name: factorial
type: function
status: stable
tags:
  - math
  - pure
---

# Overview

Computes the factorial of a non-negative integer. The factorial of n (written n!) is the product of all positive integers less than or equal to n.

# Interface

```yaml:schema
inputs:
  n:
    type: integer
    minimum: 0
    maximum: 20
    description: The non-negative integer to compute factorial of
outputs:
  result:
    type: integer
    minimum: 1
```

# Behavior

- **[FR-01]**: Return 1 when n is 0 (base case: 0! = 1)
- **[FR-02]**: Return n × factorial(n-1) for n > 0
- **[FR-03]**: Reject negative inputs with an error

# Constraints

- **[NFR-01]**: Must be pure (no side effects, no state)
- **[NFR-02]**: Must not use recursion deeper than n (iterative preferred)

# Contract

- **Pre**: n >= 0 and n <= 20
- **Post**: result = n!
- **Invariant**: Same input always produces same output

# Examples

| n | result | Notes |
|---|--------|-------|
| 0 | 1 | Base case |
| 1 | 1 | 1! = 1 |
| 5 | 120 | 5! = 5×4×3×2×1 |
| 10 | 3628800 | |
| 20 | 2432902008176640000 | Maximum supported |
| -1 | *Error* | Negative not allowed |
| 21 | *Error* | Exceeds maximum |
