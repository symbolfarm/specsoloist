---
name: is_prime
type: function
status: stable
tags:
  - math
  - pure
---

# 1. Overview
Determines whether a given integer is a prime number. A prime is a natural number greater than 1 that has no positive divisors other than 1 and itself.

# 2. Interface Specification

```yaml:schema
inputs:
  n:
    type: integer
    description: "The integer to check for primality"
outputs:
  result:
    type: boolean
    description: "True if n is prime, false otherwise"
```

# 3. Functional Requirements (Behavior)
- **FR-01**: Return false for n <= 1 (not prime by definition).
- **FR-02**: Return true for n = 2 (the smallest and only even prime).
- **FR-03**: Return false for even numbers greater than 2.
- **FR-04**: For odd numbers greater than 2, return true if and only if n has no odd divisors up to and including the square root of n.

# 4. Non-Functional Requirements (Constraints)
- **NFR-Purity**: Must be a pure function with no side effects.
- **NFR-Performance**: Should use efficient trial division with early termination for even numbers.

# 5. Design Contract
- **Pre-condition**: n is an integer.
- **Post-condition**: result is true if and only if n is a mathematical prime number.

# 6. Test Scenarios
| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Negative | `n: -5` | `false` |
| Zero | `n: 0` | `false` |
| One | `n: 1` | `false` |
| Smallest prime | `n: 2` | `true` |
| Small odd prime | `n: 3` | `true` |
| Small composite | `n: 4` | `false` |
| Larger prime | `n: 17` | `true` |
| Typical composite | `n: 100` | `false` |
| Larger prime (3 digits) | `n: 997` | `true` |
