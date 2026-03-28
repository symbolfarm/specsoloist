"""SpecConductor - Manages parallel builds.

The Conductor orchestrates multiple SpecSoloist instances for parallel
compilation.
"""

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from specsoloist.config import SpecSoloistConfig
from specsoloist.core import SpecSoloistCore, BuildResult
from specsoloist.events import EventBus
from specsoloist.resolver import DependencyGraph
from specsoloist.schema import Arrangement


@dataclass
class VerifyResult:
    """Result of project verification."""
    success: bool
    results: Dict[str, Dict[str, any]]  # spec_name -> verification details


class SpecConductor:
    """Manages parallel builds.

    Usage:
        conductor = SpecConductor("/path/to/project")

        # Build all specs
        build_result = conductor.build()
    """

    def __init__(
        self,
        project_dir: str,
        config: Optional[SpecSoloistConfig] = None,
        event_bus: Optional[EventBus] = None
    ):
        """Initialize the conductor.

        Args:
            project_dir: Path to project root.
            config: Optional configuration. Loads from env if not provided.
            event_bus: Optional event bus for build observability.
        """
        self.project_dir = os.path.abspath(project_dir)

        if config:
            self.config = config
        else:
            self.config = SpecSoloistConfig.from_env(project_dir)

        # Create internal SpecSoloistCore for compilation
        self._core = SpecSoloistCore(project_dir, config=self.config, event_bus=event_bus)
        self.parser = self._core.parser
        self.resolver = self._core.resolver

    def verify(self) -> VerifyResult:
        """Verify all specs for schema compliance and interface compatibility.

        Returns:
            VerifyResult with per-spec verification details.
        """
        result = self._core.verify_project()
        return VerifyResult(
            success=result["success"],
            results=result.get("results", {})
        )

    def build(
        self,
        specs: Optional[List[str]] = None,
        parallel: bool = True,
        incremental: bool = True,
        max_workers: int = 4,
        arrangement: Optional[Arrangement] = None,
        model: Optional[str] = None,
    ) -> BuildResult:
        """Build specs in dependency order.

        Args:
            specs: List of spec names to build. If None, builds all specs.
            parallel: If True, compile independent specs concurrently.
            incremental: If True, only recompile changed specs.
            max_workers: Maximum number of parallel workers.
            arrangement: Optional build arrangement.
            model: Optional LLM model override applied to all compilations.

        Returns:
            BuildResult with compilation status.
        """
        if arrangement:
            self._provision_environment(arrangement)

        result = self._core.compile_project(
            specs=specs,
            model=model,
            generate_tests=True,
            incremental=incremental,
            parallel=parallel,
            max_workers=max_workers,
            arrangement=arrangement
        )

        if arrangement and arrangement.static:
            self._copy_static_artifacts(arrangement)

        return result

    def _provision_environment(self, arrangement: Arrangement):
        """Create config files and run setup commands."""
        # 1. Write config files (arrangement is the source of truth — always overwrite)
        for filename, content in arrangement.environment.config_files.items():
            # Use runner's build_dir as base (redirection already handled in CLI for src_dir)
            target_path = os.path.join(self._core.runner.build_dir, filename)

            from specsoloist import ui
            ui.print_info(f"Provisioning config file: {filename}")
            parent_dir = os.path.dirname(target_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            # Handle placeholders
            project_name = os.path.basename(self.project_dir)
            formatted_content = content.replace("{project_name}", project_name)

            with open(target_path, 'w') as f:
                f.write(formatted_content)

        # 2. Run setup commands if files were missing
        # For now, we always run them if provided, but in a real build we might optimize
        if arrangement.environment.setup_commands:
            from specsoloist import ui
            ui.print_info("Running environment setup commands...")
            for cmd in arrangement.environment.setup_commands:
                # We use the core runner to execute commands in the correct context
                result = self._core.runner.run_custom_test(f"cd {self._core.runner.build_dir} && {cmd}")
                if not result.success:
                    ui.print_warning(f"Setup command failed: {cmd}\n{result.output}")

    def _copy_static_artifacts(self, arrangement: "Arrangement"):
        """Copy verbatim static artifacts declared in the arrangement."""
        from specsoloist import ui

        base = Path(self.project_dir)
        for entry in arrangement.static:
            src = base / entry.source
            dst = base / entry.dest

            if not src.exists():
                ui.print_warning(f"Static artifact not found: {entry.source}")
                continue

            if dst.exists() and not entry.overwrite:
                ui.print_info(f"Skipping static (overwrite=false): {entry.source}")
                continue

            if src.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

            ui.print_info(f"Copied static: {entry.source} → {entry.dest}")

    def get_build_order(self, specs: Optional[List[str]] = None) -> List[str]:
        """Get the build order without actually building.

        Args:
            specs: List of spec names. If None, includes all specs.

        Returns:
            List of spec names in build order.
        """
        return self._core.get_build_order(specs)

    def get_dependency_graph(
        self,
        specs: Optional[List[str]] = None
    ) -> DependencyGraph:
        """Get the dependency graph for visualization.

        Args:
            specs: List of spec names. If None, includes all specs.

        Returns:
            DependencyGraph showing relationships.
        """
        return self._core.get_dependency_graph(specs)
