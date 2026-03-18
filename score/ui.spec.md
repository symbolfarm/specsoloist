---
name: ui
type: bundle
tags:
  - cli
  - presentation
---

# Overview

Terminal UI utilities for the SpecSoloist CLI. Provides styled output functions for headers, status messages, tables, spinners, and user confirmation prompts. All output goes through a shared console instance.

# Functions

```yaml:functions
configure:
  inputs:
    quiet: {type: boolean, optional: true, description: "Suppress all non-error output"}
    json_mode: {type: boolean, optional: true, description: "Disable Rich; emit plain JSON"}
  outputs: {}
  behavior: "Set module-level output flags. Must be called once at startup after parsing --quiet / --json flags. In JSON or quiet mode, Rich decorations are suppressed."

is_json_mode:
  inputs: {}
  outputs:
    result: {type: boolean}
  behavior: "Return true if JSON output mode is active"

is_quiet:
  inputs: {}
  outputs:
    result: {type: boolean}
  behavior: "Return true if quiet mode is active"

print_header:
  inputs:
    title: {type: string, description: Main title text}
    subtitle: {type: string, optional: true, description: Optional subtitle}
  outputs: {}
  behavior: "Print a styled panel containing the title and optional subtitle"

print_success:
  inputs:
    message: {type: string}
  outputs: {}
  behavior: "Print a success indicator followed by message"

print_error:
  inputs:
    message: {type: string}
  outputs: {}
  behavior: "Print an error prefix followed by message"

print_warning:
  inputs:
    message: {type: string}
  outputs: {}
  behavior: "Print a warning prefix followed by message"

print_info:
  inputs:
    message: {type: string}
  outputs: {}
  behavior: "Print an info indicator followed by message"

print_step:
  inputs:
    message: {type: string}
  outputs: {}
  behavior: "Print a step/arrow indicator followed by message"

create_table:
  inputs:
    columns: {type: array, items: {type: string}, description: Column header names}
    title: {type: string, optional: true, description: Optional table title}
  outputs:
    table: {type: object, description: Table object ready for add_row() calls}
  behavior: "Create and return a styled table with the given column headers"

spinner:
  inputs:
    message: {type: string, description: Status message to display}
  outputs:
    status: {type: object, description: Context manager that shows a spinner while active}
  behavior: "Return a context manager that displays a spinner with the given message"

confirm:
  inputs:
    question: {type: string, description: Yes/no question to ask}
  outputs:
    confirmed: {type: boolean}
  behavior: "Prompt the user with question and [y/N], return True only if they enter y or Y"
```

# Constraints

- All output goes through a shared console instance with a consistent color theme
- Functions are stateless (no side effects beyond terminal output)
- The module also exports the `console` and `Panel` objects for direct use by other modules
