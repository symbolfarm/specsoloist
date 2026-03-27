"""Tests for SpecConductor."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from spechestra.conductor import SpecConductor, VerifyResult
from specsoloist.config import SpecSoloistConfig
from specsoloist.core import BuildResult
from specsoloist.schema import (
    Arrangement,
    ArrangementOutputPaths,
    ArrangementEnvironment,
    ArrangementBuildCommands,
    ArrangementStatic,
)


class TestVerifyResult:
    """Tests for VerifyResult dataclass."""

    def test_verify_result_creation(self):
        """Test VerifyResult can be created with success and results."""
        result = VerifyResult(success=True, results={})
        assert result.success is True
        assert result.results == {}

    def test_verify_result_with_details(self):
        """Test VerifyResult stores verification details."""
        details = {
            "spec1": {"valid": True},
            "spec2": {"valid": False, "errors": ["Missing section"]},
        }
        result = VerifyResult(success=False, results=details)
        assert result.success is False
        assert result.results == details
        assert "spec1" in result.results


class TestSpecConductorInit:
    """Tests for SpecConductor initialization."""

    def test_init_with_project_dir(self):
        """Test SpecConductor initializes with project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            assert conductor.project_dir == os.path.abspath(tmpdir)
            assert conductor.config is not None

    def test_init_sets_absolute_path(self):
        """Test project_dir is converted to absolute path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a relative path reference
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                conductor = SpecConductor(".")
                assert conductor.project_dir == os.path.abspath(".")
                assert not conductor.project_dir.startswith(".")
            finally:
                os.chdir(original_cwd)

    def test_init_with_config(self):
        """Test SpecConductor initializes with provided config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = SpecSoloistConfig(root_dir=tmpdir)
            conductor = SpecConductor(tmpdir, config=config)
            assert conductor.config is config

    def test_init_loads_config_from_env(self):
        """Test SpecConductor loads config from environment."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            assert conductor.config is not None
            assert hasattr(conductor.config, "root_dir")

    def test_init_exposes_parser(self):
        """Test parser is exposed as public attribute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            assert conductor.parser is not None
            assert hasattr(conductor.parser, "list_specs")

    def test_init_exposes_resolver(self):
        """Test resolver is exposed as public attribute."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            assert conductor.resolver is not None
            assert hasattr(conductor.resolver, "build_graph")


class TestVerify:
    """Tests for verify() method."""

    def test_verify_empty_project(self):
        """Test verify returns success for empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            with patch.object(conductor._core, "verify_project") as mock_verify:
                mock_verify.return_value = {"success": True, "results": {}}
                result = conductor.verify()

            assert isinstance(result, VerifyResult)
            assert result.success is True
            assert result.results == {}

    def test_verify_delegates_to_core(self):
        """Test verify delegates to SpecSoloistCore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            with patch.object(conductor._core, "verify_project") as mock_verify:
                mock_verify.return_value = {"success": True, "results": {}}
                conductor.verify()

            mock_verify.assert_called_once()

    def test_verify_returns_core_results(self):
        """Test verify returns results from core."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            core_results = {
                "success": True,
                "results": {"spec1": {"valid": True}}
            }
            with patch.object(conductor._core, "verify_project") as mock_verify:
                mock_verify.return_value = core_results
                result = conductor.verify()

            assert result.success is True
            assert result.results == {"spec1": {"valid": True}}


class TestBuild:
    """Tests for build() method."""

    def test_build_without_arrangement(self):
        """Test build without arrangement delegates to core."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            expected_result = BuildResult(
                success=True,
                specs_compiled=["spec1"],
                specs_skipped=[],
                specs_failed=[],
                build_order=["spec1"],
                errors={}
            )
            with patch.object(conductor._core, "compile_project") as mock_compile:
                mock_compile.return_value = expected_result
                result = conductor.build()

            assert result == expected_result
            mock_compile.assert_called_once()

    def test_build_with_specs_parameter(self):
        """Test build passes specs to core."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            expected_result = BuildResult(
                success=True,
                specs_compiled=["spec1"],
                specs_skipped=[],
                specs_failed=[],
                build_order=["spec1"],
                errors={}
            )
            with patch.object(conductor._core, "compile_project") as mock_compile:
                mock_compile.return_value = expected_result
                result = conductor.build(specs=["spec1"])

            mock_compile.assert_called_once()
            call_kwargs = mock_compile.call_args[1]
            assert call_kwargs["specs"] == ["spec1"]

    def test_build_with_parallel_false(self):
        """Test build respects parallel=False parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            expected_result = BuildResult(
                success=True,
                specs_compiled=[],
                specs_skipped=[],
                specs_failed=[],
                build_order=[],
                errors={}
            )
            with patch.object(conductor._core, "compile_project") as mock_compile:
                mock_compile.return_value = expected_result
                conductor.build(parallel=False)

            call_kwargs = mock_compile.call_args[1]
            assert call_kwargs["parallel"] is False

    def test_build_with_incremental_false(self):
        """Test build respects incremental=False parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            expected_result = BuildResult(
                success=True,
                specs_compiled=[],
                specs_skipped=[],
                specs_failed=[],
                build_order=[],
                errors={}
            )
            with patch.object(conductor._core, "compile_project") as mock_compile:
                mock_compile.return_value = expected_result
                conductor.build(incremental=False)

            call_kwargs = mock_compile.call_args[1]
            assert call_kwargs["incremental"] is False

    def test_build_with_max_workers(self):
        """Test build passes max_workers to core."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            expected_result = BuildResult(
                success=True,
                specs_compiled=[],
                specs_skipped=[],
                specs_failed=[],
                build_order=[],
                errors={}
            )
            with patch.object(conductor._core, "compile_project") as mock_compile:
                mock_compile.return_value = expected_result
                conductor.build(max_workers=8)

            call_kwargs = mock_compile.call_args[1]
            assert call_kwargs["max_workers"] == 8

    def test_build_with_model_override(self):
        """Test build applies model override."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            expected_result = BuildResult(
                success=True,
                specs_compiled=[],
                specs_skipped=[],
                specs_failed=[],
                build_order=[],
                errors={}
            )
            with patch.object(conductor._core, "compile_project") as mock_compile:
                mock_compile.return_value = expected_result
                conductor.build(model="gpt-4")

            call_kwargs = mock_compile.call_args[1]
            assert call_kwargs["model"] == "gpt-4"

    def test_build_with_arrangement_calls_provision(self):
        """Test build calls provision when arrangement provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}")
            )
            expected_result = BuildResult(
                success=True,
                specs_compiled=[],
                specs_skipped=[],
                specs_failed=[],
                build_order=[],
                errors={}
            )
            with patch.object(conductor, "_provision_environment") as mock_provision:
                with patch.object(conductor._core, "compile_project") as mock_compile:
                    mock_compile.return_value = expected_result
                    conductor.build(arrangement=arrangement)

            mock_provision.assert_called_once_with(arrangement)

    def test_build_calls_static_copy_when_arrangement_has_static(self):
        """Test build copies static artifacts when arrangement declares them."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            static_entry = ArrangementStatic(
                source="src/help/",
                dest="build/help/",
                description="Help files"
            )
            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}"),
                static=[static_entry]
            )
            expected_result = BuildResult(
                success=True,
                specs_compiled=[],
                specs_skipped=[],
                specs_failed=[],
                build_order=[],
                errors={}
            )
            with patch.object(conductor, "_provision_environment"):
                with patch.object(conductor, "_copy_static_artifacts") as mock_copy:
                    with patch.object(conductor._core, "compile_project") as mock_compile:
                        mock_compile.return_value = expected_result
                        conductor.build(arrangement=arrangement)

            mock_copy.assert_called_once_with(arrangement)

    def test_build_skips_static_copy_when_no_static_entries(self):
        """Test build doesn't copy static when arrangement has no static entries."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}"),
                static=[]
            )
            expected_result = BuildResult(
                success=True,
                specs_compiled=[],
                specs_skipped=[],
                specs_failed=[],
                build_order=[],
                errors={}
            )
            with patch.object(conductor, "_provision_environment"):
                with patch.object(conductor, "_copy_static_artifacts") as mock_copy:
                    with patch.object(conductor._core, "compile_project") as mock_compile:
                        mock_compile.return_value = expected_result
                        conductor.build(arrangement=arrangement)

            mock_copy.assert_not_called()


class TestProvisionEnvironment:
    """Tests for _provision_environment() method."""

    def test_provision_writes_config_files(self):
        """Test provision writes config files to build directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            # Mock the runner's build_dir
            conductor._core.runner.build_dir = tmpdir

            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                environment=ArrangementEnvironment(
                    config_files={"package.json": '{"name": "test"}'}
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}")
            )

            with patch("specsoloist.ui.print_info"):
                conductor._provision_environment(arrangement)

            config_path = os.path.join(tmpdir, "package.json")
            assert os.path.exists(config_path)
            with open(config_path) as f:
                assert f.read() == '{"name": "test"}'

    def test_provision_creates_parent_directories(self):
        """Test provision creates parent directories for config files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            conductor._core.runner.build_dir = tmpdir

            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                environment=ArrangementEnvironment(
                    config_files={"subdir/config.json": '{"test": true}'}
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}")
            )

            with patch("specsoloist.ui.print_info"):
                conductor._provision_environment(arrangement)

            config_path = os.path.join(tmpdir, "subdir", "config.json")
            assert os.path.exists(config_path)

    def test_provision_replaces_project_name_placeholder(self):
        """Test provision replaces {project_name} placeholders."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            conductor._core.runner.build_dir = tmpdir
            # The conductor's project_dir basename is used as project_name
            project_name = os.path.basename(conductor.project_dir)

            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                environment=ArrangementEnvironment(
                    config_files={"config.txt": "Project: {project_name}"}
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}")
            )

            with patch("specsoloist.ui.print_info"):
                conductor._provision_environment(arrangement)

            config_path = os.path.join(tmpdir, "config.txt")
            with open(config_path) as f:
                content = f.read()
            assert project_name in content
            assert "{project_name}" not in content

    def test_provision_runs_setup_commands(self):
        """Test provision runs setup commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            conductor._core.runner.build_dir = tmpdir

            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                environment=ArrangementEnvironment(
                    setup_commands=["echo 'setup'"]
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}")
            )

            with patch("specsoloist.ui.print_info"):
                with patch.object(conductor._core.runner, "run_custom_test", create=True) as mock_run:
                    from specsoloist.runner import TestResult
                    mock_run.return_value = TestResult(success=True, output="")
                    conductor._provision_environment(arrangement)

            mock_run.assert_called()

    def test_provision_handles_setup_command_failure(self):
        """Test provision warns on setup command failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            conductor._core.runner.build_dir = tmpdir

            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                environment=ArrangementEnvironment(
                    setup_commands=["false"]
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}")
            )

            with patch("specsoloist.ui.print_info"):
                with patch("specsoloist.ui.print_warning") as mock_warn:
                    with patch.object(conductor._core.runner, "run_custom_test", create=True) as mock_run:
                        from specsoloist.runner import TestResult
                        mock_run.return_value = TestResult(success=False, output="Error")
                        conductor._provision_environment(arrangement)

            mock_warn.assert_called()


class TestCopyStaticArtifacts:
    """Tests for _copy_static_artifacts() method."""

    def test_copy_static_directory(self):
        """Test copy static handles directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Create source directory
            src_dir = os.path.join(tmpdir, "src_static")
            os.makedirs(src_dir)
            src_file = os.path.join(src_dir, "test.txt")
            with open(src_file, "w") as f:
                f.write("test content")

            # Destination doesn't exist yet
            dst_dir = os.path.join(tmpdir, "dst_static")

            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}"),
                static=[
                    ArrangementStatic(
                        source="src_static",
                        dest="dst_static",
                        description="Test static"
                    )
                ]
            )

            with patch("specsoloist.ui.print_info"):
                conductor._copy_static_artifacts(arrangement)

            dst_file = os.path.join(dst_dir, "test.txt")
            assert os.path.exists(dst_file)
            with open(dst_file) as f:
                assert f.read() == "test content"

    def test_copy_static_file(self):
        """Test copy static handles files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Create source file
            src_file = os.path.join(tmpdir, "source.txt")
            with open(src_file, "w") as f:
                f.write("source content")

            dst_file = os.path.join(tmpdir, "dest.txt")

            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}"),
                static=[
                    ArrangementStatic(
                        source="source.txt",
                        dest="dest.txt",
                        description="Copy test"
                    )
                ]
            )

            with patch("specsoloist.ui.print_info"):
                conductor._copy_static_artifacts(arrangement)

            assert os.path.exists(dst_file)
            with open(dst_file) as f:
                assert f.read() == "source content"

    def test_copy_static_warns_on_missing_source(self):
        """Test copy static warns when source doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}"),
                static=[
                    ArrangementStatic(
                        source="nonexistent",
                        dest="dest",
                        description="Will fail"
                    )
                ]
            )

            with patch("specsoloist.ui.print_warning") as mock_warn:
                conductor._copy_static_artifacts(arrangement)

            mock_warn.assert_called()
            call_args = mock_warn.call_args[0][0]
            assert "nonexistent" in call_args

    def test_copy_static_skips_when_overwrite_false(self):
        """Test copy static skips existing destinations when overwrite=False."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Create source and existing destination
            src_file = os.path.join(tmpdir, "source.txt")
            dst_file = os.path.join(tmpdir, "dest.txt")
            with open(src_file, "w") as f:
                f.write("source content")
            with open(dst_file, "w") as f:
                f.write("existing content")

            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}"),
                static=[
                    ArrangementStatic(
                        source="source.txt",
                        dest="dest.txt",
                        description="Test",
                        overwrite=False
                    )
                ]
            )

            with patch("specsoloist.ui.print_info") as mock_info:
                conductor._copy_static_artifacts(arrangement)

            # Destination should still have original content
            with open(dst_file) as f:
                assert f.read() == "existing content"

    def test_copy_static_overwrites_when_overwrite_true(self):
        """Test copy static overwrites when overwrite=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Create source and existing destination
            src_file = os.path.join(tmpdir, "source.txt")
            dst_file = os.path.join(tmpdir, "dest.txt")
            with open(src_file, "w") as f:
                f.write("new content")
            with open(dst_file, "w") as f:
                f.write("old content")

            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}"),
                static=[
                    ArrangementStatic(
                        source="source.txt",
                        dest="dest.txt",
                        description="Test",
                        overwrite=True
                    )
                ]
            )

            with patch("specsoloist.ui.print_info"):
                conductor._copy_static_artifacts(arrangement)

            # Destination should have new content
            with open(dst_file) as f:
                assert f.read() == "new content"

    def test_copy_static_creates_parent_directories(self):
        """Test copy static creates parent directories for files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)

            # Create source file
            src_file = os.path.join(tmpdir, "source.txt")
            with open(src_file, "w") as f:
                f.write("content")

            arrangement = Arrangement(
                target_language="python",
                output_paths=ArrangementOutputPaths(
                    implementation="src/{name}.py",
                    tests="tests/test_{name}.py"
                ),
                build_commands=ArrangementBuildCommands(test="pytest {file}"),
                static=[
                    ArrangementStatic(
                        source="source.txt",
                        dest="deep/nested/dest.txt",
                        description="Test"
                    )
                ]
            )

            with patch("specsoloist.ui.print_info"):
                conductor._copy_static_artifacts(arrangement)

            dst_file = os.path.join(tmpdir, "deep", "nested", "dest.txt")
            assert os.path.exists(dst_file)


class TestGetBuildOrder:
    """Tests for get_build_order() method."""

    def test_get_build_order_delegates_to_core(self):
        """Test get_build_order delegates to SpecSoloistCore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            with patch.object(conductor._core, "get_build_order") as mock_order:
                mock_order.return_value = ["spec1", "spec2"]
                result = conductor.get_build_order()

            assert result == ["spec1", "spec2"]
            mock_order.assert_called_once()

    def test_get_build_order_with_specs(self):
        """Test get_build_order passes specs parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            with patch.object(conductor._core, "get_build_order") as mock_order:
                mock_order.return_value = ["spec1"]
                conductor.get_build_order(specs=["spec1"])

            call_args = mock_order.call_args
            # Check positional args (0-indexed tuple) or kwargs
            assert call_args[0][0] == ["spec1"] or call_args[1].get("specs") == ["spec1"]

    def test_get_build_order_empty_project(self):
        """Test get_build_order returns empty list for empty project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            with patch.object(conductor._core, "get_build_order") as mock_order:
                mock_order.return_value = []
                result = conductor.get_build_order()

            assert result == []


class TestGetDependencyGraph:
    """Tests for get_dependency_graph() method."""

    def test_get_dependency_graph_delegates_to_core(self):
        """Test get_dependency_graph delegates to SpecSoloistCore."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            with patch.object(conductor._core, "get_dependency_graph") as mock_graph:
                mock_graph.return_value = MagicMock()
                result = conductor.get_dependency_graph()

            mock_graph.assert_called_once()

    def test_get_dependency_graph_with_specs(self):
        """Test get_dependency_graph passes specs parameter."""
        with tempfile.TemporaryDirectory() as tmpdir:
            conductor = SpecConductor(tmpdir)
            with patch.object(conductor._core, "get_dependency_graph") as mock_graph:
                mock_graph.return_value = MagicMock()
                conductor.get_dependency_graph(specs=["spec1"])

            call_args = mock_graph.call_args
            # Check positional args (0-indexed tuple) or kwargs
            assert call_args[0][0] == ["spec1"] or call_args[1].get("specs") == ["spec1"]
