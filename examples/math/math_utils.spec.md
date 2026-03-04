---
name: math_utils
type: bundle
tags:
  - math
  - utils
---

# 1. Overview
Common mathematical utility functions for basic arithmetic and number manipulation.

# 2. Interface Specification

```yaml:functions
add:
  inputs:
    a: number
    b: number
  outputs:
    result: number
  behavior: "Returns the sum of a and b."

subtract:
  inputs:
    a: number
    b: number
  outputs:
    result: number
  behavior: "Returns the difference of a and b."

multiply:
  inputs:
    a: number
    b: number
  outputs:
    result: number
  behavior: "Returns the product of a and b."

divide:
  inputs:
    a: number
    b: number
  outputs:
    result: number
  behavior: "Returns the quotient of a divided by b."
  contract:
    pre: "b must not be zero."

clamp:
  inputs:
    value: number
    min: number
    max: number
  outputs:
    result: number
  behavior: "Returns the value constrained within the range [min, max]."
  contract:
    pre: "min must be less than or equal to max."

abs:
  inputs:
    n: number
  outputs:
    result: number
  behavior: "Returns the absolute (non-negative) value of n."
```
