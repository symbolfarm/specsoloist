"""
Specular: Spec-as-Source AI Coding Framework

Specular treats rigorous SRS-style Markdown specifications as the
single source of truth, using LLMs to compile them into code.
"""

from .core import SpecularCore, BuildResult
from .config import SpecularConfig
from .parser import SpecParser, ParsedSpec, SpecMetadata
from .compiler import SpecCompiler
from .runner import TestRunner, TestResult
from .resolver import (
    DependencyResolver,
    DependencyGraph,
    CircularDependencyError,
    MissingDependencyError,
)
from .providers import LLMProvider, GeminiProvider, AnthropicProvider

__all__ = [
    # Core
    "SpecularCore",
    "SpecularConfig",
    "BuildResult",
    # Parser
    "SpecParser",
    "ParsedSpec",
    "SpecMetadata",
    # Compiler
    "SpecCompiler",
    # Runner
    "TestRunner",
    "TestResult",
    # Resolver
    "DependencyResolver",
    "DependencyGraph",
    "CircularDependencyError",
    "MissingDependencyError",
    # Providers
    "LLMProvider",
    "GeminiProvider",
    "AnthropicProvider",
]
