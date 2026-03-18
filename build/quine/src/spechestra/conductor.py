"""SpecConductor is the build manager of Spechestra."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from typing import Optional

from specsoloist.config import SpecSoloistConfig
from specsoloist.core import BuildResult, SpecSoloistCore
from specsoloist.resolver import DependencyGraph
from specsoloist.schema import Arrangement


@dataclass
class VerifyResult:
    """Result of project verification."""

    success: bool
    results: dict = field(default_factory=dict)


class SpecConductor:
    """The main conductor class for Spechestra."""

    def __init__(
        self,
        project_dir: str,
        config: Optional[SpecSoloistConfig] = None,
    ) -> None:
        self.project_dir = os.path.abspath(project_dir)
        self.config = config or SpecSoloistConfig.from_env(root_dir=project_dir)

        self._core = SpecSoloistCore(
            root_dir=project_dir,
            config=self.config,
        )

        # Expose parser and resolver as public attributes
        self.parser = self._core.parser
        self.resolver = self._core.resolver

    def verify(self) -> VerifyResult:
        """Verify all specs for schema compliance and interface compatibility."""
        result = self._core.verify_project()
        return VerifyResult(
            success=result["success"],
            results=result["results"],
        )

    def build(
        self,
        specs: Optional[list[str]] = None,
        parallel: bool = True,
        incremental: bool = True,
        max_workers: int = 4,
        arrangement: Optional[Arrangement] = None,
        model: Optional[str] = None,
    ) -> BuildResult:
        """Build specs in dependency order."""
        if arrangement is not None:
            self._provision_environment(arrangement)

        return self._core.compile_project(
            specs=specs,
            model=model,
            generate_tests=True,
            incremental=incremental,
            parallel=parallel,
            max_workers=max_workers,
            arrangement=arrangement,
        )

    def _provision_environment(self, arrangement: Arrangement) -> None:
        """Write config files and run setup commands from the arrangement."""
        build_dir = self.config.build_path
        os.makedirs(build_dir, exist_ok=True)

        # Write config files
        if hasattr(arrangement, "environment") and arrangement.environment:
            env = arrangement.environment
            for filename, content in (env.config_files or {}).items():
                file_path = os.path.join(build_dir, filename)
                file_dir = os.path.dirname(file_path)
                if file_dir:
                    os.makedirs(file_dir, exist_ok=True)
                with open(file_path, "w") as f:
                    f.write(content)

            # Run setup commands
            for cmd in (env.setup_commands or []):
                try:
                    subprocess.run(
                        cmd,
                        shell=True,
                        cwd=build_dir,
                        check=True,
                        capture_output=True,
                    )
                except subprocess.CalledProcessError:
                    pass  # Continue on failure

    def get_build_order(self, specs: Optional[list[str]] = None) -> list[str]:
        """Return specs in build order without actually building."""
        if specs is None:
            specs = self.parser.list_specs()

        if not specs:
            return []

        spec_names = [
            self.parser.get_module_name(s) if s.endswith(".spec.md") else s
            for s in specs
        ]

        try:
            return self.resolver.resolve_build_order(spec_names)
        except Exception:
            return spec_names

    def get_dependency_graph(
        self, specs: Optional[list[str]] = None
    ) -> DependencyGraph:
        """Return the dependency graph for the given specs."""
        return self._core.get_dependency_graph(specs)
