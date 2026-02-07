---
name: compiler
type: bundle
tags:
  - core
  - compilation
---

# Overview

Compiles SpecSoloist specifications into implementation code, type definitions, workflow scripts, and test suites by constructing prompts and calling an LLM provider. Also handles generating and parsing fix suggestions for failing tests.

# Types

## SpecCompiler

Compiler for specs. Constructed with an `LLMProvider` instance and an optional `global_context` string (project-wide context included in all prompts).

# Functions

## SpecCompiler.compile_code(spec, model=None) -> string

Compile a function/bundle spec to implementation code. Constructs a prompt with the spec body, dependency context, and global context, then calls the LLM. Returns raw code (markdown fences stripped).

## SpecCompiler.compile_typedef(spec, model=None) -> string

Compile a type spec to type definition code. Prompts the LLM to define types using idiomatic constructs for the target language. Returns raw code.

## SpecCompiler.compile_orchestrator(spec, model=None) -> string

Compile a workflow/orchestrator spec to execution code. Extracts step references for context and prompts the LLM to implement the workflow with state passing between steps. Returns raw code.

## SpecCompiler.compile_tests(spec, model=None) -> string

Generate a test suite for a spec. Prompts the LLM to write tests covering all scenarios and edge cases from the spec. Uses appropriate test framework for the target language (pytest for Python, node:test for TypeScript). Returns raw test code.

## SpecCompiler.generate_fix(spec, code_content, test_content, error_log, model=None) -> string

Generate a fix for failing tests. Provides the spec (source of truth), current code, current tests, and error output to the LLM. Returns raw response with `### FILE: path` / `### END` markers.

## SpecCompiler.parse_fix_response(response) -> dict

Parse the LLM fix response to extract file contents. Finds all `### FILE: <path>` ... `### END` blocks and returns a dict mapping filename to cleaned content (markdown fences stripped).

# Constraints

- All compilation methods strip markdown code fences from LLM responses
- The spec body/content is passed directly to the LLM — the compiler does not interpret spec semantics
- Dependency context is built from `spec.metadata.dependencies` (supports both string and dict formats)
