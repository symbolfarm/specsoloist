"""Tests for the schema module."""

import pytest
from specsoloist.schema import (
    ArrangementBuildCommands,
    ArrangementEnvVar,
    ArrangementEnvironment,
    ArrangementOutputPathOverride,
    ArrangementOutputPaths,
    BundleFunction,
    BundleSchema,
    BundleType,
    ContractDefinition,
    InterfaceSchema,
    ParameterDefinition,
    StepsSchema,
    WorkflowStep,
    Arrangement,
    parse_bundle_functions,
    parse_bundle_types,
    parse_schema_block,
    parse_steps_block,
)


class TestParameterDefinition:
    def test_basic_creation(self):
        param = ParameterDefinition(type="string")
        assert param.type == "string"
        assert param.required is True
        assert param.description is None

    def test_full_creation(self):
        param = ParameterDefinition(
            type="integer",
            description="An integer",
            default=0,
            required=False,
            minimum=0,
            maximum=100,
        )
        assert param.minimum == 0
        assert param.maximum == 100
        assert param.required is False

    def test_compatible_with_same_type(self):
        out_param = ParameterDefinition(type="string")
        in_param = ParameterDefinition(type="string")
        assert out_param.compatible_with(in_param) is True

    def test_incompatible_with_different_type(self):
        out_param = ParameterDefinition(type="string")
        in_param = ParameterDefinition(type="integer")
        assert out_param.compatible_with(in_param) is False

    def test_compatible_with_numeric_constraints(self):
        out_param = ParameterDefinition(type="integer", minimum=0, maximum=50)
        in_param = ParameterDefinition(type="integer", minimum=60)
        # out max (50) < in min (60), so not compatible
        assert out_param.compatible_with(in_param) is False

    def test_enum_field(self):
        param = ParameterDefinition(type="string", enum=["a", "b", "c"])
        assert param.enum == ["a", "b", "c"]


class TestWorkflowStep:
    def test_basic_creation(self):
        step = WorkflowStep(name="step1", spec="my_spec")
        assert step.name == "step1"
        assert step.spec == "my_spec"
        assert step.checkpoint is False
        assert step.inputs == {}

    def test_with_inputs(self):
        step = WorkflowStep(
            name="step2",
            spec="other_spec",
            checkpoint=True,
            inputs={"data": "step1.outputs.result"},
        )
        assert step.checkpoint is True
        assert step.inputs["data"] == "step1.outputs.result"


class TestBundleFunction:
    def test_basic_creation(self):
        func = BundleFunction(behavior="Does something")
        assert func.behavior == "Does something"
        assert func.inputs == {}
        assert func.outputs == {}

    def test_with_contract(self):
        contract = ContractDefinition(pre="x > 0", post="result > x")
        func = BundleFunction(
            behavior="Doubles x",
            contract=contract,
        )
        assert func.contract.pre == "x > 0"


class TestBundleType:
    def test_basic_creation(self):
        bt = BundleType()
        assert bt.properties == {}
        assert bt.required == []

    def test_with_fields(self):
        bt = BundleType(
            properties={"name": {"type": "string"}},
            required=["name"],
            description="A user type",
        )
        assert "name" in bt.properties
        assert "name" in bt.required


class TestInterfaceSchema:
    def test_validate_inputs_missing_required(self):
        schema = InterfaceSchema(
            inputs={"name": ParameterDefinition(type="string", required=True)}
        )
        with pytest.raises(ValueError, match="name"):
            schema.validate_inputs({})

    def test_validate_inputs_ok(self):
        schema = InterfaceSchema(
            inputs={"name": ParameterDefinition(type="string", required=True)}
        )
        # Should not raise
        schema.validate_inputs({"name": "Alice"})

    def test_validate_inputs_optional(self):
        schema = InterfaceSchema(
            inputs={"name": ParameterDefinition(type="string", required=False)}
        )
        # Should not raise even without the optional field
        schema.validate_inputs({})


class TestParseSchemaBlock:
    def test_empty_schema(self):
        result = parse_schema_block({})
        assert result.inputs == {}
        assert result.outputs == {}

    def test_with_inputs_and_outputs(self):
        raw = {
            "inputs": {"x": {"type": "integer"}},
            "outputs": {"result": {"type": "string"}},
        }
        result = parse_schema_block(raw)
        assert "x" in result.inputs
        assert result.inputs["x"].type == "integer"
        assert "result" in result.outputs

    def test_shorthand_normalization(self):
        raw = {"inputs": {"x": "integer"}}
        result = parse_schema_block(raw)
        assert result.inputs["x"].type == "integer"

    def test_invalid_input_raises(self):
        with pytest.raises((ValueError, TypeError)):
            parse_schema_block("not a dict")


class TestParseBundleFunctions:
    def test_basic_function(self):
        raw = {
            "add": {
                "inputs": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                "outputs": {"result": {"type": "integer"}},
                "behavior": "Add two integers",
            }
        }
        result = parse_bundle_functions(raw)
        assert "add" in result
        assert result["add"].behavior == "Add two integers"

    def test_missing_behavior_raises(self):
        with pytest.raises(ValueError, match="behavior"):
            parse_bundle_functions({"func": {"inputs": {}}})

    def test_empty_dict(self):
        result = parse_bundle_functions({})
        assert result == {}

    def test_invalid_input_raises(self):
        with pytest.raises((ValueError, TypeError)):
            parse_bundle_functions("not a dict")


class TestParseBundleTypes:
    def test_basic_type(self):
        raw = {
            "User": {
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            }
        }
        result = parse_bundle_types(raw)
        assert "User" in result
        assert "name" in result["User"].properties

    def test_empty_dict(self):
        result = parse_bundle_types({})
        assert result == {}

    def test_invalid_input_raises(self):
        with pytest.raises((ValueError, TypeError)):
            parse_bundle_types("not a dict")


class TestParseStepsBlock:
    def test_basic_steps(self):
        raw = [
            {"name": "step1", "spec": "spec_a"},
            {"name": "step2", "spec": "spec_b", "checkpoint": True},
        ]
        result = parse_steps_block(raw)
        assert len(result) == 2
        assert result[0].name == "step1"
        assert result[1].checkpoint is True

    def test_missing_name_raises(self):
        with pytest.raises(ValueError, match="name"):
            parse_steps_block([{"spec": "spec_a"}])

    def test_missing_spec_raises(self):
        with pytest.raises(ValueError, match="spec"):
            parse_steps_block([{"name": "step1"}])

    def test_empty_list(self):
        result = parse_steps_block([])
        assert result == []

    def test_invalid_input_raises(self):
        with pytest.raises((ValueError, TypeError)):
            parse_steps_block("not a list")


class TestArrangementOutputPaths:
    def test_resolve_implementation_default(self):
        paths = ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py",
        )
        assert paths.resolve_implementation("mymod") == "src/mymod.py"
        assert paths.resolve_tests("mymod") == "tests/test_mymod.py"

    def test_resolve_with_override(self):
        paths = ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py",
            overrides={
                "special": ArrangementOutputPathOverride(
                    implementation="src/special/module.py"
                )
            },
        )
        assert paths.resolve_implementation("special") == "src/special/module.py"
        assert paths.resolve_implementation("other") == "src/other.py"

    def test_resolve_tests_with_override(self):
        paths = ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py",
            overrides={
                "mymod": ArrangementOutputPathOverride(
                    tests="tests/custom/test_mymod.py"
                )
            },
        )
        assert paths.resolve_tests("mymod") == "tests/custom/test_mymod.py"


class TestArrangement:
    def test_basic_arrangement(self):
        arr = Arrangement(
            target_language="python",
            output_paths=ArrangementOutputPaths(
                implementation="src/{name}.py",
                tests="tests/test_{name}.py",
            ),
            build_commands=ArrangementBuildCommands(test="pytest tests/"),
        )
        assert arr.target_language == "python"
        assert arr.model is None
        assert arr.constraints == []

    def test_with_model(self):
        arr = Arrangement(
            target_language="typescript",
            output_paths=ArrangementOutputPaths(
                implementation="src/{name}.ts",
                tests="tests/{name}.test.ts",
            ),
            build_commands=ArrangementBuildCommands(test="npm test"),
            model="claude-haiku-4",
        )
        assert arr.model == "claude-haiku-4"

    def test_env_vars(self):
        arr = Arrangement(
            target_language="python",
            output_paths=ArrangementOutputPaths(
                implementation="src/{name}.py",
                tests="tests/test_{name}.py",
            ),
            build_commands=ArrangementBuildCommands(test="pytest"),
            env_vars={
                "API_KEY": ArrangementEnvVar(
                    description="API key",
                    required=True,
                    example="sk-xxx",
                )
            },
        )
        assert "API_KEY" in arr.env_vars
        assert arr.env_vars["API_KEY"].required is True
