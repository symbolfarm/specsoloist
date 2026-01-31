"""
Spec parsing, validation, creation, and frontmatter extraction.
"""

import importlib.resources
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class SpecMetadata:
    """Parsed frontmatter from a spec file."""
    name: str = ""
    description: str = ""
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
    """Handles spec file discovery, reading, parsing, creation, and validation."""

    def __init__(self, src_dir: str, template_dir: Optional[str] = None):
        """
        Initialize the parser.

        Args:
            src_dir: Directory where spec files are stored.
            template_dir: Optional override for template location (for testing).
        """
        self.src_dir = os.path.abspath(src_dir)
        self.template_dir = template_dir

    def get_spec_path(self, name: str) -> str:
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
        path = self.get_spec_path(name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Spec '{name}' not found at {path}")
        with open(path, 'r') as f:
            return f.read()

    def spec_exists(self, name: str) -> bool:
        """Checks if a spec file exists."""
        path = self.get_spec_path(name)
        return os.path.exists(path)

    def create_spec(
        self,
        name: str,
        description: str,
        spec_type: str = "function"
    ) -> str:
        """
        Creates a new specification file from the template.

        Args:
            name: Component name (e.g., "auth" creates "auth.spec.md").
            description: Brief description of the component.
            spec_type: Component type ("function", "class", "module", "typedef").

        Returns:
            Path to the created spec file.

        Raises:
            FileExistsError: If the spec already exists.
        """
        path = self.get_spec_path(name)
        if os.path.exists(path):
            raise FileExistsError(f"Spec '{name}' already exists at {path}")

        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)

        content = self._load_template("spec_template.md")
        if not content:
            # Emergency fallback
            content = f"---\nname: {name}\ntype: {spec_type}\n---\n# 1. Overview\n{description}\n"
        else:
            # Fill in template placeholders
            content = content.replace("[Component Name]", name)
            content = content.replace(
                "[Brief summary of the component's purpose.]", description
            )
            content = content.replace(
                "type: [function | class | module]", f"type: {spec_type}"
            )

        with open(path, 'w') as f:
            f.write(content)

        return path

    def parse_spec(self, name: str) -> ParsedSpec:
        """Parses a spec file into structured data."""
        content = self.read_spec(name)
        path = self.get_spec_path(name)

        metadata = self._parse_frontmatter(content)
        body = self._strip_frontmatter(content)

        # Fallback: Extract description from Overview if missing
        if not metadata.description and "# 1. Overview" in body:
            try:
                # Find content between "1. Overview" and the next section header
                parts = body.split("# 1. Overview", 1)[1]
                # Split by next header (start with #)
                overview_text = ""
                for line in parts.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if line.startswith("#"):
                        break
                    overview_text = line
                    break # Take first non-empty line
                
                if overview_text:
                    metadata.description = overview_text
            except Exception:
                pass  # Keep empty if extraction fails

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

        frontmatter_text = parts[1].strip()

        try:
            raw = yaml.safe_load(frontmatter_text) or {}
        except yaml.YAMLError:
            # Fall back to empty if YAML is malformed
            raw = {}

        if not isinstance(raw, dict):
            raw = {}

        metadata.name = raw.get("name", "")
        metadata.description = raw.get("description", "")
        metadata.type = raw.get("type", "function")
        
        target = raw.get("language_target", "python")
        if isinstance(target, list) and target:
            metadata.language_target = str(target[0])
        else:
            metadata.language_target = str(target)
            
        metadata.status = raw.get("status", "draft")

        # Parse dependencies (Phase 2a format)
        # Format: dependencies:
        #           - name: User
        #             from: types.spec.md
        deps = raw.get("dependencies", [])
        if isinstance(deps, list):
            metadata.dependencies = deps

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

    def load_global_context(self) -> str:
        """Loads the global context template for compilation prompts."""
        return self._load_template("global_context.md")

    def _load_template(self, filename: str) -> str:
        """Load a template from package resources or local directory."""
        # If template_dir is set, use it (for testing)
        if self.template_dir:
            path = os.path.join(self.template_dir, filename)
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return f.read()
            return ""

        # Try package resources first
        try:
            ref = importlib.resources.files('specsoloist.templates').joinpath(filename)
            return ref.read_text(encoding='utf-8')
        except Exception:
            pass

        # Fallback for local dev
        local_path = os.path.join(
            os.path.dirname(__file__), "templates", filename
        )
        if os.path.exists(local_path):
            with open(local_path, 'r') as f:
                return f.read()

        return ""
