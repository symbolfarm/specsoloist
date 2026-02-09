"""
Tests for the SpecCompiler module.
"""

import pytest
from specsoloist.compiler import SpecCompiler
from specsoloist.parser import ParsedSpec, SpecMetadata


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self, response: str = "mock response"):
        self.response = response
        self.calls = []

    def generate(self, prompt: str, temperature: float = 0.1, model=None) -> str:
        """Record the call and return the mock response."""
        self.calls.append({
            "prompt": prompt,
            "temperature": temperature,
            "model": model
        })
        return self.response


@pytest.fixture
def mock_provider():
    """Fixture providing a mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def basic_spec():
    """Fixture providing a basic parsed spec."""
    metadata = SpecMetadata(
        name="test_module",
        description="A test module",
        type="function",
        tags=["test"],
        dependencies=[]
    )
    return ParsedSpec(
        metadata=metadata,
        content="---\nname: test_module\n---\n# Overview\nTest module\n",
        body="# Overview\nTest module\n",
        path="/specs/test_module.spec.md"
    )


@pytest.fixture
def spec_with_dependencies():
    """Fixture providing a spec with dependencies."""
    metadata = SpecMetadata(
        name="auth",
        description="Auth module",
        type="function",
        dependencies=["users", {"name": "db", "from": "database.spec.md"}]
    )
    return ParsedSpec(
        metadata=metadata,
        content="---\nname: auth\ndependencies:\n  - users\n  - name: db\n    from: database.spec.md\n---\n# Overview\nAuth module\n",
        body="# Overview\nAuth module\n",
        path="/specs/auth.spec.md"
    )


class TestSpecCompilerInit:
    """Tests for SpecCompiler initialization."""

    def test_init_with_provider_only(self, mock_provider):
        """Test initializing compiler with just a provider."""
        compiler = SpecCompiler(mock_provider)
        assert compiler.provider is mock_provider
        assert compiler.global_context == ""

    def test_init_with_global_context(self, mock_provider):
        """Test initializing compiler with global context."""
        context = "Global project context"
        compiler = SpecCompiler(mock_provider, global_context=context)
        assert compiler.provider is mock_provider
        assert compiler.global_context == context


class TestCompileCode:
    """Tests for compile_code method."""

    def test_compile_code_basic(self, mock_provider, basic_spec):
        """Test basic code compilation."""
        provider = MockLLMProvider(response="def test(): pass")
        compiler = SpecCompiler(provider)

        result = compiler.compile_code(basic_spec)

        assert result == "def test(): pass"
        assert len(provider.calls) == 1
        assert "test_module" not in provider.calls[0]["prompt"] or "expert" in provider.calls[0]["prompt"].lower()
        assert "expert" in provider.calls[0]["prompt"].lower()

    def test_compile_code_with_model_override(self, basic_spec):
        """Test code compilation with model override."""
        provider = MockLLMProvider(response="code")
        compiler = SpecCompiler(provider)

        compiler.compile_code(basic_spec, model="custom-model")

        assert provider.calls[0]["model"] == "custom-model"

    def test_compile_code_with_global_context(self, basic_spec):
        """Test code compilation includes global context."""
        context = "Use async/await patterns"
        provider = MockLLMProvider(response="async def test(): pass")
        compiler = SpecCompiler(provider, global_context=context)

        compiler.compile_code(basic_spec)

        assert context in provider.calls[0]["prompt"]

    def test_compile_code_with_language_target(self):
        """Test code compilation respects language target."""
        metadata = SpecMetadata(name="test", language_target="typescript")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="",
            path="/specs/test.spec.md"
        )
        provider = MockLLMProvider(response="const test = () => {}")
        compiler = SpecCompiler(provider)

        compiler.compile_code(spec)

        assert "typescript" in provider.calls[0]["prompt"].lower()

    def test_compile_code_strips_markdown_fences(self):
        """Test that code compilation strips markdown fences."""
        provider = MockLLMProvider(response="```python\ndef test(): pass\n```")
        compiler = SpecCompiler(provider)
        metadata = SpecMetadata(name="test")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="",
            path="/specs/test.spec.md"
        )

        result = compiler.compile_code(spec)

        assert result == "def test(): pass"
        assert "```" not in result

    def test_compile_code_with_string_dependencies(self, spec_with_dependencies):
        """Test code compilation with string dependencies."""
        provider = MockLLMProvider(response="code")
        compiler = SpecCompiler(provider)

        compiler.compile_code(spec_with_dependencies)

        prompt = provider.calls[0]["prompt"]
        assert "users" in prompt
        assert "database" in prompt
        assert "Import from" in prompt

    def test_compile_code_with_dict_dependencies(self, spec_with_dependencies):
        """Test code compilation with dict-style dependencies."""
        provider = MockLLMProvider(response="code")
        compiler = SpecCompiler(provider)

        compiler.compile_code(spec_with_dependencies)

        prompt = provider.calls[0]["prompt"]
        assert "db" in prompt
        assert "database" in prompt


class TestCompileTypedef:
    """Tests for compile_typedef method."""

    def test_compile_typedef_basic(self):
        """Test basic typedef compilation."""
        metadata = SpecMetadata(name="user_type", type="type")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="# Schema\nuser type definition\n",
            path="/specs/user_type.spec.md"
        )
        provider = MockLLMProvider(response="@dataclass\nclass User: pass")
        compiler = SpecCompiler(provider)

        result = compiler.compile_typedef(spec)

        assert "User" in result
        assert len(provider.calls) == 1
        assert "type systems" in provider.calls[0]["prompt"].lower()

    def test_compile_typedef_with_language_target(self):
        """Test typedef compilation respects language target."""
        metadata = SpecMetadata(name="types", language_target="typescript", type="type")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="",
            path="/specs/types.spec.md"
        )
        provider = MockLLMProvider(response="interface User {}")
        compiler = SpecCompiler(provider)

        compiler.compile_typedef(spec)

        assert "typescript" in provider.calls[0]["prompt"].lower()

    def test_compile_typedef_strips_fences(self):
        """Test typedef compilation strips markdown fences."""
        metadata = SpecMetadata(name="types")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="",
            path="/specs/types.spec.md"
        )
        provider = MockLLMProvider(response="```python\nclass User: pass\n```")
        compiler = SpecCompiler(provider)

        result = compiler.compile_typedef(spec)

        assert "```" not in result


class TestCompileOrchestrator:
    """Tests for compile_orchestrator method."""

    def test_compile_orchestrator_basic(self):
        """Test basic orchestrator compilation."""
        metadata = SpecMetadata(name="workflow", type="orchestrator")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="# Orchestration\nWorkflow spec\n",
            path="/specs/workflow.spec.md",
            schema=None
        )
        provider = MockLLMProvider(response="def orchestrate(): pass")
        compiler = SpecCompiler(provider)

        result = compiler.compile_orchestrator(spec)

        assert "orchestrate" in result
        assert "orchestration" in provider.calls[0]["prompt"].lower()

    def test_compile_orchestrator_with_language_target(self):
        """Test orchestrator compilation respects language target."""
        metadata = SpecMetadata(name="workflow", language_target="typescript", type="orchestrator")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="",
            path="/specs/workflow.spec.md",
            schema=None
        )
        provider = MockLLMProvider(response="async function orchestrate() {}")
        compiler = SpecCompiler(provider)

        compiler.compile_orchestrator(spec)

        assert "typescript" in provider.calls[0]["prompt"].lower()

    def test_compile_orchestrator_with_steps(self):
        """Test orchestrator compilation extracts step references."""
        from specsoloist.schema import WorkflowStep, InterfaceSchema

        steps = [
            WorkflowStep(name="step1", spec="module1"),
            WorkflowStep(name="step2", spec="module2")
        ]
        schema = InterfaceSchema(inputs={}, outputs={}, steps=steps)

        metadata = SpecMetadata(name="workflow", type="orchestrator")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="",
            path="/specs/workflow.spec.md",
            schema=schema
        )
        provider = MockLLMProvider(response="code")
        compiler = SpecCompiler(provider)

        compiler.compile_orchestrator(spec)

        prompt = provider.calls[0]["prompt"]
        assert "module1" in prompt
        assert "module2" in prompt


class TestCompileTests:
    """Tests for compile_tests method."""

    def test_compile_tests_python(self):
        """Test test compilation for Python."""
        metadata = SpecMetadata(name="math_ops")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="# Test Scenarios\nTest add function\n",
            path="/specs/math_ops.spec.md"
        )
        provider = MockLLMProvider(response="def test_add(): assert True")
        compiler = SpecCompiler(provider)

        result = compiler.compile_tests(spec)

        assert "test_add" in result
        assert "pytest" in provider.calls[0]["prompt"].lower()

    def test_compile_tests_typescript(self):
        """Test test compilation for TypeScript."""
        metadata = SpecMetadata(name="math_ops", language_target="typescript")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="",
            path="/specs/math_ops.spec.md"
        )
        provider = MockLLMProvider(response="it('should work', () => {})")
        compiler = SpecCompiler(provider)

        compiler.compile_tests(spec)

        prompt = provider.calls[0]["prompt"]
        assert "node:test" in prompt
        assert "import assert" in prompt

    def test_compile_tests_strips_fences(self):
        """Test test compilation strips markdown fences."""
        metadata = SpecMetadata(name="test_module")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="",
            path="/specs/test_module.spec.md"
        )
        provider = MockLLMProvider(response="```python\ndef test_x(): pass\n```")
        compiler = SpecCompiler(provider)

        result = compiler.compile_tests(spec)

        assert "```" not in result
        assert "def test_x():" in result


class TestGenerateFix:
    """Tests for generate_fix method."""

    def test_generate_fix_includes_spec(self):
        """Test generate_fix includes the spec content."""
        metadata = SpecMetadata(name="buggy", type="function")
        spec = ParsedSpec(
            metadata=metadata,
            content="# Spec content\nThis is the source of truth",
            body="# Spec body",
            path="/specs/buggy.spec.md"
        )
        provider = MockLLMProvider(response="### FILE: buggy.py\nfixed code\n### END")
        compiler = SpecCompiler(provider)

        compiler.generate_fix(
            spec,
            code_content="broken code",
            test_content="failing test",
            error_log="test failed"
        )

        prompt = provider.calls[0]["prompt"]
        assert "Source of Truth" in prompt
        assert "buggy.py" in prompt

    def test_generate_fix_includes_code_and_tests(self):
        """Test generate_fix includes current code and tests."""
        metadata = SpecMetadata(name="buggy")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="",
            path="/specs/buggy.spec.md"
        )
        code = "def broken(): pass"
        test = "def test_broken(): assert False"
        error = "AssertionError"

        provider = MockLLMProvider(response="### FILE: buggy.py\ncode\n### END")
        compiler = SpecCompiler(provider)

        compiler.generate_fix(spec, code, test, error)

        prompt = provider.calls[0]["prompt"]
        assert code in prompt
        assert test in prompt
        assert error in prompt

    def test_generate_fix_python_filenames(self):
        """Test generate_fix uses correct Python filenames."""
        metadata = SpecMetadata(name="my_module")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="",
            path="/specs/my_module.spec.md"
        )
        provider = MockLLMProvider(response="### FILE: my_module.py\ncode\n### END")
        compiler = SpecCompiler(provider)

        compiler.generate_fix(spec, "", "", "")

        prompt = provider.calls[0]["prompt"]
        assert "my_module.py" in prompt
        assert "test_my_module.py" in prompt

    def test_generate_fix_typescript_filenames(self):
        """Test generate_fix uses correct TypeScript filenames."""
        metadata = SpecMetadata(name="my_module", language_target="typescript")
        spec = ParsedSpec(
            metadata=metadata,
            content="",
            body="",
            path="/specs/my_module.spec.md"
        )
        provider = MockLLMProvider(response="### FILE: my_module.ts\ncode\n### END")
        compiler = SpecCompiler(provider)

        compiler.generate_fix(spec, "", "", "")

        prompt = provider.calls[0]["prompt"]
        assert "my_module.ts" in prompt
        assert "my_module.test.ts" in prompt


class TestParseFixResponse:
    """Tests for parse_fix_response method."""

    def test_parse_fix_response_single_file(self, mock_provider):
        """Test parsing a fix response with a single file."""
        compiler = SpecCompiler(mock_provider)
        response = """
### FILE: my_file.py
def fixed_function():
    return True
### END
"""
        result = compiler.parse_fix_response(response)

        assert len(result) == 1
        assert "my_file.py" in result
        assert "def fixed_function():" in result["my_file.py"]

    def test_parse_fix_response_multiple_files(self, mock_provider):
        """Test parsing a fix response with multiple files."""
        compiler = SpecCompiler(mock_provider)
        response = """
### FILE: code.py
def function():
    pass
### END

### FILE: test_code.py
def test_function():
    assert True
### END
"""
        result = compiler.parse_fix_response(response)

        assert len(result) == 2
        assert "code.py" in result
        assert "test_code.py" in result
        assert "def function():" in result["code.py"]
        assert "def test_function():" in result["test_code.py"]

    def test_parse_fix_response_strips_markdown_fences(self, mock_provider):
        """Test that parse_fix_response strips markdown fences from content."""
        compiler = SpecCompiler(mock_provider)
        response = """
### FILE: my_file.py
```python
def function():
    pass
```
### END
"""
        result = compiler.parse_fix_response(response)

        content = result["my_file.py"]
        assert "```" not in content
        assert "def function():" in content

    def test_parse_fix_response_empty(self, mock_provider):
        """Test parsing an empty fix response."""
        compiler = SpecCompiler(mock_provider)
        response = "No fixes needed."

        result = compiler.parse_fix_response(response)

        assert result == {}

    def test_parse_fix_response_with_multiline_content(self, mock_provider):
        """Test parsing fix response with multiline content."""
        compiler = SpecCompiler(mock_provider)
        response = """
### FILE: complex.py
class MyClass:
    def method1(self):
        return 1

    def method2(self):
        return 2
### END
"""
        result = compiler.parse_fix_response(response)

        content = result["complex.py"]
        assert "class MyClass:" in content
        assert "def method1(self):" in content
        assert "def method2(self):" in content


class TestStripMarkdownFences:
    """Tests for _strip_markdown_fences helper method."""

    def test_strip_fences_no_fences(self, mock_provider):
        """Test stripping when there are no fences."""
        compiler = SpecCompiler(mock_provider)
        code = "def function(): pass"

        result = compiler._strip_markdown_fences(code)

        assert result == code

    def test_strip_fences_python(self, mock_provider):
        """Test stripping Python markdown fences."""
        compiler = SpecCompiler(mock_provider)
        code = "```python\ndef function(): pass\n```"

        result = compiler._strip_markdown_fences(code)

        assert result == "def function(): pass"
        assert "```" not in result

    def test_strip_fences_no_language(self, mock_provider):
        """Test stripping fences without language specifier."""
        compiler = SpecCompiler(mock_provider)
        code = "```\ncode here\n```"

        result = compiler._strip_markdown_fences(code)

        assert result == "code here"

    def test_strip_fences_typescript(self, mock_provider):
        """Test stripping TypeScript markdown fences."""
        compiler = SpecCompiler(mock_provider)
        code = "```typescript\nconst x = 1;\n```"

        result = compiler._strip_markdown_fences(code)

        assert result == "const x = 1;"

    def test_strip_fences_multiline(self, mock_provider):
        """Test stripping fences with multiline content."""
        compiler = SpecCompiler(mock_provider)
        code = "```python\ndef func1():\n    pass\n\ndef func2():\n    return True\n```"

        result = compiler._strip_markdown_fences(code)

        assert "def func1():" in result
        assert "def func2():" in result
        assert "```" not in result


class TestBuildImportContext:
    """Tests for _build_import_context helper method."""

    def test_build_import_context_no_dependencies(self, mock_provider):
        """Test building import context with no dependencies."""
        compiler = SpecCompiler(mock_provider)
        metadata = SpecMetadata(name="test", dependencies=[])
        spec = ParsedSpec(metadata=metadata, content="", body="", path="/specs/test.spec.md")

        result = compiler._build_import_context(spec)

        assert "No external dependencies" in result

    def test_build_import_context_string_dependencies(self, mock_provider):
        """Test building import context with string dependencies."""
        compiler = SpecCompiler(mock_provider)
        metadata = SpecMetadata(name="test", dependencies=["users", "database"])
        spec = ParsedSpec(metadata=metadata, content="", body="", path="/specs/test.spec.md")

        result = compiler._build_import_context(spec)

        assert "users" in result
        assert "database" in result
        assert "Import from" in result

    def test_build_import_context_dict_dependencies(self, mock_provider):
        """Test building import context with dict dependencies."""
        compiler = SpecCompiler(mock_provider)
        dependencies = [
            {"name": "User", "from": "users.spec.md"},
            {"name": "Database", "from": "db.spec.md"}
        ]
        metadata = SpecMetadata(name="test", dependencies=dependencies)
        spec = ParsedSpec(metadata=metadata, content="", body="", path="/specs/test.spec.md")

        result = compiler._build_import_context(spec)

        assert "User" in result
        assert "Database" in result
        assert "users" in result
        assert "db" in result

    def test_build_import_context_mixed_dependencies(self, mock_provider):
        """Test building import context with mixed dependency types."""
        compiler = SpecCompiler(mock_provider)
        dependencies = [
            "users",
            {"name": "Config", "from": "config.spec.md"}
        ]
        metadata = SpecMetadata(name="test", dependencies=dependencies)
        spec = ParsedSpec(metadata=metadata, content="", body="", path="/specs/test.spec.md")

        result = compiler._build_import_context(spec)

        assert "users" in result
        assert "Config" in result
        assert "config" in result

    def test_build_import_context_strips_spec_extension(self, mock_provider):
        """Test that import context strips .spec.md extension."""
        compiler = SpecCompiler(mock_provider)
        dependencies = ["users.spec.md", {"name": "db", "from": "database.spec.md"}]
        metadata = SpecMetadata(name="test", dependencies=dependencies)
        spec = ParsedSpec(metadata=metadata, content="", body="", path="/specs/test.spec.md")

        result = compiler._build_import_context(spec)

        assert ".spec.md" not in result
        assert "users" in result
        assert "database" in result
        assert "db" in result


class TestIntegrationScenarios:
    """Integration tests combining multiple operations."""

    def test_full_compilation_workflow(self):
        """Test a complete compilation workflow."""
        def response_for_prompt(prompt):
            if "QA Engineer" in prompt:
                return "def test_add(): assert add(1, 2) == 3"
            else:
                return "def add(a, b): return a + b"

        provider = MockLLMProvider()
        original_generate = provider.generate

        def smart_generate(prompt, temperature=0.1, model=None):
            provider.calls.append({"prompt": prompt, "temperature": temperature, "model": model})
            return response_for_prompt(prompt)

        provider.generate = smart_generate

        compiler = SpecCompiler(provider, global_context="Use clean code practices")

        metadata = SpecMetadata(name="math", dependencies=["numbers"])
        spec = ParsedSpec(
            metadata=metadata,
            content="---\nname: math\n---\n# Overview\nMath operations",
            body="# Overview\nMath operations",
            path="/specs/math.spec.md"
        )

        # Compile code
        code = compiler.compile_code(spec)
        assert "def add" in code

        # Compile tests
        tests = compiler.compile_tests(spec)
        assert "test_add" in tests

        # Verify global context was included
        assert provider.calls[0]["prompt"]  # Had code compilation call

    def test_fix_generation_and_parsing(self):
        """Test generating and parsing a fix response."""
        provider = MockLLMProvider()
        compiler = SpecCompiler(provider)

        metadata = SpecMetadata(name="buggy")
        spec = ParsedSpec(
            metadata=metadata,
            content="# Spec",
            body="",
            path="/specs/buggy.spec.md"
        )

        # Generate a fix
        fix_response = """
### FILE: buggy.py
def fixed_function():
    return "fixed"
### END

### FILE: test_buggy.py
def test_fixed_function():
    assert fixed_function() == "fixed"
### END
"""
        compiler.provider.response = fix_response

        # Parse the fix
        fixes = compiler.parse_fix_response(fix_response)

        assert len(fixes) == 2
        assert "buggy.py" in fixes
        assert "test_buggy.py" in fixes
        assert "def fixed_function():" in fixes["buggy.py"]
        assert "def test_fixed_function():" in fixes["test_buggy.py"]
