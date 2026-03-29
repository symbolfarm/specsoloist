# arrangement.yaml Reference

`arrangement.yaml` bridges a set of specs to a specific build environment. It defines
the target language, where to write output files, and how to verify the build.

Run `sp schema` for the auto-generated annotated schema. This file is the narrative guide.

---

## Minimal example

```yaml
target_language: python
output_paths:
  implementation: src/{name}.py
  tests: tests/test_{name}.py
build_commands:
  test: uv run pytest tests/
```

---

## Fields

### `target_language` (required)

Language string injected into every soloist prompt. Use `"python"` or `"typescript"`.
This is the only field that affects what language soloists write — it is not validated
against the output paths.

### `specs_path` (default: `"src/"`)

Directory where spec files (`.spec.md`) are stored. Affects `sp list`, `sp status`,
`sp graph`, and `sp conduct` (when no positional `src_dir` is given).

```yaml
specs_path: specs/       # if your specs live in specs/ instead of src/
```

### `output_paths` (required)

Where to write generated files. Use `{name}` for the leaf spec name or `{path}` for the
full relative path (including subdirectories). For flat specs, `{path}` equals `{name}`.

```yaml
output_paths:
  implementation: src/{name}.py
  tests: tests/test_{name}.py
```

#### `output_paths.overrides`

Per-spec path overrides. Useful when one spec must land at a specific path (e.g. a
Next.js API route). Key is the spec name without `.spec.md`. Either field may be
omitted to fall back to the template.

```yaml
output_paths:
  implementation: src/{name}.ts
  tests: tests/{name}.test.ts
  overrides:
    chat_route:
      implementation: src/app/api/chat/route.ts
      tests: tests/chat_route.test.ts
    auth:
      implementation: src/app/api/auth/[...nextauth]/route.ts
      # tests not overridden — falls back to tests/auth.test.ts
```

### `environment` (optional)

Build environment setup. All sub-fields have empty defaults.

```yaml
environment:
  tools:
    - uv
    - node
  setup_commands:
    - uv sync
    - npm install
  config_files:
    pyproject.toml: |
      [project]
      name = "myapp"
  dependencies:
    python-fasthtml: ">=0.12,<0.13"
    starlette: ">=0.52"
```

- **`tools`**: CLI tools listed in `sp doctor` output. Not automatically installed.
- **`setup_commands`**: Run before compilation. Declared `dependencies` trigger a
  warning if no install command is found here.
- **`config_files`**: Written verbatim before compilation. Key is relative path, value
  is file content.
- **`dependencies`**: Package name → version specifier. Injected into every soloist
  prompt as a "Dependency Versions" table. PEP 440 for Python, semver for npm.

### `build_commands` (required)

```yaml
build_commands:
  test: uv run pytest tests/ -q
  lint: uv run ruff check src/       # optional
  compile: npx tsc --noEmit          # optional, for TypeScript type checking
```

`test` is required. `lint` and `compile` are optional.

### `constraints` (default: `[]`)

Free-text strings injected into every soloist prompt. Use for project-wide conventions.

```yaml
constraints:
  - Use type hints throughout
  - Follow PEP 8
  - Prefer dataclasses over plain dicts
```

### `env_vars` (default: `{}`)

Declare environment variables the project needs. Values are never stored — only names,
descriptions, and whether they are required. `sp doctor --arrangement` warns on unset
required vars.

```yaml
env_vars:
  DATABASE_URL:
    description: PostgreSQL connection string
    required: true
    example: postgresql://user:pass@localhost/mydb
  OPENAI_API_KEY:
    description: OpenAI API key for chat routes
    required: true
    example: sk-...
```

### `static` (default: `[]`)

Verbatim files or directories to copy into the output during `sp conduct`. Use for
docs, templates, scripts, and other hand-crafted assets that are part of the project
but not generated from specs.

```yaml
static:
  - source: help/
    dest: src/myapp/help/
    description: "Bundled help files copied verbatim into the package"
  - source: templates/
    dest: src/myapp/templates/
  - source: scripts/seed.py
    dest: scripts/seed.py
  - source: ARRANGEMENT.md
    dest: ARRANGEMENT.md
    overwrite: false   # don't clobber user edits
```

- **`source`**: Source path relative to the project root (directory containing `arrangement.yaml`).
- **`dest`**: Destination path, also relative to the project root.
- **`description`**: Optional human-readable note (for agents and documentation).
- **`overwrite`**: If `false`, skip copying when the destination already exists. Default: `true`.

Missing source paths produce a warning from `sp doctor` but do not fail the build.

### `model` (optional)

LLM model override for this project. Precedence: `--model` CLI flag > this field >
`SPECSOLOIST_LLM_MODEL` env var > provider default.

```yaml
model: claude-haiku-4-5-20251001
```

---

## Arrangement auto-discovery

`sp list`, `sp status`, `sp graph`, `sp validate`, `sp compile`, `sp conduct`, and
`sp doctor` all auto-discover `arrangement.yaml` in the current working directory when
no `--arrangement FILE` flag is given.

---

## See also

- `sp schema` — annotated schema derived from Pydantic models (always in sync)
- `sp help overrides` — focused guide on `output_paths.overrides`
- `sp help specs-path` — focused guide on `specs_path`
