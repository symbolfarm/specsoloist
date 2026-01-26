# Spec Template

When you run `specular create`, it generates a file based on this standard template.

```markdown
---
name: [Component Name]
type: function
language_target: python
status: draft
dependencies: []
---

# 1. Overview
[Brief summary of the component's purpose.]

# 2. Interface Specification
...
```

### Key Fields

-   **`name`**: The module name.
-   **`type`**: `function`, `class`, `module`, or `typedef`.
-   **`language_target`**: `python` or `typescript`.
-   **`dependencies`**: List of other specs this module depends on.
