"""Tests for respec module."""

import os
import tempfile
import shutil
import pytest

from specsoloist.respec import Respecer
from specsoloist.config import SpecSoloistConfig


class MockProvider:
    """Mock LLM provider for testing."""

    def __init__(self, response_func=None):
        """Initialize with an optional response function.

        Args:
            response_func: Callable that takes a prompt and returns a string.
        """
        self.response_func = response_func or (lambda p: "---\nname: test\n---\n# Test spec")
        self.calls = []

    def generate(self, prompt: str, temperature: float = 0.1, model=None) -> str:
        """Generate a response from the LLM.

        Args:
            prompt: The prompt to send to the LLM.
            temperature: Sampling temperature (unused in mock).
            model: Optional model override.

        Returns:
            The mocked response.
        """
        self.calls.append({"prompt": prompt, "model": model})
        return self.response_func(prompt)


@pytest.fixture
def temp_project():
    """Create a temporary project directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_respecer_init_with_config():
    """Test Respecer initialization with custom config."""
    mock_provider = MockProvider()
    config = SpecSoloistConfig()
    respecer = Respecer(config=config, provider=mock_provider)
    assert respecer.config is config


def test_respecer_init_without_config(temp_project):
    """Test Respecer initialization with default config from environment."""
    mock_provider = MockProvider()
    # Create a Respecer with a custom config and mock provider
    respecer = Respecer(
        config=SpecSoloistConfig(root_dir=temp_project),
        provider=mock_provider
    )
    assert respecer.config is not None
    assert respecer.config.root_dir == temp_project


def test_respecer_init_with_provider():
    """Test Respecer initialization with custom provider."""
    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(),
        provider=mock_provider
    )
    assert respecer.provider is mock_provider


def test_respec_source_file_not_found(temp_project):
    """Test respec raises FileNotFoundError when source doesn't exist."""
    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(root_dir=temp_project),
        provider=mock_provider
    )

    with pytest.raises(FileNotFoundError):
        respecer.respec("/nonexistent/source.py")


def test_respec_basic_source_file(temp_project):
    """Test respec with a basic source file."""
    # Create a source file
    src_file = os.path.join(temp_project, "example.py")
    with open(src_file, 'w') as f:
        f.write("""def hello():
    return "Hello, World!"
""")

    def response_func(p):
        return "---\nname: test\n---\n# Test spec"

    mock_provider = MockProvider(response_func=response_func)
    respecer = Respecer(
        config=SpecSoloistConfig(root_dir=temp_project),
        provider=mock_provider
    )

    spec = respecer.respec(src_file)

    # Check that provider was called
    assert len(mock_provider.calls) == 1
    # Check that the response was processed (should contain spec content)
    assert "name: test" in spec
    assert "# Test spec" in spec


def test_respec_with_test_file(temp_project):
    """Test respec with both source and test files."""
    # Create source file
    src_file = os.path.join(temp_project, "example.py")
    with open(src_file, 'w') as f:
        f.write("""def add(a, b):
    return a + b
""")

    # Create test file
    test_file = os.path.join(temp_project, "test_example.py")
    with open(test_file, 'w') as f:
        f.write("""def test_add():
    from example import add
    assert add(1, 2) == 3
""")

    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(root_dir=temp_project),
        provider=mock_provider
    )

    spec = respecer.respec(src_file, test_path=test_file)

    # Verify both files were referenced in the prompt
    assert len(mock_provider.calls) == 1
    prompt = mock_provider.calls[0]["prompt"]
    assert "Existing Tests" in prompt
    assert "test_add" in prompt


def test_respec_ignores_missing_test_file(temp_project):
    """Test respec when test_path is provided but file doesn't exist."""
    src_file = os.path.join(temp_project, "example.py")
    with open(src_file, 'w') as f:
        f.write("def hello(): return 'hi'")

    def response_func(p):
        return "---\nname: test\n---\n# Test spec"

    mock_provider = MockProvider(response_func=response_func)
    respecer = Respecer(
        config=SpecSoloistConfig(root_dir=temp_project),
        provider=mock_provider
    )

    # Should not raise error, just ignore the missing test file
    spec = respecer.respec(src_file, test_path="/nonexistent/test.py")
    assert "name: test" in spec
    assert "# Test spec" in spec


def test_respec_with_model_override(temp_project):
    """Test respec with model parameter override."""
    src_file = os.path.join(temp_project, "example.py")
    with open(src_file, 'w') as f:
        f.write("def hello(): return 'hi'")

    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(root_dir=temp_project),
        provider=mock_provider
    )

    spec = respecer.respec(src_file, model="gpt-4")

    # Verify model was passed to provider
    assert mock_provider.calls[0]["model"] == "gpt-4"


def test_respec_loads_spec_format_rules(temp_project):
    """Test respec loads and includes spec_format.spec.md when it exists."""
    # Create source file
    src_file = os.path.join(temp_project, "example.py")
    with open(src_file, 'w') as f:
        f.write("def hello(): return 'hi'")

    # Create score/spec_format.spec.md
    score_dir = os.path.join(temp_project, "score")
    os.makedirs(score_dir, exist_ok=True)
    spec_format_file = os.path.join(score_dir, "spec_format.spec.md")
    with open(spec_format_file, 'w') as f:
        f.write("# Spec Format Rules\nTest rules here")

    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(root_dir=temp_project),
        provider=mock_provider
    )

    spec = respecer.respec(src_file)

    # Verify spec_format content was included in the prompt
    prompt = mock_provider.calls[0]["prompt"]
    assert "Spec Format Rules" in prompt
    assert "Test rules here" in prompt


def test_respec_without_spec_format_rules(temp_project):
    """Test respec works when spec_format.spec.md doesn't exist."""
    src_file = os.path.join(temp_project, "example.py")
    with open(src_file, 'w') as f:
        f.write("def hello(): return 'hi'")

    def response_func(p):
        return "---\nname: test\n---\n# Test spec"

    mock_provider = MockProvider(response_func=response_func)
    respecer = Respecer(
        config=SpecSoloistConfig(root_dir=temp_project),
        provider=mock_provider
    )

    # Should not raise error even if spec_format file is missing
    spec = respecer.respec(src_file)
    assert "name: test" in spec
    assert "# Test spec" in spec


def test_clean_response_with_markdown_fence():
    """Test _clean_response removes markdown fences."""
    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(),
        provider=mock_provider
    )

    response = "```markdown\n---\nname: test\n---\n```"
    cleaned = respecer._clean_response(response)
    assert "```" not in cleaned
    assert "name: test" in cleaned


def test_clean_response_with_triple_backticks():
    """Test _clean_response removes triple backticks."""
    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(),
        provider=mock_provider
    )

    response = "```\n---\nname: test\n---\n```"
    cleaned = respecer._clean_response(response)
    assert "```" not in cleaned
    assert "name: test" in cleaned


def test_clean_response_with_only_end_fence():
    """Test _clean_response removes only trailing fence."""
    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(),
        provider=mock_provider
    )

    response = "---\nname: test\n---\n```"
    cleaned = respecer._clean_response(response)
    assert not cleaned.endswith("```")
    assert "name: test" in cleaned


def test_clean_response_no_fences():
    """Test _clean_response handles content without fences."""
    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(),
        provider=mock_provider
    )

    response = "---\nname: test\n---\n"
    cleaned = respecer._clean_response(response)
    assert "name: test" in cleaned


def test_clean_response_whitespace():
    """Test _clean_response strips whitespace."""
    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(),
        provider=mock_provider
    )

    response = "   \n\n---\nname: test\n---\n   \n\n"
    cleaned = respecer._clean_response(response)
    assert cleaned == "---\nname: test\n---"


def test_respec_prompt_includes_filename(temp_project):
    """Test that respec includes the source filename in the prompt."""
    src_file = os.path.join(temp_project, "my_module.py")
    with open(src_file, 'w') as f:
        f.write("def test(): pass")

    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(root_dir=temp_project),
        provider=mock_provider
    )

    respecer.respec(src_file)

    prompt = mock_provider.calls[0]["prompt"]
    assert "my_module.py" in prompt


def test_respec_prompt_includes_source_code(temp_project):
    """Test that respec includes the source code in the prompt."""
    src_file = os.path.join(temp_project, "example.py")
    code = "def my_special_function(): return 42"
    with open(src_file, 'w') as f:
        f.write(code)

    mock_provider = MockProvider()
    respecer = Respecer(
        config=SpecSoloistConfig(root_dir=temp_project),
        provider=mock_provider
    )

    respecer.respec(src_file)

    prompt = mock_provider.calls[0]["prompt"]
    assert "my_special_function" in prompt
    assert code in prompt
