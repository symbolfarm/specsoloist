---
name: ui
type: bundle
tags:
  - cli
  - presentation
---

# Overview

Terminal UI utilities for the SpecSoloist CLI. Provides styled output functions using the Rich library, including headers, status messages, tables, spinners, and user confirmation prompts.

All functions use a shared console instance with a custom theme (success=green, error=red, warning=yellow, info=cyan).

# Functions

```yaml:functions
print_header:
  inputs:
    title: {type: string, description: Main title text}
    subtitle: {type: string, optional: true, description: Optional subtitle displayed above title}
  outputs: {}
  behavior: "Print a styled panel with blue border containing the title (bold blue) and optional subtitle (dim, centered)"

print_success:
  inputs:
    message: {type: string}
  outputs: {}
  behavior: "Print checkmark followed by message in green"

print_error:
  inputs:
    message: {type: string}
  outputs: {}
  behavior: "Print 'Error:' prefix followed by message in bold red"

print_warning:
  inputs:
    message: {type: string}
  outputs: {}
  behavior: "Print 'Warning:' prefix followed by message in yellow"

print_info:
  inputs:
    message: {type: string}
  outputs: {}
  behavior: "Print info symbol followed by message in cyan"

print_step:
  inputs:
    message: {type: string}
  outputs: {}
  behavior: "Print arrow symbol followed by message in bold blue"

create_table:
  inputs:
    columns: {type: array, items: {type: string}, description: Column header names}
    title: {type: string, optional: true, description: Optional table title}
  outputs:
    table: {type: object, description: Rich Table instance ready for add_row() calls}
  behavior: "Create and return a Rich Table with bold cyan headers and dim borders"

spinner:
  inputs:
    message: {type: string, description: Status message to display}
  outputs:
    status: {type: object, description: Rich Status context manager}
  behavior: "Return a console.status() context manager with dots spinner and bold blue message"

confirm:
  inputs:
    question: {type: string, description: Yes/no question to ask}
  outputs:
    confirmed: {type: boolean, description: True if user entered 'y' (case-insensitive)}
  behavior: "Prompt with question and [y/N], return True only if input is 'y' or 'Y'"
```

# Constraints

- [NFR-01]: All output goes to a shared Rich Console instance
- [NFR-02]: Functions are stateless (no side effects beyond printing)
- [NFR-03]: Depends on `rich` library (Console, Table, Panel, Status, Text, Theme)
