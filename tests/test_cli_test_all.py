"""Tests for `sp test --all` command."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from specsoloist.cli import cmd_test_all
from specsoloist.manifest import BuildManifest, SpecBuildInfo


def _make_core(specs, manifest_specs=None):
    """Build a minimal mock core."""
    core = MagicMock()
    core.list_specs.return_value = specs

    manifest = BuildManifest()
    for name, files in (manifest_specs or {}).items():
        manifest.update_spec(name, "hash", [], files)
    core._get_manifest.return_value = manifest

    core.run_tests.return_value = {"success": True, "output": ""}
    return core


@patch("specsoloist.cli._resolve_arrangement", return_value=None)
@patch("specsoloist.cli._apply_arrangement")
class TestTestAll:
    def test_no_specs_returns_without_error(self, _apply, _resolve, capsys):
        core = _make_core([])
        cmd_test_all(core)  # should not raise

    def test_no_compiled_specs_shows_no_build(self, _apply, _resolve, capsys):
        core = _make_core(
            ["foo.spec.md"],
            manifest_specs={"foo": ["/nonexistent/foo.py"]},
        )
        cmd_test_all(core)
        core.run_tests.assert_not_called()

    def test_no_manifest_entry_shows_no_build(self, _apply, _resolve):
        core = _make_core(["foo.spec.md"], manifest_specs={})
        cmd_test_all(core)
        core.run_tests.assert_not_called()

    def test_passing_specs_exit_0(self, _apply, _resolve, tmp_path):
        impl = tmp_path / "foo.py"
        impl.write_text("# impl")
        core = _make_core(
            ["foo.spec.md"],
            manifest_specs={"foo": [str(impl)]},
        )
        core.run_tests.return_value = {"success": True, "output": ""}
        cmd_test_all(core)  # should not sys.exit

    def test_failing_spec_exits_1(self, _apply, _resolve, tmp_path):
        impl = tmp_path / "bar.py"
        impl.write_text("# impl")
        core = _make_core(
            ["bar.spec.md"],
            manifest_specs={"bar": [str(impl)]},
        )
        core.run_tests.return_value = {"success": False, "output": "FAIL"}
        with pytest.raises(SystemExit) as exc:
            cmd_test_all(core)
        assert exc.value.code == 1


class TestTestParser:
    def test_no_args_exits_1(self):
        """sp test with no name and no --all should exit 1."""
        from specsoloist.cli import main
        with patch("sys.argv", ["sp", "test"]):
            with pytest.raises(SystemExit) as exc:
                main()
        assert exc.value.code == 1
