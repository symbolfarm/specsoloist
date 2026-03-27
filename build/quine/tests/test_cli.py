"""Tests for the SpecSoloist CLI module."""

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call
from io import StringIO

import pytest

from specsoloist.cli import (
    main,
    cmd_list,
    cmd_create,
    cmd_validate,
    cmd_verify,
    cmd_graph,
    cmd_compile,
    cmd_test,
    cmd_test_all,
    cmd_fix,
    cmd_build,
    cmd_compose,
    cmd_vibe,
    cmd_conduct,
    cmd_respec,
    cmd_spec_diff,
    cmd_diff,
    cmd_status,
    cmd_init,
    cmd_list_templates,
    cmd_install_skills,
    cmd_help,
    cmd_schema,
    cmd_doctor,
)
from specsoloist.core import SpecSoloistCore
from specsoloist import ui


class TestMainArgumentParsing:
    """Test CLI argument parsing and main entry point."""

    def test_main_no_args_prints_help(self, capsys):
        """main() with no arguments prints help and exits."""
        with patch("sys.argv", ["sp"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_version_flag(self, capsys):
        """--version flag prints version and exits."""
        with patch("sys.argv", ["sp", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0
            captured = capsys.readouterr()
            assert "specsoloist" in captured.out

    def test_main_quiet_flag_configures_ui(self, capsys):
        """--quiet flag is passed to ui.configure()."""
        with patch("sys.argv", ["sp", "--quiet", "help"]):
            with patch("specsoloist.cli.ui.configure") as mock_configure:
                main()
                mock_configure.assert_called_once()
                call_kwargs = mock_configure.call_args[1]
                assert call_kwargs["quiet"] is True

    def test_main_json_flag_configures_ui(self, capsys):
        """--json flag is passed to ui.configure()."""
        with patch("sys.argv", ["sp", "--json", "help"]):
            with patch("specsoloist.cli.ui.configure") as mock_configure:
                main()
                mock_configure.assert_called_once()
                call_kwargs = mock_configure.call_args[1]
                assert call_kwargs["json_mode"] is True

    def test_main_help_command(self, capsys):
        """help command without topic lists available topics."""
        with patch("sys.argv", ["sp", "help"]):
            with patch("specsoloist.cli.cmd_help") as mock_cmd:
                main()
                mock_cmd.assert_called_once_with(None)

    def test_main_help_with_topic(self, capsys):
        """help command with topic shows help for that topic."""
        with patch("sys.argv", ["sp", "help", "arrangement"]):
            with patch("specsoloist.cli.cmd_help") as mock_cmd:
                main()
                mock_cmd.assert_called_once_with("arrangement")

    def test_main_schema_command(self, capsys):
        """schema command is handled."""
        with patch("sys.argv", ["sp", "schema"]):
            with patch("specsoloist.cli.cmd_schema") as mock_cmd:
                main()
                mock_cmd.assert_called_once()

    def test_main_doctor_command(self, capsys):
        """doctor command is handled."""
        with patch("sys.argv", ["sp", "doctor"]):
            with patch("specsoloist.cli.cmd_doctor") as mock_cmd:
                main()
                mock_cmd.assert_called_once()

    def test_main_init_without_name_prints_help(self, capsys):
        """init command without name prints help."""
        with patch("sys.argv", ["sp", "init"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_main_init_with_name(self, capsys):
        """init command with name creates project."""
        with patch("sys.argv", ["sp", "init", "myproject"]):
            with patch("specsoloist.cli.cmd_init") as mock_cmd:
                main()
                mock_cmd.assert_called_once_with("myproject", "python", None)

    def test_main_init_with_template(self, capsys):
        """init command with --template argument."""
        with patch("sys.argv", ["sp", "init", "myproject", "--template", "python-fasthtml"]):
            with patch("specsoloist.cli.cmd_init") as mock_cmd:
                main()
                mock_cmd.assert_called_once_with("myproject", "python", "python-fasthtml")

    def test_main_init_list_templates(self, capsys):
        """init --list-templates lists templates."""
        with patch("sys.argv", ["sp", "init", "--list-templates"]):
            with patch("specsoloist.cli.cmd_list_templates") as mock_cmd:
                main()
                mock_cmd.assert_called_once()

    def test_main_install_skills_with_target(self, capsys):
        """install-skills with --target argument."""
        with patch("sys.argv", ["sp", "install-skills", "--target", "/custom/path"]):
            with patch("specsoloist.cli.cmd_install_skills") as mock_cmd:
                main()
                mock_cmd.assert_called_once_with("/custom/path")

    def test_main_keyboard_interrupt_exits_130(self):
        """KeyboardInterrupt during command execution exits with 130."""
        with patch("sys.argv", ["sp", "list"]):
            with patch("specsoloist.cli.SpecSoloistCore"):
                with patch("specsoloist.cli.cmd_list", side_effect=KeyboardInterrupt()):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    assert exc_info.value.code == 130

    def test_main_circular_dependency_error_exits_1(self):
        """CircularDependencyError during command execution exits with 1."""
        from specsoloist.resolver import CircularDependencyError
        with patch("sys.argv", ["sp", "list"]):
            with patch("specsoloist.cli.SpecSoloistCore"):
                with patch("specsoloist.cli.cmd_list", side_effect=CircularDependencyError(["a", "b"])):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    assert exc_info.value.code == 1

    def test_main_missing_dependency_error_exits_1(self):
        """MissingDependencyError during command execution exits with 1."""
        from specsoloist.resolver import MissingDependencyError
        with patch("sys.argv", ["sp", "list"]):
            with patch("specsoloist.cli.SpecSoloistCore"):
                with patch("specsoloist.cli.cmd_list", side_effect=MissingDependencyError("spec", "missing")):
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    assert exc_info.value.code == 1


class TestListCommand:
    """Test the list command."""

    def test_cmd_list_no_specs(self, capsys):
        """list command with no specs shows warning."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.list_specs.return_value = []

        with patch("specsoloist.cli.ui.print_warning") as mock_warn:
            cmd_list(mock_core)
            mock_warn.assert_called()

    def test_cmd_list_with_specs(self, capsys):
        """list command displays specs in a table."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.list_specs.return_value = ["parser.spec.md", "compiler.spec.md"]
        mock_core.validate_spec.return_value = {"valid": True, "errors": []}
        mock_core.read_spec.return_value = "type: bundle\n\n# Overview\nA module"

        with patch("specsoloist.cli.ui.create_table") as mock_table:
            with patch("specsoloist.cli.ui.console"):
                cmd_list(mock_core)
                mock_table.assert_called_once()


class TestCreateCommand:
    """Test the create command."""

    def test_cmd_create_success(self, capsys):
        """create command creates a spec."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.create_spec.return_value = "Spec created: parser"

        with patch("specsoloist.cli.ui.print_success") as mock_success:
            cmd_create(mock_core, "parser", "Parsing module", "bundle")
            mock_success.assert_called_with("Spec created: parser")

    def test_cmd_create_failure(self, capsys):
        """create command handles errors."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.create_spec.side_effect = Exception("File exists")

        with patch("specsoloist.cli.ui.print_error"):
            with pytest.raises(SystemExit) as exc_info:
                cmd_create(mock_core, "parser", "Parsing module", "bundle")
            assert exc_info.value.code == 1


class TestValidateCommand:
    """Test the validate command."""

    def test_cmd_validate_valid_spec(self, capsys):
        """validate command with valid spec shows success."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.validate_spec.return_value = {"valid": True, "errors": []}

        with patch("specsoloist.cli.ui.print_success") as mock_success:
            cmd_validate(mock_core, "parser")
            mock_success.assert_called()

    def test_cmd_validate_invalid_spec(self, capsys):
        """validate command with invalid spec shows errors."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.validate_spec.return_value = {
            "valid": False,
            "errors": ["Missing Overview section", "Invalid metadata"]
        }

        with patch("specsoloist.cli.ui.print_error"):
            with patch("specsoloist.cli.ui.print_info"):
                with pytest.raises(SystemExit) as exc_info:
                    cmd_validate(mock_core, "parser")
                assert exc_info.value.code == 1

    def test_cmd_validate_json_output(self, capsys):
        """validate command with --json outputs JSON."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.validate_spec.return_value = {"valid": True, "errors": []}

        with patch("builtins.print") as mock_print:
            cmd_validate(mock_core, "parser", json_output=True)
            mock_print.assert_called()
            args = mock_print.call_args[0][0]
            assert isinstance(json.loads(args), dict)


class TestVerifyCommand:
    """Test the verify command."""

    def test_cmd_verify_success(self, capsys):
        """verify command shows success when all specs are valid."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.verify_project.return_value = {"success": True, "results": []}

        with patch("specsoloist.cli.ui.print_success") as mock_success:
            cmd_verify(mock_core)
            mock_success.assert_called()

    def test_cmd_verify_failure(self, capsys):
        """verify command shows errors when verification fails."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.verify_project.return_value = {
            "success": False,
            "results": ["Circular dependency detected"]
        }

        with patch("specsoloist.cli.ui.print_error"):
            with patch("specsoloist.cli.ui.print_warning"):
                with pytest.raises(SystemExit) as exc_info:
                    cmd_verify(mock_core)
                assert exc_info.value.code == 1


class TestCompileCommand:
    """Test the compile command."""

    def test_cmd_compile_success(self, capsys):
        """compile command compiles a spec."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.compile_spec.return_value = "Spec compiled successfully"

        with patch("specsoloist.cli.ui.spinner"):
            with patch("specsoloist.cli.ui.print_success") as mock_success:
                cmd_compile(mock_core, "parser", generate_tests=True)
                mock_success.assert_called()

    def test_cmd_compile_failure(self, capsys):
        """compile command handles compilation errors."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.compile_spec.side_effect = Exception("LLM error")

        with patch("specsoloist.cli.ui.spinner"):
            with patch("specsoloist.cli.ui.print_error"):
                with pytest.raises(SystemExit) as exc_info:
                    cmd_compile(mock_core, "parser")
                assert exc_info.value.code == 1

    def test_cmd_compile_json_output(self, capsys):
        """compile command with --json outputs JSON."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.compile_spec.return_value = "Success"

        with patch("specsoloist.cli.ui.spinner"):
            with patch("builtins.print") as mock_print:
                cmd_compile(mock_core, "parser", json_output=True)
                mock_print.assert_called()


class TestTestCommand:
    """Test the test command."""

    def test_cmd_test_success(self, capsys):
        """test command runs tests successfully."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.run_tests.return_value = {"success": True, "output": "All tests passed"}

        with patch("specsoloist.cli.ui.print_success") as mock_success:
            cmd_test(mock_core, "parser")
            mock_success.assert_called()

    def test_cmd_test_failure(self, capsys):
        """test command shows errors when tests fail."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.run_tests.return_value = {"success": False, "output": "Test failed"}

        with patch("specsoloist.cli.ui.print_error"):
            with patch("specsoloist.cli.ui.print_info"):
                with pytest.raises(SystemExit) as exc_info:
                    cmd_test(mock_core, "parser")
                assert exc_info.value.code == 1


class TestTestAllCommand:
    """Test the test --all command."""

    def test_cmd_test_all_success(self, capsys):
        """test --all runs all tests successfully."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.run_all_tests.return_value = {
            "success": True,
            "results": {}
        }

        with patch("specsoloist.cli.ui.print_success") as mock_success:
            cmd_test_all(mock_core)
            mock_success.assert_called()

    def test_cmd_test_all_failure(self, capsys):
        """test --all shows errors when tests fail."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.run_all_tests.return_value = {
            "success": False,
            "results": {
                "parser": {"success": False},
                "compiler": {"success": True}
            }
        }

        with patch("specsoloist.cli.ui.print_error"):
            with patch("specsoloist.cli.ui.print_info"):
                with pytest.raises(SystemExit) as exc_info:
                    cmd_test_all(mock_core)
                assert exc_info.value.code == 1


class TestFixCommand:
    """Test the fix command."""

    def test_cmd_fix_success(self, capsys):
        """fix command attempts to fix failing tests."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.attempt_fix.return_value = "Tests fixed successfully"

        with patch("specsoloist.cli.ui.spinner"):
            with patch("specsoloist.cli.ui.print_success") as mock_success:
                cmd_fix(mock_core, "parser")
                mock_success.assert_called()


class TestBuildCommand:
    """Test the build command."""

    def test_cmd_build_success(self, capsys):
        """build command compiles all specs."""
        from specsoloist.core import BuildResult

        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.compile_project.return_value = BuildResult(
            success=True,
            specs_compiled=["parser", "compiler"],
            specs_skipped=[],
            specs_failed=[],
            build_order=["parser", "compiler"],
            errors={}
        )

        with patch("specsoloist.cli.ui.spinner"):
            with patch("specsoloist.cli.ui.print_success") as mock_success:
                cmd_build(mock_core)
                mock_success.assert_called()

    def test_cmd_build_failure(self, capsys):
        """build command shows errors when build fails."""
        from specsoloist.core import BuildResult

        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.compile_project.return_value = BuildResult(
            success=False,
            specs_compiled=[],
            specs_skipped=[],
            specs_failed=["parser"],
            build_order=[],
            errors={"parser": "Compilation error"}
        )

        with patch("specsoloist.cli.ui.spinner"):
            with patch("specsoloist.cli.ui.print_error"):
                with patch("specsoloist.cli.ui.print_info"):
                    with pytest.raises(SystemExit) as exc_info:
                        cmd_build(mock_core)
                    assert exc_info.value.code == 1


class TestStatusCommand:
    """Test the status command."""

    def test_cmd_status_shows_table(self, capsys):
        """status command displays spec compilation status."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.list_specs.return_value = ["parser.spec.md", "compiler.spec.md"]

        with patch("specsoloist.cli.ui.create_table"):
            with patch("specsoloist.cli.ui.console"):
                with patch("specsoloist.cli._file_exists", return_value=True):
                    cmd_status(mock_core)

    def test_cmd_status_no_specs(self, capsys):
        """status command with no specs shows message."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.list_specs.return_value = []

        with patch("specsoloist.cli.ui.print_info"):
            cmd_status(mock_core)


class TestInitCommand:
    """Test the init command."""

    def test_cmd_init_creates_project(self):
        """init command creates a new project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = os.path.join(tmpdir, "newproject")

            with patch("specsoloist.cli.Path", wraps=Path):
                with patch("specsoloist.cli.ui.print_success"):
                    cmd_init(project_path, "python")

            assert os.path.exists(project_path)
            assert os.path.exists(os.path.join(project_path, "src"))
            assert os.path.exists(os.path.join(project_path, "tests"))
            assert os.path.exists(os.path.join(project_path, "arrangement.yaml"))

    def test_cmd_init_existing_directory_fails(self, tmpdir):
        """init command fails if directory exists."""
        project_path = str(tmpdir)

        with patch("specsoloist.cli.ui.print_error"):
            with pytest.raises(SystemExit) as exc_info:
                cmd_init(project_path, "python")
            assert exc_info.value.code == 1


class TestListTemplatesCommand:
    """Test the list templates command."""

    def test_cmd_list_templates_shows_templates(self, capsys):
        """list-templates shows available templates."""
        with patch("specsoloist.cli.ui.print_header"):
            with patch("specsoloist.cli.ui.print_info") as mock_info:
                cmd_list_templates()
                assert mock_info.call_count >= 3


class TestInstallSkillsCommand:
    """Test the install-skills command."""

    def test_cmd_install_skills_creates_directory(self):
        """install-skills creates target directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            target = os.path.join(tmpdir, "skills")

            with patch("specsoloist.cli.ui.print_success"):
                cmd_install_skills(target)

            assert os.path.exists(target)


class TestHelpCommand:
    """Test the help command."""

    def test_cmd_help_no_topic_lists_topics(self, capsys):
        """help without topic lists available topics."""
        with patch("specsoloist.cli.ui.print_header"):
            with patch("specsoloist.cli.ui.print_info") as mock_info:
                cmd_help()
                assert mock_info.call_count >= 5

    def test_cmd_help_with_valid_topic(self, capsys):
        """help with valid topic shows help."""
        with patch("specsoloist.cli.ui.print_header"):
            with patch("specsoloist.cli.ui.print_info"):
                cmd_help("arrangement")

    def test_cmd_help_with_invalid_topic(self, capsys):
        """help with invalid topic shows error."""
        with patch("specsoloist.cli.ui.print_error"):
            with pytest.raises(SystemExit) as exc_info:
                cmd_help("invalid_topic")
            assert exc_info.value.code == 1


class TestSchemaCommand:
    """Test the schema command."""

    def test_cmd_schema_no_topic(self, capsys):
        """schema without topic shows full schema."""
        with patch("specsoloist.cli.ui.print_header"):
            with patch("specsoloist.cli.ui.print_info"):
                cmd_schema()

    def test_cmd_schema_with_valid_topic(self, capsys):
        """schema with valid topic shows that topic."""
        with patch("specsoloist.cli.ui.print_header"):
            with patch("specsoloist.cli.ui.print_info"):
                cmd_schema("output_paths")

    def test_cmd_schema_with_invalid_topic(self, capsys):
        """schema with invalid topic shows error."""
        with patch("specsoloist.cli.ui.print_error"):
            with pytest.raises(SystemExit) as exc_info:
                cmd_schema("invalid_topic")
            assert exc_info.value.code == 1

    def test_cmd_schema_json_output(self, capsys):
        """schema with --json outputs JSON."""
        with patch("builtins.print") as mock_print:
            cmd_schema(json_output=True)
            mock_print.assert_called()


class TestDoctorCommand:
    """Test the doctor command."""

    def test_cmd_doctor_checks_environment(self, capsys):
        """doctor command checks environment."""
        with patch("specsoloist.cli.ui.print_header"):
            with patch("specsoloist.cli.ui.print_step"):
                with patch("specsoloist.cli.ui.print_success"):
                    with patch("specsoloist.cli.ui.print_warning"):
                        cmd_doctor()


class TestComposeCommand:
    """Test the compose command."""

    def test_cmd_compose_requires_spechestra(self, capsys):
        """compose command shows warning about spechestra."""
        mock_core = MagicMock(spec=SpecSoloistCore)

        with patch("specsoloist.cli.ui.print_warning") as mock_warn:
            cmd_compose(mock_core, "Build a todo app")
            mock_warn.assert_called()


class TestVibeCommand:
    """Test the vibe command."""

    def test_cmd_vibe_requires_spechestra(self, capsys):
        """vibe command shows warning about spechestra."""
        mock_core = MagicMock(spec=SpecSoloistCore)

        with patch("specsoloist.cli.ui.print_warning") as mock_warn:
            cmd_vibe(mock_core, "Build a todo app")
            mock_warn.assert_called()


class TestConductCommand:
    """Test the conduct command."""

    def test_cmd_conduct_requires_spechestra(self, capsys):
        """conduct command shows warning about spechestra."""
        mock_core = MagicMock(spec=SpecSoloistCore)

        with patch("specsoloist.cli.ui.print_warning") as mock_warn:
            cmd_conduct(mock_core)
            mock_warn.assert_called()


class TestRespecCommand:
    """Test the respec command."""

    def test_cmd_respec_requires_integration(self, capsys):
        """respec command shows warning about integration."""
        mock_core = MagicMock(spec=SpecSoloistCore)

        with patch("specsoloist.cli.ui.print_warning") as mock_warn:
            cmd_respec(mock_core, "src/module.py")
            mock_warn.assert_called()


class TestDiffCommands:
    """Test the diff commands."""

    def test_cmd_spec_diff(self, capsys):
        """spec_diff command checks drift."""
        mock_core = MagicMock(spec=SpecSoloistCore)

        with patch("specsoloist.cli.ui.print_info"):
            cmd_spec_diff(mock_core, "parser")

    def test_cmd_diff(self, capsys):
        """diff command compares builds."""
        mock_core = MagicMock(spec=SpecSoloistCore)

        with patch("specsoloist.cli.ui.print_info"):
            cmd_diff(mock_core, "build1", "build2", None, None, "report.json", None)


class TestGraphCommand:
    """Test the graph command."""

    def test_cmd_graph_exports_mermaid(self, capsys):
        """graph command exports dependency graph."""
        mock_core = MagicMock(spec=SpecSoloistCore)
        mock_core.get_dependency_graph.return_value = MagicMock()

        with patch("specsoloist.cli.ui.print_info"):
            cmd_graph(mock_core)
