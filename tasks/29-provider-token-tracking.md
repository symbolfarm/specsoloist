# Task 29: Provider token tracking

**Effort**: Small–Medium

**Depends on**: Task 27 (event bus)

## Motivation

LLM API calls are the primary cost of running SpecSoloist. Both the Anthropic and Gemini APIs
return token usage metadata in their responses, but the current providers discard it — they
return only the generated text. This task extracts and emits that metadata so downstream
consumers (token tracker, cost reports, NDJSON logs) can observe LLM usage.

## Design Decisions (locked)

- **New return type**: Providers return a `LLMResponse` dataclass instead of a bare `str`.
  `LLMResponse` has `text` (str), `input_tokens` (int | None), `output_tokens` (int | None),
  `model` (str | None). Fields are optional because not all providers report usage.
- **Backward compatibility**: `LLMResponse.__str__()` returns `self.text`, so existing code
  that treats the return as a string continues to work. Gradually migrate callers to use
  `.text` explicitly (but not required in this task — just ensure nothing breaks).
- **Event emission**: When an event bus is available, the provider (or core, depending on
  where the bus is accessible) emits `llm.request` before the call and `llm.response` after.
- **Provider changes are minimal**: each provider already has a `generate()` method. Change
  the return type and extract usage from the API response object.

## Implementation

### New/modified in `src/specsoloist/providers/`

**`base.py`** (or wherever the Protocol lives):
- Add `LLMResponse` dataclass
- Update `LLMProvider` protocol: `generate()` returns `LLMResponse`

**`anthropic.py`**:
- `response.usage.input_tokens` and `response.usage.output_tokens` are available on the
  Anthropic API response. Extract them into `LLMResponse`.

**`gemini.py`**:
- `response.usage_metadata.prompt_token_count` and `.candidates_token_count` — extract.

**`pydantic_ai_provider.py`**:
- PydanticAI's `result.usage()` returns token counts. Extract.

### Event emission in `src/specsoloist/compiler.py`

The compiler calls `self._provider.generate(prompt)`. Wrap this call to emit:
- `llm.request`: `model`, `prompt_length` (character count — tokens are provider-specific)
- `llm.response`: `model`, `input_tokens`, `output_tokens`, `duration_seconds`

The compiler needs access to the event bus. Pass it from core (similar to how runner gets it
in task 28).

### Tests

- `tests/test_provider_token_tracking.py`
- Mock provider returns `LLMResponse` with token counts
- Verify `LLMResponse.__str__()` returns text (backward compat)
- Verify event emission for `llm.request` and `llm.response`
- Verify existing compiler tests still pass with new return type

## Files to Read Before Starting

- `src/specsoloist/providers/anthropic.py` — current `generate()` implementation
- `src/specsoloist/providers/gemini.py` — same
- `src/specsoloist/providers/pydantic_ai_provider.py` — same
- `src/specsoloist/compiler.py` — where `generate()` is called
- `src/specsoloist/core.py` — how compiler is instantiated

## Success Criteria

- `uv run python -m pytest tests/` — all tests pass (no regressions)
- `uv run ruff check src/` — clean
- Token counts are available in `LLMResponse` for Anthropic and Gemini providers
- `llm.request` / `llm.response` events emitted when bus is present
