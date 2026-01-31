"""
Build manifest for tracking spec compilation state.

The manifest tracks file hashes and build metadata to enable
incremental builds (only recompiling changed specs).
"""

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class SpecBuildInfo:
    """Build information for a single spec."""
    spec_hash: str  # Hash of spec file content
    built_at: str  # ISO timestamp of last build
    dependencies: List[str]  # Spec names this depends on
    output_files: List[str]  # Generated file paths (relative to build/)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SpecBuildInfo":
        return cls(**data)


@dataclass
class BuildManifest:
    """
    Tracks build state for incremental compilation.

    Stored as `.specsoloist-manifest.json` in the build directory.
    """
    version: str = "1.0"
    specs: Dict[str, SpecBuildInfo] = field(default_factory=dict)

    MANIFEST_FILENAME = ".specsoloist-manifest.json"

    def get_spec_info(self, name: str) -> Optional[SpecBuildInfo]:
        """Get build info for a spec, or None if never built."""
        return self.specs.get(name)

    def update_spec(
        self,
        name: str,
        spec_hash: str,
        dependencies: List[str],
        output_files: List[str]
    ):
        """Update build info for a spec after successful compilation."""
        self.specs[name] = SpecBuildInfo(
            spec_hash=spec_hash,
            built_at=datetime.utcnow().isoformat(),
            dependencies=dependencies,
            output_files=output_files
        )

    def remove_spec(self, name: str):
        """Remove a spec from the manifest (e.g., if spec file deleted)."""
        if name in self.specs:
            del self.specs[name]

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "specs": {name: info.to_dict() for name, info in self.specs.items()}
        }

    @classmethod
    def from_dict(cls, data: dict) -> "BuildManifest":
        manifest = cls(version=data.get("version", "1.0"))
        for name, info_data in data.get("specs", {}).items():
            manifest.specs[name] = SpecBuildInfo.from_dict(info_data)
        return manifest

    def save(self, build_dir: str):
        """Save manifest to the build directory."""
        path = os.path.join(build_dir, self.MANIFEST_FILENAME)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, build_dir: str) -> "BuildManifest":
        """Load manifest from build directory, or return empty manifest."""
        path = os.path.join(build_dir, cls.MANIFEST_FILENAME)
        if not os.path.exists(path):
            return cls()
        try:
            with open(path, 'r') as f:
                return cls.from_dict(json.load(f))
        except (json.JSONDecodeError, KeyError):
            # Corrupted manifest, start fresh
            return cls()


def compute_file_hash(path: str) -> str:
    """Compute SHA-256 hash of a file's contents."""
    if not os.path.exists(path):
        return ""
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of string content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


class IncrementalBuilder:
    """
    Determines which specs need rebuilding based on changes.
    """

    def __init__(self, manifest: BuildManifest, src_dir: str):
        self.manifest = manifest
        self.src_dir = src_dir

    def needs_rebuild(
        self,
        spec_name: str,
        current_hash: str,
        current_deps: List[str],
        rebuilt_specs: set
    ) -> bool:
        """
        Determine if a spec needs rebuilding.

        A spec needs rebuilding if:
        1. It has never been built (not in manifest)
        2. Its content hash has changed
        3. Its dependencies have changed
        4. Any of its dependencies were rebuilt in this build cycle

        Args:
            spec_name: Name of the spec to check.
            current_hash: Current hash of the spec file.
            current_deps: Current list of dependencies.
            rebuilt_specs: Set of specs already rebuilt in this cycle.

        Returns:
            True if the spec needs rebuilding.
        """
        info = self.manifest.get_spec_info(spec_name)

        # Never built
        if info is None:
            return True

        # Content changed
        if info.spec_hash != current_hash:
            return True

        # Dependencies changed
        if set(info.dependencies) != set(current_deps):
            return True

        # Any dependency was rebuilt
        if any(dep in rebuilt_specs for dep in current_deps):
            return True

        return False

    def get_rebuild_plan(
        self,
        build_order: List[str],
        spec_hashes: Dict[str, str],
        spec_deps: Dict[str, List[str]]
    ) -> List[str]:
        """
        Determine which specs in the build order need rebuilding.

        Processes specs in order, tracking which have been rebuilt
        to properly cascade rebuilds to dependents.

        Args:
            build_order: Specs in topological order.
            spec_hashes: Map of spec name -> current content hash.
            spec_deps: Map of spec name -> list of dependencies.

        Returns:
            List of spec names that need rebuilding, in build order.
        """
        rebuilt = set()
        needs_rebuild = []

        for spec_name in build_order:
            current_hash = spec_hashes.get(spec_name, "")
            current_deps = spec_deps.get(spec_name, [])

            if self.needs_rebuild(spec_name, current_hash, current_deps, rebuilt):
                needs_rebuild.append(spec_name)
                rebuilt.add(spec_name)

        return needs_rebuild
