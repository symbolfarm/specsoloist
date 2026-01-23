import pytest
import os
import shutil
from specular.core import SpecularCore

@pytest.fixture
def test_env():
    """Sets up a temporary directory for testing and cleans it up afterwards."""
    env_dir = "test_env_pytest"
    if os.path.exists(env_dir):
        shutil.rmtree(env_dir)
    os.makedirs(env_dir)
    
    yield env_dir
    
    if os.path.exists(env_dir):
        shutil.rmtree(env_dir)

def test_create_spec(test_env):
    core = SpecularCore(test_env)
    msg = core.create_spec("login", "Handles user login.")
    
    path = os.path.join(test_env, "src", "login.spec.md")
    assert os.path.exists(path)
    assert "login.spec.md" in core.list_specs()
    
    content = core.read_spec("login")
    assert "name: login" in content
    assert "Handles user login." in content

def test_validate_spec_invalid(test_env):
    core = SpecularCore(test_env)
    # Create a spec but don't fill it in (it has placeholders but missing required sections depending on template state)
    # Actually, our template currently HAS the headers. 
    # So `create_spec` produces a structurally "valid" file regarding HEADERS, 
    # even if the content is just placeholders.
    # Let's manually create a broken file.
    
    bad_path = os.path.join(test_env, "src", "broken.spec.md")
    os.makedirs(os.path.dirname(bad_path), exist_ok=True)
    with open(bad_path, 'w') as f:
        f.write("Just some text")
        
    res = core.validate_spec("broken")
    assert res["valid"] is False
    assert "Missing YAML frontmatter." in res["errors"]

def test_compile_spec_mock(test_env, monkeypatch):
    """Test compilation without hitting the real API."""
    core = SpecularCore(test_env, api_key="test_key")
    core.create_spec("math_utils", "Adds two numbers.")
    
    # Mock the _call_google_llm method to avoid network calls
    def mock_llm(*args, **kwargs):
        return "def add(a, b): return a + b"
    
    monkeypatch.setattr(core, "_call_google_llm", mock_llm)
    
    output_msg = core.compile_spec("math_utils")
    assert "Compiled to" in output_msg
    
    build_file = os.path.join(test_env, "build", "math_utils.py")
    assert os.path.exists(build_file)
    with open(build_file, 'r') as f:
        assert "def add(a, b):" in f.read()

def test_compile_and_run_tests_mock(test_env, monkeypatch):
    core = SpecularCore(test_env, api_key="test_key")
    core.create_spec("math_utils", "Adds two numbers.")
    
    # Mock LLM to return different code based on the prompt content
    def mock_llm(prompt, model):
        if "QA Engineer" in prompt:
            # Return a valid pytest file
            return """
import pytest
from math_utils import add

def test_add():
    assert add(1, 2) == 3
"""
        else:
            # Return the implementation
            return "def add(a, b): return a + b"

    monkeypatch.setattr(core, "_call_google_llm", mock_llm)
    
    # 1. Compile Code
    core.compile_spec("math_utils")
    
    # 2. Compile Tests
    msg = core.compile_tests("math_utils")
    assert "Generated tests" in msg
    test_file = os.path.join(test_env, "build", "test_math_utils.py")
    assert os.path.exists(test_file)
    
    # 3. Run Tests
    # We need to ensure pytest is available. Since we are running FROM pytest, 
    # we know it's installed.
    result = core.run_tests("math_utils")
    
    # Note: subprocess.run inside the test might fail if 'pytest' isn't in PATH correctly
    # or if it picks up the wrong env. 
    # But since we use 'uv run pytest' to run THIS test, the environment should be consistent.
    if not result["success"]:
        print("Test Output Failure:", result["output"])
        
    assert result["success"] is True
    assert "1 passed" in result["output"]
