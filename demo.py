import os
import sys
from specsoloist.core import SpecSoloistCore

def main():
    # Ensure API Key is present
    if "GEMINI_API_KEY" not in os.environ:
        print("ERROR: GEMINI_API_KEY environment variable not found.")
        print("Please run: export GEMINI_API_KEY='your_key_here'")
        sys.exit(1)

    print("--- SpecSoloist Demo: End-to-End Flow ---")
    
    # Initialize Core
    core = SpecSoloistCore(".")

    spec_name = "math_demo"
    
    # 1. Create a spec from template
    try:
        core.create_spec(spec_name, "A robust factorial and prime check library.")
    except FileExistsError:
        print(f"Spec {spec_name} already exists, proceeding to overwrite with demo content.")

    # 2. Overwrite with a high-quality definition to ensure LLM success
    spec_path = core.parser.get_spec_path(spec_name)
    demo_spec_content = """---
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
""".strip()
    with open(spec_path, 'w') as f:
        f.write(demo_spec_content)
    print(f"1. Spec created/updated at: {spec_path}")

    # 3. Compile Code
    print(f"2. Compiling {spec_name} to code...")
    print(core.compile_spec(spec_name))

    # 4. Compile Tests
    print(f"3. Compiling {spec_name} to tests...")
    print(core.compile_tests(spec_name))

    # 5. Run Tests
    print("4. Running tests...")
    result = core.run_tests(spec_name)
    
    if result["success"]:
        print("\nSUCCESS: All tests passed!")
    else:
        print("\nFAILURE: Tests failed.")
        print("--- Test Output ---")
        print(result["output"][:500] + "...") # Print snippet
        
        print("\n5. Attempting Auto-Fix (Self-Correction)...")
        fix_msg = core.attempt_fix(spec_name)
        print(fix_msg)
        
        print("6. Rerunning tests after fix...")
        result_retry = core.run_tests(spec_name)
        if result_retry["success"]:
            print("\nSUCCESS: Auto-fix worked! All tests passed.")
        else:
            print("\nFAILURE: Auto-fix failed to resolve the issue.")
            print(result_retry["output"])

if __name__ == "__main__":
    main()
