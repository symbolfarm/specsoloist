"""Composer is the architect component of Spechestra."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

import yaml

from specsoloist.config import SpecSoloistConfig
from specsoloist.parser import SpecParser


@dataclass
class ComponentDef:
    """Definition of a single component in an architecture plan."""

    name: str
    type: str
    description: str
    inputs: dict = field(default_factory=dict)
    outputs: dict = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class Architecture:
    """An architecture plan for a project."""

    components: list[ComponentDef] = field(default_factory=list)
    dependencies: dict[str, list[str]] = field(default_factory=dict)
    build_order: list[str] = field(default_factory=list)
    description: str = ""

    def to_yaml(self) -> str:
        """Serialize the architecture to a YAML string."""
        data = {
            "description": self.description,
            "components": [
                {
                    "name": c.name,
                    "type": c.type,
                    "description": c.description,
                    "dependencies": c.dependencies,
                }
                for c in self.components
            ],
            "dependencies": self.dependencies,
            "build_order": self.build_order,
        }
        return yaml.dump(data, default_flow_style=False)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "Architecture":
        """Parse an Architecture from a YAML string."""
        try:
            data = yaml.safe_load(yaml_str)
            if not isinstance(data, dict):
                return cls()

            components = []
            for comp_data in data.get("components", []):
                if not isinstance(comp_data, dict):
                    continue
                components.append(
                    ComponentDef(
                        name=comp_data.get("name", ""),
                        type=comp_data.get("type", "bundle"),
                        description=comp_data.get("description", ""),
                        inputs=comp_data.get("inputs", {}),
                        outputs=comp_data.get("outputs", {}),
                        dependencies=comp_data.get("dependencies", []),
                    )
                )

            return cls(
                components=components,
                dependencies=data.get("dependencies", {}),
                build_order=data.get("build_order", []),
                description=data.get("description", ""),
            )
        except (yaml.YAMLError, AttributeError, TypeError):
            return cls()


@dataclass
class CompositionResult:
    """Result of a compose operation."""

    architecture: Architecture
    spec_paths: list[str] = field(default_factory=list)
    ready_for_build: bool = False
    cancelled: bool = False


class SpecComposer:
    """The main composer class."""

    def __init__(
        self,
        project_dir: str,
        config: Optional[SpecSoloistConfig] = None,
        provider=None,
    ) -> None:
        self.project_dir = os.path.abspath(project_dir)
        self.config = config or SpecSoloistConfig.from_env(root_dir=project_dir)
        self._provider = provider

        # Initialize parser
        self.parser = SpecParser(self.config.src_path)

    @property
    def provider(self):
        """Get or create LLM provider."""
        if self._provider is None:
            self._provider = self.config.create_provider()
        return self._provider

    def draft_architecture(
        self,
        request: str,
        context: Optional[dict] = None,
    ) -> Architecture:
        """Draft an architecture plan from a natural language request."""
        context = context or {}

        existing_specs = context.get("existing_specs", [])

        prompt_parts = [
            "You are a software architect. Given a plain English request, "
            "break it into discrete components, identify their dependencies, "
            "and suggest a build order.",
            "",
            f"Request: {request}",
        ]

        if existing_specs:
            prompt_parts.extend([
                "",
                "Existing specs (integrate with these if relevant):",
                ", ".join(existing_specs),
            ])

        prompt_parts.extend([
            "",
            "Respond with a YAML architecture plan in this format:",
            "```yaml",
            "description: Brief description of the architecture",
            "components:",
            "  - name: component_name",
            "    type: bundle  # function, type, bundle, module, or workflow",
            "    description: What this component does",
            "    dependencies: []  # list of other component names",
            "dependencies:",
            "  component_name: [dep1, dep2]",
            "build_order: [dep1, dep2, component_name]",
            "```",
            "",
            "Respond with ONLY the YAML, no additional text.",
        ])

        prompt = "\n".join(prompt_parts)

        try:
            response = self.provider.generate(prompt)
            # Strip code fences
            import re
            response = re.sub(r"^```[a-zA-Z]*\n", "", response, flags=re.MULTILINE)
            response = re.sub(r"\n```\s*$", "", response.strip())
            return Architecture.from_yaml(response)
        except Exception:
            return Architecture()

    def generate_specs(self, architecture: Architecture) -> list[str]:
        """Generate *.spec.md files for each component in the architecture."""
        created_paths = []

        for component in architecture.components:
            if self.parser.spec_exists(component.name):
                continue  # Skip existing specs

            # Generate spec content via LLM
            deps_str = (
                ", ".join(component.dependencies)
                if component.dependencies
                else "none"
            )
            prompt = (
                f"Write a SpecSoloist spec file for a {component.type} component called '{component.name}'.\n"
                f"Description: {component.description}\n"
                f"Dependencies: {deps_str}\n\n"
                "The spec should include YAML frontmatter with name, type, and dependencies, "
                "and appropriate sections for the spec type (Overview, Functions/Interface/Steps, etc.).\n"
                "Respond with ONLY the spec file content."
            )

            try:
                content = self.provider.generate(prompt)
                # Strip code fences
                import re
                content = re.sub(r"^```[a-zA-Z]*\n", "", content, flags=re.MULTILINE)
                content = re.sub(r"\n```\s*$", "", content.strip())

                spec_path = self.parser.get_spec_path(component.name)
                os.makedirs(os.path.dirname(spec_path) or ".", exist_ok=True)

                with open(spec_path, "w") as f:
                    f.write(content)

                created_paths.append(spec_path)
            except Exception:
                pass

        return created_paths

    def compose(
        self,
        request: str,
        auto_accept: bool = False,
        context: Optional[dict] = None,
    ) -> CompositionResult:
        """Full composition workflow: draft architecture then generate specs."""
        context = context or {}

        # Discover existing specs
        existing_specs = [
            self.parser.get_module_name(s)
            for s in self.parser.list_specs()
        ]
        if existing_specs:
            context.setdefault("existing_specs", existing_specs)

        # Draft architecture
        architecture = self.draft_architecture(request, context=context)

        # Check if empty
        if not architecture.components:
            return CompositionResult(
                architecture=architecture,
                cancelled=True,
                ready_for_build=False,
            )

        # Generate specs
        spec_paths = self.generate_specs(architecture)

        return CompositionResult(
            architecture=architecture,
            spec_paths=spec_paths,
            ready_for_build=True,
        )
