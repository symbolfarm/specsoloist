import os
import pytest
import tempfile
from specsoloist.core import SpecSoloistCore
from specsoloist.schema import InterfaceSchema

@pytest.fixture
def core():
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a mock src directory and spec file
        src_dir = os.path.join(tmp_dir, "src")
        os.makedirs(src_dir)
        
        math_spec_path = os.path.join(src_dir, "math_demo.spec.md")
        with open(math_spec_path, "w") as f:
            f.write("""---
name: math_demo
type: module
---
# 1. Overview
A math demo.

# 2. Interface Specification
```yaml:schema
inputs:
  operation: {type: string}
  n: {type: integer}
outputs:
  result: {type: string}
```
""")
        
        # Yield the core pointing to this temp directory
        yield SpecSoloistCore(tmp_dir)

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
