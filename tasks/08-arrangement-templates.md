# Task: Arrangement Templates and `sp init --template`

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.
The arrangement system is the build configuration layer (`arrangement.yaml`). The CLI has an
`sp init` command that scaffolds a new project, but it creates a blank arrangement.

Every new FastHTML or Next.js project currently rediscovers the correct arrangement from
scratch: which `setup_commands` to use, which `test:` command, which constraints to include,
how to handle the Starlette test client for FastHTML, how to configure vitest for Next.js.
This is unnecessary friction. The `examples/` directory already has working, validated
arrangements — they should be available as `sp init` templates.

## What to Build

### 1. Template directory

Create `arrangements/` at the project root containing ready-to-use arrangement templates:

**`arrangements/python-fasthtml.yaml`**

Based on the validated `examples/fasthtml_app/arrangement.yaml` (post task 05/06):
```yaml
# FastHTML + uv + pytest arrangement
# Usage: sp init --template python-fasthtml
target_language: python

output_paths:
  implementation: src/{name}.py
  tests: tests/test_{name}.py

environment:
  tools: [uv, pytest]
  setup_commands: [uv sync]
  dependencies:
    python-fasthtml: ">=0.12"
    starlette: ">=0.52"
    httpx: ">=0.24"
    pytest: ">=7.0"

build_commands:
  compile: ""
  lint: ""
  test: uv run pytest

constraints:
  - Use python-fasthtml (import from fasthtml.common)
  - Use reference specs for third-party library documentation
  - Tests must use the Starlette test client (from starlette.testclient import TestClient)
  - Guard serve() with: if __name__ == "__main__": serve()
  - Separate layout, routing, and state into distinct specs
```

**`arrangements/nextjs-vitest.yaml`**

Based on the validated `examples/nextjs_ai_chat/arrangement.yaml` (post task 07):
```yaml
# Next.js App Router + TypeScript + vitest arrangement
# Usage: sp init --template nextjs-vitest
target_language: typescript

output_paths:
  implementation: src/{name}.ts
  tests: tests/{name}.test.ts

environment:
  tools: [node, npm]
  setup_commands: [npm install]
  dependencies:
    next: ">=14.0"
    react: ">=18.0"
    typescript: ">=5.0"
    vitest: ">=1.0"
    "@testing-library/react": ">=14.0"

build_commands:
  compile: npx tsc --noEmit
  lint: ""
  test: npx vitest run

constraints:
  - Use TypeScript strict mode
  - Use Next.js App Router (app/ directory), not Pages Router
  - Server components are the default; mark client components with "use client"
  - Use reference specs for third-party SDK documentation (ai, @ai-sdk/openai, etc.)
  - API routes go in app/api/{name}/route.ts
```

**`arrangements/nextjs-playwright.yaml`**

A template for projects needing E2E browser testing (see also task 09):
```yaml
# Next.js + Playwright E2E arrangement
# Usage: sp init --template nextjs-playwright
target_language: typescript

output_paths:
  implementation: src/{name}.ts
  tests: e2e/{name}.spec.ts

environment:
  tools: [node, npm, npx]
  setup_commands: [npm install, npx playwright install --with-deps]
  dependencies:
    next: ">=14.0"
    "@playwright/test": ">=1.40"

build_commands:
  compile: ""
  lint: ""
  test: npx playwright test

constraints:
  - Tests are Playwright E2E tests, not unit tests
  - Use page.goto(), page.click(), page.fill(), page.locator() — not import statements
  - Each test file covers one user-facing feature or page
  - Use data-testid attributes for selectors in generated component code
```

### 2. `sp init --template` flag

Extend `sp init` in `src/specsoloist/cli.py` to accept an optional `--template` argument:

```bash
sp init my-project                           # blank arrangement (current behaviour)
sp init my-project --template python-fasthtml
sp init my-project --template nextjs-vitest
sp init my-project --template nextjs-playwright
```

When a template is specified:
- Look up the template in the `arrangements/` directory bundled with the package
- Copy it to `<project>/arrangement.yaml` instead of the blank template
- Print a short note explaining what was included and what the user needs to do next
  (e.g. "Run `uv init` and `uv add python-fasthtml` to set up the Python project")

Use `importlib.resources` or `pkg_resources` to bundle `arrangements/` with the package so
templates are available after `pip install specsoloist`.

### 3. `sp init --list-templates`

```bash
sp init --list-templates
```

Lists available templates with a one-line description each. Read descriptions from a comment
at the top of each template file (the `# FastHTML + uv + pytest arrangement` line).

### 4. Package the templates

Update `pyproject.toml` to include `arrangements/*.yaml` as package data so templates are
included in the PyPI distribution.

### 5. Document in README and `sp init --help`

Update the README's "Getting Started" section to mention `--template`. Update the `sp init`
help text to list available templates.

## Files to Read First

- `src/specsoloist/cli.py` — `cmd_init()` and `main()`
- `examples/fasthtml_app/arrangement.yaml` — source for FastHTML template
- `examples/nextjs_ai_chat/arrangement.yaml` — source for Next.js template
- `pyproject.toml` — to understand package data configuration
- `score/arrangement.spec.md` — arrangement schema reference

## Success Criteria

1. `arrangements/python-fasthtml.yaml`, `arrangements/nextjs-vitest.yaml`, and
   `arrangements/nextjs-playwright.yaml` exist and are valid arrangement files.
2. `sp init my-project --template python-fasthtml` creates `my-project/arrangement.yaml`
   with the FastHTML template content.
3. `sp init --list-templates` lists all three templates with descriptions.
4. `sp init` without `--template` still works exactly as before (no regression).
5. Templates are included in the installed package (accessible after `pip install specsoloist`).
6. All existing tests pass: `uv run python -m pytest tests/`
7. Ruff passes: `uv run ruff check src/`
