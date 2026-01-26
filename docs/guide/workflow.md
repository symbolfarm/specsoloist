# The Specular Workflow

Using Specular requires a shift in mindset: **You are no longer a Coder; you are an Architect.**

Instead of writing logic, you define constraints and behaviors. This guide outlines the recommended workflow for building scalable systems.

## 1. The "Leaves-Up" Strategy

Do not try to compile an entire application in one go. Build from the bottom up.

1.  **Domain First**: Start by defining your data structures (Type Specs). This creates the "vocabulary" for your system.
2.  **Dependencies Second**: Build utility modules and helpers that depend on those types.
3.  **Core Logic Third**: Build the business logic that uses the utilities.
4.  **API/UI Last**: Build the interface layer.

### Example Order
1.  `types.spec.md` (User, Order structs)
2.  `validation.spec.md` (Input checkers)
3.  `order_service.spec.md` (Business logic)

## 2. The Iteration Loop

Once a component exists, you enter the daily development loop. You rarely touch generated code directly.

### Scenario A: Adding a Feature
1.  Open `auth.spec.md`.
2.  Add a new function signature to **Interface Specification**.
3.  Add a **Functional Requirement** (e.g., `FR-05: The system shall hash passwords using bcrypt`).
4.  Run `specular compile auth`.
5.  Run `specular test auth`. (Specular generates new tests for the new requirements).

### Scenario B: Fixing a Bug
1.  You run `specular test` and see a failure.
2.  **Do not edit the code.**
3.  Run `specular fix auth`.
4.  The agent analyzes the failure, reads the spec, and patches the code.
5.  *If it fails repeatedly:* Your spec is likely ambiguous. **Refine the spec** (e.g., add a constraint or clarify an edge case).

## 3. The Hybrid Reality

For large projects, you don't have to use Specular for 100% of the code.

*   **Specular**: Use it for "pure" logic, data models, complex algorithms, and utilities.
*   **Hand-Written**: Use manual code for "glue," framework boilerplate (like FastAPI setup or React routing), or highly visual UI components.

Specular generates standard Python/TypeScript files in `build/`. You can import them into your hand-written `main.py` just like any other library.

!!! warning "Do not edit build artifacts"
    If you manually edit a file in `build/`, Specular will overwrite your changes the next time you compile. If you need manual control, move the file out of `build/` and stop managing it with Specular.

## 4. Best Practices

*   **NFRs are your Friend**: If the code works but is "bad" (slow, messy), add a **Non-Functional Requirement**.
    *   *Bad*: "Make it fast."
    *   *Good*: "NFR-Performance: Must use binary search, O(log n)."
*   **Explicit Dependencies**: Ensure your `dependencies: []` list in the spec frontmatter is accurate. This tells the LLM exactly what other modules it can import.
