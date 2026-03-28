# HK-26: Update score specs for event bus integration

## Motivation

Tasks 27–30 added the event bus, event emission, LLMResponse, and NDJSON subscriber.
The score specs (`core.spec.md`, `compiler.spec.md`) do not yet describe the `event_bus`
parameter or `_emit()` / `_generate()` methods. This means a quine run will generate
core.py and compiler.py *without* event emission.

This is fine for now — the quine tests the spec-to-code pipeline, not observability — but
the score should be updated before the next quine validation to avoid drift.

## What to Update

### `score/core.spec.md`

- Add `event_bus: Optional[EventBus] = None` parameter to `SpecSoloistCore.__init__`
- Document `_emit()` helper method
- Note that `compile_project`, `_compile_single_spec`, `run_tests`, and `attempt_fix`
  emit events at method boundaries

### `score/compiler.spec.md`

- Add `event_bus: Optional[EventBus] = None` parameter to `SpecCompiler.__init__`
- Document `_generate()` wrapper that emits `llm.request` / `llm.response` events

### `score/events.spec.md`

- Already exists and is accurate — no changes needed

### Provider specs (if any exist in score/)

- Check if there's a provider spec that needs updating for `LLMResponse` return type

### `score/arrangement.yaml`

- May need to add `events` to the spec list if not auto-discovered

## Success Criteria

- All score specs accurately reflect the current source code
- `sp validate` passes on all updated specs
- `sp diff` shows no drift for updated modules
