# Task 20: Pydantic AI Provider Abstraction

## Status: DISCUSS WITH USER BEFORE STARTING

This is an architectural change with significant scope. Read this task and
output `NEEDS_HUMAN` if picked up by the ralph loop.

## Why

The hand-rolled `LLMProvider` abstraction covers only Gemini and Anthropic, requires
maintenance per-provider, and locks the `--no-agent` path to a small set of models.
Pydantic AI provides:
- Most major providers (OpenAI, Gemini, Anthropic, Ollama, Mistral, Groq...) for free
- Structured outputs via Pydantic models rather than prompt-parsed text
- Consistent retry, timeout, and error handling across providers
- A path to writing custom agents in pure Python, independent of Claude Code / Gemini CLI

Ollama support (via Pydantic AI) is specifically needed for local LLM use cases
(e.g. TamaTalky's pet personality).

## Scope Questions (discuss with user)

1. **Replace or wrap?** Replace `LLMProvider` entirely, or wrap Pydantic AI behind the
   existing interface to minimise blast radius?

2. **Agent independence timeline.** The current architecture uses Claude Code / Gemini CLI
   as the agent runtime for `sp conduct` (agent mode). Pydantic AI opens the door to
   writing conductor/soloist agents in pure Python. Is this a Phase 9 goal, or Phase 10?

3. **Breaking change risk.** Replacing the provider abstraction may change behaviour
   for existing users. Is a major version bump (0.5.0) appropriate for this change?

4. **Ollama first?** Ollama support may be the most immediately useful addition
   (enables local LLM use, zero cost, privacy). Could be added to the existing provider
   abstraction without the full Pydantic AI migration.

## Files to Read (when starting)

- `src/specsoloist/providers/` — existing LLMProvider implementations
- `src/specsoloist/compiler.py` — how providers are called
- `src/specsoloist/config.py` — how provider and model are configured
- Pydantic AI docs: https://ai.pydantic.dev

## Estimated Effort

Medium-Large. The provider abstraction itself is Small, but testing across providers
and ensuring backward compat is Medium. Full agent independence is Large.
