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

## Scaffolding

Generate an arrangement for your project with `sp init`:

```bash
# Generic Python arrangement
sp init myproject --arrangement python

# Named template (includes language-specific tools and examples)
sp init myproject --template python-fasthtml
sp init myproject --template nextjs-vitest
sp init myproject --template nextjs-playwright

# List all available templates
sp init --list-templates
```

## Annotated Example

```yaml
# arrangement.yaml

target_language: python

output_paths:
  implementation: src/mypackage/{name}.py   # {name} is the spec name
  tests: tests/test_{name}.py

environment:
  tools:
    - uv
    - pytest
  setup_commands:
    # These run in the build directory before each test run
    - uv sync
  dependencies:
    # Package name → version specifier (PEP 440 for Python, semver for npm)
    # Injected into soloist prompts so agents know exact API versions to target
    python-fasthtml: ">=0.12,<0.13"
    starlette: ">=0.27"

build_commands:
  lint: uv run ruff check src/
  test: uv run python -m pytest {file} -v

env_vars:
  DATABASE_URL:
    description: "PostgreSQL connection string"
    required: true
    example: "postgres://user:pass@localhost:5432/mydb"
  OPENAI_API_KEY:
    description: "OpenAI key for AI features"
    required: false
    example: "sk-..."

model: claude-haiku-4-5-20251001   # optional: pin LLM model for this project
```

## Fields

| Field | Description |
| --- | --- |
| `target_language` | Target language (e.g. `python`, `typescript`) |
| `specs_path` | Directory where spec files are discovered (default: `src/`); used by `sp list`, `sp status`, `sp graph`, and `sp conduct` |
| `output_paths.implementation` | Path template for generated implementation files (`{name}` = spec name) |
| `output_paths.tests` | Path template for generated test files |
| `output_paths.overrides` | Per-spec path overrides (see below) |
| `environment.tools` | Tools the agent should use (informational, injected into prompts) |
| `environment.setup_commands` | Shell commands run before each test invocation |
| `environment.dependencies` | Package versions to pin (name → specifier); injected as a "Dependency Versions" table in prompts |
| `build_commands.lint` | Command to lint the generated code (optional) |
| `build_commands.test` | Command template to run tests (`{file}` is the test path) |
| `env_vars` | Declared environment variable names — values never stored (see below) |
| `model` | LLM model to use; overridden by `--model` CLI flag or `SPECSOLOIST_LLM_MODEL` env var |

## `specs_path`

Override where SpecSoloist looks for spec files (default: `src/`):

```yaml
specs_path: specs/
```

This affects `sp list`, `sp status`, `sp graph`, and `sp conduct`. Useful when your spec files live outside `src/` — for example in a dedicated `specs/` directory or at the project root.

You can also override per-command with `--arrangement`:

```bash
sp list --arrangement arrangement.yaml
sp conduct --arrangement arrangement.yaml
```

## `output_paths.overrides`

Override the default output paths for specific specs. The default `implementation` and `tests` templates apply to all specs; `overrides` lets you set different paths for individual ones:

```yaml
output_paths:
  implementation: src/{name}.py
  tests: tests/test_{name}.py
  overrides:
    auth:
      implementation: src/myapp/auth.py
      tests: tests/myapp/test_auth.py
    db:
      implementation: src/myapp/db.py
      # tests path falls back to the default template
```

Each key under `overrides` is the spec name (without `.spec.md`). You can override `implementation`, `tests`, or both — omitting one falls back to the default template.

## `setup_commands`

Shell commands executed in the build directory **before** running tests. Use them to install dependencies or prepare the environment:

```yaml
environment:
  setup_commands:
    - uv sync
```

Commands run in order. If any command fails, the test run is aborted and the failure is reported.

## `dependencies`

Pin the exact package versions your project uses. SpecSoloist injects these into every soloist prompt as a "Dependency Versions" table, so agents target the right API:

```yaml
environment:
  dependencies:
    python-fasthtml: ">=0.12,<0.13"
    starlette: ">=0.27"
```

For Python use PEP 440 specifiers; for npm use semver ranges.

## `env_vars`

Declare the environment variables your project expects. **Values are never stored** — only names, descriptions, and whether they're required:

```yaml
env_vars:
  DATABASE_URL:
    description: "PostgreSQL connection string"
    required: true
    example: "postgres://user:pass@localhost:5432/mydb"
  STRIPE_KEY:
    description: "Stripe secret key"
    required: false
    example: "sk_live_..."
```

`sp doctor --arrangement arrangement.yaml` checks that all `required: true` variables are set in your environment and warns about any that are missing.

Soloist agents are also informed of these variables (names and descriptions only) so generated code can reference them correctly.

## `model`

Pin the LLM model for this project:

```yaml
model: claude-haiku-4-5-20251001
```

Precedence (highest to lowest): `--model` CLI flag → arrangement `model` field → `SPECSOLOIST_LLM_MODEL` env var → provider default.

## Example: A TypeScript Project

```yaml
target_language: typescript

output_paths:
  implementation: src/{name}.ts
  tests: tests/{name}.test.ts

environment:
  tools:
    - node
    - npm
  setup_commands:
    - npm install
  dependencies:
    "@ai-sdk/openai": "^0.0.9"
    next: "^14"

build_commands:
  lint: npx eslint src/
  test: npx vitest run {file}

env_vars:
  OPENAI_API_KEY:
    description: "OpenAI API key for AI SDK"
    required: true
    example: "sk-..."
```

See `src/specsoloist/arrangements/` for the bundled template files.
