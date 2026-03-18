"""Tests for the ui module."""

import pytest
from unittest.mock import patch, MagicMock

import specsoloist.ui as ui


class TestConfigure:
    def setup_method(self):
        """Reset ui state before each test."""
        ui.configure(quiet=False, json_mode=False)

    def test_default_state(self):
        assert ui.is_quiet() is False
        assert ui.is_json_mode() is False

    def test_quiet_mode(self):
        ui.configure(quiet=True)
        assert ui.is_quiet() is True
        assert ui.is_json_mode() is False

    def test_json_mode(self):
        ui.configure(json_mode=True)
        assert ui.is_json_mode() is True
        assert ui.is_quiet() is False

    def test_both_modes(self):
        ui.configure(quiet=True, json_mode=True)
        assert ui.is_quiet() is True
        assert ui.is_json_mode() is True


class TestPrintFunctions:
    def setup_method(self):
        ui.configure(quiet=False, json_mode=False)

    def test_print_success_does_not_raise(self):
        ui.print_success("All good")

    def test_print_error_does_not_raise(self):
        ui.print_error("Something failed")

    def test_print_warning_does_not_raise(self):
        ui.print_warning("Watch out")

    def test_print_info_does_not_raise(self):
        ui.print_info("FYI")

    def test_print_step_does_not_raise(self):
        ui.print_step("Doing step 1")

    def test_print_header_does_not_raise(self):
        ui.print_header("Title")

    def test_print_header_with_subtitle(self):
        ui.print_header("Title", subtitle="Subtitle")

    def test_quiet_mode_suppresses_most_output(self):
        ui.configure(quiet=True)
        # These should not raise even in quiet mode
        ui.print_success("msg")
        ui.print_info("msg")
        ui.print_step("msg")

    def test_error_shown_even_in_quiet_mode(self):
        ui.configure(quiet=True)
        # Errors should still work
        ui.print_error("critical error")

    def test_json_mode_suppresses_rich_output(self):
        ui.configure(json_mode=True)
        # Should not raise
        ui.print_success("msg")
        ui.print_info("msg")


class TestCreateTable:
    def test_basic_table(self):
        table = ui.create_table(["Column A", "Column B"])
        assert table is not None
        # Should be able to add rows
        table.add_row("val1", "val2")

    def test_table_with_title(self):
        table = ui.create_table(["Name", "Value"], title="My Table")
        assert table is not None


class TestSpinner:
    def test_spinner_returns_context_manager(self):
        ctx = ui.spinner("Working...")
        assert ctx is not None
        # Should work as context manager
        with ctx:
            pass


class TestConfirm:
    def test_confirm_yes(self):
        with patch("builtins.input", return_value="y"):
            assert ui.confirm("Are you sure?") is True

    def test_confirm_no(self):
        with patch("builtins.input", return_value="n"):
            assert ui.confirm("Are you sure?") is False

    def test_confirm_empty(self):
        with patch("builtins.input", return_value=""):
            assert ui.confirm("Are you sure?") is False

    def test_confirm_uppercase_y(self):
        with patch("builtins.input", return_value="Y"):
            assert ui.confirm("Are you sure?") is True

    def test_confirm_uppercase_n(self):
        with patch("builtins.input", return_value="N"):
            assert ui.confirm("Are you sure?") is False


class TestModuleExports:
    def test_console_exported(self):
        assert hasattr(ui, "console")

    def test_panel_exported(self):
        assert hasattr(ui, "Panel")
