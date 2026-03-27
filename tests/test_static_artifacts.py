"""Integration tests for static artifact copying in the conductor (task 25)."""

import os

import pytest

from specsoloist.schema import (
    Arrangement,
    ArrangementBuildCommands,
    ArrangementOutputPaths,
    ArrangementStatic,
)
from spechestra.conductor import SpecConductor


def _minimal_arrangement(tmp_path, statics: list) -> Arrangement:
    """Build a minimal Arrangement with absolute output paths and given static entries."""
    return Arrangement(
        target_language="python",
        output_paths=ArrangementOutputPaths(
            implementation=str(tmp_path / "src" / "{name}.py"),
            tests=str(tmp_path / "tests" / "test_{name}.py"),
        ),
        build_commands=ArrangementBuildCommands(test="echo test"),
        static=statics,
    )


def test_conductor_copies_static_directory(tmp_path):
    """Conductor copies a declared static directory to the dest after compilation."""
    # Create source directory with a file
    src_dir = tmp_path / "help"
    src_dir.mkdir()
    (src_dir / "guide.md").write_text("# Help Guide")

    dst_dir = tmp_path / "out" / "help"

    arr = _minimal_arrangement(tmp_path, [
        ArrangementStatic(source="help/", dest="out/help/"),
    ])

    conductor = SpecConductor(str(tmp_path))
    conductor._copy_static_artifacts(arr)

    assert (dst_dir / "guide.md").exists()
    assert (dst_dir / "guide.md").read_text() == "# Help Guide"


def test_conductor_copies_static_file(tmp_path):
    """Conductor copies a declared static file to the dest after compilation."""
    src_file = tmp_path / "seed.py"
    src_file.write_text("# seed")

    arr = _minimal_arrangement(tmp_path, [
        ArrangementStatic(source="seed.py", dest="scripts/seed.py"),
    ])

    conductor = SpecConductor(str(tmp_path))
    conductor._copy_static_artifacts(arr)

    assert (tmp_path / "scripts" / "seed.py").exists()
    assert (tmp_path / "scripts" / "seed.py").read_text() == "# seed"


def test_conductor_skips_existing_dest_when_overwrite_false(tmp_path):
    """Conductor skips copying when overwrite=False and destination already exists."""
    src_file = tmp_path / "notes.md"
    src_file.write_text("new content")

    dst_file = tmp_path / "out" / "notes.md"
    dst_file.parent.mkdir(parents=True)
    dst_file.write_text("original content")

    arr = _minimal_arrangement(tmp_path, [
        ArrangementStatic(source="notes.md", dest="out/notes.md", overwrite=False),
    ])

    conductor = SpecConductor(str(tmp_path))
    conductor._copy_static_artifacts(arr)

    assert dst_file.read_text() == "original content"


def test_conductor_overwrites_existing_dest_when_overwrite_true(tmp_path):
    """Conductor overwrites destination when overwrite=True (the default)."""
    src_file = tmp_path / "notes.md"
    src_file.write_text("new content")

    dst_file = tmp_path / "out" / "notes.md"
    dst_file.parent.mkdir(parents=True)
    dst_file.write_text("original content")

    arr = _minimal_arrangement(tmp_path, [
        ArrangementStatic(source="notes.md", dest="out/notes.md", overwrite=True),
    ])

    conductor = SpecConductor(str(tmp_path))
    conductor._copy_static_artifacts(arr)

    assert dst_file.read_text() == "new content"


def test_conductor_warns_on_missing_source_but_does_not_fail(tmp_path, capsys):
    """Conductor warns when a static source path does not exist, but does not raise."""
    arr = _minimal_arrangement(tmp_path, [
        ArrangementStatic(source="nonexistent/", dest="out/nonexistent/"),
    ])

    conductor = SpecConductor(str(tmp_path))
    # Should not raise
    conductor._copy_static_artifacts(arr)

    # The missing dest was not created
    assert not (tmp_path / "out" / "nonexistent").exists()
