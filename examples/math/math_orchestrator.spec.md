---
name: math_orchestrator
type: orchestrator
---

# 1. Overview
An orchestrator that calculates a factorial and then checks if the result is prime.

# 2. Interface Specification

```yaml:schema
inputs:
  start_val:
    type: integer
    minimum: 0
steps:
  - name: calc_fact
    spec: math_demo
    inputs:
      operation: factorial
      n: inputs.start_val
  - name: check_prime
    spec: math_demo
    checkpoint: true
    inputs:
      operation: is_prime
      n: calc_fact.outputs.result
```

# 3. Functional Requirements
1. Receive an integer input.
2. Calculate its factorial.
3. Check if the factorial is a prime number.

# 4. Non-Functional Requirements
*   **NFR-Efficiency**: The orchestration should avoid redundant LLM calls.

# 5. Design Contract
*   **Pre-condition**: `start_val >= 0`.

