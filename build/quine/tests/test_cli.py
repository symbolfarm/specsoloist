"""
Tests for the CLI module.

Tests command parsing, execution, error handling, and API key validation.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

from specsoloist.cli import (
    main, cmd_list, cmd_create, cmd_validate, cmd_verify, cmd_graph,
    cmd_compile, cmd_test, cmd_fix, cmd_build,
    cmd_compose, cmd_conduct, cmd_perform, cmd_respec, cmd_mcp,
    _detect_agent_cli, _run_agent_oneshot, _check_api_key
)
from specsoloist.resolver import CircularDependencyError, MissingDependencyError


class TestArgumentParsing:
    """Tests for command-line argument parsing."""

    def test_list_command(self):
        """Test sp list command parsing."""
        with patch("specsoloist.cli.cmd_list"):
            with patch("specsoloist.cli.SpecSoloistCore"):
                sys.argv = ["sp", "list"]
                try:
                    main()
                except SystemExit:
                    pass

    def test_create_command(self):
        """Test sp create command parsing with name, description, and optional type."""
        with patch("specsoloist.cli.cmd_create") as mock_cmd:
            with patch("specsoloist.cli.SpecSoloistCore"):
                sys.argv = ["sp", "create", "auth", "Authentication module", "--type", "bundle"]
                try:
                    main()
                except SystemExit:
                    pass
                # Command should be parsed and dispatched
                assert mock_cmd.called

    def test_validate_command(self):
        """Test sp validate command with spec name."""
        with patch("specsoloist.cli.cmd_validate"):
            with patch("specsoloist.cli.SpecSoloistCore"):
                sys.argv = ["sp", "validate", "auth"]
                try:
                    main()
                except SystemExit:
                    pass

    def test_compile_command_with_model(self):
        """Test sp compile command with --model flag."""
        with patch("specsoloist.cli.cmd_compile") as mock_cmd:
            with patch("specsoloist.cli.SpecSoloistCore"):
                sys.argv = ["sp", "compile", "auth", "--model", "claude-3-sonnet"]
                try:
                    main()
                except SystemExit:
                    pass
                assert mock_cmd.called

    def test_build_command_with_parallel(self):
        """Test sp build command with --parallel and --workers."""
        with patch("specsoloist.cli.cmd_build") as mock_cmd:
            with patch("specsoloist.cli.SpecSoloistCore"):
                sys.argv = ["sp", "build", "--parallel", "--workers", "8"]
                try:
                    main()
                except SystemExit:
                    pass
                assert mock_cmd.called

    def test_compose_command(self):
        """Test sp compose command with natural language request."""
        with patch("specsoloist.cli.cmd_compose") as mock_cmd:
            with patch("specsoloist.cli.SpecSoloistCore"):
                sys.argv = ["sp", "compose", "Build me a todo app"]
                try:
                    main()
                except SystemExit:
                    pass
                assert mock_cmd.called

    def test_conduct_command_with_src_dir(self):
        """Test sp conduct command with optional src_dir."""
        with patch("specsoloist.cli.cmd_conduct") as mock_cmd:
            with patch("specsoloist.cli.SpecSoloistCore"):
                sys.argv = ["sp", "conduct", "score/"]
                try:
                    main()
                except SystemExit:
                    pass
                assert mock_cmd.called

    def test_respec_command(self):
        """Test sp respec command with file and optional test/out paths."""
        with patch("specsoloist.cli.cmd_respec") as mock_cmd:
            with patch("specsoloist.cli.SpecSoloistCore"):
                sys.argv = ["sp", "respec", "foo.py", "--test", "test_foo.py", "--out", "foo.spec.md"]
                try:
                    main()
                except SystemExit:
                    pass
                assert mock_cmd.called


class TestCommandExecution:
    """Tests for command execution logic."""

    @patch("specsoloist.cli.ui")
    def test_cmd_list_empty(self, mock_ui):
        """Test cmd_list with no specs."""
        mock_core = Mock()
        mock_core.list_specs.return_value = []

        cmd_list(mock_core)

        mock_ui.print_warning.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_list_with_specs(self, mock_ui):
        """Test cmd_list with multiple specs."""
        mock_core = Mock()
        mock_core.list_specs.return_value = ["auth.spec.md", "db.spec.md"]
        mock_parsed = Mock()
        mock_parsed.metadata.type = "bundle"
        mock_parsed.metadata.status = "stable"
        mock_parsed.metadata.description = "Authentication"
        mock_core.parser.parse_spec.return_value = mock_parsed
        mock_ui.create_table.return_value = Mock()

        cmd_list(mock_core)

        # Should create a table and print it
        mock_ui.create_table.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_create_success(self, mock_ui):
        """Test cmd_create successfully creates a spec."""
        mock_core = Mock()
        mock_core.create_spec.return_value = "/path/to/auth.spec.md"

        cmd_create(mock_core, "auth", "Authentication module", "bundle")

        mock_core.create_spec.assert_called_with("auth", "Authentication module", type="bundle")
        mock_ui.print_success.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_create_already_exists(self, mock_ui):
        """Test cmd_create when spec already exists."""
        mock_core = Mock()
        mock_core.create_spec.side_effect = FileExistsError("Spec already exists")

        with pytest.raises(SystemExit):
            cmd_create(mock_core, "auth", "Authentication module", "bundle")

        mock_ui.print_error.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_validate_valid_spec(self, mock_ui):
        """Test cmd_validate with a valid spec."""
        mock_core = Mock()
        mock_core.validate_spec.return_value = {"valid": True, "errors": []}

        cmd_validate(mock_core, "auth")

        mock_ui.print_success.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_validate_invalid_spec(self, mock_ui):
        """Test cmd_validate with an invalid spec."""
        mock_core = Mock()
        mock_core.validate_spec.return_value = {
            "valid": False,
            "errors": ["Missing description", "Invalid YAML"]
        }

        with pytest.raises(SystemExit):
            cmd_validate(mock_core, "auth")

        mock_ui.print_error.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_verify(self, mock_ui):
        """Test cmd_verify with verification results."""
        mock_core = Mock()
        mock_core.verify_project.return_value = {
            "success": True,
            "results": {
                "auth": {"status": "valid", "schema_defined": True, "errors": [], "message": ""},
                "db": {"status": "warning", "schema_defined": False, "errors": [], "message": "Missing schema"}
            }
        }
        mock_ui.create_table.return_value = Mock()

        cmd_verify(mock_core)

        mock_ui.print_success.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_graph(self, mock_ui):
        """Test cmd_graph with dependency graph."""
        mock_core = Mock()
        mock_graph = Mock()
        mock_graph.specs = ["auth", "db"]
        mock_graph.get_dependencies.side_effect = lambda s: ["db"] if s == "auth" else []
        mock_core.get_dependency_graph.return_value = mock_graph
        mock_ui.Panel = lambda x, title: x

        cmd_graph(mock_core)

        mock_ui.print_info.assert_called()

    @patch("specsoloist.cli._check_api_key")
    @patch("specsoloist.cli.ui")
    def test_cmd_compile_success(self, mock_ui, mock_check_key):
        """Test cmd_compile successfully compiles a spec."""
        mock_core = Mock()
        mock_core.validate_spec.return_value = {"valid": True, "errors": []}
        mock_core.compile_spec.return_value = "Compiled to /path/to/module.py"
        mock_spec = Mock()
        mock_spec.metadata.type = "bundle"
        mock_core.parser.parse_spec.return_value = mock_spec
        mock_core.compile_tests.return_value = "Generated tests"
        mock_ui.spinner.return_value.__enter__ = Mock()
        mock_ui.spinner.return_value.__exit__ = Mock()

        cmd_compile(mock_core, "auth", None, True)

        mock_core.compile_spec.assert_called()
        mock_core.compile_tests.assert_called()

    @patch("specsoloist.cli._check_api_key")
    @patch("specsoloist.cli.ui")
    def test_cmd_compile_invalid_spec(self, mock_ui, mock_check_key):
        """Test cmd_compile with invalid spec."""
        mock_core = Mock()
        mock_core.validate_spec.return_value = {
            "valid": False,
            "errors": ["Missing dependencies"]
        }

        with pytest.raises(SystemExit):
            cmd_compile(mock_core, "auth", None, True)

        mock_ui.print_error.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_test_passing(self, mock_ui):
        """Test cmd_test with passing tests."""
        mock_core = Mock()
        mock_core.run_tests.return_value = {
            "success": True,
            "output": "All tests passed"
        }
        mock_ui.spinner.return_value.__enter__ = Mock()
        mock_ui.spinner.return_value.__exit__ = Mock()

        cmd_test(mock_core, "auth")

        mock_ui.print_success.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_test_failing(self, mock_ui):
        """Test cmd_test with failing tests."""
        mock_core = Mock()
        mock_core.run_tests.return_value = {
            "success": False,
            "output": "Test failed: AssertionError"
        }
        mock_ui.spinner.return_value.__enter__ = Mock()
        mock_ui.spinner.return_value.__exit__ = Mock()

        with pytest.raises(SystemExit):
            cmd_test(mock_core, "auth")

        mock_ui.print_error.assert_called()

    @patch("specsoloist.cli._check_api_key")
    @patch("specsoloist.cli.ui")
    def test_cmd_fix(self, mock_ui, mock_check_key):
        """Test cmd_fix with fix result."""
        mock_core = Mock()
        mock_core.attempt_fix.return_value = "Applied fixes to: module.py"
        mock_ui.spinner.return_value.__enter__ = Mock()
        mock_ui.spinner.return_value.__exit__ = Mock()

        cmd_fix(mock_core, "auth", None)

        mock_core.attempt_fix.assert_called()
        mock_ui.print_success.assert_called()

    @patch("specsoloist.cli._check_api_key")
    @patch("specsoloist.cli.ui")
    def test_cmd_build_success(self, mock_ui, mock_check_key):
        """Test cmd_build with successful compilation."""
        mock_core = Mock()
        mock_core.list_specs.return_value = ["auth.spec.md", "db.spec.md"]
        mock_result = Mock()
        mock_result.success = True
        mock_result.specs_compiled = ["auth", "db"]
        mock_result.specs_skipped = []
        mock_result.specs_failed = []
        mock_result.errors = {}
        mock_core.compile_project.return_value = mock_result
        mock_ui.create_table.return_value = Mock()
        mock_ui.spinner.return_value.__enter__ = Mock()
        mock_ui.spinner.return_value.__exit__ = Mock()

        cmd_build(mock_core, False, False, 4, None, True)

        mock_core.compile_project.assert_called()
        mock_ui.print_success.assert_called()

    @patch("specsoloist.cli._check_api_key")
    @patch("specsoloist.cli.ui")
    def test_cmd_build_no_specs(self, mock_ui, mock_check_key):
        """Test cmd_build with no specs found."""
        mock_core = Mock()
        mock_core.list_specs.return_value = []

        with pytest.raises(SystemExit):
            cmd_build(mock_core, False, False, 4, None, True)

        mock_ui.print_warning.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_compose_with_agent(self, mock_ui):
        """Test cmd_compose with agent mode."""
        mock_core = Mock()
        with patch("specsoloist.cli._compose_with_agent") as mock_agent:
            cmd_compose(mock_core, "Build a todo app", False, False, None)
            mock_agent.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_compose_no_agent_mode(self, mock_ui):
        """Test cmd_compose with --no-agent flag."""
        mock_core = Mock()
        with pytest.raises(SystemExit):
            cmd_compose(mock_core, "Build a todo app", True, False, None)
        mock_ui.print_error.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_conduct_with_agent(self, mock_ui):
        """Test cmd_conduct with agent mode."""
        mock_core = Mock()
        with patch("specsoloist.cli._conduct_with_agent") as mock_agent:
            cmd_conduct(mock_core, None, False, False, False, False, 4, None)
            mock_agent.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_conduct_no_agent_mode(self, mock_ui):
        """Test cmd_conduct with --no-agent flag."""
        mock_core = Mock()
        with pytest.raises(SystemExit):
            cmd_conduct(mock_core, None, True, False, False, False, 4, None)
        mock_ui.print_error.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_perform(self, mock_ui):
        """Test cmd_perform with invalid JSON."""
        mock_core = Mock()
        with pytest.raises(SystemExit):
            cmd_perform(mock_core, "workflow", "not valid json")
        mock_ui.print_error.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_perform_valid_json(self, mock_ui):
        """Test cmd_perform with valid JSON inputs."""
        mock_core = Mock()
        with pytest.raises(SystemExit):
            cmd_perform(mock_core, "workflow", '{"key": "value"}')
        # Should error because spechestra is not available
        # Verify it called print_error with the appropriate message
        call_args = [str(call) for call in mock_ui.print_error.call_args_list]
        assert len(call_args) > 0

    @patch("specsoloist.cli.ui")
    def test_cmd_respec_with_agent(self, mock_ui):
        """Test cmd_respec with agent mode."""
        mock_core = Mock()
        with patch("specsoloist.cli._respec_with_agent") as mock_agent:
            cmd_respec(mock_core, "foo.py", None, None, False, None, False)
            mock_agent.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_respec_no_agent_mode(self, mock_ui):
        """Test cmd_respec with --no-agent flag."""
        mock_core = Mock()
        with pytest.raises(SystemExit):
            cmd_respec(mock_core, "foo.py", None, None, True, None, False)
        mock_ui.print_error.assert_called()

    @patch("specsoloist.cli.ui")
    def test_cmd_mcp(self, mock_ui):
        """Test cmd_mcp (should error as MCP not available in this build)."""
        with pytest.raises(SystemExit):
            cmd_mcp()
        # Verify it called print_error
        call_args = [str(call) for call in mock_ui.print_error.call_args_list]
        assert len(call_args) > 0


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    @patch("specsoloist.cli.ui")
    @patch("specsoloist.cli.SpecSoloistCore")
    def test_keyboard_interrupt(self, mock_core_class, mock_ui):
        """Test handling of keyboard interrupt."""
        mock_core = Mock()
        mock_core.list_specs.return_value = []
        mock_core_class.return_value = mock_core

        with patch("specsoloist.cli.cmd_list") as mock_cmd:
            mock_cmd.side_effect = KeyboardInterrupt()
            sys.argv = ["sp", "list"]

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 130
            mock_ui.print_warning.assert_called()

    @patch("specsoloist.cli.ui")
    @patch("specsoloist.cli.SpecSoloistCore")
    def test_circular_dependency_error(self, mock_core_class, mock_ui):
        """Test handling of CircularDependencyError."""
        mock_core = Mock()
        mock_core.list_specs.return_value = []
        mock_core_class.return_value = mock_core

        with patch("specsoloist.cli.cmd_build") as mock_cmd:
            mock_cmd.side_effect = CircularDependencyError(["a", "b", "a"])
            sys.argv = ["sp", "build"]

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            mock_ui.print_error.assert_called()

    @patch("specsoloist.cli.ui")
    @patch("specsoloist.cli.SpecSoloistCore")
    def test_missing_dependency_error(self, mock_core_class, mock_ui):
        """Test handling of MissingDependencyError."""
        mock_core = Mock()
        mock_core.list_specs.return_value = []
        mock_core_class.return_value = mock_core

        with patch("specsoloist.cli.cmd_build") as mock_cmd:
            mock_cmd.side_effect = MissingDependencyError("auth", "crypto")
            sys.argv = ["sp", "build"]

            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            mock_ui.print_error.assert_called()

    @patch("specsoloist.cli.ui")
    @patch("specsoloist.cli.SpecSoloistCore")
    def test_general_exception(self, mock_core_class, mock_ui):
        """Test handling of general exceptions."""
        mock_core_class.side_effect = ValueError("Something went wrong")
        sys.argv = ["sp", "list"]

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_ui.print_error.assert_called()


class TestHelperFunctions:
    """Tests for helper functions."""

    def test_detect_agent_cli_claude(self):
        """Test detecting claude CLI when available."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "claude" if x == "claude" else None
            result = _detect_agent_cli()
            assert result == "claude"

    def test_detect_agent_cli_gemini(self):
        """Test detecting gemini CLI when available."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "gemini" if x == "gemini" else None
            result = _detect_agent_cli()
            assert result == "gemini"

    def test_detect_agent_cli_none(self):
        """Test when no agent CLI is available."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            result = _detect_agent_cli()
            assert result is None

    def test_detect_agent_cli_prefers_claude(self):
        """Test that claude is preferred over gemini."""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: x  # Both available
            result = _detect_agent_cli()
            assert result == "claude"

    @patch("subprocess.run")
    def test_run_agent_oneshot_claude(self, mock_run):
        """Test running claude agent in one-shot mode."""
        mock_run.return_value.returncode = 0
        _run_agent_oneshot("claude", "test prompt", False, None)

        # Should call subprocess.run with claude command
        args = mock_run.call_args[0][0]
        assert args[0] == "claude"
        assert "-p" in args
        assert "test prompt" in args

    @patch("subprocess.run")
    def test_run_agent_oneshot_claude_with_model(self, mock_run):
        """Test running claude agent with model override."""
        mock_run.return_value.returncode = 0
        _run_agent_oneshot("claude", "test prompt", False, "claude-3-opus")

        args = mock_run.call_args[0][0]
        assert "--model" in args
        assert "claude-3-opus" in args

    @patch("subprocess.run")
    def test_run_agent_oneshot_claude_with_auto_accept(self, mock_run):
        """Test running claude agent with auto-accept."""
        mock_run.return_value.returncode = 0
        _run_agent_oneshot("claude", "test prompt", True, None)

        args = mock_run.call_args[0][0]
        assert "--permission-mode" in args
        assert "bypassPermissions" in args

    @patch("subprocess.run")
    def test_run_agent_oneshot_gemini(self, mock_run):
        """Test running gemini agent in one-shot mode."""
        mock_run.return_value.returncode = 0
        _run_agent_oneshot("gemini", "test prompt", False, None)

        args = mock_run.call_args[0][0]
        assert args[0] == "gemini"
        assert "-p" in args

    @patch("subprocess.run")
    def test_run_agent_oneshot_failure(self, mock_run):
        """Test handling of agent command failure."""
        mock_run.return_value.returncode = 1
        with pytest.raises(RuntimeError):
            _run_agent_oneshot("claude", "test prompt", False, None)

    @patch("os.environ.get")
    def test_check_api_key_gemini_missing(self, mock_env):
        """Test API key check when GEMINI_API_KEY is missing."""
        mock_env.side_effect = lambda k, default=None: {
            "SPECSOLOIST_LLM_PROVIDER": "gemini"
        }.get(k, default)

        with patch.dict(os.environ, {}, clear=True):
            with patch("specsoloist.cli.ui") as mock_ui:
                with pytest.raises(SystemExit):
                    _check_api_key()
                mock_ui.print_error.assert_called()

    @patch("os.environ.get")
    def test_check_api_key_anthropic_missing(self, mock_env):
        """Test API key check when ANTHROPIC_API_KEY is missing."""
        mock_env.side_effect = lambda k, default=None: {
            "SPECSOLOIST_LLM_PROVIDER": "anthropic"
        }.get(k, default)

        with patch.dict(os.environ, {}, clear=True):
            with patch("specsoloist.cli.ui") as mock_ui:
                with pytest.raises(SystemExit):
                    _check_api_key()
                mock_ui.print_error.assert_called()

    @patch("os.environ.get")
    def test_check_api_key_present(self, mock_env):
        """Test API key check when key is present."""
        mock_env.side_effect = lambda k, default=None: {
            "SPECSOLOIST_LLM_PROVIDER": "gemini"
        }.get(k, default)

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}):
            # Should not raise
            _check_api_key()


class TestMainFlow:
    """Tests for main entry point and flow."""

    @patch("specsoloist.cli.SpecSoloistCore")
    @patch("specsoloist.cli.cmd_list")
    def test_main_dispatch_list(self, mock_cmd, mock_core_class):
        """Test main dispatches to cmd_list."""
        mock_core_class.return_value = Mock()
        sys.argv = ["sp", "list"]

        try:
            main()
        except SystemExit:
            pass

        mock_cmd.assert_called()

    @patch("specsoloist.cli.SpecSoloistCore")
    def test_main_no_command(self, mock_core_class):
        """Test main with no command shows help."""
        mock_core_class.return_value = Mock()
        sys.argv = ["sp"]

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0

    @patch("specsoloist.cli.SpecSoloistCore")
    def test_main_init_failure(self, mock_core_class):
        """Test main when SpecSoloistCore initialization fails."""
        mock_core_class.side_effect = RuntimeError("Config error")
        sys.argv = ["sp", "list"]

        with patch("specsoloist.cli.ui") as mock_ui:
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
            mock_ui.print_error.assert_called()


class TestAgentDetection:
    """Tests for agent detection and agent commands."""

    @patch("specsoloist.cli._detect_agent_cli")
    @patch("specsoloist.cli._run_agent_oneshot")
    @patch("specsoloist.cli.ui")
    def test_compose_with_agent_success(self, mock_ui, mock_run, mock_detect):
        """Test compose with agent successfully runs."""
        mock_detect.return_value = "claude"
        mock_ui.print_info = Mock()

        from specsoloist.cli import _compose_with_agent
        _compose_with_agent("Build a todo app", False, None)

        mock_run.assert_called()

    @patch("specsoloist.cli._detect_agent_cli")
    @patch("specsoloist.cli.ui")
    def test_compose_with_agent_not_found(self, mock_ui, mock_detect):
        """Test compose when no agent is found."""
        mock_detect.return_value = None

        from specsoloist.cli import _compose_with_agent
        with pytest.raises(SystemExit):
            _compose_with_agent("Build a todo app", False, None)

        mock_ui.print_error.assert_called()

    @patch("specsoloist.cli._detect_agent_cli")
    @patch("specsoloist.cli._run_agent_oneshot")
    @patch("specsoloist.cli.ui")
    def test_conduct_with_agent_quine_mode(self, mock_ui, mock_run, mock_detect):
        """Test conduct with agent in quine mode."""
        mock_detect.return_value = "claude"
        mock_ui.print_info = Mock()

        from specsoloist.cli import _conduct_with_agent
        _conduct_with_agent("score/", False, None)

        # Should detect quine mode from "score" in path
        mock_run.assert_called()
        args = mock_run.call_args
        assert "quine" in args[0][1].lower() or "score" in args[0][1]

    @patch("specsoloist.cli._detect_agent_cli")
    @patch("specsoloist.cli._run_agent_oneshot")
    @patch("specsoloist.cli.ui")
    def test_respec_with_agent(self, mock_ui, mock_run, mock_detect):
        """Test respec with agent."""
        mock_detect.return_value = "gemini"
        mock_ui.print_info = Mock()

        from specsoloist.cli import _respec_with_agent
        _respec_with_agent("foo.py", "test_foo.py", None, False, None)

        mock_run.assert_called()
        args = mock_run.call_args[0][1]
        assert "respec" in args
        assert "foo.py" in args
        assert "test_foo.py" in args
