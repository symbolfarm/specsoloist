"""
Integration tests for the Arrangement pipeline.

Tests cover: output path routing, test path routing, compiler context injection,
custom test command execution, YAML file loading, and compile_project with arrangement.
"""

import os
import tempfile

from specsoloist.compiler import SpecCompiler
from specsoloist.core import SpecSoloistCore
from specsoloist.parser import SpecParser
from specsoloist.runner import TestRunner
from specsoloist.schema import (
    Arrangement,
    ArrangementBuildCommands,
    ArrangementOutputPaths,
)


class MockProvider:
    """Mock LLM provider for testing."""

    def __init__(self, response_func=None):
        self.response_func = response_func or (lambda p: "# Mock code")
        self.calls = []

    def generate(self, prompt: str, temperature: float = 0.1, model=None) -> str:
        self.calls.append({"prompt": prompt, "model": model})
        return self.response_func(prompt)


def _make_arrangement(impl_path: str, tests_path: str) -> Arrangement:
    """Helper to build a minimal Arrangement with absolute output paths."""
    return Arrangement(
        target_language="python",
        output_paths=ArrangementOutputPaths(
            implementation=impl_path,
            tests=tests_path,
        ),
        build_commands=ArrangementBuildCommands(test="echo test"),
    )


def test_arrangement_output_path_routing():
    """compile_spec with arrangement routes implementation to arrangement.output_paths.implementation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        core = SpecSoloistCore(tmp_dir)
        core.create_spec("math_utils", "Adds two numbers.")
        core._provider = MockProvider(lambda p: "def add(a, b): return a + b")

        impl_path = os.path.join(tmp_dir, "custom_src", "math_utils.py")
        tests_path = os.path.join(tmp_dir, "custom_tests", "test_math.py")
        arr = _make_arrangement(impl_path, tests_path)

        result = core.compile_spec("math_utils", arrangement=arr)

        assert "Compiled to" in result
        assert os.path.exists(impl_path)
        with open(impl_path) as f:
            assert "def add" in f.read()


def test_arrangement_test_path_routing():
    """compile_tests with arrangement routes tests to arrangement.output_paths.tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        core = SpecSoloistCore(tmp_dir)
        core.create_spec("math_utils", "Adds two numbers.")
        core._provider = MockProvider(lambda p: "def test_add(): assert True")

        impl_path = os.path.join(tmp_dir, "custom_src", "math_utils.py")
        tests_path = os.path.join(tmp_dir, "custom_tests", "test_math.py")
        arr = _make_arrangement(impl_path, tests_path)

        result = core.compile_tests("math_utils", arrangement=arr)

        assert "Generated tests at" in result
        assert os.path.exists(tests_path)
        with open(tests_path) as f:
            assert "test_add" in f.read()


def test_arrangement_compiler_context_injected():
    """_build_arrangement_context includes target language, paths, commands, and constraints."""
    arr = Arrangement(
        target_language="python",
        output_paths=ArrangementOutputPaths(
            implementation="src/math_utils.py",
            tests="tests/test_math_utils.py",
        ),
        build_commands=ArrangementBuildCommands(
            lint="uv run ruff check .",
            test="uv run pytest",
        ),
        constraints=["Must use type hints", "Must pass ruff"],
    )

    compiler = SpecCompiler(provider=None, global_context="")
    context = compiler._build_arrangement_context(arr)

    assert "python" in context
    assert "src/math_utils.py" in context
    assert "tests/test_math_utils.py" in context
    assert "uv run pytest" in context
    assert "Must use type hints" in context


def test_arrangement_custom_test_command():
    """run_custom_test executes a shell command and returns success with captured output."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        runner = TestRunner(tmp_dir)
        result = runner.run_custom_test("echo hello")

        assert result.success is True
        assert "hello" in result.output
        assert result.return_code == 0


def test_arrangement_load_from_yaml_file():
    """parse_arrangement reads a bare YAML file and returns a correct Arrangement."""
    yaml_content = """\
target_language: python
output_paths:
  implementation: src/math_utils.py
  tests: tests/test_math_utils.py
environment:
  tools:
    - uv
    - pytest
build_commands:
  test: uv run pytest
constraints:
  - Must use type hints
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yaml_path = os.path.join(tmp_dir, "arrangement.yaml")
        with open(yaml_path, "w") as f:
            f.write(yaml_content)

        parser = SpecParser(tmp_dir)
        with open(yaml_path) as f:
            content = f.read()
        arrangement = parser.parse_arrangement(content)

        assert arrangement.target_language == "python"
        assert arrangement.output_paths.implementation == "src/math_utils.py"
        assert arrangement.output_paths.tests == "tests/test_math_utils.py"
        assert arrangement.environment.tools == ["uv", "pytest"]
        assert arrangement.build_commands.test == "uv run pytest"
        assert arrangement.constraints == ["Must use type hints"]


def test_arrangement_compile_project_with_arrangement():
    """compile_project with arrangement sends outputs to arrangement paths for all specs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        core = SpecSoloistCore(tmp_dir)
        core.create_spec("math_utils", "Adds two numbers.")
        core._provider = MockProvider(lambda p: "def add(a, b): return a + b")

        impl_path = os.path.join(tmp_dir, "custom_src", "math_utils.py")
        tests_path = os.path.join(tmp_dir, "custom_tests", "test_math.py")
        arr = _make_arrangement(impl_path, tests_path)

        result = core.compile_project(generate_tests=True, arrangement=arr)

        assert result.success is True
        assert "math_utils" in result.specs_compiled
        assert os.path.exists(impl_path)
        assert os.path.exists(tests_path)
