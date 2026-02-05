---
name: config
type: bundle
tags:
  - configuration
  - core
---

# Overview

Configuration management for SpecSoloist. Provides dataclasses for framework configuration and language-specific settings, with support for loading from environment variables and creating LLM provider instances.

# Types

```yaml:types
language_config:
  description: "Configuration for a specific programming language's build and test settings"
  properties:
    extension: {type: string, description: "Source file extension (e.g., '.py')"}
    test_extension: {type: string, description: "Test file extension"}
    test_filename_pattern: {type: string, description: "Pattern for test filenames, e.g., 'test_{name}' or '{name}.test'"}
    test_command: {type: array, items: {type: string}, description: "Command to run tests, with {file} and {build_dir} placeholders"}
    env_vars: {type: object, description: "Environment variables to set when running tests"}
  required: [extension, test_extension, test_filename_pattern, test_command]

specsoloist_config:
  description: "Main configuration for SpecSoloist framework"
  properties:
    llm_provider: {type: string, enum: [gemini, anthropic], description: "LLM provider to use"}
    llm_model: {type: string, optional: true, description: "Model identifier, or null for provider default"}
    api_key: {type: string, optional: true, description: "API key, or null to load from environment"}
    root_dir: {type: string, description: "Project root directory"}
    src_dir: {type: string, description: "Source directory name (relative to root)"}
    build_dir: {type: string, description: "Build output directory name (relative to root)"}
    languages: {type: object, description: "Map of language name to LanguageConfig"}
    src_path: {type: string, description: "Computed absolute path to src directory"}
    build_path: {type: string, description: "Computed absolute path to build directory"}
  required: [llm_provider, root_dir, src_dir, build_dir]
```

# Functions

```yaml:functions
config_from_env:
  inputs:
    root_dir: {type: string, default: ".", description: "Project root directory"}
  outputs:
    config: {type: ref, ref: specsoloist_config}
  behavior: "Load configuration from environment variables: SPECSOLOIST_LLM_PROVIDER (gemini|anthropic), SPECSOLOIST_LLM_MODEL, GEMINI_API_KEY or ANTHROPIC_API_KEY based on provider"

create_provider:
  inputs:
    config: {type: ref, ref: specsoloist_config}
  outputs:
    provider: {type: object, description: "LLMProvider instance (GeminiProvider or AnthropicProvider)"}
  behavior: "Create and return an LLM provider instance based on config.llm_provider"
  contract:
    pre: "config.llm_provider must be 'gemini' or 'anthropic'"
    post: "Returns a valid LLMProvider instance"
  examples:
    - input: {config: {llm_provider: gemini, api_key: "key123"}}
      output: "GeminiProvider instance"
    - input: {config: {llm_provider: unknown}}
      output: "ValueError: Unknown LLM provider"

ensure_directories:
  inputs:
    config: {type: ref, ref: specsoloist_config}
  outputs: {}
  behavior: "Create config.src_path and config.build_path directories if they don't exist"
```

# Constraints

- [NFR-01]: Default languages dict includes Python and TypeScript configurations
- [NFR-02]: src_path and build_path are computed as absolute paths in post-init
- [NFR-03]: API key resolution is provider-aware (GEMINI_API_KEY vs ANTHROPIC_API_KEY)
