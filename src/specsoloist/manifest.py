"""
Build manifest for tracking spec compilation state.

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
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SpecBuildInfo":
        return cls(**data)


@dataclass
class BuildManifest:
    """Collection of build records, persisted as JSON."""

    MANIFEST_FILENAME = ".specsoloist-manifest.json"

    version: str = "1.0"
    specs: Dict[str, SpecBuildInfo] = field(default_factory=dict)

    def get_spec_info(self, name: str) -> Optional[SpecBuildInfo]:
        return self.specs.get(name)

    def update_spec(
        self, name: str, spec_hash: str,
        dependencies: List[str], output_files: List[str]
    ):
        self.specs[name] = SpecBuildInfo(
            spec_hash=spec_hash,
            built_at=datetime.utcnow().isoformat(),
            dependencies=dependencies,
            output_files=output_files,
        )

    def remove_spec(self, name: str):
        self.specs.pop(name, None)

    def save(self, build_dir: str):
        path = os.path.join(build_dir, self.MANIFEST_FILENAME)
        with open(path, "w") as f:
            json.dump(
                {"version": self.version,
                 "specs": {k: v.to_dict() for k, v in self.specs.items()}},
                f, indent=2,
            )

    @classmethod
    def load(cls, build_dir: str) -> "BuildManifest":
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
        self.manifest = manifest
        self.src_dir = src_dir

    def needs_rebuild(
        self, spec_name: str, current_hash: str,
        current_deps: List[str], rebuilt_specs: set
    ) -> bool:
        info = self.manifest.get_spec_info(spec_name)
        if info is None:
            return True
        if info.spec_hash != current_hash:
            return True
        if set(info.dependencies) != set(current_deps):
            return True
        if any(dep in rebuilt_specs for dep in current_deps):
            return True
        return False

    def get_rebuild_plan(
        self, build_order: List[str],
        spec_hashes: Dict[str, str],
        spec_deps: Dict[str, List[str]]
    ) -> List[str]:
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
