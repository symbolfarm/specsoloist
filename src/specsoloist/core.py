"""
SpecularCore: The main orchestrator for spec-driven development.

This module provides the high-level API for compiling specs to code.
It delegates to specialized modules for parsing, compilation, and testing.
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .config import SpecSoloistConfig
from .parser import SpecParser
from .compiler import SpecCompiler
from .runner import TestRunner
from .resolver import DependencyResolver, DependencyGraph
from .manifest import BuildManifest, IncrementalBuilder, compute_content_hash
from .providers import LLMProvider


@dataclass
class BuildResult:
    """Result of a multi-spec build operation."""
    success: bool
    specs_compiled: List[str]
    specs_skipped: List[str]  # Skipped due to no changes (incremental)
    specs_failed: List[str]
    build_order: List[str]
    errors: Dict[str, str]  # spec name -> error message


class SpecSoloistCore:
    """
    Main orchestrator for the SpecSoloist framework.

    Coordinates spec parsing, code compilation, test generation,
    and the self-healing fix loop.
    """

    def __init__(
        self,
        root_dir: str = ".",
        api_key: Optional[str] = None,
        config: Optional[SpecSoloistConfig] = None
    ):
        """
        Initialize SpecSoloistCore.

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
            self.config = SpecSoloistConfig.from_env(root_dir)
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
        self.runner = TestRunner(self.config.build_path, config=self.config)
        self.resolver = DependencyResolver(self.parser)
        self._compiler: Optional[SpecCompiler] = None
        self._provider: Optional[LLMProvider] = None
        self._manifest: Optional[BuildManifest] = None

    def _get_manifest(self) -> BuildManifest:
        """Lazily load the build manifest."""
        if self._manifest is None:
            self._manifest = BuildManifest.load(self.config.build_path)
        return self._manifest

    def _save_manifest(self):
        """Save the build manifest to disk."""
        if self._manifest is not None:
            self._manifest.save(self.config.build_path)

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

    def compile_spec(
        self,
        name: str,
        model: Optional[str] = None,
        skip_tests: bool = False
    ) -> str:
        """
        Compile a spec to implementation code.

        Args:
            name: Spec filename (with or without .spec.md extension).
            model: Override the default LLM model (optional).
            skip_tests: If True, don't generate tests (default for typedef specs).

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

        # Use appropriate compilation method based on spec type
        if spec.metadata.type == "typedef":
            code = compiler.compile_typedef(spec, model=model)
        else:
            code = compiler.compile_code(spec, model=model)

        # Write output
        module_name = self.parser.get_module_name(name)
        output_path = self.runner.write_code(
            module_name, code, language=spec.metadata.language_target
        )

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

        # Skip test generation for typedef specs
        if spec.metadata.type == "typedef":
            return f"Skipped tests for typedef spec: {name}"

        compiler = self._get_compiler()
        code = compiler.compile_tests(spec, model=model)

        module_name = self.parser.get_module_name(name)
        output_path = self.runner.write_tests(
            module_name, code, language=spec.metadata.language_target
        )

        return f"Generated tests at {output_path}"

    def compile_project(
        self,
        specs: List[str] = None,
        model: Optional[str] = None,
        generate_tests: bool = True,
        incremental: bool = False,
        parallel: bool = False,
        max_workers: int = 4
    ) -> BuildResult:
        """
        Compile multiple specs in dependency order.

        This is the main entry point for building a project with
        interdependent specs.

        Args:
            specs: List of spec names to compile. If None, compiles all specs.
            model: Override the default LLM model (optional).
            generate_tests: Whether to generate tests for non-typedef specs.
            incremental: If True, only recompile specs that have changed.
            parallel: If True, compile independent specs concurrently.
            max_workers: Maximum number of parallel compilation workers.

        Returns:
            BuildResult with compilation status and details.
        """
        if parallel:
            return self._compile_project_parallel(
                specs, model, generate_tests, incremental, max_workers
            )
        else:
            return self._compile_project_sequential(
                specs, model, generate_tests, incremental
            )

    def _compile_project_sequential(
        self,
        specs: List[str],
        model: Optional[str],
        generate_tests: bool,
        incremental: bool
    ) -> BuildResult:
        """Sequential compilation - original implementation."""
        # Resolve build order
        build_order = self.resolver.resolve_build_order(specs)

        # For incremental builds, determine what needs rebuilding
        specs_to_build = set(build_order)
        if incremental:
            specs_to_build = set(self._get_incremental_build_list(build_order))

        compiled = []
        skipped = []
        failed = []
        errors = {}

        for spec_name in build_order:
            if spec_name not in specs_to_build:
                skipped.append(spec_name)
                continue

            result = self._compile_single_spec(spec_name, model, generate_tests)
            if result["success"]:
                compiled.append(spec_name)
            else:
                failed.append(spec_name)
                errors[spec_name] = result["error"]

        # Save manifest after build
        self._save_manifest()

        return BuildResult(
            success=len(failed) == 0,
            specs_compiled=compiled,
            specs_skipped=skipped,
            specs_failed=failed,
            build_order=build_order,
            errors=errors
        )

    def _compile_project_parallel(
        self,
        specs: List[str],
        model: Optional[str],
        generate_tests: bool,
        incremental: bool,
        max_workers: int
    ) -> BuildResult:
        """Parallel compilation - compiles independent specs concurrently."""
        # Get build order grouped by levels
        levels = self.resolver.get_parallel_build_order(specs)
        build_order = [spec for level in levels for spec in level]

        # For incremental builds, determine what needs rebuilding
        specs_to_build = set(build_order)
        if incremental:
            specs_to_build = set(self._get_incremental_build_list(build_order))

        compiled = []
        skipped = []
        failed = []
        errors = {}

        # Process each level - specs within a level can be compiled in parallel
        for level in levels:
            level_to_build = [s for s in level if s in specs_to_build]
            level_skipped = [s for s in level if s not in specs_to_build]
            skipped.extend(level_skipped)

            if not level_to_build:
                continue

            # Compile this level in parallel
            with ThreadPoolExecutor(max_workers=min(max_workers, len(level_to_build))) as executor:
                futures = {
                    executor.submit(self._compile_single_spec, spec_name, model, generate_tests): spec_name
                    for spec_name in level_to_build
                }

                for future in as_completed(futures):
                    spec_name = futures[future]
                    result = future.result()
                    if result["success"]:
                        compiled.append(spec_name)
                    else:
                        failed.append(spec_name)
                        errors[spec_name] = result["error"]

        # Save manifest after build
        self._save_manifest()

        return BuildResult(
            success=len(failed) == 0,
            specs_compiled=compiled,
            specs_skipped=skipped,
            specs_failed=failed,
            build_order=build_order,
            errors=errors
        )

    def _compile_single_spec(
        self,
        spec_name: str,
        model: Optional[str],
        generate_tests: bool
    ) -> Dict[str, Any]:
        """
        Compile a single spec and return result.

        Returns dict with 'success' (bool) and 'error' (str if failed).
        """
        try:
            # Parse spec for metadata
            spec = self.parser.parse_spec(spec_name)
            lang = spec.metadata.language_target
            spec_hash = compute_content_hash(spec.content)
            deps = [d.get("from", "").replace(".spec.md", "")
                    for d in spec.metadata.dependencies
                    if isinstance(d, dict)]

            # Compile the spec
            self.compile_spec(spec_name, model=model)

            # Determine output files from config
            code_path = os.path.basename(self.runner.get_code_path(spec_name, language=lang))
            output_files = [code_path]
            
            # Generate tests if requested and not a typedef
            if generate_tests and spec.metadata.type != "typedef":
                self.compile_tests(spec_name, model=model)
                test_path = os.path.basename(self.runner.get_test_path(spec_name, language=lang))
                output_files.append(test_path)

            # Update manifest
            manifest = self._get_manifest()
            manifest.update_spec(spec_name, spec_hash, deps, output_files)

            return {"success": True, "error": ""}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_incremental_build_list(self, build_order: List[str]) -> List[str]:
        """Determine which specs need rebuilding for incremental build."""
        manifest = self._get_manifest()
        builder = IncrementalBuilder(manifest, self.config.src_path)

        # Compute current hashes and deps
        spec_hashes = {}
        spec_deps = {}

        for spec_name in build_order:
            spec = self.parser.parse_spec(spec_name)
            spec_hashes[spec_name] = compute_content_hash(spec.content)
            spec_deps[spec_name] = [
                d.get("from", "").replace(".spec.md", "")
                for d in spec.metadata.dependencies
                if isinstance(d, dict)
            ]

        return builder.get_rebuild_plan(build_order, spec_hashes, spec_deps)

    def get_build_order(self, specs: List[str] = None) -> List[str]:
        """
        Get the build order for specs without actually compiling.

        Useful for previewing what would be built and in what order.

        Args:
            specs: List of spec names. If None, includes all specs.

        Returns:
            List of spec names in build order.
        """
        return self.resolver.resolve_build_order(specs)

    def get_dependency_graph(self, specs: List[str] = None) -> DependencyGraph:
        """
        Get the dependency graph for specs.

        Args:
            specs: List of spec names. If None, includes all specs.

        Returns:
            DependencyGraph showing relationships between specs.
        """
        return self.resolver.build_graph(specs)

    # =========================================================================
    # Public API - Testing
    # =========================================================================

    def run_tests(self, name: str) -> Dict[str, Any]:
        """
        Run the tests for a specific component.

        Returns:
            Dict with 'success' (bool) and 'output' (str) keys.
        """
        spec = self.parser.parse_spec(name)
        module_name = self.parser.get_module_name(name)
        result = self.runner.run_tests(
            module_name, language=spec.metadata.language_target
        )
        return {
            "success": result.success,
            "output": result.output
        }

    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run tests for all compiled specs.

        Returns:
            Dict with overall 'success' and per-spec results.
        """
        specs = self.parser.list_specs()
        results = {}
        all_passed = True

        for spec_file in specs:
            spec_name = spec_file.replace(".spec.md", "")
            spec = self.parser.parse_spec(spec_name)
            lang = spec.metadata.language_target

            # Skip typedef specs (no tests)
            if spec.metadata.type == "typedef":
                results[spec_name] = {"success": True, "output": "Skipped (typedef)"}
                continue

            # Check if test file exists
            if not self.runner.test_exists(spec_name, language=lang):
                results[spec_name] = {"success": True, "output": "No tests found"}
                continue

            result = self.run_tests(spec_name)
            results[spec_name] = result
            if not result["success"]:
                all_passed = False

        return {
            "success": all_passed,
            "results": results
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
        spec = self.parser.parse_spec(name)
        lang = spec.metadata.language_target

        # 1. Run tests to get current error
        result = self.runner.run_tests(module_name, language=lang)
        if result.success:
            return "Tests already passed. No fix needed."

        # 2. Gather context
        code_content = self.runner.read_code(module_name, language=lang) or ""
        test_content = self.runner.read_tests(module_name, language=lang) or ""

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