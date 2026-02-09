"""
Schema definitions for spec interfaces.

Supports the language-agnostic spec format with:
- Function/type interface schemas
- Bundle schemas (multiple functions/types)
- Workflow step definitions
"""

from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, ValidationError


class ParameterDefinition(BaseModel):
    """Definition of a single input or output parameter."""
    type: str
    description: Optional[str] = None
    default: Optional[Any] = None
    required: bool = True
    # Numeric constraints
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    # String constraints
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    pattern: Optional[str] = None
    format: Optional[str] = None  # email, uuid, uri, etc.
    # Enum constraint
    enum: Optional[List[Any]] = None
    # Reference to another type
    ref: Optional[str] = None
    # Array items type
    items: Optional[Dict[str, Any]] = None
    # Object properties (for nested objects)
    properties: Optional[Dict[str, Any]] = None

    def compatible_with(self, other: 'ParameterDefinition') -> bool:
        """Checks if this definition (as an output) is compatible with other (as an input).

        Types must match; if the target has numeric constraints, the source must satisfy them.
        """
        # Basic type check
        if self.type != other.type:
            return False

        # Basic constraint check (if we have a range, it must be within their range)
        if other.minimum is not None and (self.minimum is None or self.minimum < other.minimum):
            return False
        if other.maximum is not None and (self.maximum is None or self.maximum > other.maximum):
            return False

        return True


class WorkflowStep(BaseModel):
    """A single step in a workflow."""
    name: str
    spec: str
    checkpoint: bool = False
    inputs: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of input name to source (e.g., 'step1.outputs.result')"
    )


class ContractDefinition(BaseModel):
    """Pre/post conditions and invariants."""
    pre: Optional[str] = None
    post: Optional[str] = None
    invariant: Optional[str] = None


class BundleFunction(BaseModel):
    """A function definition within a bundle."""
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    behavior: str
    contract: Optional[ContractDefinition] = None
    examples: Optional[List[Dict[str, Any]]] = None


class BundleType(BaseModel):
    """A type definition within a bundle."""
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class InterfaceSchema(BaseModel):
    """
    Represents the interface schema for a spec.

    Used for:
    - Function specs: inputs/outputs
    - Type specs: properties/required
    - Workflow specs: inputs/outputs/steps
    """
    # For function/workflow specs
    inputs: Dict[str, ParameterDefinition] = Field(default_factory=dict)
    outputs: Dict[str, ParameterDefinition] = Field(default_factory=dict)

    # For type specs
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)

    # For workflow specs
    steps: Optional[List[WorkflowStep]] = None

    def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Runtime validation of input dictionary against schema.

        Validates that all required inputs are present and match expected types.
        """
        for param_name, param_def in self.inputs.items():
            if param_def.required and param_name not in inputs:
                raise ValueError(f"Missing required input: {param_name}")


class BundleSchema(BaseModel):
    """Schema for a bundle spec containing multiple functions and/or types."""
    functions: Dict[str, BundleFunction] = Field(default_factory=dict)
    types: Dict[str, BundleType] = Field(default_factory=dict)


class StepsSchema(BaseModel):
    """Schema for workflow steps."""
    steps: List[WorkflowStep] = Field(default_factory=list)


def parse_schema_block(raw_yaml: Dict[str, Any]) -> InterfaceSchema:
    """Parse a raw YAML dict into an InterfaceSchema.

    Normalizes shorthand parameter definitions (e.g., a bare string 'integer'
    becomes {type: 'integer'}).

    Raises ValueError on invalid input.
    """
    try:
        # Normalize inputs/outputs if they're simple dicts
        normalized = _normalize_schema(raw_yaml)
        return InterfaceSchema(**normalized)
    except ValidationError as e:
        raise ValueError(f"Invalid schema definition: {e}")


def parse_bundle_functions(raw_yaml: Dict[str, Any]) -> Dict[str, BundleFunction]:
    """Parse a yaml:functions block into BundleFunction objects.

    Raises ValueError on invalid input.
    """
    result = {}
    for name, definition in raw_yaml.items():
        try:
            result[name] = BundleFunction(**definition)
        except ValidationError as e:
            raise ValueError(f"Invalid function '{name}': {e}")
    return result


def parse_bundle_types(raw_yaml: Dict[str, Any]) -> Dict[str, BundleType]:
    """Parse a yaml:types block into BundleType objects.

    Raises ValueError on invalid input.
    """
    result = {}
    for name, definition in raw_yaml.items():
        try:
            result[name] = BundleType(**definition)
        except ValidationError as e:
            raise ValueError(f"Invalid type '{name}': {e}")
    return result


def parse_steps_block(raw_yaml: List[Dict[str, Any]]) -> List[WorkflowStep]:
    """Parse a yaml:steps block into WorkflowStep objects.

    Raises ValueError on invalid input.
    """
    result = []
    for step_data in raw_yaml:
        try:
            result.append(WorkflowStep(**step_data))
        except ValidationError as e:
            raise ValueError(f"Invalid step: {e}")
    return result


def _normalize_schema(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes shorthand schema notation to full ParameterDefinition format."""
    result = dict(raw)

    # Normalize inputs
    if "inputs" in result and isinstance(result["inputs"], dict):
        result["inputs"] = {
            k: _normalize_param(v) for k, v in result["inputs"].items()
        }

    # Normalize outputs
    if "outputs" in result and isinstance(result["outputs"], dict):
        result["outputs"] = {
            k: _normalize_param(v) for k, v in result["outputs"].items()
        }

    return result


def _normalize_param(param: Any) -> Dict[str, Any]:
    """Normalizes a parameter definition from shorthand to full format."""
    if isinstance(param, dict):
        # Already a dict, ensure it has 'type' if it has other fields
        if "type" not in param and len(param) > 0:
            # Might be a shorthand like {type: integer, minimum: 0}
            return param
        return param
    elif isinstance(param, str):
        # Shorthand: just the type name
        return {"type": param}
    else:
        # Unknown format, return as-is
        return {"type": str(param)}
