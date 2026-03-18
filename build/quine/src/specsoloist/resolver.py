"""Dependency resolution for multi-spec builds."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    pass


class CircularDependencyError(Exception):
    """Exception raised when specs form a dependency cycle."""

    def __init__(self, cycle: list[str]) -> None:
        self.cycle = cycle
        super().__init__(
            f"Circular dependency detected: {' -> '.join(cycle)}"
        )


class MissingDependencyError(Exception):
    """Exception raised when a spec depends on one that doesn't exist."""

    def __init__(self, spec: str, missing: str) -> None:
        self.spec = spec
        self.missing = missing
        super().__init__(
            f"Spec '{spec}' depends on '{missing}', which doesn't exist"
        )


class DependencyGraph:
    """A dependency graph with methods to query relationships."""

    def __init__(self) -> None:
        self._specs: set[str] = set()
        self._dependencies: dict[str, list[str]] = {}
        self._dependents: dict[str, list[str]] = {}

    def add_spec(self, name: str, depends_on: Optional[list[str]] = None) -> None:
        """Add a spec and its dependencies to the graph."""
        self._specs.add(name)
        deps = depends_on or []
        self._dependencies[name] = deps

        # Ensure name appears in dependents map
        if name not in self._dependents:
            self._dependents[name] = []

        # Update reverse mappings
        for dep in deps:
            if dep not in self._dependents:
                self._dependents[dep] = []
            if name not in self._dependents[dep]:
                self._dependents[dep].append(name)

    def get_dependencies(self, name: str) -> list[str]:
        """Returns the direct dependencies of the named spec."""
        return self._dependencies.get(name, [])

    def get_dependents(self, name: str) -> list[str]:
        """Returns the specs that directly depend on the named spec."""
        return self._dependents.get(name, [])


class DependencyResolver:
    """The main resolver that builds graphs and computes build orders."""

    def __init__(self, parser: object) -> None:
        """Initialize with a SpecParser instance."""
        self.parser = parser

    def _extract_dep_name(self, dep: object) -> str:
        """Extract spec name from a dependency (string or dict)."""
        if isinstance(dep, dict):
            raw = dep.get("from", "")
        else:
            raw = str(dep)
        # Strip .spec.md extension
        return raw.replace(".spec.md", "")

    def _get_spec_deps(self, spec: object) -> list[str]:
        """Get dependency names from a parsed spec."""
        deps = []
        metadata_deps = getattr(spec.metadata, "dependencies", []) or []
        for dep in metadata_deps:
            name = self._extract_dep_name(dep)
            if name:
                deps.append(name)

        # Also check workflow steps
        if hasattr(spec, "schema") and spec.schema:
            steps = getattr(spec.schema, "steps", None)
            if steps:
                for step in steps:
                    if hasattr(step, "spec") and step.spec:
                        dep_name = step.spec.replace(".spec.md", "")
                        if dep_name not in deps:
                            deps.append(dep_name)

        return deps

    def build_graph(self, spec_names: Optional[list[str]] = None) -> DependencyGraph:
        """Build a dependency graph from specs."""
        if spec_names is None:
            spec_names = self.parser.list_specs()

        # Parse all specs
        parsed_specs = {}
        for name in spec_names:
            parsed_specs[name] = self.parser.parse(name)

        graph = DependencyGraph()
        available = set(spec_names)

        for name in spec_names:
            spec = parsed_specs[name]
            deps = self._get_spec_deps(spec)

            # Validate dependencies exist
            for dep in deps:
                if dep not in available:
                    # Check if the parser knows about it
                    try:
                        self.parser.parse(dep)
                    except Exception:
                        raise MissingDependencyError(name, dep)

            graph.add_spec(name, deps)

        return graph

    def resolve_build_order(self, spec_names: Optional[list[str]] = None) -> list[str]:
        """Compute a linear build order for specs."""
        if spec_names is None:
            spec_names = self.parser.list_specs()

        graph = self.build_graph(spec_names)
        return self._topological_sort(list(spec_names), graph)

    def _topological_sort(
        self, spec_names: list[str], graph: DependencyGraph
    ) -> list[str]:
        """Perform topological sort with cycle detection."""
        visited: set[str] = set()
        in_progress: set[str] = set()
        result: list[str] = []

        def visit(name: str, path: list[str]) -> None:
            if name in in_progress:
                cycle_start = path.index(name)
                raise CircularDependencyError(path[cycle_start:] + [name])
            if name in visited:
                return

            in_progress.add(name)
            # Sort deps alphabetically for determinism
            deps = sorted(graph.get_dependencies(name))
            for dep in deps:
                visit(dep, path + [name])
            in_progress.remove(name)
            visited.add(name)
            result.append(name)

        # Process in alphabetical order for determinism
        for name in sorted(spec_names):
            if name not in visited:
                visit(name, [])

        return result

    def get_parallel_build_order(
        self, spec_names: Optional[list[str]] = None
    ) -> list[list[str]]:
        """Compute build order grouped into parallelizable levels."""
        if spec_names is None:
            spec_names = self.parser.list_specs()

        graph = self.build_graph(spec_names)
        names_set = set(spec_names)

        # Compute levels using Kahn's algorithm
        in_degree: dict[str, int] = {name: 0 for name in spec_names}
        for name in spec_names:
            for dep in graph.get_dependencies(name):
                if dep in names_set:
                    in_degree[name] += 1

        levels = []
        remaining = set(spec_names)

        while remaining:
            # Find specs with no remaining dependencies
            level = sorted(
                [name for name in remaining if in_degree[name] == 0]
            )

            if not level:
                # Cycle detected
                cycle = self._find_cycle(remaining, graph)
                raise CircularDependencyError(cycle)

            levels.append(level)
            remaining -= set(level)

            # Update in-degrees for dependents
            for name in level:
                for dependent in graph.get_dependents(name):
                    if dependent in remaining:
                        in_degree[dependent] -= 1

        return levels

    def _find_cycle(self, specs: set[str], graph: DependencyGraph) -> list[str]:
        """Find a cycle among specs using DFS."""
        visited: set[str] = set()
        in_progress: set[str] = set()

        def dfs(name: str, path: list[str]) -> Optional[list[str]]:
            if name in in_progress:
                cycle_start = path.index(name)
                return path[cycle_start:] + [name]
            if name in visited or name not in specs:
                return None
            in_progress.add(name)
            for dep in graph.get_dependencies(name):
                result = dfs(dep, path + [name])
                if result:
                    return result
            in_progress.remove(name)
            visited.add(name)
            return None

        for name in sorted(specs):
            result = dfs(name, [])
            if result:
                return result

        return list(specs)[:2]  # fallback

    def get_affected_specs(
        self, changed_spec: str, graph: Optional[DependencyGraph] = None
    ) -> list[str]:
        """Determine which specs need rebuilding when a specific spec changes."""
        if graph is None:
            graph = self.build_graph()

        # BFS to find all transitive dependents
        affected: set[str] = {changed_spec}
        queue = [changed_spec]

        while queue:
            current = queue.pop(0)
            for dependent in graph.get_dependents(current):
                if dependent not in affected:
                    affected.add(dependent)
                    queue.append(dependent)

        # Return in valid build order using topological sort
        # Only sort specs that are in the affected set
        all_names = list(affected)

        # Simple topological sort limited to only affected specs
        visited: set[str] = set()
        in_progress: set[str] = set()
        result: list[str] = []

        def visit(name: str, path: list[str]) -> None:
            if name in in_progress:
                cycle_start = path.index(name)
                raise CircularDependencyError(path[cycle_start:] + [name])
            if name in visited:
                return
            in_progress.add(name)
            # Only visit dependencies that are also affected
            deps = sorted(graph.get_dependencies(name))
            for dep in deps:
                if dep in affected:
                    visit(dep, path + [name])
            in_progress.remove(name)
            visited.add(name)
            result.append(name)

        for name in sorted(all_names):
            if name not in visited:
                visit(name, [])

        return result
