# Task 20: Pydantic AI Provider Abstraction

## Why

The hand-rolled `LLMProvider` covers only Gemini and Anthropic and requires maintenance
per-provider. Pydantic AI provides a clean model-agnostic interface with support for
Anthropic, OpenAI, Google Gemini, OpenRouter, Ollama, and others — most of which come
for free via the OpenAI-compatible endpoint pattern.

This migration improves the `--no-agent` path significantly and unblocks Ollama support
for local LLM use cases (e.g. TamaTalky).

## Design Decisions (resolved)

- **Replace `LLMProvider` with Pydantic AI.** The existing abstraction is thin enough
  that a clean replacement is better than wrapping.
- **Priority providers:** Anthropic, OpenAI, Google Gemini, OpenRouter.
- **Ollama** comes for free via the OpenAI-compatible endpoint — include it.
- **CLI agent abstraction** (replacing Claude Code / Gemini CLI as the agent runtime)
  is later work. This task only improves the `--no-agent` / direct LLM path.
- **Version bump:** This is a minor version bump (0.5.0) — `LLMProvider` is internal
  but the config keys (`SPECSOLOIST_LLM_PROVIDER`) may change.

## Pydantic AI Overview

Pydantic AI (`pydantic-ai`) provides:
- `Agent` class with model-agnostic interface
- Structured outputs via Pydantic models
- Built-in retry, timeout, and error handling
- Provider strings like `"anthropic:claude-sonnet-4-6"`, `"openai:gpt-4o"`,
  `"google-gla:gemini-2.0-flash"`, `"ollama:llama3"`
- OpenRouter via `"openai:model-name"` with `base_url` override

## Files to Read

- `src/specsoloist/providers/` — existing `LLMProvider` implementations (Gemini, Anthropic)
- `src/specsoloist/compiler.py` — how providers are called to generate code
- `src/specsoloist/config.py` — `SPECSOLOIST_LLM_PROVIDER` and `SPECSOLOIST_LLM_MODEL`
- `src/specsoloist/schema.py` — `Arrangement` model (model pinning from task 17 may land first)

## Implementation Plan

### 1. Add dependency

```toml
# pyproject.toml
dependencies = [
    "pydantic-ai>=0.0.14",
    ...
]
```

### 2. Replace provider implementations

Remove `src/specsoloist/providers/gemini.py` and `providers/anthropic.py`.

Create `src/specsoloist/providers/pydantic_ai_provider.py`:

```python
from pydantic_ai import Agent
from pydantic_ai.models import Model

def get_model(provider: str, model_name: str) -> str:
    """Map SpecSoloist provider/model config to Pydantic AI model string."""
    if provider == "anthropic":
        return f"anthropic:{model_name}"
    elif provider == "gemini":
        return f"google-gla:{model_name}"
    elif provider == "openai":
        return f"openai:{model_name}"
    elif provider == "openrouter":
        return f"openai:{model_name}"  # uses OpenAI-compat with base_url
    elif provider == "ollama":
        return f"ollama:{model_name}"
    else:
        return model_name  # pass-through for future providers

def generate_code(prompt: str, model_str: str) -> str:
    agent = Agent(model_str)
    result = agent.run_sync(prompt)
    return result.data
```

### 3. Update config

Map the existing `SPECSOLOIST_LLM_PROVIDER` values to Pydantic AI provider strings.
Add `OPENROUTER_API_KEY` and `OLLAMA_BASE_URL` support.

### 4. OpenRouter support

OpenRouter uses OpenAI-compatible API. Pydantic AI supports this via:
```python
from pydantic_ai.models.openai import OpenAIModel
model = OpenAIModel("anthropic/claude-3-5-sonnet", base_url="https://openrouter.ai/api/v1",
                    api_key=os.environ["OPENROUTER_API_KEY"])
```

### 5. Update `sp doctor`

Add checks for `OPENAI_API_KEY`, `OPENROUTER_API_KEY`. Show which providers are available
based on which API keys are set.

## Backward Compatibility

- `SPECSOLOIST_LLM_PROVIDER=gemini` and `SPECSOLOIST_LLM_PROVIDER=anthropic` continue
  to work with the same env var values
- Existing `--model` flag continues to work
- Add `SPECSOLOIST_LLM_PROVIDER=openai`, `openrouter`, `ollama` as new valid values

## Success Criteria

- `SPECSOLOIST_LLM_PROVIDER=anthropic` compiles a spec using Pydantic AI → Anthropic
- `SPECSOLOIST_LLM_PROVIDER=openai` works with `OPENAI_API_KEY`
- `SPECSOLOIST_LLM_PROVIDER=ollama` works with local Ollama (integration test, skip in CI)
- OpenRouter works via `SPECSOLOIST_LLM_PROVIDER=openrouter` + `OPENROUTER_API_KEY`
- All 270 existing tests pass
- `sp doctor` shows available providers based on env vars set

## Tests

- Unit tests for `get_model()` mapping function
- Mock Pydantic AI calls in existing compiler tests (swap the mock target)
- Skip Ollama integration test if `OLLAMA_BASE_URL` not set
