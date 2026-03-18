"""Tests for the compiler module."""

import pytest
from unittest.mock import MagicMock

from specsoloist.compiler import SpecCompiler, _strip_fences


class TestStripFences:
    def test_no_fences(self):
        code = "print('hello')"
        assert _strip_fences(code) == "print('hello')"

    def test_python_fence(self):
        code = "```python\nprint('hello')\n```"
        result = _strip_fences(code)
        assert "```" not in result
        assert "print('hello')" in result

    def test_plain_fence(self):
        code = "```\nsome code\n```"
        result = _strip_fences(code)
        assert "```" not in result
        assert "some code" in result

    def test_typescript_fence(self):
        code = "```typescript\nconsole.log('hi');\n```"
        result = _strip_fences(code)
        assert "```" not in result
        assert "console.log" in result


class MockProvider:
    def __init__(self, response="generated code"):
        self.response = response
        self.calls = []

    def generate(self, prompt, model=None):
        self.calls.append({"prompt": prompt, "model": model})
        return self.response


class MockSpec:
    def __init__(self, name="test_spec", content="# Spec content\nDo something.", deps=None):
        self.metadata = MagicMock()
        self.metadata.name = name
        self.metadata.dependencies = deps or []
        self.content = content
        self.schema = None


class TestSpecCompiler:
    def test_init(self):
        provider = MockProvider()
        compiler = SpecCompiler(provider=provider, global_context="project context")
        assert compiler.provider is provider
        assert compiler.global_context == "project context"

    def test_compile_code_calls_provider(self):
        provider = MockProvider("def foo(): pass")
        compiler = SpecCompiler(provider=provider)
        spec = MockSpec()
        result = compiler.compile_code(spec)
        assert provider.calls
        assert result == "def foo(): pass"

    def test_compile_code_strips_fences(self):
        provider = MockProvider("```python\ndef foo(): pass\n```")
        compiler = SpecCompiler(provider=provider)
        spec = MockSpec()
        result = compiler.compile_code(spec)
        assert "```" not in result
        assert "def foo(): pass" in result

    def test_compile_code_passes_model(self):
        provider = MockProvider("code")
        compiler = SpecCompiler(provider=provider)
        spec = MockSpec()
        compiler.compile_code(spec, model="claude-haiku")
        assert provider.calls[0]["model"] == "claude-haiku"

    def test_compile_code_includes_global_context(self):
        provider = MockProvider("code")
        compiler = SpecCompiler(provider=provider, global_context="My project")
        spec = MockSpec()
        compiler.compile_code(spec)
        prompt = provider.calls[0]["prompt"]
        assert "My project" in prompt

    def test_compile_typedef(self):
        provider = MockProvider("class Foo: pass")
        compiler = SpecCompiler(provider=provider)
        spec = MockSpec()
        result = compiler.compile_typedef(spec)
        assert result == "class Foo: pass"

    def test_compile_tests(self):
        provider = MockProvider("def test_foo(): pass")
        compiler = SpecCompiler(provider=provider)
        spec = MockSpec()
        result = compiler.compile_tests(spec)
        assert "def test_foo" in result

    def test_compile_tests_includes_spec_content(self):
        provider = MockProvider("test code")
        compiler = SpecCompiler(provider=provider)
        spec = MockSpec(content="# My spec\nDo things")
        compiler.compile_tests(spec)
        prompt = provider.calls[0]["prompt"]
        assert "My spec" in prompt

    def test_compile_orchestrator(self):
        provider = MockProvider("workflow code")
        compiler = SpecCompiler(provider=provider)
        spec = MockSpec()
        result = compiler.compile_orchestrator(spec)
        assert result == "workflow code"

    def test_generate_fix_returns_response(self):
        provider = MockProvider("### FILE: foo.py\nfixed code\n### END")
        compiler = SpecCompiler(provider=provider)
        spec = MockSpec()
        result = compiler.generate_fix(
            spec=spec,
            code_content="broken code",
            test_content="test code",
            error_log="AssertionError: ...",
        )
        assert "### FILE:" in result

    def test_generate_fix_includes_error_log(self):
        provider = MockProvider("response")
        compiler = SpecCompiler(provider=provider)
        spec = MockSpec()
        compiler.generate_fix(
            spec=spec,
            code_content="code",
            test_content="tests",
            error_log="FAIL: test_foo",
        )
        prompt = provider.calls[0]["prompt"]
        assert "FAIL: test_foo" in prompt

    def test_parse_fix_response_single_file(self):
        compiler = SpecCompiler(provider=MockProvider())
        response = "### FILE: src/foo.py\ndef fixed(): pass\n### END"
        result = compiler.parse_fix_response(response)
        assert "src/foo.py" in result
        assert "def fixed" in result["src/foo.py"]

    def test_parse_fix_response_multiple_files(self):
        compiler = SpecCompiler(provider=MockProvider())
        response = (
            "### FILE: src/foo.py\ncode1\n### END\n"
            "### FILE: tests/test_foo.py\ntest1\n### END"
        )
        result = compiler.parse_fix_response(response)
        assert len(result) == 2
        assert "src/foo.py" in result
        assert "tests/test_foo.py" in result

    def test_parse_fix_response_empty(self):
        compiler = SpecCompiler(provider=MockProvider())
        result = compiler.parse_fix_response("no markers here")
        assert result == {}

    def test_parse_fix_response_strips_fences(self):
        compiler = SpecCompiler(provider=MockProvider())
        response = "### FILE: foo.py\n```python\ndef foo(): pass\n```\n### END"
        result = compiler.parse_fix_response(response)
        assert "```" not in result["foo.py"]
        assert "def foo" in result["foo.py"]

    def test_compile_code_with_arrangement(self):
        provider = MockProvider("code")
        compiler = SpecCompiler(provider=provider)
        spec = MockSpec()

        arrangement = MagicMock()
        arrangement.target_language = "typescript"
        arrangement.environment = MagicMock()
        arrangement.environment.dependencies = {}
        arrangement.build_commands = MagicMock()
        arrangement.build_commands.test = "npm test"
        arrangement.constraints = []
        arrangement.env_vars = {}

        compiler.compile_code(spec, arrangement=arrangement)
        prompt = provider.calls[0]["prompt"]
        # Arrangement context should be included
        assert "typescript" in prompt.lower() or "typescript" in prompt

    def test_compile_code_with_deps(self):
        provider = MockProvider("code")
        compiler = SpecCompiler(provider=provider)
        spec = MockSpec(deps=["parser", "schema"])
        compiler.compile_code(spec)
        prompt = provider.calls[0]["prompt"]
        assert "parser" in prompt or "schema" in prompt
