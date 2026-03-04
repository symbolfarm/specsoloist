---
name: math_workflow
type: workflow
status: draft
dependencies:
  - factorial
  - is_prime
---

# 1. Overview
A demonstration workflow that computes the factorial of a number, then checks if the result is prime.

# 2. Interface Specification

```yaml:schema
inputs:
  n:
    type: integer
    minimum: 0
    maximum: 20
    description: "Starting number for factorial"
outputs:
  factorial_result:
    type: integer
  is_prime_result:
    type: boolean
```

# 3. Steps

```yaml:steps
- name: compute_factorial
  spec: factorial
  inputs:
    n: inputs.n

- name: check_prime
  spec: is_prime
  checkpoint: true
  inputs:
    n: compute_factorial.outputs.result
```

# 4. Functional Requirements (Behavior)
- **FR-01**: Execute the `compute_factorial` step using the provided input `n`.
- **FR-02**: Pass the output of the factorial calculation to the `check_prime` step.
- **FR-03**: Return both the factorial result and the primality check result.

# 5. Error Handling
- If `compute_factorial` fails: Terminate the workflow and return the error.
- If `check_prime` fails: Log the error and return the partial result containing the factorial.
