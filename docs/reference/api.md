# Public API Reference

This page documents the public API for using SpecSoloist as a library.

The primary entry point is `SpecSoloistCore`. Supporting types (`BuildResult`,
`SpecSoloistConfig`, arrangement schema classes) are documented below.

For internal module details (resolvers, compilers, parsers), see [Internals](internals.md).

---

## specsoloist

::: specsoloist.SpecSoloistCore

---

::: specsoloist.BuildResult

---

## Configuration

::: specsoloist.SpecSoloistConfig

---

## Arrangement Schema

::: specsoloist.schema.Arrangement

::: specsoloist.schema.ArrangementEnvironment

::: specsoloist.schema.ArrangementOutputPaths

::: specsoloist.schema.ArrangementBuildCommands

::: specsoloist.schema.ArrangementEnvVar

---

## LLM Providers

::: specsoloist.providers.base.LLMProvider

::: specsoloist.providers.gemini.GeminiProvider

::: specsoloist.providers.anthropic.AnthropicProvider

::: specsoloist.providers.pydantic_ai_provider.PydanticAIProvider

---

## spechestra

::: spechestra.conductor.SpecConductor
