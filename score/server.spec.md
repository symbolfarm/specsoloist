---
name: server
type: bundle
dependencies:
  - core
tags:
  - server
  - mcp
---

# Overview

Model Context Protocol (MCP) server for SpecSoloist. Exposes the SpecSoloist core orchestration functionality as tools, allowing LLMs and editors to interact with the specification-driven development workflow.

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
  behavior: "Read the content of a specification file. Returns an error message if the spec cannot be found."

create_spec:
  inputs:
    name: {type: string}
    description: {type: string}
    type: {type: optional, of: {type: string}}
  outputs:
    result: {type: string}
  behavior: "Create a new specification file from the standard template (defaulting to 'function' type) and return a status message."

validate_spec:
  inputs:
    name: {type: string}
  outputs:
    result: {type: string}
  behavior: Validate a specification's structure and return its validity status and any errors found.

compile_spec:
  inputs:
    name: {type: string}
  outputs:
    result: {type: string}
  behavior: Compile a specification into source code using the configured LLM provider.

compile_tests:
  inputs:
    name: {type: string}
  outputs:
    result: {type: string}
  behavior: Generate a test suite for a specification using the configured LLM provider.

run_tests:
  inputs:
    name: {type: string}
  outputs:
    result: {type: string}
  behavior: Execute the tests associated with a specification and return the results and output.

attempt_fix:
  inputs:
    name: {type: string}
  outputs:
    result: {type: string}
  behavior: Run a self-healing loop that analyzes test failures and attempts to fix the implementation.

main:
  inputs: {}
  outputs: {}
  behavior: Initialize and run the SpecSoloist MCP server.
```

# Behavior

## Project Root Resolution
The server determines the active project directory by checking the `SPEC_ROOT` environment variable. If not set, it defaults to the current working directory.

## MCP Integration
The server identifies itself as `SpecSoloist` to MCP clients. It wraps the `SpecSoloistCore` API into discrete tools, handling the translation between MCP tool calls and core method invocations.

## Error Handling
Tool implementations must catch exceptions from the core orchestrator and return them as informative error strings to the client, ensuring the server remains operational.