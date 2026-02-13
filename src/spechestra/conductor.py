"""
SpecConductor - Manages parallel builds and workflow execution.

The Conductor orchestrates multiple SpecSoloist instances for parallel
compilation, and can execute workflows defined by workflow specs.
"""

import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

from specsoloist.config import SpecSoloistConfig
from specsoloist.core import SpecSoloistCore, BuildResult
from specsoloist.resolver import DependencyGraph
from specsoloist.schema import Arrangement


@dataclass
class StepResult:
    """Result of a single workflow step."""
    name: str
    spec: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    success: bool
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class PerformResult:
    """Result of a workflow execution."""
    success: bool
    workflow: str
    steps: List[StepResult]
    outputs: Dict[str, Any]
    trace_path: str = ""
    duration: float = 0.0


@dataclass
class VerifyResult:
    """Result of project verification."""
    success: bool
    results: Dict[str, Dict[str, Any]]  # spec_name -> verification details


class SpecConductor:
    """
    Manages parallel builds and workflow execution.

    Usage:
        conductor = SpecConductor("/path/to/project")

        # Build all specs
        build_result = conductor.build()

        # Execute a workflow
        perform_result = conductor.perform("my_workflow", {"input": 42})

        # Or do both
        build_result, perform_result = conductor.build_and_perform(
            "my_workflow", {"input": 42}
        )
    """

    def __init__(
        self,
        project_dir: str,
        config: Optional[SpecSoloistConfig] = None
    ):
        """
        Initialize the conductor.

        Args:
            project_dir: Path to project root.
            config: Optional configuration. Loads from env if not provided.
        """
        self.project_dir = os.path.abspath(project_dir)

        if config:
            self.config = config
        else:
            self.config = SpecSoloistConfig.from_env(project_dir)

        # Create internal SpecSoloistCore for compilation
        self._core = SpecSoloistCore(project_dir, config=self.config)
        self.parser = self._core.parser
        self.resolver = self._core.resolver

    def verify(self) -> VerifyResult:
        """
        Verify all specs for schema compliance and interface compatibility.

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
        arrangement: Optional[Arrangement] = None
    ) -> BuildResult:
        """
        Build specs in dependency order.

        Args:
            specs: List of spec names to build. If None, builds all specs.
            parallel: If True, compile independent specs concurrently.
            incremental: If True, only recompile changed specs.
            max_workers: Maximum number of parallel workers.
            arrangement: Optional build arrangement.

        Returns:
            BuildResult with compilation status.
        """
        # Note: compile_project in core needs to be updated to accept arrangement
        # Or we can loop and call compile_spec individually if arrangement is provided
        return self._core.compile_project(
            specs=specs,
            generate_tests=True,
            incremental=incremental,
            parallel=parallel,
            max_workers=max_workers,
            arrangement=arrangement
        )

    def get_build_order(self, specs: Optional[List[str]] = None) -> List[str]:
        """
        Get the build order without actually building.

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
        """
        Get the dependency graph for visualization.

        Args:
            specs: List of spec names. If None, includes all specs.

        Returns:
            DependencyGraph showing relationships.
        """
        return self._core.get_dependency_graph(specs)

    def perform(
        self,
        workflow: str,
        inputs: Dict[str, Any],
        checkpoint_callback: Optional[Callable[[str], bool]] = None
    ) -> PerformResult:
        """
        Execute a workflow defined by a workflow spec.

        Args:
            workflow: Name of the workflow spec.
            inputs: Input values for the workflow.
            checkpoint_callback: Optional callback for checkpoint approval.
                                 Called with step name, returns True to continue.

        Returns:
            PerformResult with step outputs and execution trace.
        """
        start_time = time.time()

        # Parse the workflow spec
        spec = self.parser.parse_spec(workflow)

        if spec.metadata.type not in ("workflow", "orchestrator"):
            raise ValueError(f"Spec '{workflow}' is not a workflow (type: {spec.metadata.type})")

        if not spec.steps:
            raise ValueError(f"Workflow '{workflow}' has no steps defined")

        # Execute steps
        step_results = []
        step_outputs: Dict[str, Any] = {"inputs": inputs}

        for step in spec.steps:
            # Check for checkpoint
            if step.checkpoint and checkpoint_callback:
                if not checkpoint_callback(step.name):
                    return PerformResult(
                        success=False,
                        workflow=workflow,
                        steps=step_results,
                        outputs={},
                        duration=time.time() - start_time
                    )

            step_start = time.time()

            # Resolve inputs for this step
            resolved_inputs = self._resolve_step_inputs(
                step.inputs, step_outputs
            )

            # Execute the step
            try:
                result = self._execute_step(step.spec, resolved_inputs)
                step_result = StepResult(
                    name=step.name,
                    spec=step.spec,
                    inputs=resolved_inputs,
                    outputs=result,
                    success=True,
                    duration=time.time() - step_start
                )
                step_outputs[step.name] = {"outputs": result}
            except Exception as e:
                step_result = StepResult(
                    name=step.name,
                    spec=step.spec,
                    inputs=resolved_inputs,
                    outputs={},
                    success=False,
                    error=str(e),
                    duration=time.time() - step_start
                )
                step_results.append(step_result)

                # Stop on failure
                return PerformResult(
                    success=False,
                    workflow=workflow,
                    steps=step_results,
                    outputs={},
                    duration=time.time() - start_time
                )

            step_results.append(step_result)

        # Save trace
        trace_path = self._save_trace(workflow, inputs, step_results)

        # Collect final outputs
        final_outputs = {}
        if step_results:
            final_outputs = step_results[-1].outputs

        return PerformResult(
            success=True,
            workflow=workflow,
            steps=step_results,
            outputs=final_outputs,
            trace_path=trace_path,
            duration=time.time() - start_time
        )

    def _resolve_step_inputs(
        self,
        mappings: Dict[str, str],
        step_outputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve input mappings to actual values."""
        resolved = {}

        for target, source in mappings.items():
            if "." not in source:
                # Literal value
                resolved[target] = source
                continue

            parts = source.split(".")

            if parts[0] == "inputs":
                # Reference to workflow inputs
                resolved[target] = step_outputs.get("inputs", {}).get(parts[1])
            elif len(parts) >= 3 and parts[1] == "outputs":
                # Reference to step outputs: step_name.outputs.param
                step_name = parts[0]
                param = parts[2]
                step_data = step_outputs.get(step_name, {})
                outputs = step_data.get("outputs", {})

                if isinstance(outputs, dict):
                    resolved[target] = outputs.get(param)
                else:
                    resolved[target] = outputs
            else:
                # Unknown format, treat as literal
                resolved[target] = source

        return resolved

    def _execute_step(
        self,
        spec_name: str,
        inputs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a single step by loading and calling its compiled module."""
        import importlib.util
        import sys

        # Find the compiled module
        module_path = os.path.join(
            self.config.build_path,
            f"{spec_name}.py"
        )

        if not os.path.exists(module_path):
            raise FileNotFoundError(
                f"Compiled module for '{spec_name}' not found at {module_path}"
            )

        # Load the module
        module_spec = importlib.util.spec_from_file_location(spec_name, module_path)
        if module_spec is None or module_spec.loader is None:
            raise ImportError(f"Could not load module {spec_name}")

        module = importlib.util.module_from_spec(module_spec)
        sys.modules[spec_name] = module
        module_spec.loader.exec_module(module)

        # Find entry point
        for entry in ["run", "main", "execute", "handler"]:
            if hasattr(module, entry):
                func = getattr(module, entry)
                result = func(**inputs)
                if isinstance(result, dict):
                    return result
                return {"result": result}

        raise AttributeError(
            f"Module '{spec_name}' has no standard entry point (run, main, execute)"
        )

    def _save_trace(
        self,
        workflow: str,
        inputs: Dict[str, Any],
        steps: List[StepResult]
    ) -> str:
        """Save execution trace to disk."""
        import json

        trace_dir = os.path.join(self.config.build_path, ".spechestra", "traces")
        os.makedirs(trace_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trace_{workflow}_{timestamp}.json"
        path = os.path.join(trace_dir, filename)

        trace = {
            "workflow": workflow,
            "timestamp": datetime.now().isoformat(),
            "inputs": inputs,
            "steps": [
                {
                    "name": s.name,
                    "spec": s.spec,
                    "inputs": s.inputs,
                    "outputs": s.outputs,
                    "success": s.success,
                    "error": s.error,
                    "duration": s.duration
                }
                for s in steps
            ]
        }

        with open(path, 'w') as f:
            json.dump(trace, f, indent=2, default=str)

        return path

    def build_and_perform(
        self,
        workflow: str,
        inputs: Dict[str, Any],
        checkpoint_callback: Optional[Callable[[str], bool]] = None
    ) -> Tuple[BuildResult, PerformResult]:
        """
        Build all required specs, then execute the workflow.

        Args:
            workflow: Name of the workflow spec.
            inputs: Input values for the workflow.
            checkpoint_callback: Optional callback for checkpoint approval.

        Returns:
            Tuple of (BuildResult, PerformResult).
        """
        # Build first
        build_result = self.build()

        if not build_result.success:
            # Return failed build with empty perform result
            return (
                build_result,
                PerformResult(
                    success=False,
                    workflow=workflow,
                    steps=[],
                    outputs={},
                    duration=0.0
                )
            )

        # Then perform
        perform_result = self.perform(
            workflow, inputs, checkpoint_callback
        )

        return (build_result, perform_result)

    def get_trace(self, workflow: str) -> List[Dict[str, Any]]:
        """
        Get execution traces for a workflow.

        Args:
            workflow: Name of the workflow.

        Returns:
            List of trace dictionaries.
        """
        import json

        trace_dir = os.path.join(self.config.build_path, ".spechestra", "traces")

        if not os.path.exists(trace_dir):
            return []

        traces = []
        for filename in os.listdir(trace_dir):
            if filename.startswith(f"trace_{workflow}_") and filename.endswith(".json"):
                path = os.path.join(trace_dir, filename)
                with open(path, 'r') as f:
                    traces.append(json.load(f))

        # Sort by timestamp (newest first)
        traces.sort(key=lambda t: t.get("timestamp", ""), reverse=True)

        return traces
