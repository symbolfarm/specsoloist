"""Tests for the UI module."""

import io
import sys
from unittest.mock import patch, MagicMock, call
import pytest
from rich.table import Table
from rich.status import Status

# Import the module and functions to test
from specsoloist import ui


class TestConfigure:
    """Tests for the configure function."""

    def test_configure_default(self):
        """Test configure with default parameters."""
        ui.configure()
        assert not ui.is_quiet()
        assert not ui.is_json_mode()

    def test_configure_quiet_mode(self):
        """Test configure with quiet=True."""
        ui.configure(quiet=True)
        assert ui.is_quiet()
        assert not ui.is_json_mode()

    def test_configure_json_mode(self):
        """Test configure with json_mode=True."""
        ui.configure(json_mode=True)
        assert not ui.is_quiet()
        assert ui.is_json_mode()

    def test_configure_both_modes(self):
        """Test configure with both quiet and json_mode."""
        ui.configure(quiet=True, json_mode=True)
        assert ui.is_quiet()
        assert ui.is_json_mode()

    def test_configure_resets_state(self):
        """Test that configure properly resets state."""
        ui.configure(quiet=True, json_mode=True)
        ui.configure(quiet=False, json_mode=False)
        assert not ui.is_quiet()
        assert not ui.is_json_mode()


class TestIsJsonMode:
    """Tests for is_json_mode function."""

    def test_is_json_mode_default(self):
        """Test default is_json_mode returns False."""
        ui.configure()
        assert ui.is_json_mode() is False

    def test_is_json_mode_active(self):
        """Test is_json_mode returns True when active."""
        ui.configure(json_mode=True)
        assert ui.is_json_mode() is True


class TestIsQuiet:
    """Tests for is_quiet function."""

    def test_is_quiet_default(self):
        """Test default is_quiet returns False."""
        ui.configure()
        assert ui.is_quiet() is False

    def test_is_quiet_active(self):
        """Test is_quiet returns True when active."""
        ui.configure(quiet=True)
        assert ui.is_quiet() is True


class TestPrintHeader:
    """Tests for print_header function."""

    def test_print_header_title_only(self):
        """Test print_header with title only."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_header("Test Title")
            # Should be called 3 times: empty line, panel, empty line
            assert mock_print.call_count == 3

    def test_print_header_title_and_subtitle(self):
        """Test print_header with title and subtitle."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_header("Test Title", "Test Subtitle")
            assert mock_print.call_count == 3

    def test_print_header_empty_subtitle(self):
        """Test print_header with empty string subtitle."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_header("Test Title", "")
            assert mock_print.call_count == 3


class TestPrintSuccess:
    """Tests for print_success function."""

    def test_print_success(self):
        """Test print_success outputs message."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_success("Operation completed")
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "Operation completed" in call_args

    def test_print_success_empty_message(self):
        """Test print_success with empty message."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_success("")
            mock_print.assert_called_once()


class TestPrintError:
    """Tests for print_error function."""

    def test_print_error(self):
        """Test print_error outputs message."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_error("Something went wrong")
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "Something went wrong" in call_args
            assert "Error" in call_args

    def test_print_error_empty_message(self):
        """Test print_error with empty message."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_error("")
            mock_print.assert_called_once()


class TestPrintWarning:
    """Tests for print_warning function."""

    def test_print_warning(self):
        """Test print_warning outputs message."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_warning("Be careful")
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "Be careful" in call_args
            assert "Warning" in call_args

    def test_print_warning_empty_message(self):
        """Test print_warning with empty message."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_warning("")
            mock_print.assert_called_once()


class TestPrintInfo:
    """Tests for print_info function."""

    def test_print_info(self):
        """Test print_info outputs message."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_info("Important note")
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "Important note" in call_args

    def test_print_info_empty_message(self):
        """Test print_info with empty message."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_info("")
            mock_print.assert_called_once()


class TestPrintStep:
    """Tests for print_step function."""

    def test_print_step(self):
        """Test print_step outputs message."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_step("Running task")
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "Running task" in call_args

    def test_print_step_empty_message(self):
        """Test print_step with empty message."""
        ui.configure()
        with patch.object(ui.console, 'print') as mock_print:
            ui.print_step("")
            mock_print.assert_called_once()


class TestCreateTable:
    """Tests for create_table function."""

    def test_create_table_single_column(self):
        """Test create_table with single column."""
        table = ui.create_table(["Name"])
        assert isinstance(table, Table)
        assert table.title is None

    def test_create_table_multiple_columns(self):
        """Test create_table with multiple columns."""
        columns = ["Name", "Age", "City"]
        table = ui.create_table(columns)
        assert isinstance(table, Table)
        assert len(table.columns) == 3

    def test_create_table_with_title(self):
        """Test create_table with title."""
        table = ui.create_table(["Name"], title="People")
        assert isinstance(table, Table)
        assert table.title == "People"

    def test_create_table_empty_columns(self):
        """Test create_table with empty columns list."""
        table = ui.create_table([])
        assert isinstance(table, Table)
        assert len(table.columns) == 0

    def test_create_table_header_style(self):
        """Test create_table has correct header style."""
        table = ui.create_table(["Header"])
        assert table.header_style == "bold cyan"

    def test_create_table_border_style(self):
        """Test create_table has correct border style."""
        table = ui.create_table(["Header"])
        assert table.border_style == "dim"


class TestSpinner:
    """Tests for spinner function."""

    def test_spinner_returns_status(self):
        """Test spinner returns a Status context manager."""
        ui.configure()
        result = ui.spinner("Loading")
        assert isinstance(result, Status)

    def test_spinner_message(self):
        """Test spinner passes message correctly."""
        ui.configure()
        with patch.object(ui.console, 'status') as mock_status:
            mock_status.return_value = MagicMock()
            ui.spinner("Processing")
            mock_status.assert_called_once()
            call_args = mock_status.call_args[0][0]
            assert "Processing" in call_args

    def test_spinner_empty_message(self):
        """Test spinner with empty message."""
        ui.configure()
        result = ui.spinner("")
        assert isinstance(result, Status)


class TestConfirm:
    """Tests for confirm function."""

    def test_confirm_yes_lowercase(self):
        """Test confirm returns True for 'y' input."""
        ui.configure()
        with patch.object(ui.console, 'input', return_value='y'):
            result = ui.confirm("Continue?")
            assert result is True

    def test_confirm_yes_uppercase(self):
        """Test confirm returns True for 'Y' input."""
        ui.configure()
        with patch.object(ui.console, 'input', return_value='Y'):
            result = ui.confirm("Continue?")
            assert result is True

    def test_confirm_no_default(self):
        """Test confirm returns False for 'n' input."""
        ui.configure()
        with patch.object(ui.console, 'input', return_value='n'):
            result = ui.confirm("Continue?")
            assert result is False

    def test_confirm_empty_input(self):
        """Test confirm returns False for empty input."""
        ui.configure()
        with patch.object(ui.console, 'input', return_value=''):
            result = ui.confirm("Continue?")
            assert result is False

    def test_confirm_other_input(self):
        """Test confirm returns False for other input."""
        ui.configure()
        with patch.object(ui.console, 'input', return_value='maybe'):
            result = ui.confirm("Continue?")
            assert result is False

    def test_confirm_question_format(self):
        """Test confirm formats question correctly."""
        ui.configure()
        with patch.object(ui.console, 'input', return_value='n'):
            ui.confirm("Do you want to proceed?")
            call_args = ui.console.input.call_args[0][0]
            assert "Do you want to proceed?" in call_args
            assert "[y/N]" in call_args


class TestModuleExports:
    """Tests for module-level exports."""

    def test_console_exported(self):
        """Test that console object is exported."""
        assert hasattr(ui, 'console')
        assert ui.console is not None

    def test_panel_exported(self):
        """Test that Panel is available for import."""
        from specsoloist.ui import Panel
        assert Panel is not None

    def test_theme_exported(self):
        """Test that theme is available."""
        assert hasattr(ui, 'theme')
        assert ui.theme is not None


class TestIntegration:
    """Integration tests for UI module."""

    def test_configure_then_functions(self):
        """Test configuring then using functions."""
        ui.configure(quiet=True)
        with patch.object(ui.console, 'print'):
            ui.print_success("Works")
            assert ui.is_quiet() is True

    def test_json_mode_affects_console(self):
        """Test that JSON mode affects console behavior."""
        ui.configure(json_mode=True)
        # In JSON mode, console should be set to quiet
        assert ui.is_json_mode() is True

    def test_quiet_mode_affects_console(self):
        """Test that quiet mode affects console behavior."""
        ui.configure(quiet=True)
        assert ui.is_quiet() is True

    def test_print_functions_are_callable(self):
        """Test that all print functions are callable."""
        ui.configure()
        callables = [
            ui.print_header,
            ui.print_success,
            ui.print_error,
            ui.print_warning,
            ui.print_info,
            ui.print_step,
        ]
        for func in callables:
            assert callable(func)

    def test_create_table_is_reusable(self):
        """Test that created tables can be reused and modified."""
        ui.configure()
        table = ui.create_table(["Name", "Value"])
        assert len(table.columns) == 2
        # Table should support add_row
        assert hasattr(table, 'add_row')
