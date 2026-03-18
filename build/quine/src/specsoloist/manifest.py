"""Build manifest for tracking spec compilation state."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class SpecBuildInfo:
    """Build record for a single spec."""

    spec_hash: str
    built_at: str
    dependencies: list[str]
    output_files: list[str]

    def to_dict(self) -> dict:
        """Serialize to dict for JSON."""
        return {
            "spec_hash": self.spec_hash,
            "built_at": self.built_at,
            "dependencies": self.dependencies,
            "output_files": self.output_files,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SpecBuildInfo":
        """Deserialize from dict."""
        return cls(
            spec_hash=data["spec_hash"],
            built_at=data["built_at"],
            dependencies=data.get("dependencies", []),
            output_files=data.get("output_files", []),
        )


@dataclass
class BuildManifest:
    """Collection of build records."""

    version: str = "1.0"
    specs: dict[str, SpecBuildInfo] = field(default_factory=dict)

    def get_spec_info(self, name: str) -> Optional[SpecBuildInfo]:
        """Get build info for a spec by name."""
        return self.specs.get(name)

    def update_spec(
        self,
        name: str,
        spec_hash: str,
        dependencies: list[str],
        output_files: list[str],
    ) -> None:
        """Record a successful build with current UTC timestamp."""
        self.specs[name] = SpecBuildInfo(
            spec_hash=spec_hash,
            built_at=datetime.now(timezone.utc).isoformat(),
            dependencies=dependencies,
            output_files=output_files,
        )

    def remove_spec(self, name: str) -> None:
        """Remove a spec's build record."""
        self.specs.pop(name, None)

    def save(self, build_dir: str) -> None:
        """Write manifest to {build_dir}/.specsoloist-manifest.json as JSON."""
        path = os.path.join(build_dir, ".specsoloist-manifest.json")
        data = {
            "version": self.version,
            "specs": {name: info.to_dict() for name, info in self.specs.items()},
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, build_dir: str) -> "BuildManifest":
        """Load manifest from file; return empty manifest if not found or corrupted."""
        path = os.path.join(build_dir, ".specsoloist-manifest.json")
        if not os.path.exists(path):
            return cls()
        try:
            with open(path) as f:
                data = json.load(f)
            specs = {}
            for name, info_data in data.get("specs", {}).items():
                specs[name] = SpecBuildInfo.from_dict(info_data)
            return cls(version=data.get("version", "1.0"), specs=specs)
        except (json.JSONDecodeError, KeyError, TypeError):
            return cls()


@dataclass
class IncrementalBuilder:
    """Determines which specs need rebuilding."""

    manifest: BuildManifest
    src_dir: str

    def needs_rebuild(
        self,
        spec_name: str,
        current_hash: str,
        current_deps: list[str],
        rebuilt_specs: set[str],
    ) -> bool:
        """Check if a spec needs rebuilding."""
        info = self.manifest.get_spec_info(spec_name)

        # Never built
        if info is None:
            return True

        # Content hash changed
        if info.spec_hash != current_hash:
            return True

        # Dependency list changed
        if sorted(info.dependencies) != sorted(current_deps):
            return True

        # Any dependency was rebuilt this cycle
        for dep in current_deps:
            if dep in rebuilt_specs:
                return True

        return False

    def get_rebuild_plan(
        self,
        build_order: list[str],
        spec_hashes: dict[str, str],
        spec_deps: dict[str, list[str]],
    ) -> list[str]:
        """Walk build order and determine which specs need rebuilding."""
        rebuilt: set[str] = set()
        plan = []

        for spec_name in build_order:
            current_hash = spec_hashes.get(spec_name, "")
            current_deps = spec_deps.get(spec_name, [])

            if self.needs_rebuild(spec_name, current_hash, current_deps, rebuilt):
                plan.append(spec_name)
                rebuilt.add(spec_name)

        return plan


def compute_file_hash(path: str) -> str:
    """Compute SHA-256 hash of a file's contents."""
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(content.encode()).hexdigest()
