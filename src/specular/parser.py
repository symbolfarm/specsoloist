"""
Spec parsing, validation, and frontmatter extraction.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SpecMetadata:
    """Parsed frontmatter from a spec file."""
    name: str = ""
    type: str = "function"  # function | class | module | typedef
    language_target: str = "python"
    status: str = "draft"
    dependencies: List[Dict[str, str]] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedSpec:
    """A fully parsed specification."""
    metadata: SpecMetadata
    content: str  # Full content including frontmatter
    body: str     # Content without frontmatter
    path: str


class SpecParser:
    """Handles spec file discovery, reading, parsing, and validation."""

    def __init__(self, src_dir: str):
        self.src_dir = os.path.abspath(src_dir)

    def _get_spec_path(self, name: str) -> str:
        """Resolves a spec name to its full path."""
        if not name.endswith(".spec.md"):
            name += ".spec.md"
        return os.path.join(self.src_dir, name)

    def list_specs(self) -> List[str]:
        """Lists all available specification files."""
        specs = []
        if os.path.exists(self.src_dir):
            for root, _, files in os.walk(self.src_dir):
                for file in files:
                    if file.endswith(".spec.md"):
                        specs.append(file)
        return specs

    def read_spec(self, name: str) -> str:
        """Reads the raw content of a specification file."""
        path = self._get_spec_path(name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Spec '{name}' not found at {path}")
        with open(path, 'r') as f:
            return f.read()

    def spec_exists(self, name: str) -> bool:
        """Checks if a spec file exists."""
        path = self._get_spec_path(name)
        return os.path.exists(path)

    def parse_spec(self, name: str) -> ParsedSpec:
        """Parses a spec file into structured data."""
        content = self.read_spec(name)
        path = self._get_spec_path(name)

        metadata = self._parse_frontmatter(content)
        body = self._strip_frontmatter(content)

        return ParsedSpec(
            metadata=metadata,
            content=content,
            body=body,
            path=path
        )

    def _parse_frontmatter(self, content: str) -> SpecMetadata:
        """Extracts and parses YAML frontmatter from spec content."""
        metadata = SpecMetadata()

        if not content.strip().startswith("---"):
            return metadata

        parts = content.split("---", 2)
        if len(parts) < 3:
            return metadata

        frontmatter = parts[1].strip()
        raw = {}

        # Simple YAML-like parsing (avoids pyyaml dependency for core)
        for line in frontmatter.split("\n"):
            line = line.strip()
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip()
                raw[key] = value

                if key == "name":
                    metadata.name = value
                elif key == "type":
                    metadata.type = value
                elif key == "language_target":
                    metadata.language_target = value
                elif key == "status":
                    metadata.status = value

        # Parse dependencies if present (future Phase 2a)
        # Format: dependencies:\n  - name: X\n    from: Y
        metadata.raw = raw

        return metadata

    def _strip_frontmatter(self, content: str) -> str:
        """Removes YAML frontmatter from content, returning just the body."""
        if not content.startswith("---"):
            return content

        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
        return content

    def validate_spec(self, name: str) -> Dict[str, Any]:
        """
        Validates a spec for basic structure and SRS compliance.
        Returns a dict with 'valid' bool and 'errors' list.
        """
        try:
            content = self.read_spec(name)
        except FileNotFoundError:
            return {"valid": False, "errors": ["Spec file not found."]}

        errors = []

        # 1. Check Frontmatter
        if not content.strip().startswith("---"):
            errors.append("Missing YAML frontmatter.")

        # 2. Check Required Sections
        required_sections = [
            "# 1. Overview",
            "# 2. Interface Specification",
            "# 3. Functional Requirements",
            "# 4. Non-Functional Requirements",
            "# 5. Design Contract"
        ]
        for section in required_sections:
            if section not in content:
                errors.append(f"Missing required section: '{section}'")

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def get_module_name(self, name: str) -> str:
        """Extracts the module name from a spec filename."""
        return name.replace(".spec.md", "")
