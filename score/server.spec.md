---
name: server
type: bundle
dependencies:
  - specsoloist
---

# Overview
MCP (Model Context Protocol) server for SpecSoloist. It provides a set of tools that allow MCP clients to manage, validate, compile, and test specifications through the SpecSoloist framework.

# Functions
```yaml:functions
list_specs:
  inputs: {}
  outputs:
    specs: {type: array, items: {type: string}}
  behavior: List all available specification files in the project.

read_spec:
  inputs:
    name: {type: string}
  outputs:
    content: {type: string}
  behavior: "Read the content of a spec file or return 'Error: Spec not found.' if it doesn't exist."

create_spec:
  inputs:
    name: {type: string}
    description: {type: string}
    type: {type: optional, of: {type: string}}
  outputs:
    result: {type: string}
  behavior: Create a new specification file from the standard template and return its path or an error.

validate_spec:
  inputs:
    name: {type: string}
  outputs:
    result: {type: string}
  behavior: Validate a specification against the standard and return a summary status string.

compile_spec:
  inputs:
    name: {type: string}
  outputs:
    result: {type: string}
  behavior: Compile a specification into source code and return the code or an error message.

compile_tests:
  inputs:
    name: {type: string}
  outputs:
    result: {type: string}
  behavior: Generate a test suite for a specification and return the test code or an error message.

run_tests:
  inputs:
    name: {type: string}
  outputs:
    result: {type: string}
  behavior: Run the generated tests and return the result summary and output.

attempt_fix:
  inputs:
    name: {type: string}
  outputs:
    result: {type: string}
  behavior: Attempt to auto-fix a failing component by analyzing test logs.

main:
  inputs: {}
  outputs: {}
  behavior: Initialize and run the FastMCP server.
```
