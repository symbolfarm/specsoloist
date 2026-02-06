---
name: schema
type: bundle
---

# Overview
Schema definitions and parsing logic for the SpecSoloist format. This includes the data structures for parameters, workflow steps, contracts, and the various schema blocks (interface, bundle, steps) used in specification files.

# Types
```yaml:types
parameter_definition:
  properties:
    type: {type: string}
    description: {type: string}
    default: {type: any}
    required: {type: boolean}
    minimum: {type: number}
    maximum: {type: number}
    minLength: {type: integer}
    maxLength: {type: integer}
    pattern: {type: string}
    format: {type: string}
    enum: {type: array}
    ref: {type: string}
    items: {type: object}
    properties: {type: object}
  required: [type]

workflow_step:
  properties:
    name: {type: string}
    spec: {type: string}
    checkpoint: {type: boolean}
    inputs: {type: object}
  required: [name, spec]

contract_definition:
  properties:
    pre: {type: string}
    post: {type: string}
    invariant: {type: string}

bundle_function:
  properties:
    inputs: {type: object}
    outputs: {type: object}
    behavior: {type: string}
    contract: {type: ref, ref: schema/contract_definition}
    examples: {type: array}
  required: [behavior]

bundle_type:
  properties:
    properties: {type: object}
    required: {type: array, items: {type: string}}
    description: {type: string}
  required: [properties]

interface_schema:
  properties:
    inputs: {type: object}
    outputs: {type: object}
    properties: {type: object}
    required: {type: array, items: {type: string}}
    steps: {type: array}

bundle_schema:
  properties:
    functions: {type: object}
    types: {type: object}

steps_schema:
  properties:
    steps: {type: array}
  required: [steps]
```

# Functions
```yaml:functions
compatible_with:
  inputs:
    self: {type: ref, ref: schema/parameter_definition}
    other: {type: ref, ref: schema/parameter_definition}
  outputs: {result: boolean}
  behavior: "Return true if self (as output) is compatible with other (as input) based on type and numeric constraints"

parse_schema_block:
  inputs: {raw_yaml: object}
  outputs: {result: {type: ref, ref: schema/interface_schema}}
  behavior: Parse a raw YAML dictionary into an InterfaceSchema, normalizing shorthand parameter notation

parse_bundle_functions:
  inputs: {raw_yaml: object}
  outputs: {result: object}
  behavior: "Parse a yaml:functions block into a map of BundleFunction objects"

parse_bundle_types:
  inputs: {raw_yaml: object}
  outputs: {result: object}
  behavior: "Parse a yaml:types block into a map of BundleType objects"

parse_steps_block:
  inputs: {raw_yaml: array}
  outputs: {result: {type: array}}
  behavior: "Parse a yaml:steps block into a list of WorkflowStep objects"
```
