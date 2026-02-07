---
name: schema
type: bundle
---

# Overview
Schema definitions and parsers for SpecSoloist interfaces. This bundle defines the data structures for parameters, functions, types, and workflows, and provides functions to parse them from YAML.

# Types
```yaml:types
parameter_definition:
  description: Definition of a single input or output parameter.
  properties:
    type: {type: string}
    description: {type: string}
    default: {type: any}
    required: {type: boolean, default: true}
    minimum: {type: number}
    maximum: {type: number}
    minLength: {type: integer}
    maxLength: {type: integer}
    pattern: {type: string}
    format: {type: string}
    enum: {type: array, items: {type: any}}
    ref: {type: string}
    items: {type: object}
    properties: {type: object}

workflow_step:
  description: A single step in a workflow.
  properties:
    name: {type: string}
    spec: {type: string}
    checkpoint: {type: boolean, default: false}
    inputs:
      type: object
      description: "Mapping of input name to source (e.g., 'step1.outputs.result')"
  required: [name, spec]

contract_definition:
  description: Pre/post conditions and invariants.
  properties:
    pre: {type: string}
    post: {type: string}
    invariant: {type: string}

bundle_function:
  description: A function definition within a bundle.
  properties:
    inputs: {type: object}
    outputs: {type: object}
    behavior: {type: string}
    contract: {type: ref, ref: contract_definition}
    examples: {type: array, items: {type: object}}
  required: [behavior]

bundle_type:
  description: A type definition within a bundle.
  properties:
    properties: {type: object}
    required: {type: array, items: {type: string}}
    description: {type: string}

interface_schema:
  description: Interface schema for a spec.
  properties:
    inputs: {type: object}
    outputs: {type: object}
    properties: {type: object}
    required: {type: array, items: {type: string}}
    steps: {type: array, items: {type: ref, ref: workflow_step}}

bundle_schema:
  description: Schema for a bundle spec.
  properties:
    functions: {type: object}
    types: {type: object}

steps_schema:
  description: Schema for workflow steps.
  properties:
    steps: {type: array, items: {type: ref, ref: workflow_step}}
  required: [steps]
```

# Functions
```yaml:functions
parse_schema_block:
  inputs:
    raw_yaml: {type: object}
  outputs:
    result: {type: ref, ref: interface_schema}
  behavior: "Parses a raw YAML dictionary into an InterfaceSchema, normalizing shorthand parameter definitions (e.g. converting a string 'integer' to {type: 'integer'})."

parse_bundle_functions:
  inputs:
    raw_yaml: {type: object}
  outputs:
    result: {type: object}
  behavior: "Parses a 'yaml:functions' block into a mapping of function names to bundle_function objects."

parse_bundle_types:
  inputs:
    raw_yaml: {type: object}
  outputs:
    result: {type: object}
  behavior: "Parses a 'yaml:types' block into a mapping of type names to bundle_type objects."

parse_steps_block:
  inputs:
    raw_yaml: {type: array, items: {type: object}}
  outputs:
    result: {type: array, items: {type: ref, ref: workflow_step}}
  behavior: "Parses a 'yaml:steps' block into a list of workflow_step objects."

is_compatible:
  inputs:
    source: {type: ref, ref: parameter_definition}
    target: {type: ref, ref: parameter_definition}
  outputs:
    compatible: {type: boolean}
  behavior: "Checks if a source parameter definition (output) is compatible with a target parameter definition (input) based on type and constraints."

validate_inputs:
  inputs:
    schema: {type: ref, ref: interface_schema}
    inputs: {type: object}
  outputs: {}
  behavior: "Performs runtime validation of an input dictionary against the provided interface schema."
```
