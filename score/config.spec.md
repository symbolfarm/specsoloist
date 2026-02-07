---
name: config
type: bundle
tags:
  - configuration
  - core
---

# Overview

Configuration management for SpecSoloist. Defines the settings needed to run the framework: which LLM provider to use, where source and build files live, and how to build/test each supported language.

# Types

## LanguageConfig

Settings for building and testing in a specific programming language.

**Fields:**
- `extension`: source file extension (e.g., `".py"`)
- `test_extension`: test file extension
- `test_filename_pattern`: pattern for test filenames with `{name}` placeholder (e.g., `"test_{name}"` or `"{name}.test"`)
- `test_command`: list of command parts to run tests, with `{file}` and `{build_dir}` placeholders
- `env_vars`: optional dict of environment variables to set when running tests

## SpecSoloistConfig

Main configuration dataclass for the framework.

**Fields:**
- `llm_provider`: string, which LLM backend to use (default: `"gemini"`)
- `llm_model`: optional string, model identifier (None = provider default)
- `api_key`: optional string (None = load from environment)
- `root_dir`: string, project root directory (default: `"."`)
- `src_dir`: string, source directory name relative to root (default: `"src"`)
- `build_dir`: string, build output directory name relative to root (default: `"build"`)
- `languages`: dict mapping language name to `LanguageConfig` (defaults include Python and TypeScript)
- `src_path`: computed absolute path to source directory
- `build_path`: computed absolute path to build directory

`src_path` and `build_path` are computed automatically from `root_dir` + `src_dir`/`build_dir` after construction.

# Functions

## SpecSoloistConfig.from_env(root_dir=".") -> SpecSoloistConfig

Class method. Load configuration from environment variables.

**Environment variables:**
- `SPECSOLOIST_LLM_PROVIDER`: `"gemini"` or `"anthropic"` (default: `"gemini"`)
- `SPECSOLOIST_LLM_MODEL`: model identifier (optional)
- `SPECSOLOIST_SRC_DIR`: source directory name (default: `"src"`)
- API key: `GEMINI_API_KEY` if provider is gemini, `ANTHROPIC_API_KEY` if provider is anthropic

## SpecSoloistConfig.create_provider() -> LLMProvider

Create and return an LLM provider instance based on current config.

- If `llm_provider` is `"gemini"`, return a `GeminiProvider`
- If `llm_provider` is `"anthropic"`, return an `AnthropicProvider`
- Pass `api_key` and `llm_model` (if set) to the provider constructor
- Raise `ValueError` for unknown providers

Providers are imported from `specsoloist.providers`.

## SpecSoloistConfig.ensure_directories()

Create `src_path` and `build_path` directories if they don't exist.

# Default Language Configurations

**Python:**
- extension: `.py`, test_extension: `.py`
- test_filename_pattern: `test_{name}`
- test_command: `["python", "-m", "pytest", "{file}"]`
- env_vars: `{"PYTHONPATH": "{build_dir}"}`

**TypeScript:**
- extension: `.ts`, test_extension: `.ts`
- test_filename_pattern: `{name}.test`
- test_command: `["npx", "-y", "tsx", "{file}"]`
- env_vars: `{}`
