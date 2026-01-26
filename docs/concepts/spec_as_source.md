# Spec-as-Source

In Specular, **The Specification is the Source of Truth**. 

### The Lifecycle

1.  **Requirement**: A human defines a Functional Requirement (e.g., `FR-01`).
2.  **Compilation**: The LLM reads the spec and generates the implementation.
3.  **Verification**: Tests are generated from the `Test Scenarios` section.
4.  **Sync**: If you change the code manually, you are creating technical debt. If you change the Spec, you are evolving the software.

### Markdown Structure

Specular uses a specific SRS (Software Requirements Specification) format:

-   **Frontmatter**: YAML metadata (name, type, language, dependencies).
-   **Overview**: Purpose and context.
-   **Interface**: Types, inputs, and outputs.
-   **Functional Requirements**: Detailed behavior.
-   **Non-Functional Requirements**: Constraints like performance and purity.
-   **Design Contract**: Pre-conditions and post-conditions.
-   **Test Scenarios**: High-level test cases.
