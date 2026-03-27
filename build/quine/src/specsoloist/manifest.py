"""Build manifest for tracking spec compilation state.

Enables incremental builds by recording what was built, when, and
from what inputs.
"""

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class SpecBuildInfo:
    """Build record for a single spec."""
    spec_hash: str
    built_at: str
    dependencies: List[str]
    output_files: List[str]

    def to_dict(self) -> dict:
        """Serialize to a JSON-compatible dict."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SpecBuildInfo":
        """Deserialize from a dict produced by to_dict."""
        return cls(**data)


@dataclass
class BuildManifest:
    """Collection of build records, persisted as JSON."""

    MANIFEST_FILENAME = ".specsoloist-manifest.json"

    version: str = "1.0"
    specs: Dict[str, SpecBuildInfo] = field(default_factory=dict)

    def get_spec_info(self, name: str) -> Optional[SpecBuildInfo]:
        """Return the build record for a spec, or None if not yet built."""
        return self.specs.get(name)

    def update_spec(
        self, name: str, spec_hash: str,
        dependencies: List[str], output_files: List[str]
    ):
        """Record a successful build for a spec, stamped with the current UTC time."""
        self.specs[name] = SpecBuildInfo(
            spec_hash=spec_hash,
            built_at=datetime.utcnow().isoformat(),
            dependencies=dependencies,
            output_files=output_files,
        )

    def remove_spec(self, name: str):
        """Remove a spec's build record from the manifest (no-op if absent)."""
        self.specs.pop(name, None)

    def save(self, build_dir: str):
        """Persist the manifest to JSON in build_dir."""
        path = os.path.join(build_dir, self.MANIFEST_FILENAME)
        with open(path, "w") as f:
            json.dump(
                {"version": self.version,
                 "specs": {k: v.to_dict() for k, v in self.specs.items()}},
                f, indent=2,
            )

    @classmethod
    def load(cls, build_dir: str) -> "BuildManifest":
        """Load the manifest from build_dir, returning an empty manifest if missing or corrupt."""
        path = os.path.join(build_dir, cls.MANIFEST_FILENAME)
        if not os.path.exists(path):
            return cls()
        try:
            with open(path) as f:
                data = json.load(f)
            manifest = cls(version=data.get("version", "1.0"))
            for name, info in data.get("specs", {}).items():
                manifest.specs[name] = SpecBuildInfo.from_dict(info)
            return manifest
        except (json.JSONDecodeError, KeyError, TypeError):
            return cls()


def compute_file_hash(path: str) -> str:
    """SHA-256 hash of a file's contents, or empty string if missing."""
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def compute_content_hash(content: str) -> str:
    """SHA-256 hash of a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class IncrementalBuilder:
    """Determines which specs need rebuilding."""

    def __init__(self, manifest: BuildManifest, src_dir: str):
        """Initialize the incremental builder.

        Args:
            manifest: The current build manifest recording previous compilation state.
            src_dir: Path to the directory containing spec files.
        """
        self.manifest = manifest
        self.src_dir = src_dir

    def needs_rebuild(
        self, spec_name: str, current_hash: str,
        current_deps: List[str], rebuilt_specs: set
    ) -> bool:
        """Return True if a spec needs to be recompiled.

        Args:
            spec_name: Name of the spec to check.
            current_hash: SHA-256 hash of the current spec file content.
            current_deps: Current list of dependency names from the spec.
            rebuilt_specs: Set of spec names already rebuilt in this run.
        """
        info = self.manifest.get_spec_info(spec_name)
        if info is None:
            return True
        if info.spec_hash != current_hash:
            return True
        if set(info.dependencies) != set(current_deps):
            return True
        if any(dep in rebuilt_specs for dep in current_deps):
            return True
        # Check that all declared output files still exist on disk
        if any(not os.path.exists(f) for f in info.output_files):
            return True
        return False

    def get_rebuild_plan(
        self, build_order: List[str],
        spec_hashes: Dict[str, str],
        spec_deps: Dict[str, List[str]]
    ) -> List[str]:
        """Return the ordered subset of specs that need rebuilding.

        Args:
            build_order: Full topological build order for all specs.
            spec_hashes: Mapping of spec name to current content hash.
            spec_deps: Mapping of spec name to current dependency list.
        """
        rebuilt = set()
        plan = []
        for name in build_order:
            if self.needs_rebuild(
                name,
                spec_hashes.get(name, ""),
                spec_deps.get(name, []),
                rebuilt,
            ):
                plan.append(name)
                rebuilt.add(name)
        return plan
