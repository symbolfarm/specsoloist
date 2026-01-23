# Specular for Agents

Specular is designed to be **Agent-Native**. It provides a set of high-level tools via the **Model Context Protocol (MCP)** that allow an AI Agent to act as a Software Architect.

## The Role of the Agent
When using Specular, the Agent's role shifts from "Writing Code" to **"Defining Behavior"**.
*   **The Agent (Architect)**: Writes `*.spec.md` files.
*   **Specular (Builder)**: Compiles specs to code, writes tests, runs them, and fixes low-level bugs.

## MCP Toolset

### 1. `create_spec(name, description, type)`
Initializes a new component specification.
*   *Usage*: "Create a user authentication component."

### 2. `compile_spec(name)`
Compiles the Markdown spec into source code (e.g., Python).
*   *Usage*: "Build the auth component."

### 3. `compile_tests(name)`
Generates a test suite based on the `Test Scenarios` and `Design Contract` in the spec.
*   *Usage*: "Generate tests for auth."

### 4. `run_tests(name)`
Executes the test suite and returns the results.
*   *Usage*: "Verify the auth component."

### 5. `attempt_fix(name)`
Triggers the **Self-Healing Loop**. If tests fail, Specular analyzes the logs and automatically patches the Code or the Test file.
*   *Usage*: "The tests failed. Fix it."

## Example System Prompt for an Architect Agent

If you are configuring a custom agent to use Specular, use this system prompt:

> You are a Lead Software Architect. Your goal is to build robust software using the **Specular Framework**.
>
> **Rules:**
> 1.  **Never write source code** (Python/JS) directly. Always create or edit `*.spec.md` files.
> 2.  **Be Rigorous**: When editing specs, clearly define **Functional Requirements (FRs)** and **Design Contracts**.
> 3.  **Iterate**:
>     -   Create Spec -> `compile_spec` -> `compile_tests` -> `run_tests`.
>     -   If tests fail, use `attempt_fix` first.
>     -   If that fails, read the spec and refine the requirements.
