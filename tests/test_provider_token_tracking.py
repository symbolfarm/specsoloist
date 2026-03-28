"""Tests for LLMResponse and provider token tracking."""

import pytest

from specsoloist.providers.base import LLMResponse
from specsoloist.events import EventBus, EventType


class TestLLMResponse:
    """Tests for the LLMResponse dataclass."""

    def test_str_returns_text(self):
        r = LLMResponse(text="Hello, world!")
        assert str(r) == "Hello, world!"

    def test_defaults(self):
        r = LLMResponse(text="code")
        assert r.input_tokens is None
        assert r.output_tokens is None
        assert r.model is None

    def test_with_token_counts(self):
        r = LLMResponse(
            text="code",
            input_tokens=100,
            output_tokens=200,
            model="claude-haiku",
        )
        assert r.input_tokens == 100
        assert r.output_tokens == 200
        assert r.model == "claude-haiku"

    def test_backward_compat_string_concatenation(self):
        """LLMResponse should work wherever a string was expected."""
        r = LLMResponse(text="def foo(): pass")
        # String operations that compiler code might use
        assert "def foo" in str(r)
        assert str(r).startswith("def")


class TestCompilerLLMEvents:
    """Test that the compiler emits llm.request / llm.response events."""

    def test_llm_events_emitted(self):
        from specsoloist.compiler import SpecCompiler
        from specsoloist.parser import ParsedSpec, SpecMetadata

        bus = EventBus()
        received = []
        bus.subscribe(lambda e: received.append(e))

        # Create a mock provider
        class MockProvider:
            def generate(self, prompt, temperature=0.1, model=None):
                return LLMResponse(
                    text="def greet(): pass",
                    input_tokens=50,
                    output_tokens=100,
                    model="mock-model",
                )

        compiler = SpecCompiler(
            provider=MockProvider(),
            event_bus=bus,
        )

        spec = ParsedSpec(
            content="test",
            metadata=SpecMetadata(
                name="test",
                type="function",
                description="test",
            ),
            body="# Overview\nTest function\n\n# Functions\n\n## greet() -> str\n\nReturns a greeting.",
            path="test.spec.md",
        )

        compiler.compile_code(spec)
        bus.close()

        types = [e.event_type for e in received]
        assert EventType.LLM_REQUEST in types
        assert EventType.LLM_RESPONSE in types

    def test_llm_response_includes_tokens(self):
        from specsoloist.compiler import SpecCompiler
        from specsoloist.parser import ParsedSpec, SpecMetadata

        bus = EventBus()
        received = []
        bus.subscribe(lambda e: received.append(e))

        class MockProvider:
            def generate(self, prompt, temperature=0.1, model=None):
                return LLMResponse(
                    text="code",
                    input_tokens=50,
                    output_tokens=100,
                    model="mock",
                )

        compiler = SpecCompiler(provider=MockProvider(), event_bus=bus)
        spec = ParsedSpec(
            content="test",
            metadata=SpecMetadata(name="test", type="function", description="test"),
            body="# Overview\nTest\n\n# Functions\n\n## f() -> str\n\nDoes something.",
            path="test.spec.md",
        )

        compiler.compile_code(spec)
        bus.close()

        response_events = [e for e in received if e.event_type == EventType.LLM_RESPONSE]
        assert len(response_events) == 1
        assert response_events[0].data["input_tokens"] == 50
        assert response_events[0].data["output_tokens"] == 100
        assert response_events[0].data["duration_seconds"] >= 0

    def test_llm_request_includes_prompt_length(self):
        from specsoloist.compiler import SpecCompiler
        from specsoloist.parser import ParsedSpec, SpecMetadata

        bus = EventBus()
        received = []
        bus.subscribe(lambda e: received.append(e))

        class MockProvider:
            def generate(self, prompt, temperature=0.1, model=None):
                return LLMResponse(text="code")

        compiler = SpecCompiler(provider=MockProvider(), event_bus=bus)
        spec = ParsedSpec(
            content="test",
            metadata=SpecMetadata(name="test", type="function", description="test"),
            body="# Overview\nTest\n\n# Functions\n\n## f() -> str\n\nDoes something.",
            path="test.spec.md",
        )

        compiler.compile_code(spec)
        bus.close()

        request_events = [e for e in received if e.event_type == EventType.LLM_REQUEST]
        assert len(request_events) == 1
        assert request_events[0].data["prompt_length"] > 0

    def test_no_events_without_bus(self):
        """Compiler without event bus should work normally."""
        from specsoloist.compiler import SpecCompiler
        from specsoloist.parser import ParsedSpec, SpecMetadata

        class MockProvider:
            def generate(self, prompt, temperature=0.1, model=None):
                return LLMResponse(text="def f(): pass")

        compiler = SpecCompiler(provider=MockProvider())
        spec = ParsedSpec(
            content="test",
            metadata=SpecMetadata(name="test", type="function", description="test"),
            body="# Overview\nTest\n\n# Functions\n\n## f() -> str\n\nDoes something.",
            path="test.spec.md",
        )

        result = compiler.compile_code(spec)
        assert "def f" in result
