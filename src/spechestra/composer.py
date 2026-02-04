"""
SpecComposer - Drafts architecture and specs from natural language.

This is the "vibe-coding" entry point: users describe what they want,
and SpecComposer figures out the architecture and generates specs.
"""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from specsoloist.config import SpecSoloistConfig
from specsoloist.parser import SpecParser
from specsoloist.providers import LLMProvider


@dataclass
class ComponentDef:
    """Definition of a component in an architecture."""
    name: str
    type: str  # function, type, bundle, module, workflow
    description: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)


@dataclass
class Architecture:
    """An architecture plan for a project."""
    components: List[ComponentDef]
    dependencies: Dict[str, List[str]]  # component -> [dependencies]
    build_order: List[str]
    description: str = ""


@dataclass
class CompositionResult:
    """Result of a compose operation."""
    architecture: Architecture
    spec_paths: List[str]
    ready_for_build: bool
    cancelled: bool = False


class SpecComposer:
    """
    Drafts architecture and specs from natural language requests.

    Usage:
        composer = SpecComposer("/path/to/project")
        result = composer.compose("Build me a todo app with auth")
        # result.spec_paths contains paths to generated specs
    """

    def __init__(
        self,
        project_dir: str,
        config: Optional[SpecSoloistConfig] = None,
        provider: Optional[LLMProvider] = None
    ):
        """
        Initialize the composer.

        Args:
            project_dir: Path to project root.
            config: Optional configuration. Loads from env if not provided.
            provider: Optional LLM provider. Created from config if not provided.
        """
        self.project_dir = os.path.abspath(project_dir)

        if config:
            self.config = config
        else:
            self.config = SpecSoloistConfig.from_env(project_dir)

        self.parser = SpecParser(self.config.src_path)
        self._provider = provider

    def _get_provider(self) -> LLMProvider:
        """Lazily create the LLM provider."""
        if self._provider is None:
            self._provider = self.config.create_provider()
        return self._provider

    def draft_architecture(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Architecture:
        """
        Draft an architecture plan from a natural language request.

        Args:
            request: Natural language description of desired software.
            context: Optional context (existing specs, constraints, etc.)

        Returns:
            Architecture object with components and dependencies.
        """
        # Build context string
        context_str = ""
        if context:
            existing_specs = context.get("existing_specs", [])
            if existing_specs:
                context_str = f"\n\nExisting specs in project: {', '.join(existing_specs)}"

        prompt = f"""You are a Software Architect designing a system based on a user request.

# User Request
{request}
{context_str}

# Instructions
1. Break down the request into discrete components (functions, types, modules).
2. Identify dependencies between components.
3. Suggest a build order (dependencies first).

# Output Format
Respond with a YAML document:

```yaml
description: Brief description of the overall architecture
components:
  - name: component_name
    type: function  # or: type, bundle, module, workflow
    description: What this component does
    dependencies: []  # list of component names this depends on

build_order:
  - component1
  - component2
```

Only output the YAML block, no other text.
"""
        response = self._get_provider().generate(prompt)

        # Parse the YAML response
        return self._parse_architecture_response(response)

    def _parse_architecture_response(self, response: str) -> Architecture:
        """Parse LLM response into Architecture object."""
        import yaml

        # Extract YAML block
        yaml_text = response
        if "```yaml" in response:
            start = response.find("```yaml") + 7
            end = response.find("```", start)
            yaml_text = response[start:end].strip()
        elif "```" in response:
            start = response.find("```") + 3
            end = response.find("```", start)
            yaml_text = response[start:end].strip()

        try:
            data = yaml.safe_load(yaml_text)
        except yaml.YAMLError:
            # Fallback: create minimal architecture
            return Architecture(
                components=[],
                dependencies={},
                build_order=[],
                description="Failed to parse architecture"
            )

        if not isinstance(data, dict):
            return Architecture(
                components=[],
                dependencies={},
                build_order=[],
                description="Invalid architecture format"
            )

        # Parse components
        components = []
        deps = {}
        for comp_data in data.get("components", []):
            comp = ComponentDef(
                name=comp_data.get("name", ""),
                type=comp_data.get("type", "function"),
                description=comp_data.get("description", ""),
                dependencies=comp_data.get("dependencies", [])
            )
            components.append(comp)
            deps[comp.name] = comp.dependencies

        return Architecture(
            components=components,
            dependencies=deps,
            build_order=data.get("build_order", []),
            description=data.get("description", "")
        )

    def generate_specs(self, architecture: Architecture) -> List[str]:
        """
        Generate spec files for each component in the architecture.

        Args:
            architecture: The architecture to generate specs for.

        Returns:
            List of paths to created spec files.
        """
        created_paths = []

        for component in architecture.components:
            # Skip if spec already exists
            if self.parser.spec_exists(component.name):
                continue

            # Generate spec content
            spec_content = self._generate_spec_content(component, architecture)

            # Write spec file
            path = os.path.join(self.config.src_path, f"{component.name}.spec.md")
            os.makedirs(os.path.dirname(path), exist_ok=True)

            with open(path, 'w') as f:
                f.write(spec_content)

            created_paths.append(path)

        return created_paths

    def _generate_spec_content(
        self,
        component: ComponentDef,
        architecture: Architecture
    ) -> str:
        """Generate spec content for a component using LLM."""
        deps_str = ""
        if component.dependencies:
            deps_str = "\ndependencies:\n" + "\n".join(
                f"  - {dep}" for dep in component.dependencies
            )

        prompt = f"""You are a Technical Writer creating a specification document.

# Component
Name: {component.name}
Type: {component.type}
Description: {component.description}
{deps_str}

# Architecture Context
{architecture.description}

# Instructions
Write a complete spec.md file for this component following this format:

```markdown
---
name: {component.name}
type: {component.type}
status: draft{deps_str if component.dependencies else ''}
---

# Overview
[1-2 sentence description]

# Interface
```yaml:schema
inputs:
  [define inputs with types]
outputs:
  [define outputs with types]
```

# Behavior
- [FR-01]: [First functional requirement]
- [FR-02]: [Second functional requirement]

# Constraints
- [NFR-01]: [Non-functional requirement]

# Contract
- Pre: [Precondition]
- Post: [Postcondition]

# Examples
| Input | Output | Notes |
|-------|--------|-------|
| | | |
```

Output ONLY the markdown content, starting with ---.
"""
        response = self._get_provider().generate(prompt)

        # Clean up response
        content = response.strip()
        if content.startswith("```markdown"):
            content = content[11:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        return content.strip()

    def compose(
        self,
        request: str,
        auto_accept: bool = False,
        context: Optional[Dict[str, Any]] = None
    ) -> CompositionResult:
        """
        Full composition workflow: draft architecture and generate specs.

        Args:
            request: Natural language description of desired software.
            auto_accept: If True, skip review prompts.
            context: Optional context (existing specs, constraints, etc.)

        Returns:
            CompositionResult with architecture and spec paths.
        """
        # Get existing specs as context
        if context is None:
            context = {}

        existing = self.parser.list_specs()
        if existing:
            context["existing_specs"] = existing

        # Draft architecture
        architecture = self.draft_architecture(request, context)

        if not architecture.components:
            return CompositionResult(
                architecture=architecture,
                spec_paths=[],
                ready_for_build=False,
                cancelled=True
            )

        # TODO: In interactive mode, present for review here
        # For now, auto-accept always

        # Generate specs
        spec_paths = self.generate_specs(architecture)

        return CompositionResult(
            architecture=architecture,
            spec_paths=spec_paths,
            ready_for_build=True
        )
