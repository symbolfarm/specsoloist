---
name: math_workflow
type: workflow
status: draft
dependencies:
  - examples/factorial
  - examples/is_prime
---

# Overview

A demonstration workflow that computes the factorial of a number, then checks if the result is prime. (Spoiler: factorials > 2 are never prime.)

# Interface

```yaml:schema
inputs:
  n:
    type: integer
    minimum: 0
    maximum: 20
    description: Starting number for factorial
outputs:
  factorial_result:
    type: integer
  is_prime_result:
    type: boolean
```

# Steps

```yaml:steps
- name: compute_factorial
  spec: examples/factorial
  inputs:
    n: inputs.n

- name: check_prime
  spec: examples/is_prime
  checkpoint: true
  inputs:
    n: compute_factorial.outputs.result
```

# Error Handling

- If `compute_factorial` fails (invalid input): Return error, do not proceed
- If `check_prime` fails: Log error, return partial result with factorial only
