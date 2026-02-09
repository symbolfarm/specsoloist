import pytest
import os
import shutil
import tempfile
from unittest.mock import Mock, MagicMock, patch

from specsoloist.respec import Respecer
from specsoloist.config import SpecSoloistConfig


class MockProvider:
    """Mock LLM provider for testing."""

    def __init__(self, response_func=None):
        self.response_func = response_func or (lambda p, model=None: "---\nname: test\ntype: bundle\n---\n# Test Spec")
        self.calls = []

    def generate(self, prompt: str, model=None) -> str:
        self.calls.append({"prompt": prompt, "model": model})
        return self.response_func(prompt, model)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_config(temp_dir):
    """Create a mock config for testing."""
    config = MagicMock(spec=SpecSoloistConfig)
    config.root_dir = temp_dir
    config.create_provider = Mock(return_value=MockProvider())
    return config


@pytest.fixture
def respecer(mock_config):
    """Create a Respecer instance with mock config and provider."""
    mock_provider = MockProvider()
    return Respecer(config=mock_config, provider=mock_provider)


class TestRespecerInit:
    """Test Respecer initialization."""

    def test_init_with_defaults(self, monkeypatch):
        """Test initialization with default config and provider."""
        monkeypatch.setenv("SPECSOLOIST_LLM_PROVIDER", "gemini")
        monkeypatch.setenv("GEMINI_API_KEY", "test_key")

        respecer = Respecer()

        assert respecer.config is not None
        assert respecer.provider is not None

    def test_init_with_custom_config(self, mock_config):
        """Test initialization with custom config."""
        mock_provider = MockProvider()

        respecer = Respecer(config=mock_config, provider=mock_provider)

        assert respecer.config == mock_config
        assert respecer.provider == mock_provider

    def test_init_with_config_no_provider(self, mock_config):
        """Test initialization with config but no provider."""
        respecer = Respecer(config=mock_config)

        assert respecer.config == mock_config
        assert respecer.provider is not None


class TestRespecMethod:
    """Test the respec method."""

    def test_respec_source_file_not_found(self, respecer):
        """Test that FileNotFoundError is raised when source file doesn't exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            respecer.respec("/nonexistent/file.py")

        assert "Source file not found" in str(exc_info.value)

    def test_respec_reads_source_file(self, respecer, temp_dir):
        """Test that respec reads the source file."""
        source_path = os.path.join(temp_dir, "example.py")
        source_code = """
def add(a, b):
    return a + b
"""
        with open(source_path, 'w') as f:
            f.write(source_code)

        result = respecer.respec(source_path)

        # Check that provider was called
        assert len(respecer.provider.calls) == 1
        # Check that the source code is in the prompt
        assert "example.py" in respecer.provider.calls[0]["prompt"]
        assert "def add(a, b):" in respecer.provider.calls[0]["prompt"]
        # Check that result is a string
        assert isinstance(result, str)

    def test_respec_loads_spec_format_rules(self, respecer, temp_dir):
        """Test that respec loads spec format rules if they exist."""
        # Create spec format file
        spec_format_dir = os.path.join(temp_dir, "score")
        os.makedirs(spec_format_dir, exist_ok=True)
        spec_format_path = os.path.join(spec_format_dir, "spec_format.spec.md")
        with open(spec_format_path, 'w') as f:
            f.write("# Spec Format Rules\nRule 1: All specs must have a name")

        # Create source file
        source_path = os.path.join(temp_dir, "example.py")
        with open(source_path, 'w') as f:
            f.write("def test(): pass")

        result = respecer.respec(source_path)

        # Check that spec rules are in the prompt
        assert "Rule 1: All specs must have a name" in respecer.provider.calls[0]["prompt"]
        assert "# Spec Format Rules" in respecer.provider.calls[0]["prompt"]

    def test_respec_with_test_file(self, respecer, temp_dir):
        """Test that respec includes test file content when provided."""
        source_path = os.path.join(temp_dir, "example.py")
        with open(source_path, 'w') as f:
            f.write("def add(a, b): return a + b")

        test_path = os.path.join(temp_dir, "test_example.py")
        test_code = """
def test_add():
    assert add(1, 2) == 3
"""
        with open(test_path, 'w') as f:
            f.write(test_code)

        result = respecer.respec(source_path, test_path=test_path)

        # Check that test code is in the prompt
        assert "test_add" in respecer.provider.calls[0]["prompt"]
        assert "assert add(1, 2) == 3" in respecer.provider.calls[0]["prompt"]
        assert "# Existing Tests" in respecer.provider.calls[0]["prompt"]

    def test_respec_with_nonexistent_test_file(self, respecer, temp_dir):
        """Test that respec doesn't fail when test_path doesn't exist."""
        source_path = os.path.join(temp_dir, "example.py")
        with open(source_path, 'w') as f:
            f.write("def add(a, b): return a + b")

        result = respecer.respec(source_path, test_path="/nonexistent/test.py")

        # Should not fail and test code should not be in prompt
        assert "# Existing Tests" not in respecer.provider.calls[0]["prompt"]

    def test_respec_with_model_parameter(self, respecer, temp_dir):
        """Test that model parameter is passed to provider."""
        source_path = os.path.join(temp_dir, "example.py")
        with open(source_path, 'w') as f:
            f.write("def test(): pass")

        respecer.respec(source_path, model="claude-3-opus")

        # Check that model was passed to provider
        assert respecer.provider.calls[0]["model"] == "claude-3-opus"

    def test_respec_returns_string(self, respecer, temp_dir):
        """Test that respec returns a string."""
        source_path = os.path.join(temp_dir, "example.py")
        with open(source_path, 'w') as f:
            f.write("def test(): pass")

        result = respecer.respec(source_path)

        assert isinstance(result, str)


class TestCleanResponse:
    """Test the _clean_response method."""

    def test_clean_response_no_fences(self, respecer):
        """Test cleaning response without code fences."""
        response = "---\nname: test\ntype: bundle\n---\n# Spec"

        result = respecer._clean_response(response)

        assert result == "---\nname: test\ntype: bundle\n---\n# Spec"

    def test_clean_response_markdown_fence(self, respecer):
        """Test cleaning response with markdown fence."""
        response = "```markdown\n---\nname: test\n---\n# Spec\n```"

        result = respecer._clean_response(response)

        assert result == "---\nname: test\n---\n# Spec"

    def test_clean_response_code_fence(self, respecer):
        """Test cleaning response with code fence."""
        response = "```\n---\nname: test\n---\n# Spec\n```"

        result = respecer._clean_response(response)

        assert result == "---\nname: test\n---\n# Spec"

    def test_clean_response_with_leading_trailing_whitespace(self, respecer):
        """Test cleaning response with leading and trailing whitespace."""
        response = "   \n\n```\n---\nname: test\n---\n```\n\n   "

        result = respecer._clean_response(response)

        assert result == "---\nname: test\n---"
        assert not result.startswith(" ")
        assert not result.endswith(" ")

    def test_clean_response_only_markdown_fence(self, respecer):
        """Test cleaning response with only markdown fence."""
        response = "```markdown\nContent\n```"

        result = respecer._clean_response(response)

        assert result == "Content"

    def test_clean_response_only_code_fence(self, respecer):
        """Test cleaning response with only code fence."""
        response = "```\nContent\n```"

        result = respecer._clean_response(response)

        assert result == "Content"

    def test_clean_response_nested_fences(self, respecer):
        """Test cleaning response with nested fence markers."""
        response = "```markdown\nContent with ``` inside\n```"

        result = respecer._clean_response(response)

        # Should remove outer markdown fence, leaving content with inner fence
        assert "Content with ```" in result

    def test_clean_response_empty_string(self, respecer):
        """Test cleaning empty response."""
        response = ""

        result = respecer._clean_response(response)

        assert result == ""

    def test_clean_response_whitespace_only(self, respecer):
        """Test cleaning whitespace-only response."""
        response = "   \n\n   "

        result = respecer._clean_response(response)

        assert result == ""


class TestRespecIntegration:
    """Integration tests for the Respecer class."""

    def test_full_workflow(self, temp_dir):
        """Test full respec workflow with real files."""
        config = SpecSoloistConfig(root_dir=temp_dir)
        mock_provider = MockProvider(
            lambda p, model=None: "---\nname: math\ntype: bundle\n---\n# Math utilities spec"
        )

        respecer = Respecer(config=config, provider=mock_provider)

        # Create source and test files
        source_path = os.path.join(temp_dir, "math.py")
        with open(source_path, 'w') as f:
            f.write("def add(a, b): return a + b")

        test_path = os.path.join(temp_dir, "test_math.py")
        with open(test_path, 'w') as f:
            f.write("def test_add(): assert add(1, 2) == 3")

        result = respecer.respec(source_path, test_path=test_path)

        # Verify result
        assert "name: math" in result
        assert "type: bundle" in result
        assert "# Math utilities spec" in result

    def test_with_complex_source(self, temp_dir):
        """Test with complex multi-function source code."""
        config = SpecSoloistConfig(root_dir=temp_dir)
        mock_provider = MockProvider()
        respecer = Respecer(config=config, provider=mock_provider)

        source_path = os.path.join(temp_dir, "complex.py")
        source_code = """
class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b

def standalone_function():
    return 42
"""
        with open(source_path, 'w') as f:
            f.write(source_code)

        result = respecer.respec(source_path)

        # Verify that the provider received the full source
        prompt = respecer.provider.calls[0]["prompt"]
        assert "class Calculator:" in prompt
        assert "def standalone_function():" in prompt

    def test_provider_error_handling(self, temp_dir):
        """Test behavior when provider returns error response."""
        config = SpecSoloistConfig(root_dir=temp_dir)

        def error_response(p, model=None):
            return "Error: Unable to parse code"

        mock_provider = MockProvider(error_response)
        respecer = Respecer(config=config, provider=mock_provider)

        source_path = os.path.join(temp_dir, "test.py")
        with open(source_path, 'w') as f:
            f.write("def test(): pass")

        result = respecer.respec(source_path)

        # Should return whatever the provider returns (error handling is provider's job)
        assert "Error: Unable to parse code" in result
