# Task: Add `env_vars` Field to Arrangement Schema

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.

Production web apps require environment variables: API keys (`OPENAI_API_KEY`), database
connection strings (`DATABASE_URL`), secrets, feature flags. When soloists generate code
without knowing which environment variables are expected, they sometimes hardcode values,
use wrong variable names, or omit the lookup entirely.

The arrangement is the right place to declare expected environment variables (names and
descriptions, never values). This gives soloists a clear contract and enables `sp doctor`
and `sp validate` to warn when variables are unset.

## What to Build

### 1. Schema change (`src/specsoloist/schema.py`)

Add an optional `env_vars` field to the `Arrangement` model (not to `ArrangementEnvironment`
— this is a project-level concern, not an environment tool concern):

```python
class ArrangementEnvVar(BaseModel):
    description: str
    required: bool = True
    example: str = ""   # a non-secret example value for documentation

class Arrangement(BaseModel):
    ...
    env_vars: dict[str, ArrangementEnvVar] = {}
```

Example arrangement usage:
```yaml
env_vars:
  OPENAI_API_KEY:
    description: "OpenAI API key for the Vercel AI SDK"
    required: true
    example: "sk-..."
  DATABASE_URL:
    description: "SQLite connection string"
    required: false
    example: "sqlite:///./todos.db"
```

### 2. Compiler injection (`src/specsoloist/compiler.py`)

Include `env_vars` in the soloist prompt context:

```
## Environment Variables

This project uses the following environment variables. Reference them by name in generated
code using os.environ['VAR_NAME'] or process.env.VAR_NAME — never hardcode values.

  OPENAI_API_KEY   (required) OpenAI API key for the Vercel AI SDK
  DATABASE_URL     (optional) SQLite connection string, default: sqlite:///./todos.db
```

If `env_vars` is empty, omit the section.

### 3. `sp doctor` check

`sp doctor` already checks for API keys and tool availability. Extend it to check env vars
declared in the arrangement:

```
sp doctor --arrangement arrangement.yaml

  ✓ ANTHROPIC_API_KEY set
  ✗ OPENAI_API_KEY not set  (required by arrangement: OpenAI API key for the Vercel AI SDK)
  ✓ DATABASE_URL not set    (optional — will use default: sqlite:///./todos.db)
```

Read the arrangement file from the current directory if `--arrangement` is not specified.

### 4. `sp validate` warning

When `sp validate` is run in a project with an `arrangement.yaml` that declares required
`env_vars`, and those variables are not set in the current environment, print a warning:

```
⚠ OPENAI_API_KEY is required by arrangement but not set — sp conduct may fail at runtime
```

This is a warning, not an error. The variable might be set in the deployment environment
even if not in the local shell.

### 5. Update the Next.js AI chat arrangement

Update `examples/nextjs_ai_chat/arrangement.yaml` to use the new field:
```yaml
env_vars:
  OPENAI_API_KEY:
    description: "OpenAI API key — get one at https://platform.openai.com"
    required: true
    example: "sk-..."
```

### 6. Update `score/arrangement.spec.md`

Document the new `env_vars` field.

## Files to Read First

- `src/specsoloist/schema.py` — `Arrangement` model
- `src/specsoloist/compiler.py` — prompt construction
- `src/specsoloist/cli.py` — `cmd_doctor()`
- `score/arrangement.spec.md`
- `examples/nextjs_ai_chat/arrangement.yaml`
- `tests/test_arrangement.py`

## Success Criteria

1. `Arrangement.env_vars` is parsed from YAML correctly.
2. Soloist prompts include the env_vars section when vars are declared.
3. `sp doctor --arrangement arrangement.yaml` reports unset required env vars.
4. `sp validate` warns when required env vars are unset.
5. `examples/nextjs_ai_chat/arrangement.yaml` uses the new field.
6. `score/arrangement.spec.md` documents `env_vars`.
7. All existing tests pass: `uv run python -m pytest tests/`
8. Ruff passes: `uv run ruff check src/`
9. New tests cover: parsing env_vars, prompt injection, doctor warning for unset vars.
