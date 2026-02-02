import os
import pytest
from specsoloist.core import SpecSoloistCore
from specsoloist.schema import InterfaceSchema

@pytest.fixture
def core():
    return SpecSoloistCore(".")

def test_extract_schema(core):
    """Test that schema is correctly extracted from math_demo.spec.md"""
    spec = core.parser.parse_spec("math_demo")
    assert spec.schema is not None
    assert isinstance(spec.schema, InterfaceSchema)
    
    # Check inputs
    assert "operation" in spec.schema.inputs
    assert spec.schema.inputs["operation"].type == "string"
    assert spec.schema.inputs["n"].type == "integer"
    
    # Check outputs
    assert "result" in spec.schema.outputs
    assert spec.schema.outputs["result"].type == "string"

def test_verify_project(core):
    """Test the verify_project method."""
    result = core.verify_project()
    
    assert "math_demo" in result["results"]
    math_result = result["results"]["math_demo"]
    
    assert math_result["status"] == "valid"
    assert math_result["schema_defined"] is True
