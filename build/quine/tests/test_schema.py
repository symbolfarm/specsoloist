"""
Comprehensive tests for schema module.

Tests cover:
- ParameterDefinition creation and compatibility
- WorkflowStep creation
- ContractDefinition creation
- BundleFunction and BundleType definitions
- InterfaceSchema creation and validation
- All parse functions
- Edge cases and error conditions
"""

import pytest
import sys
from pathlib import Path

# Add the build/quine/src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from specsoloist.schema import (
    ParameterDefinition,
    WorkflowStep,
    ContractDefinition,
    BundleFunction,
    BundleType,
    InterfaceSchema,
    BundleSchema,
    StepsSchema,
    parse_schema_block,
    parse_bundle_functions,
    parse_bundle_types,
    parse_steps_block,
)


class TestParameterDefinition:
    """Tests for ParameterDefinition."""

    def test_basic_creation(self):
        """Can create a basic parameter definition."""
        param = ParameterDefinition(type="string")
        assert param.type == "string"
        assert param.required is True
        assert param.description is None

    def test_with_constraints(self):
        """Can create parameter with numeric constraints."""
        param = ParameterDefinition(
            type="integer",
            minimum=0,
            maximum=100,
            description="A number between 0 and 100"
        )
        assert param.type == "integer"
        assert param.minimum == 0
        assert param.maximum == 100
        assert param.description == "A number between 0 and 100"

    def test_with_string_constraints(self):
        """Can create parameter with string constraints."""
        param = ParameterDefinition(
            type="string",
            minLength=1,
            maxLength=255,
            pattern=r"^[a-zA-Z0-9]+$",
            format="email"
        )
        assert param.type == "string"
        assert param.minLength == 1
        assert param.maxLength == 255
        assert param.pattern == r"^[a-zA-Z0-9]+$"
        assert param.format == "email"

    def test_with_enum(self):
        """Can create parameter with enum constraint."""
        param = ParameterDefinition(
            type="string",
            enum=["red", "green", "blue"]
        )
        assert param.enum == ["red", "green", "blue"]

    def test_with_ref(self):
        """Can create parameter with reference."""
        param = ParameterDefinition(
            type="ref",
            ref="types/user"
        )
        assert param.type == "ref"
        assert param.ref == "types/user"

    def test_with_items(self):
        """Can create array parameter with items type."""
        param = ParameterDefinition(
            type="array",
            items={"type": "integer"}
        )
        assert param.type == "array"
        assert param.items == {"type": "integer"}

    def test_with_properties(self):
        """Can create object parameter with properties."""
        props = {
            "id": {"type": "string"},
            "name": {"type": "string"}
        }
        param = ParameterDefinition(
            type="object",
            properties=props
        )
        assert param.properties == props

    def test_optional_parameter(self):
        """Can mark parameter as optional."""
        param = ParameterDefinition(
            type="string",
            required=False
        )
        assert param.required is False

    def test_with_default(self):
        """Can specify default value."""
        param = ParameterDefinition(
            type="string",
            default="hello"
        )
        assert param.default == "hello"

    def test_compatible_with_same_type(self):
        """Compatible types pass type check."""
        output = ParameterDefinition(type="string")
        input_param = ParameterDefinition(type="string")
        assert output.compatible_with(input_param) is True

    def test_compatible_with_different_type(self):
        """Different types are incompatible."""
        output = ParameterDefinition(type="string")
        input_param = ParameterDefinition(type="integer")
        assert output.compatible_with(input_param) is False

    def test_compatible_with_constraints_satisfied(self):
        """Output within input constraints is compatible."""
        output = ParameterDefinition(type="integer", minimum=10, maximum=20)
        input_param = ParameterDefinition(type="integer", minimum=0, maximum=100)
        assert output.compatible_with(input_param) is True

    def test_compatible_with_constraints_violated(self):
        """Output outside input constraints is incompatible."""
        output = ParameterDefinition(type="integer", minimum=0, maximum=100)
        input_param = ParameterDefinition(type="integer", minimum=10, maximum=20)
        assert output.compatible_with(input_param) is False

    def test_compatible_with_no_input_constraint(self):
        """Output with constraint compatible when input has no constraint."""
        output = ParameterDefinition(type="integer", minimum=10, maximum=20)
        input_param = ParameterDefinition(type="integer")
        assert output.compatible_with(input_param) is True

    def test_compatible_with_input_constraint_no_output_constraint(self):
        """Output without constraint incompatible with input constraint."""
        output = ParameterDefinition(type="integer")
        input_param = ParameterDefinition(type="integer", minimum=10)
        # Output has no minimum, so it's not guaranteed to be >= 10
        assert output.compatible_with(input_param) is False


class TestWorkflowStep:
    """Tests for WorkflowStep."""

    def test_basic_creation(self):
        """Can create a basic workflow step."""
        step = WorkflowStep(name="validate", spec="validate_order")
        assert step.name == "validate"
        assert step.spec == "validate_order"
        assert step.checkpoint is False
        assert step.inputs == {}

    def test_with_inputs(self):
        """Can create step with inputs."""
        step = WorkflowStep(
            name="charge",
            spec="charge_payment",
            inputs={
                "amount": "validate.outputs.total",
                "payment_method": "inputs.order.payment"
            }
        )
        assert step.inputs == {
            "amount": "validate.outputs.total",
            "payment_method": "inputs.order.payment"
        }

    def test_with_checkpoint(self):
        """Can mark step as checkpoint."""
        step = WorkflowStep(
            name="charge",
            spec="charge_payment",
            checkpoint=True
        )
        assert step.checkpoint is True


class TestContractDefinition:
    """Tests for ContractDefinition."""

    def test_basic_creation(self):
        """Can create contract definition."""
        contract = ContractDefinition(
            pre="n >= 0",
            post="result >= 1"
        )
        assert contract.pre == "n >= 0"
        assert contract.post == "result >= 1"
        assert contract.invariant is None

    def test_with_invariant(self):
        """Can include invariant."""
        contract = ContractDefinition(invariant="balance >= 0")
        assert contract.invariant == "balance >= 0"

    def test_empty_contract(self):
        """Can create empty contract."""
        contract = ContractDefinition()
        assert contract.pre is None
        assert contract.post is None
        assert contract.invariant is None


class TestBundleFunction:
    """Tests for BundleFunction."""

    def test_basic_creation(self):
        """Can create a basic bundle function."""
        func = BundleFunction(behavior="Add two numbers")
        assert func.behavior == "Add two numbers"
        assert func.inputs == {}
        assert func.outputs == {}
        assert func.contract is None
        assert func.examples is None

    def test_with_inputs_and_outputs(self):
        """Can specify inputs and outputs."""
        func = BundleFunction(
            inputs={"a": {"type": "integer"}, "b": {"type": "integer"}},
            outputs={"result": {"type": "integer"}},
            behavior="Add two integers"
        )
        assert func.inputs == {"a": {"type": "integer"}, "b": {"type": "integer"}}
        assert func.outputs == {"result": {"type": "integer"}}

    def test_with_contract(self):
        """Can include contract."""
        contract = ContractDefinition(pre="a >= 0", post="result >= 0")
        func = BundleFunction(
            behavior="Square a number",
            contract=contract
        )
        assert func.contract == contract

    def test_with_examples(self):
        """Can include examples."""
        examples = [
            {"input": 5, "output": 25},
            {"input": 0, "output": 0}
        ]
        func = BundleFunction(
            behavior="Square a number",
            examples=examples
        )
        assert func.examples == examples


class TestBundleType:
    """Tests for BundleType."""

    def test_basic_creation(self):
        """Can create a basic bundle type."""
        btype = BundleType()
        assert btype.properties == {}
        assert btype.required == []
        assert btype.description is None

    def test_with_properties(self):
        """Can specify properties."""
        props = {
            "id": {"type": "string"},
            "name": {"type": "string"}
        }
        btype = BundleType(properties=props)
        assert btype.properties == props

    def test_with_required_fields(self):
        """Can specify required fields."""
        btype = BundleType(
            properties={"id": {"type": "string"}, "name": {"type": "string"}},
            required=["id"]
        )
        assert btype.required == ["id"]

    def test_with_description(self):
        """Can include description."""
        btype = BundleType(description="A user in the system")
        assert btype.description == "A user in the system"


class TestInterfaceSchema:
    """Tests for InterfaceSchema."""

    def test_basic_creation(self):
        """Can create basic interface schema."""
        schema = InterfaceSchema()
        assert schema.inputs == {}
        assert schema.outputs == {}
        assert schema.properties == {}
        assert schema.required == []
        assert schema.steps is None

    def test_with_inputs_and_outputs(self):
        """Can specify inputs and outputs."""
        inputs = {
            "a": ParameterDefinition(type="integer"),
            "b": ParameterDefinition(type="integer")
        }
        outputs = {
            "result": ParameterDefinition(type="integer")
        }
        schema = InterfaceSchema(inputs=inputs, outputs=outputs)
        assert schema.inputs == inputs
        assert schema.outputs == outputs

    def test_with_properties_and_required(self):
        """Can specify properties for type schemas."""
        props = {
            "id": {"type": "string"},
            "name": {"type": "string"}
        }
        schema = InterfaceSchema(properties=props, required=["id"])
        assert schema.properties == props
        assert schema.required == ["id"]

    def test_with_steps(self):
        """Can include steps for workflow schemas."""
        steps = [
            WorkflowStep(name="validate", spec="validate_order"),
            WorkflowStep(name="charge", spec="charge_payment")
        ]
        schema = InterfaceSchema(steps=steps)
        assert schema.steps == steps

    def test_validate_inputs_success(self):
        """Validate inputs passes when all required inputs present."""
        schema = InterfaceSchema(
            inputs={
                "name": ParameterDefinition(type="string", required=True),
                "age": ParameterDefinition(type="integer", required=False)
            }
        )
        # Should not raise
        schema.validate_inputs({"name": "Alice"})

    def test_validate_inputs_missing_required(self):
        """Validate inputs fails when required input missing."""
        schema = InterfaceSchema(
            inputs={
                "name": ParameterDefinition(type="string", required=True)
            }
        )
        with pytest.raises(ValueError, match="Missing required input"):
            schema.validate_inputs({})

    def test_validate_inputs_extra_fields(self):
        """Validate inputs allows extra fields."""
        schema = InterfaceSchema(
            inputs={
                "name": ParameterDefinition(type="string", required=True)
            }
        )
        # Should not raise even with extra fields
        schema.validate_inputs({"name": "Alice", "extra": "field"})


class TestBundleSchema:
    """Tests for BundleSchema."""

    def test_basic_creation(self):
        """Can create basic bundle schema."""
        schema = BundleSchema()
        assert schema.functions == {}
        assert schema.types == {}

    def test_with_functions_and_types(self):
        """Can specify functions and types."""
        functions = {
            "add": BundleFunction(
                inputs={"a": {"type": "integer"}, "b": {"type": "integer"}},
                outputs={"result": {"type": "integer"}},
                behavior="Add two integers"
            )
        }
        types = {
            "user": BundleType(
                properties={"id": {"type": "string"}},
                required=["id"]
            )
        }
        schema = BundleSchema(functions=functions, types=types)
        assert schema.functions == functions
        assert schema.types == types


class TestStepsSchema:
    """Tests for StepsSchema."""

    def test_basic_creation(self):
        """Can create basic steps schema."""
        schema = StepsSchema()
        assert schema.steps == []

    def test_with_steps(self):
        """Can specify steps."""
        steps = [
            WorkflowStep(name="validate", spec="validate_order"),
            WorkflowStep(name="charge", spec="charge_payment")
        ]
        schema = StepsSchema(steps=steps)
        assert schema.steps == steps


class TestParseSchemaBlock:
    """Tests for parse_schema_block function."""

    def test_parse_empty_schema(self):
        """Can parse empty schema."""
        result = parse_schema_block({})
        assert isinstance(result, InterfaceSchema)
        assert result.inputs == {}
        assert result.outputs == {}

    def test_parse_simple_inputs(self):
        """Can parse simple input definitions."""
        raw = {
            "inputs": {
                "a": "integer",
                "b": "integer"
            }
        }
        result = parse_schema_block(raw)
        assert "a" in result.inputs
        assert result.inputs["a"].type == "integer"
        assert result.inputs["b"].type == "integer"

    def test_parse_dict_inputs(self):
        """Can parse dict-format input definitions."""
        raw = {
            "inputs": {
                "a": {"type": "integer", "minimum": 0},
                "b": {"type": "string", "minLength": 1}
            }
        }
        result = parse_schema_block(raw)
        assert result.inputs["a"].type == "integer"
        assert result.inputs["a"].minimum == 0
        assert result.inputs["b"].type == "string"
        assert result.inputs["b"].minLength == 1

    def test_parse_simple_outputs(self):
        """Can parse simple output definitions."""
        raw = {
            "outputs": {
                "result": "integer"
            }
        }
        result = parse_schema_block(raw)
        assert "result" in result.outputs
        assert result.outputs["result"].type == "integer"

    def test_parse_inputs_and_outputs(self):
        """Can parse both inputs and outputs."""
        raw = {
            "inputs": {"a": "integer", "b": "integer"},
            "outputs": {"result": "integer"}
        }
        result = parse_schema_block(raw)
        assert len(result.inputs) == 2
        assert len(result.outputs) == 1
        assert result.outputs["result"].type == "integer"

    def test_parse_with_properties(self):
        """Can parse schema with properties."""
        raw = {
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"}
            },
            "required": ["id"]
        }
        result = parse_schema_block(raw)
        assert result.properties == raw["properties"]
        assert result.required == ["id"]

    def test_parse_ref_type(self):
        """Can parse reference types."""
        raw = {
            "outputs": {
                "user": {"type": "ref", "ref": "types/user"}
            }
        }
        result = parse_schema_block(raw)
        assert result.outputs["user"].type == "ref"
        assert result.outputs["user"].ref == "types/user"

    def test_parse_complex_schema(self):
        """Can parse complex schema with nested structures."""
        raw = {
            "inputs": {
                "data": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "values": {"type": "array", "items": {"type": "integer"}}
                    }
                }
            },
            "outputs": {
                "result": {"type": "array", "items": {"type": "object"}}
            }
        }
        result = parse_schema_block(raw)
        assert result.inputs["data"].type == "object"
        assert result.outputs["result"].type == "array"

    def test_parse_invalid_schema_raises(self):
        """Invalid schema raises ValueError."""
        raw = {
            "inputs": {
                "a": {"no_type_field": True}
            }
        }
        # Should raise because required 'type' field is missing
        with pytest.raises(ValueError):
            parse_schema_block(raw)


class TestParseBundleFunctions:
    """Tests for parse_bundle_functions function."""

    def test_parse_empty_functions(self):
        """Can parse empty functions dict."""
        result = parse_bundle_functions({})
        assert result == {}

    def test_parse_single_function(self):
        """Can parse single function."""
        raw = {
            "add": {
                "inputs": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                "outputs": {"result": {"type": "integer"}},
                "behavior": "Add two integers"
            }
        }
        result = parse_bundle_functions(raw)
        assert "add" in result
        assert isinstance(result["add"], BundleFunction)
        assert result["add"].behavior == "Add two integers"

    def test_parse_multiple_functions(self):
        """Can parse multiple functions."""
        raw = {
            "add": {
                "inputs": {"a": "integer", "b": "integer"},
                "outputs": {"result": "integer"},
                "behavior": "Add"
            },
            "subtract": {
                "inputs": {"a": "integer", "b": "integer"},
                "outputs": {"result": "integer"},
                "behavior": "Subtract"
            }
        }
        result = parse_bundle_functions(raw)
        assert len(result) == 2
        assert "add" in result
        assert "subtract" in result

    def test_parse_function_with_contract(self):
        """Can parse function with contract."""
        raw = {
            "square": {
                "inputs": {"n": "integer"},
                "outputs": {"result": "integer"},
                "behavior": "Square a number",
                "contract": {"pre": "n >= 0", "post": "result >= 0"}
            }
        }
        result = parse_bundle_functions(raw)
        assert result["square"].contract is not None
        assert result["square"].contract.pre == "n >= 0"

    def test_parse_function_with_examples(self):
        """Can parse function with examples."""
        raw = {
            "square": {
                "inputs": {"n": "integer"},
                "outputs": {"result": "integer"},
                "behavior": "Square a number",
                "examples": [{"input": 5, "output": 25}]
            }
        }
        result = parse_bundle_functions(raw)
        assert result["square"].examples is not None
        assert len(result["square"].examples) == 1

    def test_parse_invalid_function_raises(self):
        """Invalid function raises ValueError."""
        raw = {
            "bad": {
                "inputs": {},
                "outputs": {}
                # Missing required 'behavior' field
            }
        }
        with pytest.raises(ValueError, match="Invalid function"):
            parse_bundle_functions(raw)


class TestParseBundleTypes:
    """Tests for parse_bundle_types function."""

    def test_parse_empty_types(self):
        """Can parse empty types dict."""
        result = parse_bundle_types({})
        assert result == {}

    def test_parse_single_type(self):
        """Can parse single type."""
        raw = {
            "user": {
                "properties": {"id": {"type": "string"}, "name": {"type": "string"}},
                "required": ["id"]
            }
        }
        result = parse_bundle_types(raw)
        assert "user" in result
        assert isinstance(result["user"], BundleType)
        assert result["user"].required == ["id"]

    def test_parse_multiple_types(self):
        """Can parse multiple types."""
        raw = {
            "user": {
                "properties": {"id": "string"},
                "required": ["id"]
            },
            "post": {
                "properties": {"id": "string", "title": "string"},
                "required": ["id"]
            }
        }
        result = parse_bundle_types(raw)
        assert len(result) == 2
        assert "user" in result
        assert "post" in result

    def test_parse_type_with_description(self):
        """Can parse type with description."""
        raw = {
            "user": {
                "properties": {"id": "string"},
                "required": ["id"],
                "description": "A user in the system"
            }
        }
        result = parse_bundle_types(raw)
        assert result["user"].description == "A user in the system"

    def test_parse_empty_type(self):
        """Can parse type with no properties."""
        raw = {
            "empty": {
                "properties": {},
                "required": []
            }
        }
        result = parse_bundle_types(raw)
        assert "empty" in result


class TestParseStepsBlock:
    """Tests for parse_steps_block function."""

    def test_parse_empty_steps(self):
        """Can parse empty steps list."""
        result = parse_steps_block([])
        assert result == []

    def test_parse_single_step(self):
        """Can parse single step."""
        raw = [
            {
                "name": "validate",
                "spec": "validate_order"
            }
        ]
        result = parse_steps_block(raw)
        assert len(result) == 1
        assert result[0].name == "validate"
        assert result[0].spec == "validate_order"

    def test_parse_multiple_steps(self):
        """Can parse multiple steps."""
        raw = [
            {"name": "validate", "spec": "validate_order"},
            {"name": "charge", "spec": "charge_payment"},
            {"name": "confirm", "spec": "send_confirmation"}
        ]
        result = parse_steps_block(raw)
        assert len(result) == 3
        assert result[0].name == "validate"
        assert result[2].name == "confirm"

    def test_parse_step_with_checkpoint(self):
        """Can parse step with checkpoint flag."""
        raw = [
            {
                "name": "charge",
                "spec": "charge_payment",
                "checkpoint": True
            }
        ]
        result = parse_steps_block(raw)
        assert result[0].checkpoint is True

    def test_parse_step_with_inputs(self):
        """Can parse step with inputs."""
        raw = [
            {
                "name": "charge",
                "spec": "charge_payment",
                "inputs": {
                    "amount": "validate.outputs.total",
                    "payment_method": "inputs.order.payment"
                }
            }
        ]
        result = parse_steps_block(raw)
        assert result[0].inputs["amount"] == "validate.outputs.total"
        assert result[0].inputs["payment_method"] == "inputs.order.payment"

    def test_parse_complex_workflow(self):
        """Can parse complex workflow with multiple steps."""
        raw = [
            {"name": "validate", "spec": "validate_order", "inputs": {"order": "inputs.order"}},
            {
                "name": "charge",
                "spec": "charge_payment",
                "checkpoint": True,
                "inputs": {
                    "amount": "validate.outputs.total",
                    "payment_method": "inputs.order.payment"
                }
            },
            {
                "name": "confirm",
                "spec": "send_confirmation",
                "inputs": {
                    "order": "inputs.order",
                    "transaction_id": "charge.outputs.transaction_id"
                }
            }
        ]
        result = parse_steps_block(raw)
        assert len(result) == 3
        assert result[1].checkpoint is True
        assert "amount" in result[1].inputs

    def test_parse_invalid_step_raises(self):
        """Invalid step raises ValueError."""
        raw = [
            {
                "name": "bad_step"
                # Missing required 'spec' field
            }
        ]
        with pytest.raises(ValueError, match="Invalid step"):
            parse_steps_block(raw)


class TestNormalizationEdgeCases:
    """Tests for parameter normalization edge cases."""

    def test_shorthand_string_type(self):
        """Shorthand notation 'integer' becomes {type: 'integer'}."""
        raw = {"inputs": {"count": "integer"}}
        result = parse_schema_block(raw)
        assert result.inputs["count"].type == "integer"

    def test_shorthand_multiple_types(self):
        """Can mix shorthand and full definitions."""
        raw = {
            "inputs": {
                "a": "integer",
                "b": {"type": "string", "minLength": 1}
            }
        }
        result = parse_schema_block(raw)
        assert result.inputs["a"].type == "integer"
        assert result.inputs["b"].minLength == 1

    def test_nested_property_preservation(self):
        """Nested properties in inputs are preserved."""
        raw = {
            "inputs": {
                "data": {
                    "type": "object",
                    "properties": {
                        "nested": {"type": "string"}
                    }
                }
            }
        }
        result = parse_schema_block(raw)
        assert result.inputs["data"].properties is not None
