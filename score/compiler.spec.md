---
name: compiler
type: bundle
dependencies:
  - parser/types
tags:
  - core
  - compilation
---

# Overview

Provides functionality to compile SpecSoloist specifications into implementation code, type definitions, orchestration workflows, and test suites using an LLM provider. It also handles generating and parsing fixes for failing tests.

# Functions

```yaml:functions
compiler_init:
  inputs:
    provider:
      type: object
      description: LLM provider instance for generation.
    global_context:
      type: string
      description: Global project context to include in prompts.
  outputs:
    compiler:
      type: object
      description: An initialized compiler instance.
  behavior: "Initialize a SpecCompiler with an LLM provider and global context."

compile_code:
  inputs:
    compiler: {type: object}
    spec: {type: ref, ref: parser/types/parsed_spec}
    model: {type: optional, of: {type: string}}
  outputs:
    code: {type: string}
  behavior: |
    Compiles a function or bundle specification to implementation code:
    1. Identify the target language from the spec metadata.
    2. Build an import context string from the spec's dependencies.
    3. Construct a prompt for an expert developer in the target language, providing global context, dependencies, and the component specification.
    4. Instruct the LLM to implement the component strictly according to requirements and output raw code.
    5. Call the LLM provider and strip markdown fences from the result.

compile_typedef:
  inputs:
    compiler: {type: object}
    spec: {type: ref, ref: parser/types/parsed_spec}
    model: {type: optional, of: {type: string}}
  outputs:
    code: {type: string}
  behavior: |
    Compiles a type or bundle specification to type definition code:
    1. Identify the target language from the spec metadata.
    2. Construct a prompt for an expert developer specializing in type systems, providing global context and the type specification.
    3. Instruct the LLM to define all types using appropriate language constructs (e.g., dataclasses in Python), including validation and docstrings.
    4. Call the LLM provider and strip markdown fences from the result.

compile_orchestrator:
  inputs:
    compiler: {type: object}
    spec: {type: ref, ref: parser/types/parsed_spec}
    model: {type: optional, of: {type: string}}
  outputs:
    code: {type: string}
  behavior: |
    Compiles a workflow or orchestrator specification to execution code:
    1. Identify the target language from the spec metadata.
    2. Extract the list of specs used in the workflow steps to build a component context.
    3. Construct a prompt for an expert developer specializing in multi-agent orchestration, providing global context and the orchestration specification.
    4. Instruct the LLM to implement the workflow logic, state passing, and error handling.
    5. Call the LLM provider and strip markdown fences from the result.

compile_tests:
  inputs:
    compiler: {type: object}
    spec: {type: ref, ref: parser/types/parsed_spec}
    model: {type: optional, of: {type: string}}
  outputs:
    code: {type: string}
  behavior: |
    Generates a unit test suite for a specification:
    1. Identify the target language and module name from the spec metadata.
    2. Determine appropriate test framework instructions (e.g., pytest for Python, node:test for TypeScript).
    3. Construct a prompt for an expert QA engineer, providing the component specification and test instructions.
    4. Instruct the LLM to implement test cases for all scenarios and edge cases from the spec.
    5. Call the LLM provider and strip markdown fences from the result.

generate_fix:
  inputs:
    compiler: {type: object}
    spec: {type: ref, ref: parser/types/parsed_spec}
    code_content: {type: string}
    test_content: {type: string}
    error_log: {type: string}
    model: {type: optional, of: {type: string}}
  outputs:
    response: {type: string}
  behavior: |
    Generates a fix for failing tests:
    1. Identify the target language and module name.
    2. Construct a prompt for a senior software engineer to analyze the discrepancy between the spec, code, tests, and error output.
    3. Instruct the LLM to provide corrected content for the failing file(s) using a specific '### FILE:' marker format.
    4. Call the LLM provider and return the raw response.

parse_fix_response:
  inputs:
    response: {type: string}
  outputs:
    fixes: {type: object, description: "Map of filenames to corrected contents."}
  behavior: |
    Parses an LLM fix response to extract file updates:
    1. Use regex to find blocks starting with '### FILE: <path>' and ending with '### END'.
    2. For each match, extract the path and content.
    3. Strip markdown fences from the content and return a map of filename to cleaned content.

build_import_context:
  inputs:
    spec: {type: ref, ref: parser/types/parsed_spec}
  outputs:
    context: {type: string}
  behavior: "Format a spec's dependencies into a human-readable instruction string for use in compilation prompts."

strip_markdown_fences:
  inputs:
    code: {type: string}
  outputs:
    cleaned: {type: string}
  behavior: "Remove markdown code fences (e.g., ```python ... ```) from the beginning and end of a string if present."
```
