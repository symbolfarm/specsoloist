"""Tests for the manifest module."""

import json
import os
import pytest

from specsoloist.manifest import (
    BuildManifest,
    IncrementalBuilder,
    SpecBuildInfo,
    compute_content_hash,
    compute_file_hash,
)


class TestSpecBuildInfo:
    def test_creation(self):
        info = SpecBuildInfo(
            spec_hash="abc123",
            built_at="2024-01-01T00:00:00+00:00",
            dependencies=["dep1"],
            output_files=["src/foo.py"],
        )
        assert info.spec_hash == "abc123"
        assert info.dependencies == ["dep1"]

    def test_to_dict_round_trip(self):
        info = SpecBuildInfo(
            spec_hash="abc123",
            built_at="2024-01-01T00:00:00+00:00",
            dependencies=["dep1", "dep2"],
            output_files=["src/foo.py", "tests/test_foo.py"],
        )
        d = info.to_dict()
        restored = SpecBuildInfo.from_dict(d)
        assert restored.spec_hash == info.spec_hash
        assert restored.built_at == info.built_at
        assert restored.dependencies == info.dependencies
        assert restored.output_files == info.output_files

    def test_from_dict_missing_optional(self):
        d = {
            "spec_hash": "abc",
            "built_at": "2024-01-01T00:00:00+00:00",
        }
        info = SpecBuildInfo.from_dict(d)
        assert info.dependencies == []
        assert info.output_files == []


class TestBuildManifest:
    def test_default_creation(self):
        manifest = BuildManifest()
        assert manifest.version == "1.0"
        assert manifest.specs == {}

    def test_get_spec_info_missing(self):
        manifest = BuildManifest()
        assert manifest.get_spec_info("nonexistent") is None

    def test_update_and_get_spec(self):
        manifest = BuildManifest()
        manifest.update_spec(
            "myspec",
            spec_hash="abc123",
            dependencies=["dep1"],
            output_files=["src/myspec.py"],
        )
        info = manifest.get_spec_info("myspec")
        assert info is not None
        assert info.spec_hash == "abc123"
        assert info.dependencies == ["dep1"]

    def test_update_sets_timestamp(self):
        manifest = BuildManifest()
        manifest.update_spec("myspec", "abc", [], [])
        info = manifest.get_spec_info("myspec")
        assert info.built_at is not None
        assert len(info.built_at) > 0

    def test_remove_spec(self):
        manifest = BuildManifest()
        manifest.update_spec("myspec", "abc", [], [])
        manifest.remove_spec("myspec")
        assert manifest.get_spec_info("myspec") is None

    def test_remove_nonexistent_ok(self):
        manifest = BuildManifest()
        manifest.remove_spec("nonexistent")  # Should not raise

    def test_save_and_load(self, tmp_path):
        manifest = BuildManifest()
        manifest.update_spec("foo", "hash1", ["bar"], ["src/foo.py"])

        manifest.save(str(tmp_path))

        loaded = BuildManifest.load(str(tmp_path))
        assert loaded.version == "1.0"
        info = loaded.get_spec_info("foo")
        assert info is not None
        assert info.spec_hash == "hash1"

    def test_load_missing_file_returns_empty(self, tmp_path):
        manifest = BuildManifest.load(str(tmp_path))
        assert manifest.specs == {}

    def test_load_corrupted_json_returns_empty(self, tmp_path):
        path = tmp_path / ".specsoloist-manifest.json"
        path.write_text("not valid json{{{")
        manifest = BuildManifest.load(str(tmp_path))
        assert manifest.specs == {}

    def test_manifest_file_location(self, tmp_path):
        manifest = BuildManifest()
        manifest.save(str(tmp_path))
        expected = tmp_path / ".specsoloist-manifest.json"
        assert expected.exists()


class TestIncrementalBuilder:
    def test_needs_rebuild_never_built(self):
        manifest = BuildManifest()
        builder = IncrementalBuilder(manifest=manifest, src_dir="src")
        assert builder.needs_rebuild("foo", "hash1", [], set()) is True

    def test_needs_rebuild_hash_changed(self):
        manifest = BuildManifest()
        manifest.update_spec("foo", "old_hash", [], [])
        builder = IncrementalBuilder(manifest=manifest, src_dir="src")
        assert builder.needs_rebuild("foo", "new_hash", [], set()) is True

    def test_needs_rebuild_deps_changed(self):
        manifest = BuildManifest()
        manifest.update_spec("foo", "hash1", [], [])
        builder = IncrementalBuilder(manifest=manifest, src_dir="src")
        # Deps changed from [] to ["bar"]
        assert builder.needs_rebuild("foo", "hash1", ["bar"], set()) is True

    def test_needs_rebuild_dep_rebuilt(self):
        manifest = BuildManifest()
        manifest.update_spec("foo", "hash1", ["bar"], [])
        builder = IncrementalBuilder(manifest=manifest, src_dir="src")
        # bar was rebuilt this cycle
        assert builder.needs_rebuild("foo", "hash1", ["bar"], {"bar"}) is True

    def test_no_rebuild_needed(self):
        manifest = BuildManifest()
        manifest.update_spec("foo", "hash1", ["bar"], [])
        builder = IncrementalBuilder(manifest=manifest, src_dir="src")
        assert builder.needs_rebuild("foo", "hash1", ["bar"], set()) is False

    def test_get_rebuild_plan_all_new(self):
        manifest = BuildManifest()
        builder = IncrementalBuilder(manifest=manifest, src_dir="src")
        plan = builder.get_rebuild_plan(
            build_order=["a", "b", "c"],
            spec_hashes={"a": "h1", "b": "h2", "c": "h3"},
            spec_deps={"a": [], "b": ["a"], "c": ["b"]},
        )
        assert plan == ["a", "b", "c"]

    def test_get_rebuild_plan_nothing_changed(self):
        manifest = BuildManifest()
        manifest.update_spec("a", "h1", [], [])
        manifest.update_spec("b", "h2", ["a"], [])
        manifest.update_spec("c", "h3", ["b"], [])
        builder = IncrementalBuilder(manifest=manifest, src_dir="src")
        plan = builder.get_rebuild_plan(
            build_order=["a", "b", "c"],
            spec_hashes={"a": "h1", "b": "h2", "c": "h3"},
            spec_deps={"a": [], "b": ["a"], "c": ["b"]},
        )
        assert plan == []

    def test_get_rebuild_plan_cascades(self):
        manifest = BuildManifest()
        manifest.update_spec("a", "h1", [], [])
        manifest.update_spec("b", "h2", ["a"], [])
        manifest.update_spec("c", "h3", ["b"], [])
        builder = IncrementalBuilder(manifest=manifest, src_dir="src")
        # "a" changed, so b and c must also rebuild
        plan = builder.get_rebuild_plan(
            build_order=["a", "b", "c"],
            spec_hashes={"a": "new_hash", "b": "h2", "c": "h3"},
            spec_deps={"a": [], "b": ["a"], "c": ["b"]},
        )
        assert "a" in plan
        assert "b" in plan
        assert "c" in plan


class TestHashFunctions:
    def test_compute_content_hash(self):
        h = compute_content_hash("hello world")
        assert isinstance(h, str)
        assert len(h) == 64  # SHA-256 hex

    def test_compute_content_hash_deterministic(self):
        h1 = compute_content_hash("test")
        h2 = compute_content_hash("test")
        assert h1 == h2

    def test_compute_content_hash_different(self):
        h1 = compute_content_hash("test1")
        h2 = compute_content_hash("test2")
        assert h1 != h2

    def test_compute_file_hash_missing(self):
        result = compute_file_hash("/nonexistent/path/file.txt")
        assert result == ""

    def test_compute_file_hash_existing(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        h = compute_file_hash(str(f))
        assert isinstance(h, str)
        assert len(h) == 64

    def test_compute_file_hash_deterministic(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world")
        h1 = compute_file_hash(str(f))
        h2 = compute_file_hash(str(f))
        assert h1 == h2
