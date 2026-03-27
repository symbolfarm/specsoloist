"""Tests for the build manifest and incremental builds."""

import pytest
import os
import shutil

from specsoloist.manifest import (
    BuildManifest,
    IncrementalBuilder,
    compute_content_hash,
    compute_file_hash,
)


@pytest.fixture
def test_dir():
    """Sets up a temporary directory for testing."""
    dir_path = "test_manifest_env"
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)

    yield dir_path

    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)


def test_compute_content_hash():
    """Test that content hashing is consistent."""
    content = "Hello, World!"
    hash1 = compute_content_hash(content)
    hash2 = compute_content_hash(content)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 produces 64 hex chars

    # Different content should produce different hash
    hash3 = compute_content_hash("Different content")
    assert hash3 != hash1


def test_compute_file_hash(test_dir):
    """Test file hashing."""
    path = os.path.join(test_dir, "test.txt")
    with open(path, 'w') as f:
        f.write("Test content")

    hash1 = compute_file_hash(path)
    assert len(hash1) == 64

    # Non-existent file returns empty string
    assert compute_file_hash("/nonexistent/path") == ""


def test_manifest_save_and_load(test_dir):
    """Test manifest persistence."""
    manifest = BuildManifest()
    manifest.update_spec(
        name="types",
        spec_hash="abc123",
        dependencies=[],
        output_files=["types.py"]
    )
    manifest.update_spec(
        name="service",
        spec_hash="def456",
        dependencies=["types"],
        output_files=["service.py", "test_service.py"]
    )

    # Save
    manifest.save(test_dir)

    # Verify file exists
    manifest_path = os.path.join(test_dir, ".specsoloist-manifest.json")
    assert os.path.exists(manifest_path)

    # Load
    loaded = BuildManifest.load(test_dir)

    # Verify content
    assert loaded.get_spec_info("types").spec_hash == "abc123"
    assert loaded.get_spec_info("service").dependencies == ["types"]
    assert "test_service.py" in loaded.get_spec_info("service").output_files


def test_manifest_load_nonexistent(test_dir):
    """Test loading manifest when file doesn't exist."""
    manifest = BuildManifest.load(test_dir)
    assert manifest.specs == {}


def test_manifest_load_corrupted(test_dir):
    """Test loading manifest when file is corrupted."""
    path = os.path.join(test_dir, ".specsoloist-manifest.json")
    with open(path, 'w') as f:
        f.write("not valid json")

    manifest = BuildManifest.load(test_dir)
    assert manifest.specs == {}


def test_incremental_builder_needs_rebuild_never_built():
    """Test that specs never built always need rebuilding."""
    manifest = BuildManifest()
    builder = IncrementalBuilder(manifest, "/fake/path")

    assert builder.needs_rebuild("new_spec", "hash123", [], set()) is True


def test_incremental_builder_needs_rebuild_hash_changed(test_dir):
    """Test that changed spec content triggers rebuild."""
    out_file = os.path.join(test_dir, "spec1.py")
    with open(out_file, "w") as f:
        f.write("# placeholder")

    manifest = BuildManifest()
    manifest.update_spec("spec1", "old_hash", [], [out_file])

    builder = IncrementalBuilder(manifest, "/fake/path")

    # Same hash, output file exists - no rebuild
    assert builder.needs_rebuild("spec1", "old_hash", [], set()) is False

    # Different hash - needs rebuild
    assert builder.needs_rebuild("spec1", "new_hash", [], set()) is True


def test_incremental_builder_needs_rebuild_deps_changed(test_dir):
    """Test that changed dependencies trigger rebuild."""
    out_file = os.path.join(test_dir, "spec1.py")
    with open(out_file, "w") as f:
        f.write("# placeholder")

    manifest = BuildManifest()
    manifest.update_spec("spec1", "hash123", ["dep1"], [out_file])

    builder = IncrementalBuilder(manifest, "/fake/path")

    # Same deps, output file exists - no rebuild
    assert builder.needs_rebuild("spec1", "hash123", ["dep1"], set()) is False

    # Different deps - needs rebuild
    assert builder.needs_rebuild("spec1", "hash123", ["dep1", "dep2"], set()) is True
    assert builder.needs_rebuild("spec1", "hash123", [], set()) is True


def test_incremental_builder_needs_rebuild_dep_rebuilt(test_dir):
    """Test that rebuilding a dependency triggers dependent rebuild."""
    types_file = os.path.join(test_dir, "types.py")
    service_file = os.path.join(test_dir, "service.py")
    for f in (types_file, service_file):
        with open(f, "w") as fh:
            fh.write("# placeholder")

    manifest = BuildManifest()
    manifest.update_spec("types", "hash1", [], [types_file])
    manifest.update_spec("service", "hash2", ["types"], [service_file])

    builder = IncrementalBuilder(manifest, "/fake/path")

    # If types was rebuilt, service needs rebuilding too
    rebuilt = {"types"}
    assert builder.needs_rebuild("service", "hash2", ["types"], rebuilt) is True

    # If nothing rebuilt and output files exist, service doesn't need rebuilding
    assert builder.needs_rebuild("service", "hash2", ["types"], set()) is False


def test_incremental_builder_needs_rebuild_output_missing(test_dir):
    """Test that a missing output file triggers rebuild even when hash is unchanged."""
    missing_file = os.path.join(test_dir, "nonexistent.py")

    manifest = BuildManifest()
    manifest.update_spec("spec1", "hash123", [], [missing_file])

    builder = IncrementalBuilder(manifest, "/fake/path")

    # Output file does not exist on disk — must rebuild
    assert builder.needs_rebuild("spec1", "hash123", [], set()) is True


def test_incremental_builder_rebuild_plan(test_dir):
    """Test computing the full rebuild plan."""
    types_file = os.path.join(test_dir, "types.py")
    utils_file = os.path.join(test_dir, "utils.py")
    service_file = os.path.join(test_dir, "service.py")
    for f in (types_file, utils_file, service_file):
        with open(f, "w") as fh:
            fh.write("# placeholder")

    manifest = BuildManifest()
    manifest.update_spec("types", "hash1", [], [types_file])
    manifest.update_spec("utils", "hash2", [], [utils_file])
    manifest.update_spec("service", "hash3", ["types", "utils"], [service_file])

    builder = IncrementalBuilder(manifest, "/fake/path")

    build_order = ["types", "utils", "service"]

    # No changes, all output files exist - nothing to rebuild
    spec_hashes = {"types": "hash1", "utils": "hash2", "service": "hash3"}
    spec_deps = {"types": [], "utils": [], "service": ["types", "utils"]}

    plan = builder.get_rebuild_plan(build_order, spec_hashes, spec_deps)
    assert plan == []

    # Change types - types and service need rebuild (service depends on types)
    spec_hashes["types"] = "new_hash"
    plan = builder.get_rebuild_plan(build_order, spec_hashes, spec_deps)
    assert "types" in plan
    assert "service" in plan
    assert "utils" not in plan


def test_manifest_remove_spec():
    """Test removing a spec from the manifest."""
    manifest = BuildManifest()
    manifest.update_spec("spec1", "hash1", [], ["spec1.py"])
    manifest.update_spec("spec2", "hash2", [], ["spec2.py"])

    assert manifest.get_spec_info("spec1") is not None

    manifest.remove_spec("spec1")

    assert manifest.get_spec_info("spec1") is None
    assert manifest.get_spec_info("spec2") is not None
