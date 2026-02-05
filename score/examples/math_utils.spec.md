---
name: math_utils
type: bundle
tags:
  - math
  - utils
---

# Overview

Common mathematical utility functions for basic arithmetic and number manipulation.

# Functions

```yaml:functions
add:
  inputs: {a: integer, b: integer}
  outputs: {result: integer}
  behavior: Return a + b

subtract:
  inputs: {a: integer, b: integer}
  outputs: {result: integer}
  behavior: Return a - b

multiply:
  inputs: {a: integer, b: integer}
  outputs: {result: integer}
  behavior: Return a × b

divide:
  inputs: {a: number, b: number}
  outputs: {result: number}
  behavior: Return a / b
  contract:
    pre: b != 0

clamp:
  inputs:
    value: {type: number}
    min: {type: number}
    max: {type: number}
  outputs: {result: number}
  behavior: Return value constrained to [min, max]
  contract:
    pre: min <= max

abs:
  inputs: {n: number}
  outputs: {result: number}
  behavior: Return absolute value of n
  contract:
    post: result >= 0
```
