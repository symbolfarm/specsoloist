# Spec Template

When you run `sp create`, it generates a file based on the standard SpecSoloist template.

```markdown
---
name: [name]
type: bundle
status: draft
dependencies: []
---

# 1. Overview
[Brief summary of the component's purpose.]

# 2. Interface Specification

```yaml:functions
- name: [function_name]
  inputs:
    [param]: [type]
  outputs: [type]
  behavior: "[Description of what the function does.]"
```

# 3. Functional Requirements (Behavior)
...
```

### Key Fields

-   **`name`**: The unique identifier for this specification.
-   **`type`**: `bundle`, `function`, `type`, `module`, or `workflow`.
-   **`status`**: `draft`, `review`, or `stable`.
-   **`dependencies`**: List of other specs this module depends on.
