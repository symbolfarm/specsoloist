import pytest
import os
import shutil
from specsoloist.core import SpecSoloistCore
from specsoloist.config import SpecSoloistConfig


class MockProvider:
    """Mock LLM provider for testing."""

    def __init__(self, response_func=None):
        self.response_func = response_func or (lambda p: "# Mock code")
        self.calls = []

    def generate(self, prompt: str, temperature: float = 0.1, model=None) -> str:
        self.calls.append({"prompt": prompt, "model": model})
        return self.response_func(prompt)


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
    core = SpecSoloistCore(test_env)
    core.create_spec("login", "Handles user login.")

    path = os.path.join(test_env, "src", "login.spec.md")
    assert os.path.exists(path)
    assert "login.spec.md" in core.list_specs()

    content = core.read_spec("login")
    assert "name: login" in content
    assert "Handles user login." in content


def test_validate_spec_invalid(test_env):
    core = SpecSoloistCore(test_env)
    # Create a manually broken spec file
    bad_path = os.path.join(test_env, "src", "broken.spec.md")
    os.makedirs(os.path.dirname(bad_path), exist_ok=True)
    with open(bad_path, 'w') as f:
        f.write("Just some text")

    res = core.validate_spec("broken")
    assert res["valid"] is False
    assert "Missing YAML frontmatter." in res["errors"]


def test_compile_spec_mock(test_env):
    """Test compilation with a mock provider."""
    core = SpecSoloistCore(test_env)
    core.create_spec("math_utils", "Adds two numbers.")

    # Create and inject mock provider
    mock_provider = MockProvider(lambda p: "def add(a, b): return a + b")
    core._provider = mock_provider

    output_msg = core.compile_spec("math_utils")
    assert "Compiled to" in output_msg

    build_file = os.path.join(test_env, "build", "math_utils.py")
    assert os.path.exists(build_file)
    with open(build_file, 'r') as f:
        assert "def add(a, b):" in f.read()

    # Verify the provider was called
    assert len(mock_provider.calls) == 1


def test_compile_and_run_tests_mock(test_env):
    """Test full compile and run workflow with mock provider."""
    core = SpecSoloistCore(test_env)
    core.create_spec("math_utils", "Adds two numbers.")

    # Mock provider that returns different code based on prompt
    def mock_response(prompt):
        if "QA Engineer" in prompt:
            return """
import pytest
from math_utils import add

def test_add():
    assert add(1, 2) == 3
"""
        else:
            return "def add(a, b): return a + b"

    mock_provider = MockProvider(mock_response)
    core._provider = mock_provider

    # 1. Compile Code
    core.compile_spec("math_utils")

    # 2. Compile Tests
    msg = core.compile_tests("math_utils")
    assert "Generated tests" in msg
    test_file = os.path.join(test_env, "build", "test_math_utils.py")
    assert os.path.exists(test_file)

    # 3. Run Tests
    result = core.run_tests("math_utils")

    if not result["success"]:
        print("Test Output Failure:", result["output"])

    assert result["success"] is True
    assert "1 passed" in result["output"]


def test_config_from_env(test_env, monkeypatch):
    """Test that config loads from environment variables."""
    monkeypatch.setenv("SPECSOLOIST_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")

    config = SpecSoloistConfig.from_env(test_env)
    assert config.llm_provider == "anthropic"
    assert config.api_key == "test_key"


def test_config_creates_directories(test_env):
    """Test that config creates required directories."""
    config = SpecSoloistConfig(root_dir=test_env)
    config.ensure_directories()

    assert os.path.exists(config.src_path)
    assert os.path.exists(config.build_path)
