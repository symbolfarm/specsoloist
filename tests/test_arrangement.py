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
    ArrangementEnvironment,
    ArrangementOutputPathOverride,
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


# ---------------------------------------------------------------------------
# Per-spec output path overrides
# ---------------------------------------------------------------------------

def test_resolve_implementation_uses_default():
    """resolve_implementation returns the formatted default when no override exists."""
    paths = ArrangementOutputPaths(
        implementation="src/{name}.py",
        tests="tests/test_{name}.py",
    )
    assert paths.resolve_implementation("mymod") == "src/mymod.py"


def test_resolve_tests_uses_default():
    paths = ArrangementOutputPaths(
        implementation="src/{name}.py",
        tests="tests/test_{name}.py",
    )
    assert paths.resolve_tests("mymod") == "tests/test_mymod.py"


def test_resolve_implementation_uses_override():
    """resolve_implementation returns the override path when one is set for the spec."""
    paths = ArrangementOutputPaths(
        implementation="src/{name}.ts",
        tests="tests/{name}.test.ts",
        overrides={
            "chat_route": ArrangementOutputPathOverride(
                implementation="src/app/api/chat/route.ts"
            )
        },
    )
    assert paths.resolve_implementation("chat_route") == "src/app/api/chat/route.ts"
    # Other specs still use the default
    assert paths.resolve_implementation("ai_client") == "src/ai_client.ts"


def test_resolve_tests_uses_override():
    paths = ArrangementOutputPaths(
        implementation="src/{name}.ts",
        tests="tests/{name}.test.ts",
        overrides={
            "chat_route": ArrangementOutputPathOverride(
                tests="tests/chat_route.test.ts"
            )
        },
    )
    assert paths.resolve_tests("chat_route") == "tests/chat_route.test.ts"
    assert paths.resolve_tests("ai_client") == "tests/ai_client.test.ts"


def test_partial_override_falls_back_for_missing_field():
    """If only implementation is overridden, tests still fall back to the default."""
    paths = ArrangementOutputPaths(
        implementation="src/{name}.ts",
        tests="tests/{name}.test.ts",
        overrides={
            "chat_route": ArrangementOutputPathOverride(
                implementation="src/app/api/chat/route.ts"
                # no tests override
            )
        },
    )
    assert paths.resolve_implementation("chat_route") == "src/app/api/chat/route.ts"
    assert paths.resolve_tests("chat_route") == "tests/chat_route.test.ts"


def test_arrangement_override_round_trips_through_yaml():
    """Overrides survive a round-trip through YAML parsing."""
    yaml_content = """\
target_language: typescript
output_paths:
  implementation: src/{name}.ts
  tests: tests/{name}.test.ts
  overrides:
    chat_route:
      implementation: src/app/api/chat/route.ts
      tests: tests/chat_route.test.ts
build_commands:
  test: npx vitest run
"""
    parser = SpecParser(".")
    arrangement = parser.parse_arrangement(yaml_content)

    assert arrangement.output_paths.resolve_implementation("chat_route") == "src/app/api/chat/route.ts"
    assert arrangement.output_paths.resolve_tests("chat_route") == "tests/chat_route.test.ts"
    assert arrangement.output_paths.resolve_implementation("ai_client") == "src/ai_client.ts"


def test_override_path_used_when_compiling(tmp_path):
    """compile_spec writes to the override path, not the default template path."""
    core = SpecSoloistCore(str(tmp_path))
    core.create_spec("mymod", "Does something.")
    core._provider = MockProvider(lambda p: "def run(): pass")

    override_path = str(tmp_path / "special" / "mymod_custom.py")
    arr = Arrangement(
        target_language="python",
        output_paths=ArrangementOutputPaths(
            implementation=str(tmp_path / "src" / "{name}.py"),
            tests=str(tmp_path / "tests" / "test_{name}.py"),
            overrides={
                "mymod": ArrangementOutputPathOverride(implementation=override_path)
            },
        ),
        build_commands=ArrangementBuildCommands(test="echo test"),
    )

    result = core.compile_spec("mymod", arrangement=arr)

    assert os.path.exists(override_path)
    assert not os.path.exists(str(tmp_path / "src" / "mymod.py"))


# ---------------------------------------------------------------------------
# dependencies field
# ---------------------------------------------------------------------------

def test_dependencies_parsed_from_yaml():
    """ArrangementEnvironment.dependencies is populated from YAML."""
    yaml_content = """\
target_language: python
output_paths:
  implementation: src/{name}.py
  tests: tests/test_{name}.py
environment:
  tools: [uv, pytest]
  setup_commands: [uv sync]
  dependencies:
    python-fasthtml: ">=0.12,<0.13"
    starlette: ">=0.52"
    pytest: ">=7.0"
build_commands:
  test: uv run pytest
"""
    parser = SpecParser(".")
    arrangement = parser.parse_arrangement(yaml_content)

    assert arrangement.environment.dependencies == {
        "python-fasthtml": ">=0.12,<0.13",
        "starlette": ">=0.52",
        "pytest": ">=7.0",
    }


def test_empty_dependencies_default():
    """ArrangementEnvironment.dependencies defaults to an empty dict."""
    env = ArrangementEnvironment()
    assert env.dependencies == {}


def test_dependencies_injected_into_prompt():
    """_build_arrangement_context includes a Dependency Versions table when dependencies are set."""
    arr = Arrangement(
        target_language="python",
        output_paths=ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py",
        ),
        environment=ArrangementEnvironment(
            setup_commands=["uv sync"],
            dependencies={
                "python-fasthtml": ">=0.12,<0.13",
                "starlette": ">=0.52",
            },
        ),
        build_commands=ArrangementBuildCommands(test="uv run pytest"),
    )

    compiler = SpecCompiler(provider=None, global_context="")
    context = compiler._build_arrangement_context(arr)

    assert "Dependency Versions" in context
    assert "python-fasthtml" in context
    assert ">=0.12,<0.13" in context
    assert "starlette" in context
    assert ">=0.52" in context


def test_empty_dependencies_not_injected():
    """_build_arrangement_context omits the Dependency Versions section when dependencies is empty."""
    arr = Arrangement(
        target_language="python",
        output_paths=ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py",
        ),
        environment=ArrangementEnvironment(setup_commands=["uv sync"]),
        build_commands=ArrangementBuildCommands(test="uv run pytest"),
    )

    compiler = SpecCompiler(provider=None, global_context="")
    context = compiler._build_arrangement_context(arr)

    assert "Dependency Versions" not in context


def test_dependencies_without_install_command_warns():
    """_check_arrangement_dependencies returns a warning when dependencies lack an install command."""
    from specsoloist.cli import _check_arrangement_dependencies

    arr = Arrangement(
        target_language="python",
        output_paths=ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py",
        ),
        environment=ArrangementEnvironment(
            setup_commands=["uv run ruff check ."],  # no install command
            dependencies={"python-fasthtml": ">=0.12"},
        ),
        build_commands=ArrangementBuildCommands(test="uv run pytest"),
    )

    warnings = _check_arrangement_dependencies(arr)
    assert len(warnings) == 1
    assert "install command" in warnings[0]


def test_dependencies_with_install_command_no_warning():
    """_check_arrangement_dependencies returns no warning when setup_commands includes an install step."""
    from specsoloist.cli import _check_arrangement_dependencies

    arr = Arrangement(
        target_language="python",
        output_paths=ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py",
        ),
        environment=ArrangementEnvironment(
            setup_commands=["uv sync"],
            dependencies={"python-fasthtml": ">=0.12"},
        ),
        build_commands=ArrangementBuildCommands(test="uv run pytest"),
    )

    warnings = _check_arrangement_dependencies(arr)
    assert warnings == []


def test_no_dependencies_no_warning():
    """_check_arrangement_dependencies returns no warning when dependencies is empty."""
    from specsoloist.cli import _check_arrangement_dependencies

    arr = Arrangement(
        target_language="python",
        output_paths=ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py",
        ),
        environment=ArrangementEnvironment(setup_commands=[]),
        build_commands=ArrangementBuildCommands(test="uv run pytest"),
    )

    warnings = _check_arrangement_dependencies(arr)
    assert warnings == []


def test_compiler_context_includes_overrides():
    """_build_arrangement_context mentions per-spec overrides."""
    arr = Arrangement(
        target_language="typescript",
        output_paths=ArrangementOutputPaths(
            implementation="src/{name}.ts",
            tests="tests/{name}.test.ts",
            overrides={
                "chat_route": ArrangementOutputPathOverride(
                    implementation="src/app/api/chat/route.ts"
                )
            },
        ),
        build_commands=ArrangementBuildCommands(test="npx vitest run"),
    )
    compiler = SpecCompiler(provider=None, global_context="")
    context = compiler._build_arrangement_context(arr)

    assert "chat_route" in context
    assert "src/app/api/chat/route.ts" in context
