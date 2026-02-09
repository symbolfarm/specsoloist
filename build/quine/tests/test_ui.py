"""
Tests for ui module.

Tests all public API functions and their behaviors including edge cases.
"""

import pytest
from io import StringIO
from unittest.mock import patch, MagicMock, call
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.status import Status

# Import the module under test
import sys
from pathlib import Path

# Add src to path to import the module
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from specsoloist.ui import (
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_step,
    create_table,
    spinner,
    confirm,
    console,
    Panel as ExportedPanel,
)


class TestPrintHeader:
    """Tests for print_header function."""

    def test_print_header_with_title_only(self):
        """Test printing header with only title."""
        with patch.object(console, 'print') as mock_print:
            print_header("Test Title")
            # Should call print 3 times (newline, panel, newline)
            assert mock_print.call_count == 3
            # Second call should be the Panel with the title
            panel_call = mock_print.call_args_list[1]
            panel_arg = panel_call[0][0]
            assert isinstance(panel_arg, Panel)

    def test_print_header_with_title_and_subtitle(self):
        """Test printing header with both title and subtitle."""
        with patch.object(console, 'print') as mock_print:
            print_header("Test Title", "Test Subtitle")
            assert mock_print.call_count == 3
            panel_call = mock_print.call_args_list[1]
            panel_arg = panel_call[0][0]
            assert isinstance(panel_arg, Panel)

    def test_print_header_with_none_subtitle(self):
        """Test printing header with None subtitle."""
        with patch.object(console, 'print') as mock_print:
            print_header("Test Title", None)
            assert mock_print.call_count == 3
            panel_call = mock_print.call_args_list[1]
            panel_arg = panel_call[0][0]
            assert isinstance(panel_arg, Panel)

    def test_print_header_with_empty_subtitle(self):
        """Test printing header with empty string subtitle."""
        with patch.object(console, 'print') as mock_print:
            print_header("Test Title", "")
            assert mock_print.call_count == 3


class TestPrintSuccess:
    """Tests for print_success function."""

    def test_print_success_basic(self):
        """Test printing success message."""
        with patch.object(console, 'print') as mock_print:
            print_success("Operation completed")
            mock_print.assert_called_once()
            call_arg = mock_print.call_args[0][0]
            assert "✔" in call_arg
            assert "Operation completed" in call_arg

    def test_print_success_empty_message(self):
        """Test printing success with empty message."""
        with patch.object(console, 'print') as mock_print:
            print_success("")
            mock_print.assert_called_once()

    def test_print_success_with_special_chars(self):
        """Test printing success with special characters."""
        with patch.object(console, 'print') as mock_print:
            print_success("File: /path/to/file.txt [DONE]")
            mock_print.assert_called_once()


class TestPrintError:
    """Tests for print_error function."""

    def test_print_error_basic(self):
        """Test printing error message."""
        with patch.object(console, 'print') as mock_print:
            print_error("Something went wrong")
            mock_print.assert_called_once()
            call_arg = mock_print.call_args[0][0]
            assert "✖" in call_arg
            assert "Error:" in call_arg
            assert "Something went wrong" in call_arg

    def test_print_error_empty_message(self):
        """Test printing error with empty message."""
        with patch.object(console, 'print') as mock_print:
            print_error("")
            mock_print.assert_called_once()

    def test_print_error_with_traceback_info(self):
        """Test printing error with traceback information."""
        with patch.object(console, 'print') as mock_print:
            print_error("Error at line 42: ValueError")
            mock_print.assert_called_once()


class TestPrintWarning:
    """Tests for print_warning function."""

    def test_print_warning_basic(self):
        """Test printing warning message."""
        with patch.object(console, 'print') as mock_print:
            print_warning("This might be deprecated")
            mock_print.assert_called_once()
            call_arg = mock_print.call_args[0][0]
            assert "!" in call_arg
            assert "Warning:" in call_arg
            assert "This might be deprecated" in call_arg

    def test_print_warning_empty_message(self):
        """Test printing warning with empty message."""
        with patch.object(console, 'print') as mock_print:
            print_warning("")
            mock_print.assert_called_once()

    def test_print_warning_with_details(self):
        """Test printing warning with detailed message."""
        with patch.object(console, 'print') as mock_print:
            print_warning("Using default value for config.timeout")
            mock_print.assert_called_once()


class TestPrintInfo:
    """Tests for print_info function."""

    def test_print_info_basic(self):
        """Test printing info message."""
        with patch.object(console, 'print') as mock_print:
            print_info("Processing started")
            mock_print.assert_called_once()
            call_arg = mock_print.call_args[0][0]
            assert "ℹ" in call_arg
            assert "Processing started" in call_arg

    def test_print_info_empty_message(self):
        """Test printing info with empty message."""
        with patch.object(console, 'print') as mock_print:
            print_info("")
            mock_print.assert_called_once()

    def test_print_info_with_details(self):
        """Test printing info with detailed message."""
        with patch.object(console, 'print') as mock_print:
            print_info("Build version: 1.2.3")
            mock_print.assert_called_once()


class TestPrintStep:
    """Tests for print_step function."""

    def test_print_step_basic(self):
        """Test printing step message."""
        with patch.object(console, 'print') as mock_print:
            print_step("Building module")
            mock_print.assert_called_once()
            call_arg = mock_print.call_args[0][0]
            assert "→" in call_arg
            assert "Building module" in call_arg

    def test_print_step_empty_message(self):
        """Test printing step with empty message."""
        with patch.object(console, 'print') as mock_print:
            print_step("")
            mock_print.assert_called_once()

    def test_print_step_with_details(self):
        """Test printing step with detailed message."""
        with patch.object(console, 'print') as mock_print:
            print_step("Compiling spec: config.spec.md")
            mock_print.assert_called_once()


class TestCreateTable:
    """Tests for create_table function."""

    def test_create_table_single_column(self):
        """Test creating table with single column."""
        table = create_table(["Name"])
        assert isinstance(table, Table)
        assert table.title is None

    def test_create_table_multiple_columns(self):
        """Test creating table with multiple columns."""
        columns = ["Name", "Status", "Path"]
        table = create_table(columns)
        assert isinstance(table, Table)
        # Table should have the columns added
        assert len(table.columns) == 3

    def test_create_table_with_title(self):
        """Test creating table with title."""
        table = create_table(["ID", "Value"], title="Results")
        assert isinstance(table, Table)
        assert table.title == "Results"

    def test_create_table_without_title(self):
        """Test creating table without title (explicit None)."""
        table = create_table(["Column1", "Column2"], title=None)
        assert isinstance(table, Table)
        assert table.title is None

    def test_create_table_empty_columns(self):
        """Test creating table with empty column list."""
        table = create_table([])
        assert isinstance(table, Table)
        assert len(table.columns) == 0

    def test_create_table_add_row(self):
        """Test that returned table can add rows."""
        table = create_table(["Name", "Value"])
        table.add_row("Item1", "42")
        # If we can add a row without error, the table is usable
        assert len(table.rows) == 1

    def test_create_table_special_column_names(self):
        """Test creating table with special column names."""
        columns = ["Status ✓", "Error ✖", "Path [rel]"]
        table = create_table(columns)
        assert isinstance(table, Table)
        assert len(table.columns) == 3


class TestSpinner:
    """Tests for spinner function."""

    def test_spinner_returns_status_object(self):
        """Test that spinner returns a Status context manager."""
        result = spinner("Loading...")
        assert isinstance(result, Status)

    def test_spinner_message_in_context(self):
        """Test spinner with different messages."""
        result = spinner("Compiling specs")
        assert isinstance(result, Status)

    def test_spinner_empty_message(self):
        """Test spinner with empty message."""
        result = spinner("")
        assert isinstance(result, Status)

    def test_spinner_can_be_used_as_context_manager(self):
        """Test that spinner result can be used as context manager."""
        with spinner("Testing") as status:
            # Just entering and exiting should work
            pass
        # If we get here without exception, the context manager works

    def test_spinner_special_message(self):
        """Test spinner with special characters in message."""
        result = spinner("Building [config, resolver, manifest]...")
        assert isinstance(result, Status)


class TestConfirm:
    """Tests for confirm function."""

    def test_confirm_user_enters_y(self):
        """Test confirm returns True when user enters 'y'."""
        with patch.object(console, 'input', return_value='y'):
            result = confirm("Continue?")
            assert result is True

    def test_confirm_user_enters_Y(self):
        """Test confirm returns True when user enters 'Y'."""
        with patch.object(console, 'input', return_value='Y'):
            result = confirm("Continue?")
            assert result is True

    def test_confirm_user_enters_n(self):
        """Test confirm returns False when user enters 'n'."""
        with patch.object(console, 'input', return_value='n'):
            result = confirm("Continue?")
            assert result is False

    def test_confirm_user_enters_N(self):
        """Test confirm returns False when user enters 'N'."""
        with patch.object(console, 'input', return_value='N'):
            result = confirm("Continue?")
            assert result is False

    def test_confirm_user_enters_empty_string(self):
        """Test confirm returns False when user enters empty string."""
        with patch.object(console, 'input', return_value=''):
            result = confirm("Continue?")
            assert result is False

    def test_confirm_user_enters_yes(self):
        """Test confirm returns False when user enters 'yes' (only 'y' accepted)."""
        with patch.object(console, 'input', return_value='yes'):
            result = confirm("Continue?")
            assert result is False

    def test_confirm_user_enters_no(self):
        """Test confirm returns False when user enters 'no'."""
        with patch.object(console, 'input', return_value='no'):
            result = confirm("Continue?")
            assert result is False

    def test_confirm_question_in_prompt(self):
        """Test that confirm passes question to input."""
        with patch.object(console, 'input', return_value='n') as mock_input:
            confirm("Delete all files?")
            mock_input.assert_called_once()
            prompt = mock_input.call_args[0][0]
            assert "Delete all files?" in prompt
            assert "[y/N]" in prompt

    def test_confirm_with_different_questions(self):
        """Test confirm with various question formats."""
        test_questions = [
            "Proceed?",
            "Are you sure?",
            "Deploy to production?",
        ]
        with patch.object(console, 'input', return_value='n'):
            for question in test_questions:
                result = confirm(question)
                assert result is False


class TestConsoleExport:
    """Tests for exported console object."""

    def test_console_is_available(self):
        """Test that console object is exported."""
        assert console is not None
        assert isinstance(console, Console)

    def test_console_is_functional(self):
        """Test that console object is functional."""
        # Console should be usable for output
        with patch.object(console, 'print') as mock_print:
            console.print("test")
            mock_print.assert_called_once()


class TestPanelExport:
    """Tests for exported Panel class."""

    def test_panel_class_is_available(self):
        """Test that Panel class is exported."""
        assert ExportedPanel is not None
        assert ExportedPanel is Panel


class TestReturnTypes:
    """Tests for function return types."""

    def test_print_header_returns_none(self):
        """Test that print_header returns None."""
        with patch.object(console, 'print'):
            result = print_header("Title")
            assert result is None

    def test_print_success_returns_none(self):
        """Test that print_success returns None."""
        with patch.object(console, 'print'):
            result = print_success("Message")
            assert result is None

    def test_print_error_returns_none(self):
        """Test that print_error returns None."""
        with patch.object(console, 'print'):
            result = print_error("Message")
            assert result is None

    def test_print_warning_returns_none(self):
        """Test that print_warning returns None."""
        with patch.object(console, 'print'):
            result = print_warning("Message")
            assert result is None

    def test_print_info_returns_none(self):
        """Test that print_info returns None."""
        with patch.object(console, 'print'):
            result = print_info("Message")
            assert result is None

    def test_print_step_returns_none(self):
        """Test that print_step returns None."""
        with patch.object(console, 'print'):
            result = print_step("Message")
            assert result is None

    def test_create_table_returns_table(self):
        """Test that create_table returns Table."""
        result = create_table(["Col"])
        assert isinstance(result, Table)

    def test_spinner_returns_status(self):
        """Test that spinner returns Status."""
        result = spinner("Message")
        assert isinstance(result, Status)

    def test_confirm_returns_bool(self):
        """Test that confirm returns bool."""
        with patch.object(console, 'input', return_value='y'):
            result = confirm("Question?")
            assert isinstance(result, bool)


class TestStatelessBehavior:
    """Tests for stateless behavior (no side effects beyond terminal output)."""

    def test_multiple_calls_independent(self):
        """Test that multiple function calls don't interfere."""
        with patch.object(console, 'print') as mock_print:
            print_info("First")
            print_info("Second")
            assert mock_print.call_count == 2

    def test_no_state_modification(self):
        """Test that functions don't modify shared state."""
        with patch.object(console, 'print'):
            print_success("Test1")
            table1 = create_table(["A"])
            print_success("Test2")
            table2 = create_table(["B"])
            # Tables should be independent
            assert table1 is not table2


class TestIntegration:
    """Integration tests for typical usage patterns."""

    def test_build_and_print_table(self):
        """Test typical usage: create table, add rows, print."""
        with patch.object(console, 'print'):
            table = create_table(["Module", "Status"])
            table.add_row("config", "✓")
            table.add_row("resolver", "✓")
            # Should not raise any exceptions
            assert len(table.rows) == 2

    def test_typical_build_flow(self):
        """Test typical build status flow."""
        with patch.object(console, 'print') as mock_print:
            with patch.object(console, 'input', return_value='y'):
                print_header("Building SpecSoloist", "Phase 6")
                print_step("Compiling config")
                print_success("config compiled")
                confirmed = confirm("Continue?")
                assert confirmed is True
                print_step("Compiling resolver")
                print_success("resolver compiled")
                assert mock_print.call_count >= 5  # At least 5 print calls

    def test_error_reporting_flow(self):
        """Test typical error reporting flow."""
        with patch.object(console, 'print'):
            print_header("Build Results")
            print_error("Failed to compile ui module")
            print_warning("Some tests may have been skipped")
            print_info("Check the logs for details")
