"""The main orchestrator for SpecSoloist."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional

from specsoloist.compiler import SpecCompiler
from specsoloist.config import SpecSoloistConfig
from specsoloist.manifest import BuildManifest, IncrementalBuilder, compute_content_hash
from specsoloist.parser import SpecParser
from specsoloist.resolver import DependencyGraph, DependencyResolver
from specsoloist.runner import TestRunner


@dataclass
class BuildResult:
    """Result of a multi-spec build operation."""

    success: bool
    specs_compiled: list[str] = field(default_factory=list)
    specs_skipped: list[str] = field(default_factory=list)
    specs_failed: list[str] = field(default_factory=list)
    build_order: list[str] = field(default_factory=list)
    errors: dict[str, str] = field(default_factory=dict)


class SpecSoloistCore:
    """Main orchestrator for SpecSoloist."""

    def __init__(
        self,
        root_dir: str = ".",
        api_key: Optional[str] = None,
        config: Optional[SpecSoloistConfig] = None,
    ) -> None:
        if config is None:
            config = SpecSoloistConfig.from_env(root_dir=root_dir)
        if api_key:
            config.api_key = api_key

        self.config = config
        self.project_dir = os.path.abspath(root_dir)
        self.config.ensure_directories()

        self.parser = SpecParser(self.config.src_path)
        self.runner = TestRunner(self.config.build_path, config=self.config)
        self.resolver = DependencyResolver(parser=self.parser)

        # Lazy initialization
        self._compiler: Optional[SpecCompiler] = None
        self._manifest: Optional[BuildManifest] = None

    @property
    def compiler(self) -> SpecCompiler:
        """Get or create compiler."""
        if self._compiler is None:
            provider = self.config.create_provider()
            global_context = self.parser.load_global_context()
            self._compiler = SpecCompiler(provider=provider, global_context=global_context)
        return self._compiler

    @property
    def manifest(self) -> BuildManifest:
        """Get or create build manifest."""
        if self._manifest is None:
            self._manifest = BuildManifest.load(self.config.build_path)
        return self._manifest

    # Spec Management

    def list_specs(self) -> list[str]:
        """List all available spec files."""
        return self.parser.list_specs()

    def read_spec(self, name: str) -> str:
        """Read spec file content."""
        return self.parser.read_spec(name)

    def create_spec(
        self, name: str, description: str, type: str = "function"
    ) -> str:
        """Create a spec from template."""
        path = self.parser.create_spec(name, description, type)
        return f"Created spec at {path}"

    def validate_spec(self, name: str) -> dict:
        """Validate spec structure."""
        return self.parser.validate_spec(name)

    # Verification

    def verify_project(self) -> dict:
        """Verify all specs for structure and dependency integrity."""
        specs = self.parser.list_specs()
        results = {}
        all_valid = True

        for spec_name in specs:
            result = self.parser.validate_spec(spec_name)
            results[spec_name] = result
            if not result["valid"]:
                all_valid = False

        # Check dependency integrity
        try:
            self.resolver.build_graph()
        except Exception as e:
            all_valid = False
            results["__dependency_graph__"] = {"valid": False, "errors": [str(e)]}

        return {"success": all_valid, "results": results}

    # Compilation

    def compile_spec(
        self,
        name: str,
        model: Optional[str] = None,
        skip_tests: bool = False,
        arrangement=None,
    ) -> str:
        """Compile one spec to code."""
        spec = self.parser.parse_spec(name)
        spec_type = spec.metadata.type

        # Reference specs: documentation only, no code generated
        if spec_type == "reference":
            return f"Skipped {name}: type: reference specs are documentation only"

        # Collect reference spec dependencies
        reference_specs = {}
        for dep in spec.metadata.dependencies:
            dep_name = dep if isinstance(dep, str) else dep.get("from", "").replace(".spec.md", "")
            if not dep_name:
                continue
            try:
                dep_spec = self.parser.parse_spec(dep_name)
                if dep_spec.metadata.type == "reference":
                    reference_specs[dep_name] = dep_spec
            except FileNotFoundError:
                pass

        # Dispatch to appropriate compiler
        if spec_type in ("typedef", "type"):
            code = self.compiler.compile_typedef(spec, model=model, arrangement=arrangement)
        elif spec_type in ("orchestrator", "workflow"):
            code = self.compiler.compile_orchestrator(spec, model=model, arrangement=arrangement)
        else:
            code = self.compiler.compile_code(
                spec, model=model, arrangement=arrangement,
                reference_specs=reference_specs if reference_specs else None
            )

        module_name = self.parser.get_module_name(name)
        self.runner.write_code(module_name, code)

        return code

    def compile_tests(
        self,
        name: str,
        model: Optional[str] = None,
        arrangement=None,
    ) -> str:
        """Generate test suite for a spec."""
        spec = self.parser.parse_spec(name)
        spec_type = spec.metadata.type

        # Skip typedef specs
        if spec_type in ("typedef",):
            return f"Skipped tests for {name}: typedef specs don't need tests"

        module_name = self.parser.get_module_name(name)

        # Reference specs: extract verification snippet
        if spec_type == "reference":
            snippet = self.parser.extract_verification_snippet(spec.body)
            if not snippet:
                return f"Skipped tests for {name}: no verification snippet found"
            test_code = f"def test_verify():\n    {snippet}\n"
            self.runner.write_tests(module_name, test_code)
            return test_code

        # Collect reference spec dependencies
        reference_specs = {}
        for dep in spec.metadata.dependencies:
            dep_name = dep if isinstance(dep, str) else dep.get("from", "").replace(".spec.md", "")
            if not dep_name:
                continue
            try:
                dep_spec = self.parser.parse_spec(dep_name)
                if dep_spec.metadata.type == "reference":
                    reference_specs[dep_name] = dep_spec
            except FileNotFoundError:
                pass

        test_code = self.compiler.compile_tests(
            spec, model=model, arrangement=arrangement,
            reference_specs=reference_specs if reference_specs else None
        )
        self.runner.write_tests(module_name, test_code)

        return test_code

    def compile_project(
        self,
        specs: Optional[list[str]] = None,
        model: Optional[str] = None,
        generate_tests: bool = True,
        incremental: bool = False,
        parallel: bool = False,
        max_workers: int = 4,
        arrangement=None,
    ) -> BuildResult:
        """Compile multiple specs in dependency order."""
        if specs is None:
            specs = self.parser.list_specs()

        # Normalize spec names
        spec_names = [
            self.parser.get_module_name(s) if s.endswith(".spec.md") else s
            for s in specs
        ]

        try:
            build_order = self.resolver.resolve_build_order(spec_names)
        except Exception as e:
            return BuildResult(
                success=False,
                errors={"__build_order__": str(e)},
            )

        # Compute incremental rebuild plan if needed
        if incremental:
            spec_hashes = {}
            spec_deps = {}
            for name in build_order:
                try:
                    content = self.parser.read_spec(name)
                    spec_hashes[name] = compute_content_hash(content)
                    parsed = self.parser.parse_spec(name)
                    deps = []
                    for dep in parsed.metadata.dependencies:
                        dep_name = dep if isinstance(dep, str) else dep.get("from", "").replace(".spec.md", "")
                        if dep_name:
                            deps.append(dep_name)
                    spec_deps[name] = deps
                except Exception:
                    spec_hashes[name] = ""
                    spec_deps[name] = []

            builder = IncrementalBuilder(manifest=self.manifest, src_dir=self.config.src_path)
            rebuild_plan = builder.get_rebuild_plan(build_order, spec_hashes, spec_deps)
        else:
            rebuild_plan = build_order

        result = BuildResult(success=True, build_order=build_order)

        # Track which specs to skip
        skip_set = set(build_order) - set(rebuild_plan)
        result.specs_skipped = sorted(skip_set)

        if parallel:
            self._compile_parallel(
                rebuild_plan, result, model, generate_tests, arrangement, max_workers
            )
        else:
            self._compile_sequential(
                rebuild_plan, result, model, generate_tests, arrangement
            )

        # Update manifest for successful builds
        if incremental:
            for name in result.specs_compiled:
                try:
                    content = self.parser.read_spec(name)
                    spec_hash = compute_content_hash(content)
                    parsed = self.parser.parse_spec(name)
                    deps = []
                    for dep in parsed.metadata.dependencies:
                        dep_name = dep if isinstance(dep, str) else dep.get("from", "").replace(".spec.md", "")
                        if dep_name:
                            deps.append(dep_name)
                    output_files = [
                        self.runner.get_code_path(name),
                        self.runner.get_test_path(name),
                    ]
                    self.manifest.update_spec(name, spec_hash, deps, output_files)
                except Exception:
                    pass
            self.manifest.save(self.config.build_path)

        if result.specs_failed:
            result.success = False

        return result

    def _compile_sequential(
        self,
        spec_names: list[str],
        result: BuildResult,
        model: Optional[str],
        generate_tests: bool,
        arrangement,
    ) -> None:
        """Compile specs one at a time."""
        for name in spec_names:
            try:
                self.compile_spec(name, model=model, arrangement=arrangement)
                if generate_tests:
                    self.compile_tests(name, model=model, arrangement=arrangement)
                result.specs_compiled.append(name)
            except Exception as e:
                result.specs_failed.append(name)
                result.errors[name] = str(e)

    def _compile_parallel(
        self,
        spec_names: list[str],
        result: BuildResult,
        model: Optional[str],
        generate_tests: bool,
        arrangement,
        max_workers: int,
    ) -> None:
        """Compile specs using parallel execution by levels."""
        try:
            levels = self.resolver.get_parallel_build_order(spec_names)
        except Exception:
            # Fall back to sequential
            self._compile_sequential(spec_names, result, model, generate_tests, arrangement)
            return

        for level in levels:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}
                for name in level:
                    future = executor.submit(
                        self._compile_one, name, model, generate_tests, arrangement
                    )
                    futures[future] = name

                for future in as_completed(futures):
                    name = futures[future]
                    try:
                        future.result()
                        result.specs_compiled.append(name)
                    except Exception as e:
                        result.specs_failed.append(name)
                        result.errors[name] = str(e)

    def _compile_one(
        self, name: str, model: Optional[str], generate_tests: bool, arrangement
    ) -> None:
        """Compile a single spec (for parallel execution)."""
        self.compile_spec(name, model=model, arrangement=arrangement)
        if generate_tests:
            self.compile_tests(name, model=model, arrangement=arrangement)

    # Build Order

    def get_build_order(self, specs: Optional[list[str]] = None) -> list[str]:
        """Preview build order without compiling."""
        if specs is None:
            specs = self.parser.list_specs()
        spec_names = [
            self.parser.get_module_name(s) if s.endswith(".spec.md") else s
            for s in specs
        ]
        return self.resolver.resolve_build_order(spec_names)

    def get_dependency_graph(
        self, specs: Optional[list[str]] = None
    ) -> DependencyGraph:
        """Get the dependency graph."""
        if specs is None:
            specs = self.parser.list_specs()
        spec_names = [
            self.parser.get_module_name(s) if s.endswith(".spec.md") else s
            for s in specs
        ]
        return self.resolver.build_graph(spec_names)

    # Testing

    def run_tests(self, name: str) -> dict:
        """Run tests for one spec."""
        result = self.runner.run_tests(name)
        return {"success": result.success, "output": result.output}

    def run_all_tests(self) -> dict:
        """Run tests for all compiled specs."""
        specs = self.parser.list_specs()
        results = {}
        all_success = True

        for spec in specs:
            module_name = self.parser.get_module_name(spec)
            if self.runner.test_exists(module_name):
                test_result = self.runner.run_tests(module_name)
                results[module_name] = {
                    "success": test_result.success,
                    "output": test_result.output,
                }
                if not test_result.success:
                    all_success = False

        return {"success": all_success, "results": results}

    # Self-Healing

    def attempt_fix(
        self,
        name: str,
        model: Optional[str] = None,
        arrangement=None,
    ) -> str:
        """Run tests, analyze failures with LLM, apply generated fixes."""
        module_name = self.parser.get_module_name(name)

        # Run tests first
        test_result = self.runner.run_tests(module_name)
        if test_result.success:
            return "Tests already passing, no fix needed"

        # Get current code and tests
        spec = self.parser.parse_spec(name)
        code_content = self.runner.read_code(module_name) or ""
        test_content = self.runner.read_tests(module_name) or ""

        # Generate fix
        fix_response = self.compiler.generate_fix(
            spec=spec,
            code_content=code_content,
            test_content=test_content,
            error_log=test_result.output,
            model=model,
            arrangement=arrangement,
        )

        # Parse and apply fix
        fixes = self.compiler.parse_fix_response(fix_response)
        for filename, content in fixes.items():
            self.runner.write_file(filename, content)

        return fix_response
