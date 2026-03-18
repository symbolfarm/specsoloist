"""Spec file discovery, reading, parsing, creation, and validation."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Optional

import yaml

from specsoloist.schema import (
    BundleFunction,
    BundleType,
    InterfaceSchema,
    WorkflowStep,
    parse_bundle_functions,
    parse_bundle_types,
    parse_schema_block,
    parse_steps_block,
)

# Valid spec type strings
SPEC_TYPES = {
    "function",
    "type",
    "bundle",
    "module",
    "workflow",
    "typedef",
    "class",
    "orchestrator",
    "reference",
    "specification",
}


@dataclass
class SpecMetadata:
    """Parsed YAML frontmatter from a spec file."""

    name: str = ""
    description: str = ""
    type: str = "function"
    status: str = "draft"
    version: str = ""
    tags: list = field(default_factory=list)
    dependencies: list = field(default_factory=list)
    language_target: Optional[str] = None
    raw: dict = field(default_factory=dict)


@dataclass
class ParsedSpec:
    """Fully parsed specification file."""

    metadata: SpecMetadata
    content: str
    body: str
    path: str
    schema: Optional[InterfaceSchema] = None
    bundle_functions: dict[str, BundleFunction] = field(default_factory=dict)
    bundle_types: dict[str, BundleType] = field(default_factory=dict)
    steps: list[WorkflowStep] = field(default_factory=list)


def _extract_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and return (frontmatter_dict, body)."""
    stripped = content.lstrip()
    if not stripped.startswith("---"):
        return {}, content

    # Find the closing ---
    rest = stripped[3:]
    end_idx = rest.find("\n---")
    if end_idx == -1:
        return {}, content

    fm_text = rest[:end_idx].strip()
    body = rest[end_idx + 4:].lstrip("\n")

    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        fm = {}

    return fm, body


def _extract_yaml_block(body: str, block_type: str) -> Optional[dict]:
    """Extract content from a fenced yaml:TYPE block."""
    pattern = f"```yaml:{block_type}"
    start_idx = body.find(pattern)
    if start_idx == -1:
        return None

    # Find content start (after the opening line)
    content_start = body.find("\n", start_idx)
    if content_start == -1:
        return None
    content_start += 1

    # Find closing ```
    end_idx = body.find("\n```", content_start)
    if end_idx == -1:
        # Try without leading newline
        end_idx = body.find("```", content_start)
        if end_idx == -1:
            return None

    block_content = body[content_start:end_idx].strip()
    if not block_content:
        return None

    try:
        return yaml.safe_load(block_content)
    except yaml.YAMLError:
        return None


def _extract_description_from_body(body: str) -> str:
    """Extract first non-empty, non-heading line after Overview heading."""
    lines = body.split("\n")
    in_overview = False

    for line in lines:
        stripped = line.strip()
        if stripped in ("# Overview", "# 1. Overview"):
            in_overview = True
            continue
        if in_overview:
            if stripped.startswith("#"):
                break  # Next section, stop
            if stripped:
                return stripped

    return ""


class SpecParser:
    """Main class for spec file operations."""

    def __init__(self, src_dir: str, template_dir: Optional[str] = None) -> None:
        self.src_dir = os.path.abspath(src_dir)
        self.template_dir = template_dir

    def get_spec_path(self, name: str) -> str:
        """Resolve a spec name to its full file path."""
        if os.path.isabs(name):
            return name

        if name.endswith(".spec.md") and os.path.exists(name):
            return name

        if not name.endswith(".spec.md"):
            name = name + ".spec.md"

        return os.path.join(self.src_dir, name)

    def list_specs(self) -> list[str]:
        """List all available spec files in the source directory."""
        if not os.path.exists(self.src_dir):
            return []

        result = []
        for root, dirs, files in os.walk(self.src_dir):
            # Skip hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for fname in files:
                if fname.endswith(".spec.md"):
                    rel = os.path.relpath(os.path.join(root, fname), self.src_dir)
                    result.append(rel)

        return sorted(result)

    def read_spec(self, name: str) -> str:
        """Read the raw content of a spec file."""
        path = self.get_spec_path(name)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Spec file not found: {path}")
        with open(path) as f:
            return f.read()

    def spec_exists(self, name: str) -> bool:
        """Check whether a spec file exists on disk."""
        path = self.get_spec_path(name)
        return os.path.exists(path)

    def create_spec(
        self, name: str, description: str, spec_type: str = "function"
    ) -> str:
        """Create a new specification file from a template."""
        path = self.get_spec_path(name)
        if os.path.exists(path):
            raise FileExistsError(f"Spec file already exists: {path}")

        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

        template = self._get_template(name, description, spec_type)
        with open(path, "w") as f:
            f.write(template)

        return path

    def _get_template(self, name: str, description: str, spec_type: str) -> str:
        """Generate template content for a spec type."""
        if spec_type == "function":
            return f"""---
name: {name}
description: {description}
type: function
---

# Overview

{description}

# Interface

```yaml:schema
inputs:
  param1: {{type: string}}
outputs:
  result: {{type: string}}
```

# Behavior

- FR1: TODO

# Examples

| Input | Expected Output |
|-------|----------------|
| ... | ... |
"""
        elif spec_type == "type":
            return f"""---
name: {name}
description: {description}
type: type
---

# Overview

{description}

# Schema

```yaml:schema
properties:
  field1:
    type: string
required:
  - field1
```

# Examples

| Field | Value |
|-------|-------|
| ... | ... |
"""
        elif spec_type == "bundle":
            return f"""---
name: {name}
description: {description}
type: bundle
---

# Overview

{description}

# Functions

```yaml:functions
my_function:
  inputs:
    param: {{type: string}}
  outputs:
    result: {{type: string}}
  behavior: "TODO"
```

# Types
"""
        elif spec_type == "workflow":
            return f"""---
name: {name}
description: {description}
type: workflow
dependencies: []
---

# Overview

{description}

# Interface

```yaml:schema
inputs:
  input1: {{type: string}}
outputs:
  result: {{type: string}}
```

# Steps

```yaml:steps
- name: step1
  spec: some_spec
  inputs: {{}}
```

# Error Handling

TODO
"""
        else:  # module or default
            return f"""---
name: {name}
description: {description}
type: {spec_type}
---

# Overview

{description}

# Exports

- TODO
"""

    def parse_spec(self, name: str) -> ParsedSpec:
        """Parse a spec file into structured data."""
        content = self.read_spec(name)
        path = self.get_spec_path(name)

        fm, body = _extract_frontmatter(content)

        # Build metadata
        tags = fm.get("tags", [])
        if not isinstance(tags, list):
            tags = []

        lang_target = fm.get("language_target")
        if isinstance(lang_target, list):
            lang_target = lang_target[0] if lang_target else None

        deps = fm.get("dependencies", [])
        if not isinstance(deps, list):
            deps = []

        description = fm.get("description", "")
        if not description:
            description = _extract_description_from_body(body)

        metadata = SpecMetadata(
            name=fm.get("name", ""),
            description=description,
            type=fm.get("type", "function"),
            status=fm.get("status", "draft"),
            version=str(fm.get("version", "")),
            tags=tags,
            dependencies=deps,
            language_target=lang_target,
            raw=fm,
        )

        spec_type = metadata.type
        schema = None
        bundle_functions = {}
        bundle_types = {}
        steps = []

        if spec_type == "bundle":
            raw_funcs = _extract_yaml_block(body, "functions")
            if raw_funcs:
                try:
                    bundle_functions = parse_bundle_functions(raw_funcs)
                except (ValueError, TypeError):
                    pass

            raw_types = _extract_yaml_block(body, "types")
            if raw_types:
                try:
                    bundle_types = parse_bundle_types(raw_types)
                except (ValueError, TypeError):
                    pass

        elif spec_type in ("workflow", "orchestrator"):
            raw_schema = _extract_yaml_block(body, "schema")
            if raw_schema:
                try:
                    schema = parse_schema_block(raw_schema)
                except (ValueError, TypeError):
                    pass

            raw_steps = _extract_yaml_block(body, "steps")
            if raw_steps:
                try:
                    steps = parse_steps_block(raw_steps)
                    if schema is not None:
                        schema.steps = steps
                except (ValueError, TypeError):
                    pass

        else:
            raw_schema = _extract_yaml_block(body, "schema")
            if raw_schema:
                try:
                    schema = parse_schema_block(raw_schema)
                except (ValueError, TypeError):
                    pass

        return ParsedSpec(
            metadata=metadata,
            content=content,
            body=body,
            path=path,
            schema=schema,
            bundle_functions=bundle_functions,
            bundle_types=bundle_types,
            steps=steps,
        )

    def validate_spec(self, name: str) -> dict:
        """Validate a spec for structural correctness."""
        if not self.spec_exists(name):
            return {"valid": False, "errors": ["Spec file not found."]}

        try:
            spec = self.parse_spec(name)
        except Exception as e:
            return {"valid": False, "errors": [f"Parse error: {e}"]}

        errors = []
        content = spec.content
        body = spec.body
        spec_type = spec.metadata.type

        # Check frontmatter
        if not content.lstrip().startswith("---"):
            errors.append("Missing YAML frontmatter.")
            return {"valid": False, "errors": errors}

        has_overview = bool(
            re.search(r"^# Overview|^# 1\. Overview", body, re.MULTILINE)
        )

        if spec_type in ("function", "class"):
            if not has_overview:
                errors.append("Missing # Overview section.")
            has_interface = "# Interface" in body or "```yaml:schema" in body
            if not has_interface:
                errors.append("Missing # Interface section or yaml:schema block.")
            has_behavior = "# Behavior" in body or "# 3. Functional Requirements" in body
            if not has_behavior:
                errors.append("Missing # Behavior section.")

        elif spec_type == "type":
            if not has_overview:
                errors.append("Missing # Overview section.")
            has_schema = "# Schema" in body or "```yaml:schema" in body
            if not has_schema:
                errors.append("Missing # Schema section or yaml:schema block.")

        elif spec_type == "bundle":
            if not has_overview:
                errors.append("Missing # Overview section.")
            has_funcs = bool(spec.bundle_functions)
            has_types = bool(spec.bundle_types)
            if not has_funcs and not has_types:
                errors.append(
                    "Bundle must define at least one function or type in YAML blocks."
                )

        elif spec_type in ("workflow", "orchestrator"):
            if not has_overview:
                errors.append("Missing # Overview section.")
            if not spec.steps:
                errors.append("Workflow must define steps in a yaml:steps block.")

        elif spec_type == "module":
            if not has_overview:
                errors.append("Missing # Overview section.")
            has_exports = (
                "# Exports" in body
                or "# Interface" in body
                or bool(spec.metadata.dependencies)
            )
            if not has_exports:
                errors.append("Module must have # Exports section or dependencies.")

        elif spec_type == "specification":
            pass  # No additional requirements

        else:
            # Legacy: check for numbered sections
            for i in range(1, 6):
                if f"# {i}." not in body:
                    errors.append(f"Missing section # {i}.")

        return {"valid": len(errors) == 0, "errors": errors}

    def get_module_name(self, name: str) -> str:
        """Extract the module name from a spec filename."""
        base = os.path.basename(name)
        return base.replace(".spec.md", "")

    def extract_verification_snippet(self, body: str) -> str:
        """Extract the code block from the # Verification section."""
        lines = body.split("\n")
        in_verification = False
        in_code = False
        code_lines = []

        for line in lines:
            if re.match(r"^# Verification\b", line):
                in_verification = True
                continue
            if in_verification:
                if line.startswith("#"):
                    break  # Next heading
                if line.startswith("```") and not in_code:
                    in_code = True
                    continue
                if line.startswith("```") and in_code:
                    break  # End of code block
                if in_code:
                    code_lines.append(line)

        return "\n".join(code_lines)

    def load_global_context(self) -> str:
        """Load the global context template."""
        # Try template_dir first
        if self.template_dir:
            path = os.path.join(self.template_dir, "global_context.md")
            if os.path.exists(path):
                with open(path) as f:
                    return f.read()

        # Try package resources
        try:
            import importlib.resources as pkg_resources
            try:
                ref = pkg_resources.files("specsoloist.templates").joinpath(
                    "global_context.md"
                )
                return ref.read_text()
            except (AttributeError, FileNotFoundError, ModuleNotFoundError):
                pass
        except ImportError:
            pass

        # Try local templates/ relative to module
        module_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(module_dir, "templates", "global_context.md")
        if os.path.exists(path):
            with open(path) as f:
                return f.read()

        return ""

    def parse(self, name: str) -> ParsedSpec:
        """Alias for parse_spec for compatibility."""
        return self.parse_spec(name)
