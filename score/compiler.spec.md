---
name: compiler
type: bundle
dependencies:
  - events
tags:
  - core
  - compilation
---

# Overview

Compiles SpecSoloist specifications into implementation code, type definitions, workflow scripts, and test suites by constructing prompts and calling an LLM provider. Also handles generating and parsing fix suggestions for failing tests.

# Types

## SpecCompiler

Compiler for specs. Constructed with an `LLMProvider` instance, an optional `global_context` string (project-wide context included in all prompts), and an optional `event_bus` (EventBus).

# Functions

## SpecCompiler.compile_code(spec, model=None, arrangement=None, reference_specs=None) -> string

Compile a function/bundle spec to implementation code. Constructs a prompt with the spec body, dependency context, arrangement context, and global context, then calls the LLM. Returns raw code (markdown fences stripped).

- `reference_specs`: optional dict of dep name to ParsedSpec for dependencies that are `type: reference`. Their spec bodies are injected as API documentation in the prompt rather than as import instructions.

## SpecCompiler.compile_typedef(spec, model=None, arrangement=None) -> string

Compile a type spec to type definition code. Prompts the LLM to define types using idiomatic constructs for the target language. Returns raw code.

## SpecCompiler.compile_orchestrator(spec, model=None, arrangement=None) -> string

Compile a workflow/orchestrator spec to execution code. Extracts step references for context and prompts the LLM to implement the workflow with state passing between steps. Returns raw code.

## SpecCompiler.compile_tests(spec, model=None, arrangement=None, reference_specs=None) -> string

Generate a test suite for a spec. Prompts the LLM to write tests covering all scenarios and edge cases from the spec. Uses appropriate test framework for the target language (pytest for Python, node:test for TypeScript). Returns raw test code.

## SpecCompiler.generate_fix(spec, code_content, test_content, error_log, model=None, arrangement=None) -> string

Generate a fix for failing tests. Provides the spec (source of truth), current code, current tests, and error output to the LLM. Returns raw response with `### FILE: path` / `### END` markers.

## SpecCompiler.parse_fix_response(response) -> dict

Parse the LLM fix response to extract file contents. Finds all `### FILE: <path>` ... `### END` blocks and returns a dict mapping filename to cleaned content (markdown fences stripped).

# Constraints

- All compilation methods strip markdown code fences from LLM responses
- The spec body/content is passed directly to the LLM — the compiler does not interpret spec semantics
- Dependency context is built from `spec.metadata.dependencies` (supports both string and dict formats)
- When an `arrangement` is provided, its target language, output paths, dependency versions, env vars, and build commands are injected into the prompt as additional context
- Reference spec bodies are injected verbatim as API documentation, not as import lines
- When `event_bus` is provided, a `_generate()` wrapper around LLM calls emits `llm.request` (with model name) and `llm.response` (with input_tokens and output_tokens) events
