"""
Spec parsing, validation, creation, and frontmatter extraction.

Supports the language-agnostic spec format with:
- function, type, bundle, module, workflow spec types
- yaml:schema, yaml:functions, yaml:types, yaml:steps blocks
"""

import importlib.resources
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml

from .schema import (
    InterfaceSchema,
    BundleFunction,
    BundleType,
    WorkflowStep,
    parse_schema_block,
    parse_bundle_functions,
    parse_bundle_types,
    parse_steps_block,
)


# Valid spec types
SPEC_TYPES = {"function", "type", "bundle", "module", "workflow", "typedef", "class", "orchestrator"}


@dataclass
class SpecMetadata:
    """Parsed frontmatter from a spec file."""
    name: str = ""
    description: str = ""
    type: str = "function"  # function | type | bundle | module | workflow
    status: str = "draft"   # draft | review | stable
    version: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[Any] = field(default_factory=list)  # Can be strings or dicts
    # Language target is now optional (build config, not spec)
    language_target: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedSpec:
    """A fully parsed specification."""
    metadata: SpecMetadata
    content: str  # Full content including frontmatter
    body: str     # Content without frontmatter
    path: str
    schema: Optional[InterfaceSchema] = None
    # For bundle specs
    bundle_functions: Dict[str, BundleFunction] = field(default_factory=dict)
    bundle_types: Dict[str, BundleType] = field(default_factory=dict)
    # For workflow specs
    steps: List[WorkflowStep] = field(default_factory=list)


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
                for f in files:
                    if f.endswith(".spec.md"):
                        # Return relative path from src_dir
                        rel_path = os.path.relpath(os.path.join(root, f), self.src_dir)
                        specs.append(rel_path)
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
            spec_type: Component type ("function", "type", "bundle", "module", "workflow").

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

        # Generate appropriate template based on type
        content = self._generate_template(name, description, spec_type)

        with open(path, 'w') as f:
            f.write(content)

        return path

    def _generate_template(self, name: str, description: str, spec_type: str) -> str:
        """Generates a spec template based on type."""
        if spec_type == "bundle":
            return self._generate_bundle_template(name, description)
        elif spec_type == "workflow":
            return self._generate_workflow_template(name, description)
        elif spec_type == "type":
            return self._generate_type_template(name, description)
        elif spec_type == "module":
            return self._generate_module_template(name, description)
        else:
            return self._generate_function_template(name, description)

    def _generate_function_template(self, name: str, description: str) -> str:
        """Generates a function spec template."""
        return f"""---
name: {name}
type: function
---

# Overview

{description}

# Interface

```yaml:schema
inputs:
  # param_name:
  #   type: integer
  #   description: What this parameter represents
outputs:
  result:
    type: string
    description: What the function returns
```

# Behavior

- [FR-01]: [Describe what this function does, not how it does it]

# Examples

| Input | Output | Notes |
|-------|--------|-------|
| | | |
"""

    def _generate_type_template(self, name: str, description: str) -> str:
        """Generates a type spec template."""
        return f"""---
name: {name}
type: type
---

# Overview

{description}

# Schema

```yaml:schema
properties:
  # field_name:
  #   type: string
  #   description: What this field represents
required: []
```

# Examples

| Valid | Invalid | Why |
|-------|---------|-----|
| | | |
"""

    def _generate_bundle_template(self, name: str, description: str) -> str:
        """Generates a bundle spec template."""
        return f"""---
name: {name}
type: bundle
---

# Overview

{description}

# Functions

```yaml:functions
example_function:
  inputs: {{a: integer, b: integer}}
  outputs: {{result: integer}}
  behavior: "Describe what this function does"
```

# Types

Describe public types here using prose — fields, methods, behavior.
Remove this section if the module has no public types.
"""

    def _generate_workflow_template(self, name: str, description: str) -> str:
        """Generates a workflow spec template."""
        return f"""---
name: {name}
type: workflow
dependencies:
  - step1_spec
  - step2_spec
---

# Overview

{description}

# Interface

```yaml:schema
inputs:
  input_param:
    type: string
    description: What this workflow receives
outputs:
  result:
    type: string
    description: What this workflow produces
```

# Steps

```yaml:steps
- name: step1
  spec: step1_spec
  inputs:
    param: inputs.input_param

- name: step2
  spec: step2_spec
  inputs:
    param: step1.outputs.result
```

# Error Handling

- If step1 fails: [describe what should happen]
"""

    def _generate_module_template(self, name: str, description: str) -> str:
        """Generates a module spec template."""
        return f"""---
name: {name}
type: module
---

# Overview

{description}

# Exports

- `export1`: [What this does]
- `export2`: [What this does]

Describe each export's public interface and behavior below.
"""

    def parse_spec(self, name: str) -> ParsedSpec:
        """Parses a spec file into structured data."""
        content = self.read_spec(name)
        path = self.get_spec_path(name)

        metadata = self._parse_frontmatter(content)
        body = self._strip_frontmatter(content)

        # Parse based on spec type
        schema = None
        bundle_functions = {}
        bundle_types = {}
        steps = []

        spec_type = metadata.type

        if spec_type == "bundle":
            # Parse yaml:functions and yaml:types blocks
            bundle_functions = self._extract_bundle_functions(body)
            bundle_types = self._extract_bundle_types(body)
        elif spec_type in ("workflow", "orchestrator"):
            # Parse yaml:schema and yaml:steps blocks
            schema = self._extract_schema(body)
            steps = self._extract_steps(body)
            # Also add steps to schema if present
            if schema and steps:
                schema.steps = steps
        else:
            # Parse yaml:schema block
            schema = self._extract_schema(body)

        # Fallback: Extract description from Overview if missing
        if not metadata.description:
            metadata.description = self._extract_overview_description(body)

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

    def _extract_overview_description(self, body: str) -> str:
        """Extracts description from the Overview section."""
        # Try both "# 1. Overview" and "# Overview" formats
        for marker in ["# 1. Overview", "# Overview"]:
            if marker in body:
                try:
                    parts = body.split(marker, 1)[1]
                    for line in parts.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("#"):
                            break
                        return line
                except Exception:
                    pass
        return ""

    def _extract_schema(self, content: str) -> Optional[InterfaceSchema]:
        """Extracts and parses the ```yaml:schema block."""
        yaml_text = self._extract_yaml_block(content, "yaml:schema")
        if not yaml_text:
            return None

        try:
            raw_data = yaml.safe_load(yaml_text)
            if not isinstance(raw_data, dict):
                return None
            return parse_schema_block(raw_data)
        except Exception:
            return None

    def _extract_bundle_functions(self, content: str) -> Dict[str, BundleFunction]:
        """Extracts and parses the ```yaml:functions block."""
        yaml_text = self._extract_yaml_block(content, "yaml:functions")
        if not yaml_text:
            return {}

        try:
            raw_data = yaml.safe_load(yaml_text)
            if not isinstance(raw_data, dict):
                return {}
            return parse_bundle_functions(raw_data)
        except Exception:
            return {}

    def _extract_bundle_types(self, content: str) -> Dict[str, BundleType]:
        """Extracts and parses the ```yaml:types block."""
        yaml_text = self._extract_yaml_block(content, "yaml:types")
        if not yaml_text:
            return {}

        try:
            raw_data = yaml.safe_load(yaml_text)
            if not isinstance(raw_data, dict):
                return {}
            return parse_bundle_types(raw_data)
        except Exception:
            return {}

    def _extract_steps(self, content: str) -> List[WorkflowStep]:
        """Extracts and parses the ```yaml:steps block."""
        yaml_text = self._extract_yaml_block(content, "yaml:steps")
        if not yaml_text:
            return []

        try:
            raw_data = yaml.safe_load(yaml_text)
            if not isinstance(raw_data, list):
                return []
            return parse_steps_block(raw_data)
        except Exception:
            return []

    def _extract_yaml_block(self, content: str, block_type: str) -> Optional[str]:
        """Extracts content from a ```<block_type> ... ``` block."""
        start_marker = f"```{block_type}"
        if start_marker not in content:
            return None

        try:
            start_idx = content.find(start_marker)
            if start_idx == -1:
                return None

            start_content = start_idx + len(start_marker)

            # Find the closing ``` at the start of a line
            # We look for \n``` or just ``` if it's the very end of the string
            # But more robustly, we look for \n```
            search_pos = start_content
            while True:
                end_idx = content.find("```", search_pos)
                if end_idx == -1:
                    return None

                # Check if it's at the start of a line (preceded by \n or it's the start of content)
                if end_idx == 0 or content[end_idx-1] == '\n':
                    return content[start_content:end_idx].strip()

                search_pos = end_idx + 3
        except Exception:
            return None

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
            raw = {}

        if not isinstance(raw, dict):
            raw = {}

        metadata.name = raw.get("name", "")
        metadata.description = raw.get("description", "")
        metadata.type = raw.get("type", "function")
        metadata.status = raw.get("status", "draft")
        metadata.version = raw.get("version", "")

        # Tags can be a list
        tags = raw.get("tags", [])
        if isinstance(tags, list):
            metadata.tags = [str(t) for t in tags]

        # Language target is optional (for backwards compatibility)
        target = raw.get("language_target")
        if target:
            if isinstance(target, list) and target:
                metadata.language_target = str(target[0])
            else:
                metadata.language_target = str(target)

        # Parse dependencies (can be strings or dicts)
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
        Validates a spec for basic structure based on its type.
        Returns a dict with 'valid' bool and 'errors' list.
        """
        try:
            parsed = self.parse_spec(name)
        except FileNotFoundError:
            return {"valid": False, "errors": ["Spec file not found."]}
        except Exception as e:
            return {"valid": False, "errors": [f"Parse error: {e}"]}

        errors = []
        spec_type = parsed.metadata.type

        # Check frontmatter
        if not parsed.content.strip().startswith("---"):
            errors.append("Missing YAML frontmatter.")

        # Check required sections based on type
        if spec_type in ("function", "class"):
            errors.extend(self._validate_function_sections(parsed))
        elif spec_type == "type":
            errors.extend(self._validate_type_sections(parsed.body))
        elif spec_type == "bundle":
            errors.extend(self._validate_bundle_sections(parsed))
        elif spec_type in ("workflow", "orchestrator"):
            errors.extend(self._validate_workflow_sections(parsed))
        elif spec_type == "module":
            errors.extend(self._validate_module_sections(parsed))
        elif spec_type == "specification":
            pass
        else:
            # Legacy validation for unknown types
            errors.extend(self._validate_legacy_sections(parsed.body))

        return {
            "valid": len(errors) == 0,
            "errors": errors
        }

    def _validate_function_sections(self, parsed: ParsedSpec) -> List[str]:
        """Validates required sections for function specs."""
        errors = []
        body = parsed.body

        # Check Overview
        if "# Overview" not in body and "# 1. Overview" not in body:
            errors.append("Missing required section: '# Overview'")

        # Check Interface (Header OR YAML Block)
        has_interface = any(h in body for h in ["# Interface", "# 2. Interface Specification"])
        has_yaml = parsed.schema is not None
        if not (has_interface or has_yaml):
            errors.append("Missing required section: '# Interface' or yaml:schema block")

        # Check Behavior
        if "# Behavior" not in body and "# 3. Functional Requirements" not in body:
            errors.append("Missing required section: '# Behavior'")

        return errors

    def _validate_type_sections(self, body: str) -> List[str]:
        """Validates required sections for type specs."""
        errors = []
        if "# Overview" not in body and "# 1. Overview" not in body:
            errors.append("Missing required section: '# Overview'")
        # Already checked for yaml:schema in parse_spec, but let's be thorough
        if "# Schema" not in body and "```yaml:schema" not in body:
            errors.append("Missing required section: '# Schema' or yaml:schema block")
        return errors

    def _validate_bundle_sections(self, parsed: ParsedSpec) -> List[str]:
        """Validates required sections for bundle specs."""
        errors = []
        if "# Overview" not in parsed.body and "# 1. Overview" not in parsed.body:
            errors.append("Missing required section: '# Overview'")
        if not parsed.bundle_functions and not parsed.bundle_types:
            errors.append("Bundle must have at least one function or type defined")
        return errors

    def _validate_workflow_sections(self, parsed: ParsedSpec) -> List[str]:
        """Validates required sections for workflow specs."""
        errors = []
        if "# Overview" not in parsed.body and "# 1. Overview" not in parsed.body:
            errors.append("Missing required section: '# Overview'")
        if not parsed.steps:
            errors.append("Workflow must have steps defined in yaml:steps block")
        return errors

    def _validate_module_sections(self, parsed: ParsedSpec) -> List[str]:
        """Validates required sections for module specs."""
        errors = []
        body = parsed.body
        if "# Overview" not in body and "# 1. Overview" not in body:
            errors.append("Missing required section: '# Overview'")

        # New format uses Exports, legacy uses Interface Specification
        has_exports = "# Exports" in body
        has_interface = "# 2. Interface Specification" in body
        has_yaml = parsed.bundle_functions or parsed.bundle_types or (parsed.metadata.dependencies and len(parsed.metadata.dependencies) > 0)

        if not (has_exports or has_interface or has_yaml):
            errors.append("Module must have '# Exports', legacy interface, or dependencies")

        return errors

    def _validate_legacy_sections(self, body: str) -> List[str]:
        """Validates required sections for legacy specs."""
        errors = []
        required_sections = [
            "# 1. Overview",
            "# 2. Interface Specification",
            "# 3. Functional Requirements",
            "# 4. Non-Functional Requirements",
            "# 5. Design Contract"
        ]
        for section in required_sections:
            if section not in body:
                errors.append(f"Missing required section: '{section}'")
        return errors

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
