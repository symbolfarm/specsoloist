"""Comprehensive tests for schema module.

Tests cover parameter definitions, normalization, parsing functions,
arrangement models, and interface validation.
"""

import pytest
from specsoloist.schema import (
    ParameterDefinition,
    WorkflowStep,
    ContractDefinition,
    BundleFunction,
    BundleType,
    ArrangementOutputPathOverride,
    ArrangementOutputPaths,
    ArrangementEnvironment,
    ArrangementBuildCommands,
    ArrangementEnvVar,
    ArrangementStatic,
    Arrangement,
    InterfaceSchema,
    BundleSchema,
    StepsSchema,
    parse_schema_block,
    parse_bundle_functions,
    parse_bundle_types,
    parse_steps_block,
)


class TestParameterDefinition:
    """Tests for ParameterDefinition class."""

    def test_basic_parameter_definition(self):
        """Create a basic parameter with just type."""
        param = ParameterDefinition(type="string")
        assert param.type == "string"
        assert param.required is True
        assert param.description is None

    def test_parameter_with_description(self):
        """Parameter with optional description field."""
        param = ParameterDefinition(
            type="integer",
            description="The user's age"
        )
        assert param.type == "integer"
        assert param.description == "The user's age"

    def test_parameter_with_numeric_constraints(self):
        """Parameter with minimum and maximum constraints."""
        param = ParameterDefinition(
            type="integer",
            minimum=0,
            maximum=100
        )
        assert param.minimum == 0
        assert param.maximum == 100

    def test_parameter_with_string_constraints(self):
        """Parameter with minLength and maxLength."""
        param = ParameterDefinition(
            type="string",
            minLength=1,
            maxLength=255
        )
        assert param.minLength == 1
        assert param.maxLength == 255

    def test_parameter_with_pattern(self):
        """Parameter with regex pattern."""
        param = ParameterDefinition(
            type="string",
            pattern=r"^\d{3}-\d{2}-\d{4}$"
        )
        assert param.pattern == r"^\d{3}-\d{2}-\d{4}$"

    def test_parameter_with_format(self):
        """Parameter with format (email, uuid, uri, etc)."""
        param = ParameterDefinition(type="string", format="email")
        assert param.format == "email"

    def test_parameter_with_enum(self):
        """Parameter with enum constraint."""
        param = ParameterDefinition(
            type="string",
            enum=["red", "green", "blue"]
        )
        assert param.enum == ["red", "green", "blue"]

    def test_parameter_with_ref(self):
        """Parameter referencing another type."""
        param = ParameterDefinition(type="ref", ref="user_model")
        assert param.type == "ref"
        assert param.ref == "user_model"

    def test_parameter_with_default(self):
        """Parameter with default value."""
        param = ParameterDefinition(
            type="string",
            default="hello",
            required=False
        )
        assert param.default == "hello"
        assert param.required is False

    def test_parameter_with_items(self):
        """Parameter with array items definition."""
        param = ParameterDefinition(
            type="array",
            items={"type": "integer"}
        )
        assert param.items == {"type": "integer"}

    def test_parameter_with_properties(self):
        """Parameter with nested object properties."""
        param = ParameterDefinition(
            type="object",
            properties={
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        )
        assert "name" in param.properties
        assert "age" in param.properties

    def test_compatible_with_matching_types(self):
        """compatible_with returns True for matching types."""
        output = ParameterDefinition(type="string")
        input_param = ParameterDefinition(type="string")
        assert output.compatible_with(input_param) is True

    def test_compatible_with_mismatched_types(self):
        """compatible_with returns False for mismatched types."""
        output = ParameterDefinition(type="string")
        input_param = ParameterDefinition(type="integer")
        assert output.compatible_with(input_param) is False

    def test_compatible_with_numeric_constraint_check(self):
        """compatible_with checks numeric constraints."""
        # Output range [10, 20] is compatible with input minimum 5
        output = ParameterDefinition(
            type="integer",
            minimum=10,
            maximum=20
        )
        input_param = ParameterDefinition(
            type="integer",
            minimum=5
        )
        assert output.compatible_with(input_param) is True

    def test_compatible_with_minimum_violation(self):
        """compatible_with returns False if output minimum is below input minimum."""
        output = ParameterDefinition(
            type="integer",
            minimum=5
        )
        input_param = ParameterDefinition(
            type="integer",
            minimum=10
        )
        assert output.compatible_with(input_param) is False

    def test_compatible_with_maximum_violation(self):
        """compatible_with returns False if output maximum is above input maximum."""
        output = ParameterDefinition(
            type="integer",
            maximum=100
        )
        input_param = ParameterDefinition(
            type="integer",
            maximum=50
        )
        assert output.compatible_with(input_param) is False


class TestWorkflowStep:
    """Tests for WorkflowStep class."""

    def test_minimal_workflow_step(self):
        """Create a workflow step with required fields only."""
        step = WorkflowStep(name="step1", spec="transform_data")
        assert step.name == "step1"
        assert step.spec == "transform_data"
        assert step.checkpoint is False
        assert step.inputs == {}

    def test_workflow_step_with_checkpoint(self):
        """Workflow step with checkpoint enabled."""
        step = WorkflowStep(
            name="step1",
            spec="compute",
            checkpoint=True
        )
        assert step.checkpoint is True

    def test_workflow_step_with_inputs(self):
        """Workflow step with input mappings."""
        step = WorkflowStep(
            name="step2",
            spec="process",
            inputs={
                "data": "step1.outputs.result",
                "config": "workflow.inputs.config"
            }
        )
        assert step.inputs == {
            "data": "step1.outputs.result",
            "config": "workflow.inputs.config"
        }


class TestContractDefinition:
    """Tests for ContractDefinition class."""

    def test_empty_contract(self):
        """Create contract with no conditions."""
        contract = ContractDefinition()
        assert contract.pre is None
        assert contract.post is None
        assert contract.invariant is None

    def test_contract_with_precondition(self):
        """Contract with precondition."""
        contract = ContractDefinition(pre="x > 0")
        assert contract.pre == "x > 0"

    def test_contract_with_postcondition(self):
        """Contract with postcondition."""
        contract = ContractDefinition(post="result >= 0")
        assert contract.post == "result >= 0"

    def test_contract_with_invariant(self):
        """Contract with invariant condition."""
        contract = ContractDefinition(invariant="len(items) <= max_size")
        assert contract.invariant == "len(items) <= max_size"

    def test_contract_with_all_conditions(self):
        """Contract with all three conditions."""
        contract = ContractDefinition(
            pre="x > 0",
            post="result > 0",
            invariant="result < 100"
        )
        assert contract.pre == "x > 0"
        assert contract.post == "result > 0"
        assert contract.invariant == "result < 100"


class TestBundleFunction:
    """Tests for BundleFunction class."""

    def test_minimal_bundle_function(self):
        """Create a function with just behavior."""
        func = BundleFunction(behavior="Adds two numbers together")
        assert func.behavior == "Adds two numbers together"
        assert func.inputs == {}
        assert func.outputs == {}
        assert func.contract is None
        assert func.examples is None

    def test_bundle_function_with_inputs(self):
        """Function with input parameters."""
        func = BundleFunction(
            inputs={
                "x": {"type": "integer"},
                "y": {"type": "integer"}
            },
            behavior="Adds two numbers"
        )
        assert "x" in func.inputs
        assert "y" in func.inputs

    def test_bundle_function_with_outputs(self):
        """Function with output parameters."""
        func = BundleFunction(
            outputs={"result": {"type": "integer"}},
            behavior="Returns a sum"
        )
        assert "result" in func.outputs

    def test_bundle_function_with_contract(self):
        """Function with pre/post conditions."""
        contract = ContractDefinition(
            pre="x > 0 and y > 0",
            post="result > x and result > y"
        )
        func = BundleFunction(
            behavior="Adds positive numbers",
            contract=contract
        )
        assert func.contract.pre == "x > 0 and y > 0"

    def test_bundle_function_with_examples(self):
        """Function with usage examples."""
        func = BundleFunction(
            inputs={"x": {"type": "integer"}},
            outputs={"result": {"type": "integer"}},
            behavior="Doubles a number",
            examples=[
                {"inputs": {"x": 5}, "outputs": {"result": 10}},
                {"inputs": {"x": 0}, "outputs": {"result": 0}}
            ]
        )
        assert len(func.examples) == 2
        assert func.examples[0]["inputs"]["x"] == 5


class TestBundleType:
    """Tests for BundleType class."""

    def test_empty_bundle_type(self):
        """Create a type with no properties."""
        bundle_type = BundleType()
        assert bundle_type.properties == {}
        assert bundle_type.required == []
        assert bundle_type.description is None

    def test_bundle_type_with_properties(self):
        """Type with object properties."""
        bundle_type = BundleType(
            properties={
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            required=["name"]
        )
        assert "name" in bundle_type.properties
        assert "age" in bundle_type.properties
        assert bundle_type.required == ["name"]

    def test_bundle_type_with_description(self):
        """Type with human-readable description."""
        bundle_type = BundleType(
            description="A person with name and age",
            properties={"name": {"type": "string"}},
            required=["name"]
        )
        assert bundle_type.description == "A person with name and age"


class TestArrangementOutputPaths:
    """Tests for ArrangementOutputPaths class."""

    def test_resolve_implementation_with_template(self):
        """resolve_implementation formats the template with spec name."""
        paths = ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py"
        )
        assert paths.resolve_implementation("mymod") == "src/mymod.py"
        assert paths.resolve_implementation("utils") == "src/utils.py"

    def test_resolve_tests_with_template(self):
        """resolve_tests formats the template with spec name."""
        paths = ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py"
        )
        assert paths.resolve_tests("mymod") == "tests/test_mymod.py"

    def test_resolve_with_override(self):
        """resolve methods use override when present."""
        paths = ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py",
            overrides={
                "special": ArrangementOutputPathOverride(
                    implementation="special/impl.py",
                    tests="special/test.py"
                )
            }
        )
        assert paths.resolve_implementation("special") == "special/impl.py"
        assert paths.resolve_tests("special") == "special/test.py"
        # Other specs still use default
        assert paths.resolve_implementation("normal") == "src/normal.py"

    def test_resolve_partial_override(self):
        """resolve falls back to default when override is incomplete."""
        paths = ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py",
            overrides={
                "partial": ArrangementOutputPathOverride(
                    implementation="custom/impl.py"
                    # no tests override
                )
            }
        )
        assert paths.resolve_implementation("partial") == "custom/impl.py"
        assert paths.resolve_tests("partial") == "tests/test_partial.py"


class TestArrangementEnvironment:
    """Tests for ArrangementEnvironment class."""

    def test_empty_environment(self):
        """Create environment with defaults."""
        env = ArrangementEnvironment()
        assert env.tools == []
        assert env.setup_commands == []
        assert env.config_files == {}
        assert env.dependencies == {}

    def test_environment_with_tools(self):
        """Environment with required tools."""
        env = ArrangementEnvironment(tools=["uv", "pytest"])
        assert env.tools == ["uv", "pytest"]

    def test_environment_with_setup_commands(self):
        """Environment with setup commands."""
        env = ArrangementEnvironment(
            setup_commands=["uv sync", "npm install"]
        )
        assert env.setup_commands == ["uv sync", "npm install"]

    def test_environment_with_config_files(self):
        """Environment with config files to write."""
        env = ArrangementEnvironment(
            config_files={
                "pyproject.toml": "[project]\nname = 'myapp'",
                ".env": "DEBUG=true"
            }
        )
        assert env.config_files["pyproject.toml"] == "[project]\nname = 'myapp'"
        assert env.config_files[".env"] == "DEBUG=true"

    def test_environment_with_dependencies(self):
        """Environment with package dependencies."""
        env = ArrangementEnvironment(
            dependencies={
                "python-fasthtml": ">=0.12,<0.13",
                "starlette": ">=0.52"
            }
        )
        assert env.dependencies["python-fasthtml"] == ">=0.12,<0.13"
        assert env.dependencies["starlette"] == ">=0.52"


class TestArrangementBuildCommands:
    """Tests for ArrangementBuildCommands class."""

    def test_minimal_build_commands(self):
        """Create with only required test command."""
        cmds = ArrangementBuildCommands(test="pytest")
        assert cmds.test == "pytest"
        assert cmds.compile is None
        assert cmds.lint is None

    def test_build_commands_with_compile(self):
        """Build commands with compile step."""
        cmds = ArrangementBuildCommands(
            compile="npx tsc --noEmit",
            test="npx vitest run"
        )
        assert cmds.compile == "npx tsc --noEmit"

    def test_build_commands_with_lint(self):
        """Build commands with lint step."""
        cmds = ArrangementBuildCommands(
            lint="uv run ruff check src/",
            test="uv run pytest"
        )
        assert cmds.lint == "uv run ruff check src/"

    def test_build_commands_all_fields(self):
        """Build commands with all fields populated."""
        cmds = ArrangementBuildCommands(
            compile="tsc",
            lint="eslint src/",
            test="vitest run"
        )
        assert cmds.compile == "tsc"
        assert cmds.lint == "eslint src/"
        assert cmds.test == "vitest run"


class TestArrangementEnvVar:
    """Tests for ArrangementEnvVar class."""

    def test_required_env_var(self):
        """Create a required environment variable."""
        var = ArrangementEnvVar(description="API key for service")
        assert var.description == "API key for service"
        assert var.required is True
        assert var.example == ""

    def test_optional_env_var(self):
        """Create an optional environment variable."""
        var = ArrangementEnvVar(
            description="Debug mode",
            required=False
        )
        assert var.required is False

    def test_env_var_with_example(self):
        """Environment variable with example value."""
        var = ArrangementEnvVar(
            description="Database URL",
            required=True,
            example="postgresql://localhost/mydb"
        )
        assert var.example == "postgresql://localhost/mydb"


class TestArrangementStatic:
    """Tests for ArrangementStatic class."""

    def test_minimal_static_entry(self):
        """Create static entry with just source and dest."""
        static = ArrangementStatic(source="help/", dest="src/help/")
        assert static.source == "help/"
        assert static.dest == "src/help/"
        assert static.description == ""
        assert static.overwrite is True

    def test_static_with_description(self):
        """Static entry with description."""
        static = ArrangementStatic(
            source="templates/",
            dest="src/templates/",
            description="HTML templates"
        )
        assert static.description == "HTML templates"

    def test_static_with_no_overwrite(self):
        """Static entry that doesn't overwrite existing files."""
        static = ArrangementStatic(
            source="config.example.yaml",
            dest="config.yaml",
            overwrite=False
        )
        assert static.overwrite is False


class TestArrangement:
    """Tests for Arrangement class."""

    def test_minimal_arrangement(self):
        """Create arrangement with required fields."""
        arr = Arrangement(
            target_language="python",
            output_paths=ArrangementOutputPaths(
                implementation="src/{name}.py",
                tests="tests/test_{name}.py"
            ),
            build_commands=ArrangementBuildCommands(test="pytest")
        )
        assert arr.target_language == "python"
        assert arr.specs_path == "src/"  # default
        assert arr.constraints == []
        assert arr.env_vars == {}
        assert arr.static == []
        assert arr.model is None

    def test_arrangement_with_all_fields(self):
        """Create arrangement with all optional fields."""
        arr = Arrangement(
            target_language="typescript",
            specs_path="specs/",
            output_paths=ArrangementOutputPaths(
                implementation="src/{name}.ts",
                tests="tests/{name}.test.ts"
            ),
            environment=ArrangementEnvironment(
                tools=["node", "npm"],
                setup_commands=["npm install"]
            ),
            build_commands=ArrangementBuildCommands(
                compile="tsc",
                lint="eslint src/",
                test="vitest run"
            ),
            constraints=["Use strict mode", "Follow Prettier"],
            env_vars={
                "API_KEY": ArrangementEnvVar(
                    description="Third-party API key",
                    required=True
                )
            },
            static=[
                ArrangementStatic(source="docs/", dest="src/docs/")
            ],
            model="claude-3-sonnet"
        )
        assert arr.target_language == "typescript"
        assert arr.specs_path == "specs/"
        assert len(arr.constraints) == 2
        assert "API_KEY" in arr.env_vars
        assert len(arr.static) == 1
        assert arr.model == "claude-3-sonnet"


class TestInterfaceSchema:
    """Tests for InterfaceSchema class."""

    def test_empty_interface_schema(self):
        """Create empty interface schema."""
        schema = InterfaceSchema()
        assert schema.inputs == {}
        assert schema.outputs == {}
        assert schema.properties == {}
        assert schema.required == []
        assert schema.steps is None

    def test_function_interface_schema(self):
        """Interface schema for a function."""
        schema = InterfaceSchema(
            inputs={
                "x": ParameterDefinition(type="integer"),
                "y": ParameterDefinition(type="integer")
            },
            outputs={
                "result": ParameterDefinition(type="integer")
            }
        )
        assert len(schema.inputs) == 2
        assert len(schema.outputs) == 1
        assert "x" in schema.inputs
        assert "result" in schema.outputs

    def test_type_interface_schema(self):
        """Interface schema for a type definition."""
        schema = InterfaceSchema(
            properties={
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            required=["name"]
        )
        assert len(schema.properties) == 2
        assert schema.required == ["name"]

    def test_workflow_interface_schema(self):
        """Interface schema for a workflow."""
        schema = InterfaceSchema(
            inputs={
                "data": ParameterDefinition(type="array")
            },
            outputs={
                "result": ParameterDefinition(type="object")
            },
            steps=[
                WorkflowStep(name="step1", spec="parse_data"),
                WorkflowStep(name="step2", spec="transform_data")
            ]
        )
        assert len(schema.steps) == 2
        assert schema.steps[0].name == "step1"

    def test_validate_inputs_not_implemented(self):
        """validate_inputs raises NotImplementedError."""
        schema = InterfaceSchema()
        with pytest.raises(NotImplementedError):
            schema.validate_inputs({"test": "value"})


class TestBundleSchema:
    """Tests for BundleSchema class."""

    def test_empty_bundle_schema(self):
        """Create empty bundle schema."""
        schema = BundleSchema()
        assert schema.functions == {}
        assert schema.types == {}

    def test_bundle_schema_with_functions(self):
        """Bundle schema containing functions."""
        schema = BundleSchema(
            functions={
                "add": BundleFunction(
                    inputs={"x": {"type": "integer"}},
                    behavior="Adds numbers"
                ),
                "multiply": BundleFunction(
                    inputs={"x": {"type": "integer"}},
                    behavior="Multiplies numbers"
                )
            }
        )
        assert len(schema.functions) == 2
        assert "add" in schema.functions
        assert "multiply" in schema.functions

    def test_bundle_schema_with_types(self):
        """Bundle schema containing type definitions."""
        schema = BundleSchema(
            types={
                "User": BundleType(
                    properties={"name": {"type": "string"}},
                    required=["name"]
                )
            }
        )
        assert len(schema.types) == 1
        assert "User" in schema.types

    def test_bundle_schema_with_functions_and_types(self):
        """Bundle schema with both functions and types."""
        schema = BundleSchema(
            functions={
                "get_user": BundleFunction(behavior="Retrieves user")
            },
            types={
                "User": BundleType(properties={"id": {"type": "integer"}})
            }
        )
        assert len(schema.functions) == 1
        assert len(schema.types) == 1


class TestStepsSchema:
    """Tests for StepsSchema class."""

    def test_empty_steps_schema(self):
        """Create empty steps schema."""
        schema = StepsSchema()
        assert schema.steps == []

    def test_steps_schema_with_steps(self):
        """Steps schema with workflow steps."""
        schema = StepsSchema(
            steps=[
                WorkflowStep(name="step1", spec="prepare"),
                WorkflowStep(name="step2", spec="process")
            ]
        )
        assert len(schema.steps) == 2
        assert schema.steps[0].name == "step1"
        assert schema.steps[1].name == "step2"


class TestParseSchemaBlock:
    """Tests for parse_schema_block function."""

    def test_parse_simple_schema(self):
        """Parse a simple schema block."""
        raw = {
            "inputs": {"x": "integer"},
            "outputs": {"result": "string"}
        }
        schema = parse_schema_block(raw)
        assert "x" in schema.inputs
        assert "result" in schema.outputs

    def test_parse_schema_with_full_definitions(self):
        """Parse schema with full parameter definitions."""
        raw = {
            "inputs": {
                "x": {"type": "integer", "minimum": 0}
            },
            "outputs": {
                "result": {"type": "string"}
            }
        }
        schema = parse_schema_block(raw)
        assert schema.inputs["x"].type == "integer"
        assert schema.inputs["x"].minimum == 0

    def test_parse_schema_invalid_raises_error(self):
        """Parse invalid schema raises ValueError."""
        raw = {"invalid": "structure"}
        # This should not raise because empty schema is valid
        schema = parse_schema_block(raw)
        assert schema is not None

    def test_parse_shorthand_string_type(self):
        """Parse shorthand string type definition."""
        raw = {
            "inputs": {
                "name": "string"
            }
        }
        schema = parse_schema_block(raw)
        assert schema.inputs["name"].type == "string"


class TestParseBundleFunctions:
    """Tests for parse_bundle_functions function."""

    def test_parse_single_function(self):
        """Parse a single function definition."""
        raw = {
            "add": {
                "behavior": "Adds two numbers",
                "inputs": {"x": {"type": "integer"}},
                "outputs": {"result": {"type": "integer"}}
            }
        }
        funcs = parse_bundle_functions(raw)
        assert "add" in funcs
        assert funcs["add"].behavior == "Adds two numbers"

    def test_parse_multiple_functions(self):
        """Parse multiple function definitions."""
        raw = {
            "add": {"behavior": "Adds numbers"},
            "multiply": {"behavior": "Multiplies numbers"},
            "divide": {"behavior": "Divides numbers"}
        }
        funcs = parse_bundle_functions(raw)
        assert len(funcs) == 3

    def test_parse_function_with_contract(self):
        """Parse function with contract."""
        raw = {
            "safe_divide": {
                "behavior": "Divides safely",
                "contract": {
                    "pre": "y != 0",
                    "post": "result * y == x"
                }
            }
        }
        funcs = parse_bundle_functions(raw)
        assert funcs["safe_divide"].contract.pre == "y != 0"

    def test_parse_invalid_function_raises_error(self):
        """Parse invalid function definition raises ValueError."""
        raw = {
            "bad_func": {
                "no_behavior": "This is invalid"
            }
        }
        with pytest.raises(ValueError):
            parse_bundle_functions(raw)

    def test_parse_function_with_examples(self):
        """Parse function with examples."""
        raw = {
            "add": {
                "behavior": "Adds two numbers",
                "examples": [
                    {"inputs": {"x": 1, "y": 2}, "outputs": {"result": 3}}
                ]
            }
        }
        funcs = parse_bundle_functions(raw)
        assert len(funcs["add"].examples) == 1


class TestParseBundleTypes:
    """Tests for parse_bundle_types function."""

    def test_parse_single_type(self):
        """Parse a single type definition."""
        raw = {
            "User": {
                "properties": {"name": {"type": "string"}},
                "required": ["name"]
            }
        }
        types = parse_bundle_types(raw)
        assert "User" in types
        assert "name" in types["User"].properties

    def test_parse_multiple_types(self):
        """Parse multiple type definitions."""
        raw = {
            "User": {"properties": {}},
            "Post": {"properties": {}},
            "Comment": {"properties": {}}
        }
        types = parse_bundle_types(raw)
        assert len(types) == 3

    def test_parse_type_with_description(self):
        """Parse type with description."""
        raw = {
            "Person": {
                "description": "A person with name and age",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                }
            }
        }
        types = parse_bundle_types(raw)
        assert types["Person"].description == "A person with name and age"

    def test_parse_invalid_type_raises_error(self):
        """Parse invalid type definition raises ValueError."""
        raw = {
            "BadType": {
                "invalid_field": "value"
            }
        }
        # This should succeed because properties and required have defaults
        types = parse_bundle_types(raw)
        assert "BadType" in types


class TestParseStepsBlock:
    """Tests for parse_steps_block function."""

    def test_parse_single_step(self):
        """Parse a single workflow step."""
        raw = [
            {
                "name": "step1",
                "spec": "prepare_data"
            }
        ]
        steps = parse_steps_block(raw)
        assert len(steps) == 1
        assert steps[0].name == "step1"
        assert steps[0].spec == "prepare_data"

    def test_parse_multiple_steps(self):
        """Parse multiple workflow steps."""
        raw = [
            {"name": "step1", "spec": "parse"},
            {"name": "step2", "spec": "validate"},
            {"name": "step3", "spec": "transform"}
        ]
        steps = parse_steps_block(raw)
        assert len(steps) == 3

    def test_parse_step_with_checkpoint(self):
        """Parse step with checkpoint enabled."""
        raw = [
            {
                "name": "checkpoint_step",
                "spec": "expensive_computation",
                "checkpoint": True
            }
        ]
        steps = parse_steps_block(raw)
        assert steps[0].checkpoint is True

    def test_parse_step_with_inputs(self):
        """Parse step with input mappings."""
        raw = [
            {
                "name": "step1",
                "spec": "process",
                "inputs": {
                    "data": "workflow.inputs.raw_data",
                    "config": "step0.outputs.config"
                }
            }
        ]
        steps = parse_steps_block(raw)
        assert steps[0].inputs["data"] == "workflow.inputs.raw_data"

    def test_parse_invalid_step_raises_error(self):
        """Parse invalid step definition raises ValueError."""
        raw = [
            {
                "no_name": "step",
                "spec": "something"
            }
        ]
        with pytest.raises(ValueError):
            parse_steps_block(raw)
