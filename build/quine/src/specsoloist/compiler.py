"""Compiles SpecSoloist specifications into implementation code and test suites."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from specsoloist.schema import Arrangement


def _strip_fences(code: str) -> str:
    """Strip markdown code fences from LLM response."""
    # Remove opening fence (```python, ```typescript, ``` etc)
    code = re.sub(r"^```[a-zA-Z]*\n", "", code, flags=re.MULTILINE)
    # Remove closing fence
    code = re.sub(r"\n```\s*$", "", code.strip())
    # Also handle if entire response is fenced
    if code.startswith("```"):
        lines = code.split("\n")
        # Remove first line (```lang)
        lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)
    return code.strip()


def _build_dep_context(spec: Any, reference_specs: Optional[dict] = None) -> str:
    """Build dependency context string from spec metadata."""
    deps = getattr(spec.metadata, "dependencies", [])
    if not deps:
        return ""

    lines = ["## Dependencies"]
    for dep in deps:
        if isinstance(dep, dict):
            dep_name = dep.get("from", "").replace(".spec.md", "")
        else:
            dep_name = str(dep)

        if reference_specs and dep_name in reference_specs:
            ref_spec = reference_specs[dep_name]
            lines.append(f"\n### {dep_name} (reference API documentation)")
            lines.append(ref_spec.content)
        else:
            lines.append(f"- {dep_name}: import from specsoloist.{dep_name} or spechestra.{dep_name}")

    return "\n".join(lines)


def _build_arrangement_context(arrangement: Any) -> str:
    """Build arrangement context string."""
    if arrangement is None:
        return ""

    lines = [
        "## Arrangement",
        f"- Target language: {arrangement.target_language}",
    ]

    if hasattr(arrangement, "environment") and arrangement.environment:
        env = arrangement.environment
        if env.dependencies:
            lines.append("- Dependencies: " + ", ".join(
                f"{k}=={v}" for k, v in env.dependencies.items()
            ))

    if hasattr(arrangement, "build_commands") and arrangement.build_commands:
        lines.append(f"- Test command: {arrangement.build_commands.test}")

    if hasattr(arrangement, "constraints") and arrangement.constraints:
        lines.append("- Constraints: " + "; ".join(arrangement.constraints))

    if hasattr(arrangement, "env_vars") and arrangement.env_vars:
        lines.append("- Required env vars: " + ", ".join(arrangement.env_vars.keys()))

    return "\n".join(lines)


class SpecCompiler:
    """Compiler for specs."""

    def __init__(self, provider: Any, global_context: str = "") -> None:
        """Initialize with an LLM provider and optional global context."""
        self.provider = provider
        self.global_context = global_context

    def _build_prompt(
        self,
        spec: Any,
        task: str,
        arrangement: Optional[Any] = None,
        reference_specs: Optional[dict] = None,
        extra_context: str = "",
    ) -> str:
        """Build a compilation prompt."""
        parts = []

        if self.global_context:
            parts.append(f"## Project Context\n{self.global_context}")

        arrangement_ctx = _build_arrangement_context(arrangement)
        if arrangement_ctx:
            parts.append(arrangement_ctx)

        dep_context = _build_dep_context(spec, reference_specs)
        if dep_context:
            parts.append(dep_context)

        if extra_context:
            parts.append(extra_context)

        parts.append(f"## Spec\n{spec.content}")
        parts.append(task)

        return "\n\n".join(parts)

    def compile_code(
        self,
        spec: Any,
        model: Optional[str] = None,
        arrangement: Optional[Any] = None,
        reference_specs: Optional[dict] = None,
    ) -> str:
        """Compile a function/bundle spec to implementation code."""
        lang = "Python"
        if arrangement and hasattr(arrangement, "target_language"):
            lang = arrangement.target_language.capitalize()

        task = (
            f"Implement the above spec in {lang}. "
            "Write complete, working implementation code. "
            "Do not include test code. "
            "Return only the code, no explanations."
        )

        prompt = self._build_prompt(
            spec, task, arrangement=arrangement, reference_specs=reference_specs
        )
        response = self.provider.generate(prompt, model=model)
        return _strip_fences(response)

    def compile_typedef(
        self,
        spec: Any,
        model: Optional[str] = None,
        arrangement: Optional[Any] = None,
    ) -> str:
        """Compile a type spec to type definition code."""
        lang = "Python"
        if arrangement and hasattr(arrangement, "target_language"):
            lang = arrangement.target_language.capitalize()

        task = (
            f"Define the types described in this spec using idiomatic {lang} constructs. "
            "Return only the type definitions, no test code."
        )

        prompt = self._build_prompt(spec, task, arrangement=arrangement)
        response = self.provider.generate(prompt, model=model)
        return _strip_fences(response)

    def compile_orchestrator(
        self,
        spec: Any,
        model: Optional[str] = None,
        arrangement: Optional[Any] = None,
    ) -> str:
        """Compile a workflow/orchestrator spec to execution code."""
        # Extract step references for context
        steps_info = ""
        if hasattr(spec, "schema") and spec.schema and hasattr(spec.schema, "steps"):
            if spec.schema.steps:
                step_names = [s.spec for s in spec.schema.steps]
                steps_info = f"\n## Steps\nThis workflow orchestrates: {', '.join(step_names)}"

        task = (
            "Implement the workflow described in this spec. "
            "Handle state passing between steps. "
            "Return only the implementation code."
        )

        prompt = self._build_prompt(
            spec, task, arrangement=arrangement, extra_context=steps_info
        )
        response = self.provider.generate(prompt, model=model)
        return _strip_fences(response)

    def compile_tests(
        self,
        spec: Any,
        model: Optional[str] = None,
        arrangement: Optional[Any] = None,
        reference_specs: Optional[dict] = None,
    ) -> str:
        """Generate a test suite for a spec."""
        lang = "Python"
        framework = "pytest"
        if arrangement and hasattr(arrangement, "target_language"):
            lang = arrangement.target_language.capitalize()
            if lang.lower() == "typescript":
                framework = "node:test"

        task = (
            f"Write a comprehensive test suite using {framework} for the above spec. "
            "Cover all scenarios and edge cases described. "
            "Return only the test code."
        )

        prompt = self._build_prompt(
            spec, task, arrangement=arrangement, reference_specs=reference_specs
        )
        response = self.provider.generate(prompt, model=model)
        return _strip_fences(response)

    def generate_fix(
        self,
        spec: Any,
        code_content: str,
        test_content: str,
        error_log: str,
        model: Optional[str] = None,
        arrangement: Optional[Any] = None,
    ) -> str:
        """Generate a fix for failing tests."""
        prompt = f"""## Spec (Source of Truth)
{spec.content}

## Current Implementation
{code_content}

## Current Tests
{test_content}

## Error Output
{error_log}

Fix the implementation and/or tests so that all tests pass.
The spec is the source of truth — do not change the spec's intent.

Return fixed files using this format:
### FILE: <path>
<file contents>
### END

Only include files that need changes."""

        if arrangement:
            arrangement_ctx = _build_arrangement_context(arrangement)
            if arrangement_ctx:
                prompt = arrangement_ctx + "\n\n" + prompt

        if self.global_context:
            prompt = f"## Project Context\n{self.global_context}\n\n" + prompt

        return self.provider.generate(prompt, model=model)

    def parse_fix_response(self, response: str) -> dict[str, str]:
        """Parse the LLM fix response to extract file contents."""
        result = {}
        pattern = r"### FILE: (.+?)\n(.*?)### END"
        matches = re.findall(pattern, response, re.DOTALL)

        for path, content in matches:
            path = path.strip()
            content = _strip_fences(content.strip())
            result[path] = content

        return result
