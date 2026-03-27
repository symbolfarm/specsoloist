"""Tests for SpecCompiler."""

import os
import tempfile
from unittest.mock import Mock, MagicMock

from specsoloist.compiler import SpecCompiler
from specsoloist.parser import SpecParser, ParsedSpec, SpecMetadata
from specsoloist.schema import (
    Arrangement,
    ArrangementOutputPaths,
    ArrangementEnvironment,
    ArrangementBuildCommands,
    ArrangementEnvVar,
    ArrangementOutputPathOverride,
)


def create_mock_provider():
    """Create a mock LLM provider."""
    provider = Mock()
    provider.generate = Mock(return_value="def test():\n    pass\n")
    return provider


def create_simple_spec():
    """Create a simple parsed spec for testing."""
    metadata = SpecMetadata(
        name="test_component",
        type="function",
        dependencies=[]
    )
    parsed = ParsedSpec(
        metadata=metadata,
        content="# Overview\nA test component.\n\n# Interface\n```yaml:schema\ninputs:\n  x: integer\noutputs:\n  result: integer\n```",
        body="# Overview\nA test component.\n\n# Interface\n```yaml:schema\ninputs:\n  x: integer\noutputs:\n  result: integer\n```",
        path="/tmp/test_component.spec.md"
    )
    return parsed


def create_simple_arrangement():
    """Create a simple arrangement for testing."""
    return Arrangement(
        target_language="python",
        output_paths=ArrangementOutputPaths(
            implementation="src/{name}.py",
            tests="tests/test_{name}.py"
        ),
        build_commands=ArrangementBuildCommands(test="pytest")
    )


class TestSpecCompilerInit:
    """Test SpecCompiler initialization."""

    def test_init_with_provider_only(self):
        """Test initialization with just a provider."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        assert compiler.provider is provider
        assert compiler.global_context == ""

    def test_init_with_global_context(self):
        """Test initialization with global context."""
        provider = create_mock_provider()
        context = "Project context here"
        compiler = SpecCompiler(provider, global_context=context)
        assert compiler.global_context == context


class TestCompileCode:
    """Test compile_code method."""

    def test_compile_code_basic(self):
        """Test basic code compilation."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()
        spec.metadata.language_target = "python"

        result = compiler.compile_code(spec)

        assert result == "def test():\n    pass\n"
        provider.generate.assert_called_once()
        call_args = provider.generate.call_args
        assert "expert python developer" in call_args[0][0].lower()

    def test_compile_code_with_model_override(self):
        """Test code compilation with model override."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()

        compiler.compile_code(spec, model="gpt-4")

        provider.generate.assert_called_once()
        assert provider.generate.call_args[1]["model"] == "gpt-4"

    def test_compile_code_with_arrangement(self):
        """Test code compilation with arrangement."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()
        arrangement = create_simple_arrangement()

        result = compiler.compile_code(spec, arrangement=arrangement)

        provider.generate.assert_called_once()
        call_args = provider.generate.call_args[0][0]
        assert "src/{name}.py" in call_args
        assert "tests/test_{name}.py" in call_args
        assert "pytest" in call_args

    def test_compile_code_strips_markdown_fences(self):
        """Test that markdown fences are stripped from response."""
        provider = create_mock_provider()
        provider.generate = Mock(return_value="```python\ndef test():\n    pass\n```")
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()

        result = compiler.compile_code(spec)

        assert result == "def test():\n    pass"
        assert not result.startswith("```")
        assert not result.endswith("```")

    def test_compile_code_with_dependencies(self):
        """Test code compilation with dependencies."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        metadata = SpecMetadata(
            name="dependent",
            type="function",
            dependencies=["base_module", {"name": "Helper", "from": "helper.spec.md"}]
        )
        spec = ParsedSpec(
            metadata=metadata,
            content="Test content",
            body="Test body",
            path="/tmp/dependent.spec.md"
        )

        compiler.compile_code(spec)

        call_args = provider.generate.call_args[0][0]
        assert "base_module" in call_args
        assert "Helper" in call_args
        assert "helper" in call_args

    def test_compile_code_with_reference_specs(self):
        """Test code compilation with reference specs."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        metadata = SpecMetadata(
            name="test",
            type="function",
            dependencies=["reference_api"]
        )
        spec = ParsedSpec(
            metadata=metadata,
            content="test content",
            body="test body",
            path="/tmp/test.spec.md"
        )

        ref_spec = create_simple_spec()
        ref_spec.metadata.name = "reference_api"
        ref_spec.body = "# API Documentation\n\nDetailed API docs here."

        reference_specs = {"reference_api": ref_spec}

        compiler.compile_code(spec, reference_specs=reference_specs)

        call_args = provider.generate.call_args[0][0]
        assert "Reference: reference_api" in call_args
        assert "Detailed API docs here" in call_args

    def test_compile_code_with_global_context(self):
        """Test that global context is included in prompt."""
        provider = create_mock_provider()
        global_ctx = "This is global context."
        compiler = SpecCompiler(provider, global_context=global_ctx)
        spec = create_simple_spec()

        compiler.compile_code(spec)

        call_args = provider.generate.call_args[0][0]
        assert "This is global context." in call_args


class TestCompileTypedef:
    """Test compile_typedef method."""

    def test_compile_typedef_basic(self):
        """Test basic typedef compilation."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()

        result = compiler.compile_typedef(spec)

        assert result == "def test():\n    pass\n"
        provider.generate.assert_called_once()
        call_args = provider.generate.call_args[0][0]
        assert "type system" in call_args.lower()

    def test_compile_typedef_with_arrangement(self):
        """Test typedef compilation with arrangement."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()
        arrangement = create_simple_arrangement()

        compiler.compile_typedef(spec, arrangement=arrangement)

        call_args = provider.generate.call_args[0][0]
        assert "Build Arrangement (python)" in call_args

    def test_compile_typedef_dataclass_instruction(self):
        """Test that Python-specific instructions are included."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()
        spec.metadata.language_target = "python"

        compiler.compile_typedef(spec)

        call_args = provider.generate.call_args[0][0]
        assert "dataclass" in call_args.lower()


class TestCompileOrchestrator:
    """Test compile_orchestrator method."""

    def test_compile_orchestrator_basic(self):
        """Test basic orchestrator compilation."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()
        spec.metadata.type = "orchestrator"

        result = compiler.compile_orchestrator(spec)

        assert result == "def test():\n    pass\n"
        provider.generate.assert_called_once()
        call_args = provider.generate.call_args[0][0]
        assert "orchestration" in call_args.lower()

    def test_compile_orchestrator_with_steps(self):
        """Test orchestrator compilation with workflow steps."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        # Create a spec with steps schema
        spec = create_simple_spec()
        spec.metadata.type = "orchestrator"

        # Mock the schema with steps
        from specsoloist.schema import WorkflowStep
        step1 = WorkflowStep(name="step1", spec="component1")
        step2 = WorkflowStep(name="step2", spec="component2")

        from specsoloist.schema import InterfaceSchema
        spec.schema = InterfaceSchema(
            inputs={},
            outputs={},
            steps=[step1, step2]
        )

        compiler.compile_orchestrator(spec)

        call_args = provider.generate.call_args[0][0]
        assert "component1" in call_args
        assert "component2" in call_args


class TestCompileTests:
    """Test compile_tests method."""

    def test_compile_tests_python(self):
        """Test test compilation for Python."""
        provider = create_mock_provider()
        provider.generate = Mock(return_value="def test_example():\n    pass\n")
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()
        spec.metadata.language_target = "python"

        result = compiler.compile_tests(spec)

        assert "def test_example" in result
        call_args = provider.generate.call_args[0][0]
        assert "pytest" in call_args

    def test_compile_tests_typescript(self):
        """Test test compilation for TypeScript."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()
        spec.metadata.language_target = "typescript"

        compiler.compile_tests(spec)

        call_args = provider.generate.call_args[0][0]
        assert "node:test" in call_args
        assert "node:assert" in call_args

    def test_compile_tests_with_arrangement(self):
        """Test test compilation with arrangement."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()
        arrangement = create_simple_arrangement()

        compiler.compile_tests(spec, arrangement=arrangement)

        call_args = provider.generate.call_args[0][0]
        assert "test_component" in call_args

    def test_compile_tests_strips_markdown_fences(self):
        """Test that markdown fences are stripped from test response."""
        provider = create_mock_provider()
        provider.generate = Mock(return_value="```python\ndef test_x():\n    assert True\n```")
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()

        result = compiler.compile_tests(spec)

        assert result == "def test_x():\n    assert True"
        assert not result.startswith("```")


class TestGenerateFix:
    """Test generate_fix method."""

    def test_generate_fix_basic(self):
        """Test basic fix generation."""
        provider = create_mock_provider()
        provider.generate = Mock(
            return_value="### FILE: build/test_component.py\ndef fixed():\n    pass\n### END"
        )
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()

        result = compiler.generate_fix(
            spec,
            code_content="def broken():\n    pass",
            test_content="def test_broken():\n    pass",
            error_log="AssertionError: expected 1 but got 2"
        )

        assert "### FILE:" in result
        provider.generate.assert_called_once()
        call_args = provider.generate.call_args[0][0]
        assert "broken" in call_args or "test_component" in call_args
        assert "AssertionError" in call_args

    def test_generate_fix_with_arrangement(self):
        """Test fix generation with arrangement."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()
        arrangement = create_simple_arrangement()

        compiler.generate_fix(
            spec,
            code_content="code",
            test_content="test",
            error_log="error",
            arrangement=arrangement
        )

        call_args = provider.generate.call_args[0][0]
        assert "src/{name}.py" in call_args
        assert "tests/test_{name}.py" in call_args

    def test_generate_fix_spec_is_source_of_truth(self):
        """Test that spec content is included as source of truth."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()

        compiler.generate_fix(
            spec,
            code_content="broken",
            test_content="bad_test",
            error_log="failed"
        )

        call_args = provider.generate.call_args[0][0]
        assert "Source of Truth" in call_args
        assert spec.content in call_args


class TestParseFixResponse:
    """Test parse_fix_response method."""

    def test_parse_fix_response_single_file(self):
        """Test parsing a fix response with a single file."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        response = """### FILE: /path/to/file.py
def fixed_code():
    return 42
### END
"""
        result = compiler.parse_fix_response(response)

        assert len(result) == 1
        assert "/path/to/file.py" in result
        assert "def fixed_code" in result["/path/to/file.py"]

    def test_parse_fix_response_multiple_files(self):
        """Test parsing a fix response with multiple files."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        response = """### FILE: /path/to/impl.py
def fixed():
    pass
### END

### FILE: /path/to/test.py
def test_fixed():
    pass
### END
"""
        result = compiler.parse_fix_response(response)

        assert len(result) == 2
        assert "/path/to/impl.py" in result
        assert "/path/to/test.py" in result

    def test_parse_fix_response_with_markdown_fences(self):
        """Test that markdown fences are stripped from parsed content."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        response = """### FILE: /test.py
```python
def test():
    pass
```
### END
"""
        result = compiler.parse_fix_response(response)

        assert len(result) == 1
        content = result["/test.py"]
        assert not content.startswith("```")
        assert not content.endswith("```")
        assert "def test" in content

    def test_parse_fix_response_empty(self):
        """Test parsing an empty fix response."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        response = "No fixes needed."
        result = compiler.parse_fix_response(response)

        assert len(result) == 0

    def test_parse_fix_response_with_whitespace(self):
        """Test that whitespace is properly stripped."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        response = """
### FILE:   /path/to/file.py
def code():
    pass
### END
"""
        result = compiler.parse_fix_response(response)

        assert "/path/to/file.py" in result


class TestStripMarkdownFences:
    """Test _strip_markdown_fences method."""

    def test_strip_no_fences(self):
        """Test stripping when there are no fences."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        code = "def test():\n    pass\n"
        result = compiler._strip_markdown_fences(code)

        assert result == code

    def test_strip_python_fences(self):
        """Test stripping Python code fences."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        code = "```python\ndef test():\n    pass\n```"
        result = compiler._strip_markdown_fences(code)

        assert result == "def test():\n    pass"
        assert not result.startswith("```")

    def test_strip_generic_fences(self):
        """Test stripping generic code fences."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        code = "```\ndef test():\n    pass\n```"
        result = compiler._strip_markdown_fences(code)

        assert result == "def test():\n    pass"

    def test_strip_fences_preserves_content(self):
        """Test that content is preserved when stripping fences."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        code = "```typescript\nfunction test() {\n  return 42;\n}\n```"
        result = compiler._strip_markdown_fences(code)

        assert "function test" in result
        assert "return 42" in result


class TestBuildImportContext:
    """Test _build_import_context method."""

    def test_no_dependencies(self):
        """Test import context with no dependencies."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()

        context = compiler._build_import_context(spec)

        assert "No external dependencies" in context

    def test_string_dependencies(self):
        """Test import context with string dependencies."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        metadata = SpecMetadata(
            name="test",
            type="function",
            dependencies=["module1", "module2"]
        )
        spec = ParsedSpec(
            metadata=metadata,
            content="test",
            body="test",
            path="/tmp/test.spec.md"
        )

        context = compiler._build_import_context(spec)

        assert "module1" in context
        assert "module2" in context

    def test_dict_dependencies(self):
        """Test import context with dict dependencies."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        metadata = SpecMetadata(
            name="test",
            type="function",
            dependencies=[
                {"name": "Helper", "from": "helper"}
            ]
        )
        spec = ParsedSpec(
            metadata=metadata,
            content="test",
            body="test",
            path="/tmp/test.spec.md"
        )

        context = compiler._build_import_context(spec)

        assert "Helper" in context
        assert "helper" in context

    def test_reference_specs_included(self):
        """Test that reference specs are included as API documentation."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        metadata = SpecMetadata(
            name="test",
            type="function",
            dependencies=["api_module"]
        )
        spec = ParsedSpec(
            metadata=metadata,
            content="test",
            body="test",
            path="/tmp/test.spec.md"
        )

        ref_spec = create_simple_spec()
        ref_spec.metadata.name = "api_module"
        ref_spec.body = "# API Documentation\n\nAPI methods here."

        context = compiler._build_import_context(spec, reference_specs={"api_module": ref_spec})

        assert "Reference: api_module" in context
        assert "API Documentation" in context


class TestBuildArrangementContext:
    """Test _build_arrangement_context method."""

    def test_no_arrangement(self):
        """Test that empty context is returned when no arrangement."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        context = compiler._build_arrangement_context(None)

        assert context == ""

    def test_arrangement_basic_fields(self):
        """Test arrangement context includes basic fields."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        arrangement = create_simple_arrangement()

        context = compiler._build_arrangement_context(arrangement)

        assert "python" in context
        assert "src/{name}.py" in context
        assert "tests/test_{name}.py" in context

    def test_arrangement_with_dependencies(self):
        """Test arrangement context includes dependencies."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        arrangement = Arrangement(
            target_language="python",
            output_paths=ArrangementOutputPaths(
                implementation="src/{name}.py",
                tests="tests/test_{name}.py"
            ),
            environment=ArrangementEnvironment(
                dependencies={"numpy": ">=1.20", "pandas": ">=1.0"}
            ),
            build_commands=ArrangementBuildCommands(test="pytest")
        )

        context = compiler._build_arrangement_context(arrangement)

        assert "numpy" in context
        assert "1.20" in context
        assert "pandas" in context

    def test_arrangement_with_env_vars(self):
        """Test arrangement context includes environment variables."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        arrangement = Arrangement(
            target_language="python",
            output_paths=ArrangementOutputPaths(
                implementation="src/{name}.py",
                tests="tests/test_{name}.py"
            ),
            environment=ArrangementEnvironment(
                dependencies={}
            ),
            env_vars={
                "API_KEY": ArrangementEnvVar(description="API key"),
                "DEBUG": ArrangementEnvVar(description="Debug mode", required=False, example="false")
            },
            build_commands=ArrangementBuildCommands(test="pytest")
        )

        context = compiler._build_arrangement_context(arrangement)

        assert "API_KEY" in context
        assert "DEBUG" in context
        assert "required" in context

    def test_arrangement_with_constraints(self):
        """Test arrangement context includes constraints."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        arrangement = Arrangement(
            target_language="python",
            output_paths=ArrangementOutputPaths(
                implementation="src/{name}.py",
                tests="tests/test_{name}.py"
            ),
            build_commands=ArrangementBuildCommands(test="pytest"),
            constraints=["Must support Python 3.8+", "No external HTTP requests"]
        )

        context = compiler._build_arrangement_context(arrangement)

        assert "Python 3.8+" in context
        assert "HTTP" in context

    def test_arrangement_with_output_overrides(self):
        """Test arrangement context includes output path overrides."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)

        arrangement = Arrangement(
            target_language="python",
            output_paths=ArrangementOutputPaths(
                implementation="src/{name}.py",
                tests="tests/test_{name}.py",
                overrides={
                    "special_spec": ArrangementOutputPathOverride(
                        implementation="custom/impl.py",
                        tests="custom/test.py"
                    )
                }
            ),
            build_commands=ArrangementBuildCommands(test="pytest")
        )

        context = compiler._build_arrangement_context(arrangement)

        assert "special_spec" in context
        assert "custom/impl.py" in context


class TestIntegration:
    """Integration tests for the compiler."""

    def test_full_compilation_flow(self):
        """Test a full compilation flow."""
        provider = create_mock_provider()
        provider.generate = Mock(return_value="def implementation():\n    pass")
        compiler = SpecCompiler(provider, global_context="Global context")
        spec = create_simple_spec()
        arrangement = create_simple_arrangement()

        code = compiler.compile_code(spec, arrangement=arrangement)
        tests = compiler.compile_tests(spec, arrangement=arrangement)

        assert "def implementation" in code
        assert provider.generate.call_count == 2

    def test_fix_flow(self):
        """Test a fix and re-generation flow."""
        provider = create_mock_provider()
        compiler = SpecCompiler(provider)
        spec = create_simple_spec()

        # Generate initial fix response
        provider.generate = Mock(
            return_value="### FILE: /test.py\ndef fixed():\n    pass\n### END"
        )

        fix_response = compiler.generate_fix(
            spec,
            code_content="broken",
            test_content="test",
            error_log="failed"
        )

        parsed = compiler.parse_fix_response(fix_response)

        assert len(parsed) == 1
        assert "fixed" in list(parsed.values())[0]
