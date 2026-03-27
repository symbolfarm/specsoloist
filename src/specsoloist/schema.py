"""Schema definitions for spec interfaces.

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
        """Checks if this definition (as an output) is compatible with other (as an input)."""
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


class ArrangementOutputPathOverride(BaseModel):
    """Per-spec output path overrides (either field may be omitted to fall back to the default)."""
    implementation: Optional[str] = Field(
        default=None,
        description="Override implementation path for this spec. Omit to use the default template."
    )
    tests: Optional[str] = Field(
        default=None,
        description="Override test path for this spec. Omit to use the default template."
    )


class ArrangementOutputPaths(BaseModel):
    """Output paths for implementation and tests, with optional per-spec overrides."""
    implementation: str = Field(
        description="Path template for implementation files. Use {name} as the spec name placeholder. "
                    "e.g. 'src/{name}.py' or 'src/app/api/{name}/route.ts'."
    )
    tests: str = Field(
        description="Path template for test files. Use {name} as the spec name placeholder. "
                    "e.g. 'tests/test_{name}.py' or 'tests/{name}.test.ts'."
    )
    overrides: Dict[str, ArrangementOutputPathOverride] = Field(
        default_factory=dict,
        description="Per-spec path overrides. Key is spec name (without .spec.md). "
                    "Overrides the default template for that spec only."
    )

    def resolve_implementation(self, name: str) -> str:
        """Return the implementation path for a spec, checking per-spec overrides first."""
        override = self.overrides.get(name)
        if override and override.implementation:
            return override.implementation
        return self.implementation.format(name=name)

    def resolve_tests(self, name: str) -> str:
        """Return the tests path for a spec, checking per-spec overrides first."""
        override = self.overrides.get(name)
        if override and override.tests:
            return override.tests
        return self.tests.format(name=name)


class ArrangementEnvironment(BaseModel):
    """Environment settings for the build."""
    tools: List[str] = Field(
        default_factory=list,
        description="CLI tools that must be available (e.g. 'uv', 'node'). Listed in sp doctor output."
    )
    setup_commands: List[str] = Field(
        default_factory=list,
        description="Shell commands to run before compilation (e.g. 'uv sync', 'npm install')."
    )
    config_files: Dict[str, str] = Field(
        default_factory=dict,
        description="Files to write verbatim before compilation. Key is relative path, value is file content."
    )
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Package name to version specifier (e.g. 'python-fasthtml': '>=0.12,<0.13'). "
                    "Format follows the native package manager: PEP 440 for Python, semver for npm."
    )


class ArrangementBuildCommands(BaseModel):
    """Build, lint, and test commands."""
    compile: Optional[str] = Field(
        default=None,
        description="Optional compile/build step (e.g. 'npx tsc --noEmit' for TypeScript). "
                    "Run after code generation to catch type errors."
    )
    lint: Optional[str] = Field(
        default=None,
        description="Optional lint command (e.g. 'uv run ruff check src/'). "
                    "Run after compilation to enforce code style."
    )
    test: str = Field(
        description="Command to run the test suite (required). "
                    "e.g. 'uv run pytest tests/' or 'npx vitest run'."
    )


class ArrangementEnvVar(BaseModel):
    """Declaration of a single environment variable expected by the project."""
    description: str
    required: bool = True
    example: str = ""


class ArrangementStatic(BaseModel):
    """A verbatim file or directory to copy during sp conduct."""

    source: str = Field(description="Source path relative to the arrangement file.")
    dest: str = Field(description="Destination path relative to the arrangement file.")
    description: str = Field(default="", description="Human-readable note for agents.")
    overwrite: bool = Field(
        default=True,
        description="If False, skip copying when the destination already exists.",
    )


class Arrangement(BaseModel):
    """An Arrangement file bridges a Score (spec) to a specific Build Environment.

    It defines how and where the code should be generated and verified.
    """
    target_language: str = Field(
        description="Language for generated code. e.g. 'python', 'typescript'. "
                    "Injected into every soloist prompt."
    )
    specs_path: str = Field(
        default="src/",
        description="Directory where spec files (.spec.md) are stored. "
                    "Used by sp list, sp status, sp graph, and sp conduct."
    )
    output_paths: ArrangementOutputPaths = Field(
        description="Where to write generated implementation and test files."
    )
    environment: ArrangementEnvironment = Field(
        default_factory=ArrangementEnvironment,
        description="Build environment: tools, setup commands, config files, and dependency versions."
    )
    build_commands: ArrangementBuildCommands = Field(
        description="Shell commands for testing, linting, and compiling the generated code."
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Free-text constraints injected into every soloist prompt. "
                    "e.g. 'Use type hints throughout', 'Follow PEP 8'."
    )
    env_vars: Dict[str, ArrangementEnvVar] = Field(
        default_factory=dict,
        description="Declared environment variable names with descriptions and requirements. "
                    "Values are never stored — only names, descriptions, and whether required."
    )
    static: list[ArrangementStatic] = Field(
        default_factory=list,
        description=(
            "Verbatim files or directories to copy into the output during sp conduct. "
            "Use for docs, templates, scripts, and other hand-crafted assets that are "
            "part of the project but not generated from specs."
        ),
    )
    model: Optional[str] = Field(
        default=None,
        description="LLM model to use for compilation. Overridden by the --model CLI flag. "
                    "Falls back to SPECSOLOIST_LLM_MODEL env var or provider default if unset."
    )


class InterfaceSchema(BaseModel):
    """Represents the interface schema for a spec.

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
        """Runtime validation of input dictionary against schema."""
        raise NotImplementedError(
            "validate_inputs() is not yet implemented. "
            "Workflow step input validation is a planned feature."
        )


class BundleSchema(BaseModel):
    """Schema for a bundle spec containing multiple functions and/or types."""
    functions: Dict[str, BundleFunction] = Field(default_factory=dict)
    types: Dict[str, BundleType] = Field(default_factory=dict)


class StepsSchema(BaseModel):
    """Schema for workflow steps."""
    steps: List[WorkflowStep] = Field(default_factory=list)


def parse_schema_block(raw_yaml: Dict[str, Any]) -> InterfaceSchema:
    """Parses a raw YAML dictionary into an InterfaceSchema."""
    try:
        # Normalize inputs/outputs if they're simple dicts
        normalized = _normalize_schema(raw_yaml)
        return InterfaceSchema(**normalized)
    except ValidationError as e:
        raise ValueError(f"Invalid schema definition: {e}")


def parse_bundle_functions(raw_yaml: Dict[str, Any]) -> Dict[str, BundleFunction]:
    """Parses a yaml:functions block into BundleFunction objects."""
    result = {}
    for name, definition in raw_yaml.items():
        try:
            result[name] = BundleFunction(**definition)
        except ValidationError as e:
            raise ValueError(f"Invalid function '{name}': {e}")
    return result


def parse_bundle_types(raw_yaml: Dict[str, Any]) -> Dict[str, BundleType]:
    """Parses a yaml:types block into BundleType objects."""
    result = {}
    for name, definition in raw_yaml.items():
        try:
            result[name] = BundleType(**definition)
        except ValidationError as e:
            raise ValueError(f"Invalid type '{name}': {e}")
    return result


def parse_steps_block(raw_yaml: List[Dict[str, Any]]) -> List[WorkflowStep]:
    """Parses a yaml:steps block into WorkflowStep objects."""
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
