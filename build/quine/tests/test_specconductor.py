"""
Comprehensive test suite for SpecConductor.

Tests cover:
- Initialization and configuration
- Verification of specs
- Building specs in dependency order
- Workflow execution with step resolution
- Checkpoints and error handling
- Trace persistence and retrieval
"""

import json
import os
import tempfile
import time
from unittest.mock import MagicMock, Mock, patch

import pytest

from spechestra.specconductor import (
    PerformResult,
    SpecConductor,
    StepResult,
    VerifyResult,
)
from specsoloist.config import SpecSoloistConfig
from specsoloist.core import BuildResult
from specsoloist.resolver import DependencyGraph


class TestStepResult:
    """Tests for the StepResult dataclass."""

    def test_create_step_result_basic(self):
        """Test creating a basic step result."""
        result = StepResult(
            name="step1",
            spec="my_spec",
            inputs={"a": 1},
            outputs={"b": 2},
            success=True
        )
        assert result.name == "step1"
        assert result.spec == "my_spec"
        assert result.inputs == {"a": 1}
        assert result.outputs == {"b": 2}
        assert result.success is True
        assert result.error is None
        assert result.duration == 0.0

    def test_step_result_with_error(self):
        """Test step result with error details."""
        result = StepResult(
            name="step1",
            spec="my_spec",
            inputs={},
            outputs={},
            success=False,
            error="Something went wrong"
        )
        assert result.success is False
        assert result.error == "Something went wrong"

    def test_step_result_with_duration(self):
        """Test step result with duration."""
        result = StepResult(
            name="step1",
            spec="my_spec",
            inputs={},
            outputs={},
            success=True,
            duration=1.23
        )
        assert result.duration == 1.23


class TestPerformResult:
    """Tests for the PerformResult dataclass."""

    def test_create_perform_result(self):
        """Test creating a perform result."""
        result = PerformResult(
            success=True,
            workflow="my_workflow",
            steps=[],
            outputs={"result": 42}
        )
        assert result.success is True
        assert result.workflow == "my_workflow"
        assert result.steps == []
        assert result.outputs == {"result": 42}
        assert result.trace_path == ""
        assert result.duration == 0.0

    def test_perform_result_with_trace_and_duration(self):
        """Test perform result with trace path and duration."""
        result = PerformResult(
            success=True,
            workflow="test",
            steps=[],
            outputs={},
            trace_path="/path/to/trace.json",
            duration=5.0
        )
        assert result.trace_path == "/path/to/trace.json"
        assert result.duration == 5.0


class TestVerifyResult:
    """Tests for the VerifyResult dataclass."""

    def test_create_verify_result(self):
        """Test creating a verify result."""
        results = {
            "spec1": {"status": "valid"},
            "spec2": {"status": "warning"}
        }
        result = VerifyResult(success=True, results=results)
        assert result.success is True
        assert result.results == results


class TestSpecConductorInit:
    """Tests for SpecConductor initialization."""

    def test_init_with_path(self):
        """Test initializing conductor with a project path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            assert conductor.project_dir == os.path.abspath(tmpdir)
            assert conductor.config is not None
            assert conductor.parser is not None
            assert conductor.resolver is not None

    def test_init_with_config(self):
        """Test initializing conductor with explicit config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig.from_env(tmpdir)
            conductor = SpecConductor(tmpdir, config=config)
            assert conductor.config is config

    def test_init_creates_core(self):
        """Test that init creates a SpecSoloistCore instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            assert conductor._core is not None
            assert conductor.parser is conductor._core.parser
            assert conductor.resolver is conductor._core.resolver


class TestSpecConductorVerify:
    """Tests for verify() method."""

    def test_verify_empty_project(self):
        """Test verifying an empty project returns success."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            with patch.object(conductor._core, 'verify_project') as mock_verify:
                mock_verify.return_value = {
                    "success": True,
                    "results": {}
                }

                result = conductor.verify()
                assert isinstance(result, VerifyResult)
                assert result.success is True
                assert result.results == {}

    def test_verify_returns_verify_result(self):
        """Test that verify returns a VerifyResult object."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            with patch.object(conductor._core, 'verify_project') as mock_verify:
                mock_verify.return_value = {
                    "success": False,
                    "results": {
                        "spec1": {
                            "status": "invalid",
                            "errors": ["Missing schema"]
                        }
                    }
                }

                result = conductor.verify()
                assert isinstance(result, VerifyResult)
                assert result.success is False
                assert "spec1" in result.results


class TestSpecConductorBuild:
    """Tests for build() method."""

    def test_build_calls_core_compile_project(self):
        """Test that build delegates to core.compile_project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            with patch.object(conductor._core, 'compile_project') as mock_compile:
                mock_compile.return_value = BuildResult(
                    success=True,
                    specs_compiled=[],
                    specs_skipped=[],
                    specs_failed=[],
                    build_order=[],
                    errors={}
                )

                result = conductor.build()
                assert isinstance(result, BuildResult)
                assert result.success is True

    def test_build_with_specs_list(self):
        """Test building specific specs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            with patch.object(conductor._core, 'compile_project') as mock_compile:
                mock_compile.return_value = BuildResult(
                    success=True,
                    specs_compiled=["spec1"],
                    specs_skipped=[],
                    specs_failed=[],
                    build_order=["spec1"],
                    errors={}
                )

                result = conductor.build(specs=["spec1"])
                mock_compile.assert_called_once()
                call_args = mock_compile.call_args
                assert call_args[1]["specs"] == ["spec1"]

    def test_build_with_parallel_disabled(self):
        """Test build with parallel compilation disabled."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            with patch.object(conductor._core, 'compile_project') as mock_compile:
                mock_compile.return_value = BuildResult(
                    success=True,
                    specs_compiled=[],
                    specs_skipped=[],
                    specs_failed=[],
                    build_order=[],
                    errors={}
                )

                conductor.build(parallel=False)
                call_args = mock_compile.call_args
                assert call_args[1]["parallel"] is False

    def test_build_with_custom_max_workers(self):
        """Test build with custom max workers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            with patch.object(conductor._core, 'compile_project') as mock_compile:
                mock_compile.return_value = BuildResult(
                    success=True,
                    specs_compiled=[],
                    specs_skipped=[],
                    specs_failed=[],
                    build_order=[],
                    errors={}
                )

                conductor.build(max_workers=8)
                call_args = mock_compile.call_args
                assert call_args[1]["max_workers"] == 8


class TestSpecConductorBuildOrder:
    """Tests for get_build_order() method."""

    def test_get_build_order_empty_project(self):
        """Test build order for empty project returns empty list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            with patch.object(conductor._core, 'get_build_order') as mock_order:
                mock_order.return_value = []
                result = conductor.get_build_order()
                assert result == []

    def test_get_build_order_with_specs(self):
        """Test getting build order for specific specs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            with patch.object(conductor._core, 'get_build_order') as mock_order:
                mock_order.return_value = ["dep", "dependent"]
                result = conductor.get_build_order(specs=["dependent"])
                mock_order.assert_called_once_with(["dependent"])
                assert "dep" in result
                assert "dependent" in result


class TestSpecConductorDependencyGraph:
    """Tests for get_dependency_graph() method."""

    def test_get_dependency_graph(self):
        """Test getting dependency graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            with patch.object(conductor._core, 'get_dependency_graph') as mock_graph:
                mock_graph.return_value = DependencyGraph()
                result = conductor.get_dependency_graph()
                assert isinstance(result, DependencyGraph)

    def test_get_dependency_graph_with_specs(self):
        """Test getting dependency graph for specific specs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            with patch.object(conductor._core, 'get_dependency_graph') as mock_graph:
                mock_graph.return_value = DependencyGraph()
                conductor.get_dependency_graph(specs=["spec1", "spec2"])
                mock_graph.assert_called_once_with(["spec1", "spec2"])


class TestSpecConductorPerform:
    """Tests for perform() method."""

    def test_perform_invalid_spec_type(self):
        """Test perform raises ValueError for non-workflow spec."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Create a mock spec with type "function"
            mock_spec = Mock()
            mock_spec.metadata.type = "function"
            mock_spec.steps = []

            with patch.object(conductor.parser, 'parse_spec') as mock_parse:
                mock_parse.return_value = mock_spec

                with pytest.raises(ValueError, match="is not a workflow"):
                    conductor.perform("func_spec", {})

    def test_perform_no_steps(self):
        """Test perform raises ValueError for workflow with no steps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            mock_spec = Mock()
            mock_spec.metadata.type = "workflow"
            mock_spec.steps = []

            with patch.object(conductor.parser, 'parse_spec') as mock_parse:
                mock_parse.return_value = mock_spec

                with pytest.raises(ValueError, match="has no steps"):
                    conductor.perform("empty_workflow", {})

    def test_perform_single_step_success(self):
        """Test successful workflow execution with a single step."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Create a mock step
            mock_step = Mock()
            mock_step.name = "step1"
            mock_step.spec = "spec1"
            mock_step.inputs = {}
            mock_step.checkpoint = False

            # Create mock spec
            mock_spec = Mock()
            mock_spec.metadata.type = "workflow"
            mock_spec.steps = [mock_step]

            with patch.object(conductor.parser, 'parse_spec') as mock_parse:
                mock_parse.return_value = mock_spec

                with patch.object(conductor, '_execute_step') as mock_execute:
                    mock_execute.return_value = {"output": "result"}

                    with patch.object(conductor, '_save_trace') as mock_save:
                        mock_save.return_value = "/path/to/trace.json"

                        result = conductor.perform("test_workflow", {})
                        assert result.success is True
                        assert len(result.steps) == 1
                        assert result.steps[0].name == "step1"
                        assert result.outputs == {"output": "result"}
                        assert result.trace_path == "/path/to/trace.json"

    def test_perform_step_failure(self):
        """Test workflow execution when a step fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            mock_step = Mock()
            mock_step.name = "step1"
            mock_step.spec = "spec1"
            mock_step.inputs = {}
            mock_step.checkpoint = False

            mock_spec = Mock()
            mock_spec.metadata.type = "workflow"
            mock_spec.steps = [mock_step]

            with patch.object(conductor.parser, 'parse_spec') as mock_parse:
                mock_parse.return_value = mock_spec

                with patch.object(conductor, '_execute_step') as mock_execute:
                    mock_execute.side_effect = RuntimeError("Step failed")

                    result = conductor.perform("test_workflow", {})
                    assert result.success is False
                    assert len(result.steps) == 1
                    assert result.steps[0].success is False
                    assert "Step failed" in result.steps[0].error

    def test_perform_with_checkpoint_continue(self):
        """Test workflow with checkpoint callback returning True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            mock_step = Mock()
            mock_step.name = "step1"
            mock_step.spec = "spec1"
            mock_step.inputs = {}
            mock_step.checkpoint = True

            mock_spec = Mock()
            mock_spec.metadata.type = "workflow"
            mock_spec.steps = [mock_step]

            with patch.object(conductor.parser, 'parse_spec') as mock_parse:
                mock_parse.return_value = mock_spec

                with patch.object(conductor, '_execute_step') as mock_execute:
                    mock_execute.return_value = {"output": "result"}

                    with patch.object(conductor, '_save_trace'):
                        callback = Mock(return_value=True)
                        result = conductor.perform(
                            "test_workflow", {}, checkpoint_callback=callback
                        )
                        assert result.success is True
                        callback.assert_called_with("step1")

    def test_perform_with_checkpoint_abort(self):
        """Test workflow with checkpoint callback returning False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            mock_step = Mock()
            mock_step.name = "step1"
            mock_step.spec = "spec1"
            mock_step.inputs = {}
            mock_step.checkpoint = True

            mock_spec = Mock()
            mock_spec.metadata.type = "workflow"
            mock_spec.steps = [mock_step]

            with patch.object(conductor.parser, 'parse_spec') as mock_parse:
                mock_parse.return_value = mock_spec

                callback = Mock(return_value=False)
                result = conductor.perform(
                    "test_workflow", {}, checkpoint_callback=callback
                )
                assert result.success is False
                assert len(result.steps) == 0

    def test_perform_resolves_inputs(self):
        """Test that perform correctly resolves step inputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            mock_step = Mock()
            mock_step.name = "step1"
            mock_step.spec = "spec1"
            mock_step.inputs = {"arg": "inputs.value"}
            mock_step.checkpoint = False

            mock_spec = Mock()
            mock_spec.metadata.type = "workflow"
            mock_spec.steps = [mock_step]

            with patch.object(conductor.parser, 'parse_spec') as mock_parse:
                mock_parse.return_value = mock_spec

                with patch.object(conductor, '_execute_step') as mock_execute:
                    mock_execute.return_value = {}

                    with patch.object(conductor, '_save_trace'):
                        conductor.perform("test_workflow", {"value": 42})
                        # Check that execute was called with resolved inputs
                        call_args = mock_execute.call_args
                        assert call_args[0][1] == {"arg": 42}


class TestSpecConductorResolveStepInputs:
    """Tests for _resolve_step_inputs() method."""

    def test_resolve_literal_values(self):
        """Test resolving literal string values."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            result = conductor._resolve_step_inputs(
                {"arg": "literal_value"},
                {"inputs": {}}
            )
            assert result == {"arg": "literal_value"}

    def test_resolve_inputs_reference(self):
        """Test resolving workflow input reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            result = conductor._resolve_step_inputs(
                {"arg": "inputs.param"},
                {"inputs": {"param": 42}}
            )
            assert result == {"arg": 42}

    def test_resolve_step_outputs_reference(self):
        """Test resolving previous step output reference."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            result = conductor._resolve_step_inputs(
                {"arg": "step1.outputs.result"},
                {
                    "step1": {
                        "outputs": {"result": "value"}
                    }
                }
            )
            assert result == {"arg": "value"}

    def test_resolve_mixed_inputs(self):
        """Test resolving a mix of literal and reference inputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            result = conductor._resolve_step_inputs(
                {
                    "literal": "hello",
                    "from_inputs": "inputs.key",
                    "from_step": "step1.outputs.val"
                },
                {
                    "inputs": {"key": "world"},
                    "step1": {"outputs": {"val": 123}}
                }
            )
            assert result == {"literal": "hello", "from_inputs": "world", "from_step": 123}

    def test_resolve_nonexistent_reference(self):
        """Test resolving reference to nonexistent input."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            result = conductor._resolve_step_inputs(
                {"arg": "inputs.missing"},
                {"inputs": {}}
            )
            assert result == {"arg": None}


class TestSpecConductorExecuteStep:
    """Tests for _execute_step() method."""

    def test_execute_step_missing_module(self):
        """Test executing a step when module doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            with pytest.raises(FileNotFoundError, match="not found"):
                conductor._execute_step("nonexistent", {})

    def test_execute_step_no_entry_point(self):
        """Test executing a step with no entry point."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Create a dummy module
            module_path = os.path.join(conductor.config.build_path, "test_module.py")
            os.makedirs(os.path.dirname(module_path), exist_ok=True)
            with open(module_path, 'w') as f:
                f.write("# empty module\n")

            with pytest.raises(AttributeError, match="no standard entry point"):
                conductor._execute_step("test_module", {})

    def test_execute_step_with_run_entry(self):
        """Test executing a step with 'run' entry point."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Create a module with 'run' function
            module_path = os.path.join(conductor.config.build_path, "test_spec.py")
            os.makedirs(os.path.dirname(module_path), exist_ok=True)
            with open(module_path, 'w') as f:
                f.write("def run(x):\n    return {'result': x * 2}\n")

            result = conductor._execute_step("test_spec", {"x": 5})
            assert result == {"result": 10}

    def test_execute_step_with_main_entry(self):
        """Test executing a step with 'main' entry point."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            module_path = os.path.join(conductor.config.build_path, "test_spec.py")
            os.makedirs(os.path.dirname(module_path), exist_ok=True)
            with open(module_path, 'w') as f:
                f.write("def main(a, b):\n    return {'sum': a + b}\n")

            result = conductor._execute_step("test_spec", {"a": 3, "b": 4})
            assert result == {"sum": 7}

    def test_execute_step_returns_dict(self):
        """Test that step returns a dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            module_path = os.path.join(conductor.config.build_path, "test_spec.py")
            os.makedirs(os.path.dirname(module_path), exist_ok=True)
            with open(module_path, 'w') as f:
                f.write("def run():\n    return {'key': 'value'}\n")

            result = conductor._execute_step("test_spec", {})
            assert isinstance(result, dict)
            assert result == {"key": "value"}

    def test_execute_step_wraps_non_dict_return(self):
        """Test that non-dict return values are wrapped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            module_path = os.path.join(conductor.config.build_path, "test_spec.py")
            os.makedirs(os.path.dirname(module_path), exist_ok=True)
            with open(module_path, 'w') as f:
                f.write("def run():\n    return 42\n")

            result = conductor._execute_step("test_spec", {})
            assert result == {"result": 42}


class TestSpecConductorSaveTrace:
    """Tests for _save_trace() method."""

    def test_save_trace_creates_directory(self):
        """Test that save_trace creates the trace directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            traces_dir = os.path.join(conductor.config.build_path, ".spechestra", "traces")
            assert not os.path.exists(traces_dir)

            trace_path = conductor._save_trace("test_workflow", {}, [])
            assert os.path.exists(traces_dir)
            assert os.path.exists(trace_path)

    def test_save_trace_contains_workflow_info(self):
        """Test that trace contains workflow metadata."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            steps = [
                StepResult(
                    name="step1",
                    spec="spec1",
                    inputs={"a": 1},
                    outputs={"b": 2},
                    success=True,
                    duration=0.5
                )
            ]

            trace_path = conductor._save_trace("my_workflow", {"input": "value"}, steps)

            with open(trace_path, 'r') as f:
                trace = json.load(f)

            assert trace["workflow"] == "my_workflow"
            assert trace["inputs"] == {"input": "value"}
            assert len(trace["steps"]) == 1
            assert trace["steps"][0]["name"] == "step1"
            assert trace["steps"][0]["outputs"] == {"b": 2}

    def test_save_trace_returns_path(self):
        """Test that save_trace returns the path to the trace file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            trace_path = conductor._save_trace("test", {}, [])
            assert isinstance(trace_path, str)
            assert trace_path.endswith(".json")
            assert "trace_test_" in trace_path


class TestSpecConductorGetTrace:
    """Tests for get_trace() method."""

    def test_get_trace_no_traces_exist(self):
        """Test getting traces when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            traces = conductor.get_trace("nonexistent")
            assert traces == []

    def test_get_trace_returns_traces(self):
        """Test getting saved traces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Save a trace
            conductor._save_trace("my_workflow", {"input": 1}, [])

            traces = conductor.get_trace("my_workflow")
            assert len(traces) == 1
            assert traces[0]["workflow"] == "my_workflow"
            assert traces[0]["inputs"] == {"input": 1}

    def test_get_trace_sorted_newest_first(self):
        """Test that traces are sorted newest first."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Save multiple traces - need to wait more than 1 second to avoid
            # filename collision since timestamps are only to second precision
            path1 = conductor._save_trace("test", {}, [])
            time.sleep(1.1)
            path2 = conductor._save_trace("test", {}, [])

            traces = conductor.get_trace("test")
            assert len(traces) == 2
            # Newer should be first
            assert traces[0]["timestamp"] > traces[1]["timestamp"]


class TestSpecConductorBuildAndPerform:
    """Tests for build_and_perform() method."""

    def test_build_and_perform_build_fails(self):
        """Test build_and_perform when build fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            failed_build = BuildResult(
                success=False,
                specs_compiled=[],
                specs_skipped=[],
                specs_failed=["spec1"],
                build_order=["spec1"],
                errors={"spec1": "Build error"}
            )

            with patch.object(conductor, 'build') as mock_build:
                mock_build.return_value = failed_build

                build_result, perform_result = conductor.build_and_perform("test", {})
                assert build_result.success is False
                assert perform_result.success is False
                assert len(perform_result.steps) == 0

    def test_build_and_perform_build_succeeds(self):
        """Test build_and_perform when build succeeds."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            build_result = BuildResult(
                success=True,
                specs_compiled=["spec1"],
                specs_skipped=[],
                specs_failed=[],
                build_order=["spec1"],
                errors={}
            )

            perform_result = PerformResult(
                success=True,
                workflow="test",
                steps=[],
                outputs={"result": 42}
            )

            with patch.object(conductor, 'build') as mock_build:
                with patch.object(conductor, 'perform') as mock_perform:
                    mock_build.return_value = build_result
                    mock_perform.return_value = perform_result

                    build, perf = conductor.build_and_perform("test", {})
                    assert build.success is True
                    assert perf.success is True
                    assert perf.outputs == {"result": 42}


class TestSpecConductorIntegration:
    """Integration tests for SpecConductor."""

    def test_conductor_initialization_and_access(self):
        """Test that conductor can be initialized and accessed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            assert conductor.project_dir == os.path.abspath(tmpdir)
            assert conductor.parser is not None
            assert conductor.resolver is not None
            assert conductor.config is not None

    def test_conductor_multiple_workflows(self):
        """Test conductor can handle multiple workflow traces."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Save traces for multiple workflows
            conductor._save_trace("workflow1", {"a": 1}, [])
            conductor._save_trace("workflow2", {"b": 2}, [])

            traces1 = conductor.get_trace("workflow1")
            traces2 = conductor.get_trace("workflow2")

            assert len(traces1) == 1
            assert len(traces2) == 1
            assert traces1[0]["workflow"] == "workflow1"
            assert traces2[0]["workflow"] == "workflow2"


# Additional edge case tests
class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    def test_perform_with_orchestrator_type(self):
        """Test that perform accepts 'orchestrator' type specs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            mock_step = Mock()
            mock_step.name = "step1"
            mock_step.spec = "spec1"
            mock_step.inputs = {}
            mock_step.checkpoint = False

            mock_spec = Mock()
            mock_spec.metadata.type = "orchestrator"
            mock_spec.steps = [mock_step]

            with patch.object(conductor.parser, 'parse_spec') as mock_parse:
                mock_parse.return_value = mock_spec

                with patch.object(conductor, '_execute_step') as mock_execute:
                    mock_execute.return_value = {}

                    with patch.object(conductor, '_save_trace'):
                        result = conductor.perform("test", {})
                        assert result.success is True

    def test_step_result_dataclass_defaults(self):
        """Test StepResult defaults match spec."""
        result = StepResult(
            name="s1",
            spec="f",
            inputs={},
            outputs={},
            success=True
        )
        assert result.error is None
        assert result.duration == 0.0

    def test_perform_result_dataclass_defaults(self):
        """Test PerformResult defaults match spec."""
        result = PerformResult(
            success=True,
            workflow="w",
            steps=[],
            outputs={"result": 42}
        )
        assert result.outputs == {"result": 42}
        assert result.trace_path == ""
        assert result.duration == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
