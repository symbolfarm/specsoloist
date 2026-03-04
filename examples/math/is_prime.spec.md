---
name: is_prime
type: function
status: stable
tags:
  - math
  - pure
---

# Overview

Determines whether a given integer is a prime number. A prime is a natural number greater than 1 that has no positive divisors other than 1 and itself.

# Interface

```yaml:schema
inputs:
  n:
    type: integer
    description: The integer to check for primality
outputs:
  result:
    type: boolean
    description: True if n is prime, false otherwise
```

# Behavior

- **[FR-01]**: Return false for n <= 1 (not prime by definition)
- **[FR-02]**: Return true for n = 2 (smallest prime)
- **[FR-03]**: Return false for even n > 2
- **[FR-04]**: For odd n > 2, check divisibility by odd numbers up to √n

# Constraints

- **[NFR-01]**: Must be pure (no side effects)
- **[NFR-02]**: Should use efficient trial division (O(√n))

# Contract

- **Pre**: n is an integer
- **Post**: result = true iff n is prime
- **Invariant**: Same input always produces same output

# Examples

| n | result | Notes |
|---|--------|-------|
| -5 | false | Negative |
| 0 | false | Zero |
| 1 | false | One is not prime |
| 2 | true | Smallest prime |
| 3 | true | Prime |
| 4 | false | 2×2 |
| 17 | true | Prime |
| 100 | false | 10×10 |
| 997 | true | Largest 3-digit prime |
