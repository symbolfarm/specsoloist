"""
SpecularCore: The main orchestrator for spec-driven development.

This module provides the high-level API for compiling specs to code.
It delegates to specialized modules for parsing, compilation, and testing.
"""

import os
from typing import Any, Dict, List, Optional

from .config import SpecularConfig
from .parser import SpecParser
from .compiler import SpecCompiler
from .runner import TestRunner
from .providers import LLMProvider


class SpecularCore:
    """
    Main orchestrator for the Specular framework.

    Coordinates spec parsing, code compilation, test generation,
    and the self-healing fix loop.
    """

    def __init__(
        self,
        root_dir: str = ".",
        api_key: Optional[str] = None,
        config: Optional[SpecularConfig] = None
    ):
        """
        Initialize SpecularCore.

        Args:
            root_dir: Project root directory.
            api_key: LLM API key (deprecated, use config instead).
            config: Full configuration object. If not provided,
                   loads from environment variables.
        """
        # Build configuration
        if config:
            self.config = config
        else:
            self.config = SpecularConfig.from_env(root_dir)
            if api_key:
                self.config.api_key = api_key

        # Legacy attributes for backwards compatibility
        self.root_dir = os.path.abspath(root_dir)
        self.src_dir = self.config.src_path
        self.build_dir = self.config.build_path
        self.api_key = self.config.api_key

        # Ensure directories exist
        self.config.ensure_directories()

        # Initialize components
        self.parser = SpecParser(self.config.src_path)
        self.runner = TestRunner(self.config.build_path)
        self._compiler: Optional[SpecCompiler] = None
        self._provider: Optional[LLMProvider] = None

    def _get_provider(self) -> LLMProvider:
        """Lazily create the LLM provider."""
        if self._provider is None:
            self._provider = self.config.create_provider()
        return self._provider

    def _get_compiler(self) -> SpecCompiler:
        """Lazily create the compiler with global context."""
        if self._compiler is None:
            global_context = self.parser.load_global_context()
            self._compiler = SpecCompiler(
                provider=self._get_provider(),
                global_context=global_context
            )
        return self._compiler

    # =========================================================================
    # Public API - Spec Management
    # =========================================================================

    def list_specs(self) -> List[str]:
        """List all available specification files."""
        return self.parser.list_specs()

    def read_spec(self, name: str) -> str:
        """Read the content of a specification file."""
        return self.parser.read_spec(name)

    def create_spec(
        self,
        name: str,
        description: str,
        type: str = "function"
    ) -> str:
        """
        Create a new specification file from the template.

        Args:
            name: Component name (e.g., "auth" creates "auth.spec.md").
            description: Brief description of the component.
            type: Component type ("function", "class", "module", "typedef").

        Returns:
            Success message with path to created file.
        """
        path = self.parser.create_spec(name, description, spec_type=type)
        return f"Created spec: {path}"

    def validate_spec(self, name: str) -> Dict[str, Any]:
        """
        Validate a spec for basic structure and SRS compliance.

        Returns:
            Dict with 'valid' (bool) and 'errors' (list) keys.
        """
        return self.parser.validate_spec(name)

    # =========================================================================
    # Public API - Compilation
    # =========================================================================

    def compile_spec(self, name: str, model: Optional[str] = None) -> str:
        """
        Compile a spec to implementation code.

        Args:
            name: Spec filename (with or without .spec.md extension).
            model: Override the default LLM model (optional).

        Returns:
            Success message with path to generated code.
        """
        # Validate first
        validation = self.validate_spec(name)
        if not validation["valid"]:
            raise ValueError(
                f"Cannot compile invalid spec: {validation['errors']}"
            )

        # Parse and compile
        spec = self.parser.parse_spec(name)
        compiler = self._get_compiler()
        code = compiler.compile_code(spec, model=model)

        # Write output
        module_name = self.parser.get_module_name(name)
        output_path = self.runner.write_code(module_name, code)

        return f"Compiled to {output_path}"

    def compile_tests(self, name: str, model: Optional[str] = None) -> str:
        """
        Generate a test suite for a spec.

        Args:
            name: Spec filename (with or without .spec.md extension).
            model: Override the default LLM model (optional).

        Returns:
            Success message with path to generated tests.
        """
        spec = self.parser.parse_spec(name)
        compiler = self._get_compiler()
        code = compiler.compile_tests(spec, model=model)

        module_name = self.parser.get_module_name(name)
        output_path = self.runner.write_tests(module_name, code)

        return f"Generated tests at {output_path}"

    # =========================================================================
    # Public API - Testing
    # =========================================================================

    def run_tests(self, name: str) -> Dict[str, Any]:
        """
        Run the tests for a specific component.

        Returns:
            Dict with 'success' (bool) and 'output' (str) keys.
        """
        module_name = self.parser.get_module_name(name)
        result = self.runner.run_tests(module_name)
        return {
            "success": result.success,
            "output": result.output
        }

    # =========================================================================
    # Public API - Self-Healing
    # =========================================================================

    def attempt_fix(self, name: str, model: Optional[str] = None) -> str:
        """
        Attempt to fix a failing component.

        Analyzes test output and rewrites either the code or tests
        to fix the failure.

        Args:
            name: Spec filename.
            model: Override the default LLM model (optional).

        Returns:
            Status message describing what was fixed.
        """
        module_name = self.parser.get_module_name(name)

        # 1. Run tests to get current error
        result = self.runner.run_tests(module_name)
        if result.success:
            return "Tests already passed. No fix needed."

        # 2. Gather context
        spec = self.parser.parse_spec(name)
        code_content = self.runner.read_code(module_name) or ""
        test_content = self.runner.read_tests(module_name) or ""

        # 3. Generate fix
        compiler = self._get_compiler()
        response = compiler.generate_fix(
            spec=spec,
            code_content=code_content,
            test_content=test_content,
            error_log=result.output,
            model=model
        )

        # 4. Parse and apply fixes
        fixes = compiler.parse_fix_response(response)

        if not fixes:
            return (
                f"LLM analyzed the error but provided no formatted fix.\n"
                f"Response:\n{response}"
            )

        changes_made = []
        for filename, content in fixes.items():
            path = self.runner.write_file(filename, content)
            changes_made.append(os.path.basename(path))

        return f"Applied fixes to: {', '.join(changes_made)}. Run tests again to verify."
