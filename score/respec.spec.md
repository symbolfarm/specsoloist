---
name: respec
type: bundle
dependencies:
  - config
tags:
  - core
  - reverse-engineering
---

# Overview

Reverse-engineers source code into SpecSoloist specifications using LLM providers. Provides a programmatic fallback for when agent-based reverse engineering is not used.

# Functions

```yaml:functions
respec_init:
  inputs:
    config:
      type: optional
      of: {type: ref, ref: config/specsoloist_config}
      description: SpecSoloist configuration.
    provider:
      type: optional
      of: {type: object}
      description: LLMProvider instance.
  outputs:
    respecer:
      type: object
      description: An initialized Respecer instance.
  behavior: "Initialize a Respecer with config (defaults to environment configuration) and provider (defaults to provider created from config)."

respec:
  inputs:
    respecer:
      type: object
      description: Respecer instance.
    source_path:
      type: string
      description: Path to the source code file.
    test_path:
      type: optional
      of: {type: string}
      description: Optional path to a test file.
    model:
      type: optional
      of: {type: string}
      description: Optional LLM model identifier.
  outputs:
    spec_content:
      type: string
      description: The generated spec content in Markdown format.
  behavior: |
    Generate a specification from source code:
    1. Verify existence of source_path; raise FileNotFoundError if missing.
    2. Read source code from source_path.
    3. Read spec format rules from 'score/spec_format.spec.md' relative to config root.
    4. If test_path is provided and exists, read its content.
    5. Construct a structured prompt for the LLM including role, goal, spec rules, source code, test context, and specific instructions for analysis and output format.
    6. Call the LLM provider to generate a response using the prompt and optional model.
    7. Clean the response by stripping Markdown code fences and return the result.

clean_response:
  inputs:
    response:
      type: string
      description: Raw LLM response.
  outputs:
    cleaned:
      type: string
      description: Response with Markdown code fences removed.
  behavior: "Remove '```markdown' and '```' fences from the beginning and end of the response string."
```
