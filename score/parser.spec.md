---
name: parser
description: Spec file discovery, reading, parsing, creation, and validation.
type: module
tags:
  - core
  - parsing
dependencies:
  - schema
---

# Overview

Spec file discovery, reading, parsing, creation, and validation. This module is the primary interface for working with `.spec.md` files on disk. It handles YAML frontmatter extraction, structured YAML block parsing (schema, functions, types, steps), template-based spec creation, and type-aware validation.

# Exports

- `SPEC_TYPES`: Set of valid spec type strings.
- `SpecMetadata`: Dataclass holding parsed frontmatter fields.
- `ParsedSpec`: Dataclass holding a fully parsed specification.
- `SpecParser`: Main parser class for spec file operations.

# SPEC_TYPES

A set containing all recognized spec type strings: `"function"`, `"type"`, `"bundle"`, `"module"`, `"workflow"`, `"typedef"`, `"class"`, `"orchestrator"`.

# SpecMetadata

Dataclass representing parsed YAML frontmatter from a spec file.

**Fields:**
- `name` (string, default `""`): Spec identifier.
- `description` (string, default `""`): Human-readable description.
- `type` (string, default `"function"`): One of the recognized spec types.
- `status` (string, default `"draft"`): Lifecycle status (`draft`, `review`, `stable`).
- `version` (string, default `""`): Semver version string.
- `tags` (list of strings, default `[]`): Organizational tags.
- `dependencies` (list, default `[]`): Dependencies; each entry may be a string or a dict.
- `language_target` (optional string, default `None`): Language target override (optional, not recommended in specs).
- `raw` (dict, default `{}`): The complete raw frontmatter dict for accessing non-standard fields.

# ParsedSpec

Dataclass representing a fully parsed specification file.

**Fields:**
- `metadata` (SpecMetadata): Parsed frontmatter.
- `content` (string): Full file content including frontmatter.
- `body` (string): Content with frontmatter stripped.
- `path` (string): Absolute path to the spec file.
- `schema` (optional InterfaceSchema): Parsed `yaml:schema` block, if present.
- `bundle_functions` (dict of string to BundleFunction, default `{}`): Parsed `yaml:functions` block entries.
- `bundle_types` (dict of string to BundleType, default `{}`): Parsed `yaml:types` block entries.
- `steps` (list of WorkflowStep, default `[]`): Parsed `yaml:steps` block entries.

# SpecParser

Main class for spec file operations. Initialized with a source directory path and an optional template directory override.

## Constructor

`SpecParser(src_dir, template_dir=None)`

- `src_dir` (string): Directory where spec files are stored. Stored as an absolute path.
- `template_dir` (optional string): Override for template location, primarily for testing.

## Methods

### get_spec_path(name) -> string

Resolve a spec name to its full file path.

**Behavior:**
- If `name` does not end with `.spec.md`, appends that suffix.
- Returns the absolute path by joining `src_dir` with the resulting filename.

### list_specs() -> list of strings

List all available specification files in the source directory.

**Behavior:**
- Recursively walks `src_dir` looking for files ending in `.spec.md`.
- Returns paths relative to `src_dir`.
- Returns an empty list if `src_dir` does not exist.

### read_spec(name) -> string

Read the raw content of a specification file.

**Behavior:**
- Resolves `name` to a path via `get_spec_path`.
- Returns the full file content as a string.

**Errors:**
- Raises `FileNotFoundError` if the spec file does not exist.

### spec_exists(name) -> bool

Check whether a spec file exists on disk.

### create_spec(name, description, spec_type="function") -> string

Create a new specification file from an appropriate template.

**Behavior:**
- Resolves the path via `get_spec_path`.
- Creates parent directories if they do not exist.
- Writes a template with correct frontmatter (`name`, `type`) and skeleton sections appropriate to the spec type.
- Returns the path to the created file.

**Template contents by type:**
- `function`: Includes `# Overview`, `# Interface` with a `yaml:schema` block, `# Behavior` with FR placeholder, and `# Examples`.
- `type`: Includes `# Overview`, `# Schema` with a `yaml:schema` block, and `# Examples`.
- `bundle`: Includes `# Overview`, `# Functions` with a `yaml:functions` block, and `# Types`.
- `workflow`: Includes `# Overview`, `# Interface` with a `yaml:schema` block, `# Steps` with a `yaml:steps` block, and `# Error Handling`. Frontmatter includes a `dependencies` list.
- `module`: Includes `# Overview` and `# Exports`.

**Errors:**
- Raises `FileExistsError` if the spec file already exists.

### parse_spec(name) -> ParsedSpec

Parse a spec file into structured data.

**Behavior:**
- Reads the file and extracts YAML frontmatter into `SpecMetadata`.
- Strips frontmatter to produce the body.
- Parses structured YAML blocks based on the spec type:
  - `bundle`: Extracts `yaml:functions` and `yaml:types` blocks.
  - `workflow` or `orchestrator`: Extracts `yaml:schema` and `yaml:steps` blocks. If both schema and steps are present, attaches steps to the schema.
  - All other types: Extracts `yaml:schema` block.
- If the frontmatter has no `description`, falls back to extracting the first non-empty, non-heading line after `# Overview` or `# 1. Overview`.

### validate_spec(name) -> dict

Validate a spec for structural correctness based on its type.

**Behavior:**
- Returns a dict with `valid` (bool) and `errors` (list of strings).
- All spec types require YAML frontmatter (content must start with `---`).
- Type-specific required sections:

| Type | Required |
|------|----------|
| `function` or `class` | `# Overview` (or `# 1. Overview`), `# Interface` or a `yaml:schema` block, `# Behavior` (or `# 3. Functional Requirements`) |
| `type` | `# Overview` (or `# 1. Overview`), `# Schema` or a `yaml:schema` block |
| `bundle` | `# Overview` (or `# 1. Overview`), at least one function or type defined in YAML blocks |
| `workflow` or `orchestrator` | `# Overview` (or `# 1. Overview`), steps defined in a `yaml:steps` block |
| `module` | `# Overview` (or `# 1. Overview`), `# Exports` or legacy interface or dependencies |
| `specification` | No additional requirements beyond frontmatter |
| Unknown types | Legacy numbered sections: `# 1. Overview` through `# 5. Design Contract` |

**Errors:**
- Returns `{valid: false, errors: ["Spec file not found."]}` if the file does not exist.
- Returns `{valid: false, errors: ["Parse error: ..."]}` if parsing raises an unexpected exception.

### get_module_name(name) -> string

Extract the module name from a spec filename by stripping the `.spec.md` suffix.

### load_global_context() -> string

Load the global context template for use in compilation prompts.

**Behavior:**
- Loads the file `global_context.md` from templates.
- If `template_dir` is set, looks there first.
- Otherwise, tries package resources (`specsoloist.templates`), then falls back to a local `templates/` directory relative to the module.
- Returns an empty string if no template is found.

# Frontmatter Parsing

The parser extracts YAML frontmatter delimited by `---` markers.

**Behavior:**
- Content must start with `---` (after stripping whitespace) to be recognized as having frontmatter.
- The frontmatter is the text between the first and second `---` markers.
- Parsed via YAML safe_load. If parsing fails, all fields get defaults.
- `tags` must be a list; non-list values are ignored.
- `language_target` accepts either a string or a list (first element is used).
- `dependencies` must be a list; entries can be strings or dicts.

# YAML Block Extraction

The parser extracts content from fenced code blocks with typed labels (e.g., `` ```yaml:schema ``).

**Behavior:**
- Finds the opening marker (e.g., `` ```yaml:schema ``).
- Finds the closing `` ``` `` that appears at the start of a line (preceded by a newline or at position 0).
- Returns the content between the markers, stripped of leading/trailing whitespace.
- Returns None if the block is not found or cannot be parsed.

# Examples

## Frontmatter extraction

| Input frontmatter | Field | Value |
|-------------------|-------|-------|
| `name: test_component` and `description: A test.` | `metadata.description` | `"A test."` |
| `name: test_component` (no description), body has `# 1. Overview\nExtracted desc.` | `metadata.description` | `"Extracted desc."` |
| `name: test_component` (no description), body has `# 1. Overview\n\n\nReal desc.` | `metadata.description` | `"Real desc."` (skips blank lines) |
| `tags: [math, pure]` | `metadata.tags` | `["math", "pure"]` |
| `version: 1.2.3` | `metadata.version` | `"1.2.3"` |
| No `language_target` field | `metadata.language_target` | `None` |
| `dependencies: [step1, step2]` | `metadata.dependencies` | `["step1", "step2"]` |

## Validation

| Spec type | Content | valid? | Error contains |
|-----------|---------|--------|----------------|
| `function` | Has Overview, Interface with yaml:schema, Behavior | `true` | - |
| `bundle` | Has Overview but no yaml:functions or yaml:types | `false` | `"function or type"` |
| `workflow` | Has Overview but no yaml:steps | `false` | `"steps"` |
| (missing file) | - | `false` | `"not found"` |

## Template creation

| spec_type | Template includes |
|-----------|-------------------|
| `function` | `name:`, `type: function`, `# Overview`, `# Interface`, `yaml:schema`, `# Behavior` |
| `bundle` | `name:`, `type: bundle`, `# Overview`, `yaml:functions` |
| `workflow` | `name:`, `type: workflow`, `# Overview`, `yaml:steps` |
