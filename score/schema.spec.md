---
name: schema
type: bundle
tags:
  - core
  - validation
---

# Overview

Schema definitions and parsers for SpecSoloist's language-agnostic spec format. Defines the data models for spec interfaces (parameters, functions, types, workflows) and provides functions to parse them from raw YAML.

Uses Pydantic for data validation.

# Types

## ParameterDefinition

Represents a single input or output parameter in a spec interface.

**Fields:**
- `type`: string (required) — the parameter type (integer, string, array, object, ref, etc.)
- `description`: optional string
- `default`: optional any — default value
- `required`: boolean (default true)
- `minimum`, `maximum`: optional numeric constraints
- `minLength`, `maxLength`: optional string length constraints
- `pattern`, `format`: optional string validation
- `enum`: optional list of allowed values
- `ref`: optional string — reference to another type spec
- `items`: optional dict — type of array items
- `properties`: optional dict — nested object properties

**Methods:**
- `compatible_with(other)` -> bool: checks if this parameter (as an output) is compatible with `other` (as an input). Types must match; if the target has numeric constraints, the source must satisfy them.

## WorkflowStep

A single step in a workflow spec.

**Fields:** `name` (string), `spec` (string — which spec to run), `checkpoint` (bool, default false), `inputs` (dict mapping input names to source expressions like `"step1.outputs.result"`).

## ContractDefinition

Pre/post conditions. **Fields:** `pre`, `post`, `invariant` (all optional strings).

## BundleFunction

A function definition within a bundle spec. **Fields:** `inputs` (dict), `outputs` (dict), `behavior` (string, required), `contract` (optional ContractDefinition), `examples` (optional list).

## BundleType

A type definition within a bundle spec. **Fields:** `properties` (dict), `required` (list of strings), `description` (optional string).

## InterfaceSchema

The parsed interface for a spec. Used for function specs (inputs/outputs), type specs (properties/required), and workflow specs (inputs/outputs/steps).

**Fields:** `inputs` (dict of ParameterDefinition), `outputs` (dict of ParameterDefinition), `properties` (dict), `required` (list), `steps` (optional list of WorkflowStep).

**Methods:**
- `validate_inputs(inputs)`: runtime validation of an input dict against the schema.

## BundleSchema

Container for bundle functions and types. **Fields:** `functions` (dict of BundleFunction), `types` (dict of BundleType).

## StepsSchema

Container for workflow steps. **Fields:** `steps` (list of WorkflowStep).

# Functions

```yaml:functions
parse_schema_block:
  inputs:
    raw_yaml: {type: object}
  outputs:
    result: {type: ref, ref: interface_schema}
  behavior: "Parse a raw YAML dict into an InterfaceSchema, normalizing shorthand parameter definitions (e.g., a bare string 'integer' becomes {type: 'integer'})"

parse_bundle_functions:
  inputs:
    raw_yaml: {type: object}
  outputs:
    result: {type: object, description: Dict of function name to BundleFunction}
  behavior: "Parse a yaml:functions block into BundleFunction objects"

parse_bundle_types:
  inputs:
    raw_yaml: {type: object}
  outputs:
    result: {type: object, description: Dict of type name to BundleType}
  behavior: "Parse a yaml:types block into BundleType objects"

parse_steps_block:
  inputs:
    raw_yaml: {type: array, items: {type: object}}
  outputs:
    result: {type: array, items: {type: ref, ref: workflow_step}}
  behavior: "Parse a yaml:steps block into WorkflowStep objects"
```

# Constraints

- All parse functions raise `ValueError` with descriptive messages on invalid input
- Parameter normalization handles shorthand (bare string type names) transparently
