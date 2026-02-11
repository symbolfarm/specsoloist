---
name: composer
type: bundle
status: draft
dependencies:
  - config
  - parser
---

# Overview

Composer is the architect component of Spechestra. It takes plain English requests and drafts a complete spec architecture -- the dependency graph and individual `*.spec.md` files for each component. This is the "vibe-coding" entry point: users describe what they want, and Composer figures out the architecture.

# Types

## ComponentDef

Definition of a single component in an architecture plan.

**Fields:** `name` (string), `type` (string -- one of function, type, bundle, module, workflow), `description` (string), `inputs` (dict, default empty), `outputs` (dict, default empty), `dependencies` (list of strings, default empty).

## Architecture

An architecture plan for a project, consisting of components and their relationships.

**Fields:** `components` (list of ComponentDef), `dependencies` (dict mapping component name to list of dependency names), `build_order` (list of component name strings), `description` (string, default empty).

**Methods:**
- `to_yaml()` -> string -- serialize the architecture to a YAML string
- `from_yaml(yaml_str)` (classmethod) -> Architecture -- parse an Architecture from a YAML string; components in the YAML each have name, type, description, and dependencies fields

## CompositionResult

Result of a compose operation.

**Fields:** `architecture` (Architecture), `spec_paths` (list of file path strings), `ready_for_build` (bool), `cancelled` (bool, default false).

# Functions

## Composer (class)

The main composer class. Constructed with a project directory path, an optional `SpecSoloistConfig`, and an optional `LLMProvider`. If config is not provided, loads from environment. The LLM provider is created lazily from the config when first needed.

### draft_architecture(request, context=None) -> Architecture

Draft an architecture plan from a natural language request.

- `request`: string, natural language description of desired software
- `context`: optional dict with additional context (e.g., existing specs)

**Behavior:**
- Sends the request to the LLM with instructions to break it into discrete components, identify dependencies, and suggest a build order.
- If context contains an `existing_specs` key, includes those spec names in the prompt so the LLM can integrate with existing components.
- Parses the LLM response (expected as YAML) into an Architecture object.
- If the YAML response cannot be parsed, returns an empty Architecture rather than raising an error.
- Does NOT create any files on disk.

### generate_specs(architecture) -> list of strings

Generate `*.spec.md` files for each component in the architecture.

- `architecture`: Architecture object to generate specs for

**Behavior:**
- For each component in the architecture, generates a spec file using the LLM.
- Skips components whose specs already exist (checked via the parser).
- Writes spec files to the configured src directory as `{component_name}.spec.md`.
- Creates parent directories if they do not exist.
- Returns a list of file paths for the specs that were created (not skipped).

### compose(request, auto_accept=False, context=None) -> CompositionResult

Full composition workflow: draft architecture then generate specs.

- `request`: string, natural language description
- `auto_accept`: bool, if true skip review prompts (default false)
- `context`: optional dict

**Behavior:**
- Discovers existing specs in the project and includes them in the context automatically.
- Calls `draft_architecture` to create the architecture plan.
- If the architecture has no components, returns a result with `cancelled=True` and `ready_for_build=False`.
- Calls `generate_specs` to create spec files.
- Returns a CompositionResult with the architecture, created spec paths, and `ready_for_build=True`.

# Behavior

## Separation of concerns

Composer never compiles specs into code. Its job ends when spec files exist on disk. Compilation is the responsibility of Conductor and SpecSoloistCore.

## LLM interaction

All architecture drafting and spec content generation happens through the LLM provider. The composer constructs prompts and parses responses. LLM results may vary between calls; the composer handles malformed responses gracefully by falling back to empty/minimal structures.

## Idempotency

Existing spec files are never overwritten. If a spec with the same name already exists, it is skipped during generation. This makes `generate_specs` safe to call multiple times.

# Examples

| Scenario | Input | Expected |
|----------|-------|----------|
| Initialize composer | `Composer("/path/to/project")` | `project_dir` is set to the absolute path |
| Architecture with dependencies | Components: add (function), calc (module depending on add) | `arch.build_order == ["add", "calc"]`, `arch.dependencies == {"calc": ["add"]}` |
| Composition result | Architecture with no components | `result.cancelled == True`, `result.ready_for_build == False` |
| Composition result | Architecture with components | `result.ready_for_build == True`, `result.spec_paths` contains created paths |
| Existing spec | Component "auth" already has a spec file | "auth" skipped, not in returned paths |
