"""Tests for --resume and --force flags in sp conduct.

These tests exercise the IncrementalBuilder and the CLI argument parsing
for the conduct subcommand. They do not invoke LLMs — they verify the
skip/recompile decision logic and the CLI wiring.
"""

import argparse
import os
import shutil

import pytest

from specsoloist.manifest import (
    BuildManifest,
    IncrementalBuilder,
    compute_file_hash,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create a temporary directory with placeholder output files."""
    return tmp_path


def _make_output_file(tmp_path, name: str) -> str:
    """Create a dummy output file and return its absolute path."""
    path = str(tmp_path / name)
    with open(path, "w") as f:
        f.write(f"# generated: {name}\n")
    return path


def _make_manifest_with_files(tmp_path, specs: dict) -> BuildManifest:
    """
    Build a manifest whose output files actually exist on disk.

    specs: { spec_name: { "hash": str, "deps": list[str], "files": list[str] } }
          where each file in "files" will be created in tmp_path.
    """
    manifest = BuildManifest()
    for name, info in specs.items():
        files = [_make_output_file(tmp_path, f) for f in info.get("files", [])]
        manifest.update_spec(
            name=name,
            spec_hash=info["hash"],
            dependencies=info.get("deps", []),
            output_files=files,
        )
    return manifest


# ---------------------------------------------------------------------------
# Test: all specs cached (nothing to rebuild)
# ---------------------------------------------------------------------------


def test_resume_all_cached(tmp_output_dir):
    """When all specs are up-to-date, get_rebuild_plan returns an empty list."""
    manifest = _make_manifest_with_files(
        tmp_output_dir,
        {
            "state": {"hash": "h1", "deps": [], "files": ["state.py"]},
            "layout": {"hash": "h2", "deps": ["state"], "files": ["layout.py"]},
            "routes": {"hash": "h3", "deps": ["layout", "state"], "files": ["routes.py"]},
        },
    )

    builder = IncrementalBuilder(manifest, "/fake/src")

    build_order = ["state", "layout", "routes"]
    spec_hashes = {"state": "h1", "layout": "h2", "routes": "h3"}
    spec_deps = {
        "state": [],
        "layout": ["state"],
        "routes": ["layout", "state"],
    }

    plan = builder.get_rebuild_plan(build_order, spec_hashes, spec_deps)
    assert plan == [], f"Expected empty plan, got: {plan}"


# ---------------------------------------------------------------------------
# Test: partial cache (one spec changed)
# ---------------------------------------------------------------------------


def test_resume_partial_cache(tmp_output_dir):
    """When one spec's hash changes, only that spec and its dependents rebuild."""
    manifest = _make_manifest_with_files(
        tmp_output_dir,
        {
            "state": {"hash": "h1", "deps": [], "files": ["state.py"]},
            "layout": {"hash": "h2", "deps": ["state"], "files": ["layout.py"]},
            "routes": {"hash": "h3", "deps": ["layout", "state"], "files": ["routes.py"]},
        },
    )

    builder = IncrementalBuilder(manifest, "/fake/src")

    build_order = ["state", "layout", "routes"]
    # "state" spec changed
    spec_hashes = {"state": "h1_CHANGED", "layout": "h2", "routes": "h3"}
    spec_deps = {
        "state": [],
        "layout": ["state"],
        "routes": ["layout", "state"],
    }

    plan = builder.get_rebuild_plan(build_order, spec_hashes, spec_deps)

    # state must rebuild (hash changed)
    assert "state" in plan
    # layout depends on state → cascade rebuild
    assert "layout" in plan
    # routes depends on layout and state → cascade rebuild
    assert "routes" in plan


# ---------------------------------------------------------------------------
# Test: cascade recompile
# ---------------------------------------------------------------------------


def test_resume_cascade_recompile(tmp_output_dir):
    """A dependency being rebuilt cascades to its dependents, even if their hashes match."""
    manifest = _make_manifest_with_files(
        tmp_output_dir,
        {
            "config": {"hash": "hc", "deps": [], "files": ["config.py"]},
            "resolver": {"hash": "hr", "deps": ["config"], "files": ["resolver.py"]},
            "core": {"hash": "hcore", "deps": ["config", "resolver"], "files": ["core.py"]},
        },
    )

    builder = IncrementalBuilder(manifest, "/fake/src")

    build_order = ["config", "resolver", "core"]
    # only config changed
    spec_hashes = {"config": "hc_CHANGED", "resolver": "hr", "core": "hcore"}
    spec_deps = {
        "config": [],
        "resolver": ["config"],
        "core": ["config", "resolver"],
    }

    plan = builder.get_rebuild_plan(build_order, spec_hashes, spec_deps)

    # All three must rebuild: config (changed), resolver (dep changed), core (dep changed)
    assert "config" in plan
    assert "resolver" in plan
    assert "core" in plan


# ---------------------------------------------------------------------------
# Test: missing output file triggers rebuild
# ---------------------------------------------------------------------------


def test_resume_missing_output_triggers_rebuild(tmp_output_dir):
    """If an output file is deleted, the spec must be recompiled even if hash matches."""
    real_file = _make_output_file(tmp_output_dir, "state.py")
    missing_file = str(tmp_output_dir / "missing.py")  # never created

    manifest = BuildManifest()
    manifest.update_spec("state", "h1", [], [real_file])
    manifest.update_spec("layout", "h2", [], [missing_file])  # output gone

    builder = IncrementalBuilder(manifest, "/fake/src")

    # state: hash matches and file exists → no rebuild
    assert builder.needs_rebuild("state", "h1", [], set()) is False

    # layout: hash matches but output file missing → must rebuild
    assert builder.needs_rebuild("layout", "h2", [], set()) is True


# ---------------------------------------------------------------------------
# Test: --resume and --force are mutually exclusive (CLI argument parsing)
# ---------------------------------------------------------------------------


def test_cli_resume_force_mutually_exclusive():
    """--resume and --force cannot be used together; argparse rejects it."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "specsoloist.cli", "conduct", "--resume", "--force"],
        capture_output=True,
        text=True,
    )
    # argparse returns exit code 2 for argument errors
    assert result.returncode == 2
    assert "not allowed with argument" in result.stderr


# ---------------------------------------------------------------------------
# Test: --resume flag is parsed correctly
# ---------------------------------------------------------------------------


def test_cli_conduct_resume_flag_parsed():
    """Verify the conduct subcommand accepts --resume and sets resume=True."""
    import argparse

    # Re-create just the conduct subparser to test argument parsing in isolation
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    conduct = sub.add_parser("conduct")
    conduct.add_argument("src_dir", nargs="?", default=None)
    conduct.add_argument("--no-agent", action="store_true")
    conduct.add_argument("--auto-accept", action="store_true")
    conduct.add_argument("--incremental", action="store_true")
    conduct.add_argument("--parallel", action="store_true")
    conduct.add_argument("--workers", type=int, default=4)
    conduct.add_argument("--model")
    conduct.add_argument("--arrangement")
    group = conduct.add_mutually_exclusive_group()
    group.add_argument("--resume", action="store_true")
    group.add_argument("--force", action="store_true")

    args = parser.parse_args(["conduct", "--resume"])
    assert args.resume is True
    assert args.force is False

    args = parser.parse_args(["conduct", "--force"])
    assert args.force is True
    assert args.resume is False

    args = parser.parse_args(["conduct"])
    assert args.resume is False
    assert args.force is False
