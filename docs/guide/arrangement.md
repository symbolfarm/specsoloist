# Arrangement Guide

An **Arrangement** is a YAML configuration file that tells SpecSoloist *how* to build your project: where to put generated files, which language and tools to use, and what setup commands to run before tests.

Think of it as the bridge between your specs (the *what*) and your build environment (the *how*).

## Auto-Discovery

SpecSoloist automatically looks for `arrangement.yaml` in the current working directory. You can also specify one explicitly:

```bash
sp compile mymodule --arrangement path/to/arrangement.yaml
sp conduct --arrangement path/to/arrangement.yaml
sp test mymodule   # also picks up arrangement.yaml automatically
```

## Annotated Example

```yaml
# arrangement.yaml

language: python

output:
  implementation: src/mypackage/{name}.py   # {name} is the spec name
  tests: tests/test_{name}.py

environment:
  tools:
    - uv
    - pytest
  setup_commands:
    # These run in the build directory before each test run
    - uv pip install -e .
    - uv pip install pytest

build:
  lint: uv run ruff check src/
  test: uv run python -m pytest {file} -v
```

## Fields

| Field | Description |
| --- | --- |
| `language` | Target language (e.g. `python`, `typescript`) |
| `output.implementation` | Path template for generated implementation files |
| `output.tests` | Path template for generated test files |
| `environment.tools` | List of tools the agent should use (informational) |
| `environment.setup_commands` | Shell commands run before each test invocation |
| `build.lint` | Command to lint the generated code |
| `build.test` | Command template to run tests (`{file}` is the test path) |

## setup_commands

`setup_commands` are shell commands executed in the build directory **before** running tests. Use them to install dependencies or prepare the environment:

```yaml
environment:
  setup_commands:
    - uv pip install -e ".[dev]"
```

Commands run in order. If any command fails, the test run is aborted and the failure is reported.

## Example: A TypeScript Project

```yaml
language: typescript

output:
  implementation: src/{name}.ts
  tests: tests/{name}.test.ts

environment:
  tools:
    - node
    - npm
  setup_commands:
    - npm install

build:
  lint: npx eslint src/
  test: npx jest {file}
```

See `arrangement.example.yaml` in the project root for a complete reference example.
