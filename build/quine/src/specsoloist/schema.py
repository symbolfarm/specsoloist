"""Schema definitions and parsers for SpecSoloist's language-agnostic spec format."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ParameterDefinition(BaseModel):
    """Represents a single input or output parameter in a spec interface."""

    type: str
    description: Optional[str] = None
    default: Optional[Any] = None
    required: bool = True
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    pattern: Optional[str] = None
    format: Optional[str] = None
    enum: Optional[list] = None
    ref: Optional[str] = None
    items: Optional[dict] = None
    properties: Optional[dict] = None

    def compatible_with(self, other: "ParameterDefinition") -> bool:
        """Check if this parameter (as output) is compatible with other (as input)."""
        if self.type != other.type:
            return False
        # Check numeric constraints
        if other.minimum is not None and self.maximum is not None:
            if self.maximum < other.minimum:
                return False
        if other.maximum is not None and self.minimum is not None:
            if self.minimum > other.maximum:
                return False
        return True


class WorkflowStep(BaseModel):
    """A single step in a workflow spec."""

    name: str
    spec: str
    checkpoint: bool = False
    inputs: dict = Field(default_factory=dict)


class ContractDefinition(BaseModel):
    """Pre/post conditions."""

    pre: Optional[str] = None
    post: Optional[str] = None
    invariant: Optional[str] = None


class BundleFunction(BaseModel):
    """A function definition within a bundle spec."""

    inputs: dict = Field(default_factory=dict)
    outputs: dict = Field(default_factory=dict)
    behavior: str
    contract: Optional[ContractDefinition] = None
    examples: Optional[list] = None


class BundleType(BaseModel):
    """A type definition within a bundle spec."""

    properties: dict = Field(default_factory=dict)
    required: list = Field(default_factory=list)
    description: Optional[str] = None


class InterfaceSchema(BaseModel):
    """The parsed interface for a spec."""

    inputs: dict[str, ParameterDefinition] = Field(default_factory=dict)
    outputs: dict[str, ParameterDefinition] = Field(default_factory=dict)
    properties: dict = Field(default_factory=dict)
    required: list = Field(default_factory=list)
    steps: Optional[list[WorkflowStep]] = None

    def validate_inputs(self, inputs: dict) -> None:
        """Runtime validation of an input dict against the schema."""
        for name, param in self.inputs.items():
            if param.required and name not in inputs:
                if param.default is None:
                    raise ValueError(f"Required input '{name}' is missing")


class BundleSchema(BaseModel):
    """Container for bundle functions and types."""

    functions: dict[str, BundleFunction] = Field(default_factory=dict)
    types: dict[str, BundleType] = Field(default_factory=dict)


class StepsSchema(BaseModel):
    """Container for workflow steps."""

    steps: list[WorkflowStep] = Field(default_factory=list)


def _normalize_param(raw: Any) -> dict:
    """Normalize shorthand parameter definitions to full dict format."""
    if isinstance(raw, str):
        return {"type": raw}
    if isinstance(raw, dict):
        return raw
    raise ValueError(f"Invalid parameter definition: {raw!r}")


def parse_schema_block(raw_yaml: dict) -> InterfaceSchema:
    """Parse a raw YAML dict into an InterfaceSchema."""
    if not isinstance(raw_yaml, dict):
        raise ValueError(f"Expected dict for schema block, got {type(raw_yaml)}")

    inputs = {}
    for name, raw in raw_yaml.get("inputs", {}).items():
        normalized = _normalize_param(raw)
        inputs[name] = ParameterDefinition(**normalized)

    outputs = {}
    for name, raw in raw_yaml.get("outputs", {}).items():
        normalized = _normalize_param(raw)
        outputs[name] = ParameterDefinition(**normalized)

    properties = raw_yaml.get("properties", {})
    required = raw_yaml.get("required", [])

    steps = None
    if "steps" in raw_yaml:
        steps = parse_steps_block(raw_yaml["steps"])

    return InterfaceSchema(
        inputs=inputs,
        outputs=outputs,
        properties=properties,
        required=required,
        steps=steps,
    )


def parse_bundle_functions(raw_yaml: dict) -> dict[str, BundleFunction]:
    """Parse a yaml:functions block into BundleFunction objects."""
    if not isinstance(raw_yaml, dict):
        raise ValueError(f"Expected dict for functions block, got {type(raw_yaml)}")

    result = {}
    for name, raw in raw_yaml.items():
        if not isinstance(raw, dict):
            raise ValueError(f"Function '{name}' must be a dict, got {type(raw)}")
        if "behavior" not in raw:
            raise ValueError(f"Function '{name}' missing required 'behavior' field")

        contract = None
        if "contract" in raw:
            contract = ContractDefinition(**raw["contract"])

        result[name] = BundleFunction(
            inputs=raw.get("inputs", {}),
            outputs=raw.get("outputs", {}),
            behavior=raw["behavior"],
            contract=contract,
            examples=raw.get("examples"),
        )

    return result


def parse_bundle_types(raw_yaml: dict) -> dict[str, BundleType]:
    """Parse a yaml:types block into BundleType objects."""
    if not isinstance(raw_yaml, dict):
        raise ValueError(f"Expected dict for types block, got {type(raw_yaml)}")

    result = {}
    for name, raw in raw_yaml.items():
        if not isinstance(raw, dict):
            raise ValueError(f"Type '{name}' must be a dict, got {type(raw)}")

        result[name] = BundleType(
            properties=raw.get("properties", {}),
            required=raw.get("required", []),
            description=raw.get("description"),
        )

    return result


def parse_steps_block(raw_yaml: list) -> list[WorkflowStep]:
    """Parse a yaml:steps block into WorkflowStep objects."""
    if not isinstance(raw_yaml, list):
        raise ValueError(f"Expected list for steps block, got {type(raw_yaml)}")

    result = []
    for raw in raw_yaml:
        if not isinstance(raw, dict):
            raise ValueError(f"Step must be a dict, got {type(raw)}")
        if "name" not in raw:
            raise ValueError("Step missing required 'name' field")
        if "spec" not in raw:
            raise ValueError(f"Step '{raw['name']}' missing required 'spec' field")

        result.append(
            WorkflowStep(
                name=raw["name"],
                spec=raw["spec"],
                checkpoint=raw.get("checkpoint", False),
                inputs=raw.get("inputs", {}),
            )
        )

    return result


# Arrangement Types


class ArrangementOutputPathOverride(BaseModel):
    """Per-spec output path overrides."""

    implementation: Optional[str] = None
    tests: Optional[str] = None


class ArrangementOutputPaths(BaseModel):
    """Output paths for implementation and tests."""

    implementation: str
    tests: str
    overrides: dict[str, ArrangementOutputPathOverride] = Field(default_factory=dict)

    def resolve_implementation(self, name: str) -> str:
        """Return the implementation path for the spec."""
        if name in self.overrides and self.overrides[name].implementation:
            return self.overrides[name].implementation
        return self.implementation.replace("{name}", name)

    def resolve_tests(self, name: str) -> str:
        """Return the tests path for the spec."""
        if name in self.overrides and self.overrides[name].tests:
            return self.overrides[name].tests
        return self.tests.replace("{name}", name)


class ArrangementEnvironment(BaseModel):
    """Environment configuration for an arrangement."""

    tools: list[str] = Field(default_factory=list)
    setup_commands: list[str] = Field(default_factory=list)
    config_files: dict[str, str] = Field(default_factory=dict)
    dependencies: dict[str, str] = Field(default_factory=dict)


class ArrangementBuildCommands(BaseModel):
    """Build commands for an arrangement."""

    compile: Optional[str] = None
    lint: Optional[str] = None
    test: str


class ArrangementEnvVar(BaseModel):
    """Declaration of a single environment variable."""

    description: str
    required: bool = True
    example: str = ""


class Arrangement(BaseModel):
    """Top-level build arrangement model."""

    target_language: str
    output_paths: ArrangementOutputPaths
    environment: ArrangementEnvironment = Field(default_factory=ArrangementEnvironment)
    build_commands: ArrangementBuildCommands
    constraints: list[str] = Field(default_factory=list)
    env_vars: dict[str, ArrangementEnvVar] = Field(default_factory=dict)
    model: Optional[str] = None
