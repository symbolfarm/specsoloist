"""
Dependency resolution for multi-spec compilation.

Builds a dependency graph from specs and computes build order
via topological sort.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set

from .parser import SpecParser, ParsedSpec


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected."""

    def __init__(self, cycle: List[str]):
        self.cycle = cycle
        cycle_str = " -> ".join(cycle + [cycle[0]])
        super().__init__(f"Circular dependency detected: {cycle_str}")


class MissingDependencyError(Exception):
    """Raised when a dependency references a non-existent spec."""

    def __init__(self, spec: str, missing: str):
        self.spec = spec
        self.missing = missing
        super().__init__(f"Spec '{spec}' depends on '{missing}', which does not exist")


@dataclass
class DependencyGraph:
    """
    Represents the dependency relationships between specs.
    """
    # Map of spec name -> list of specs it depends on
    dependencies: Dict[str, List[str]] = field(default_factory=dict)

    # Map of spec name -> list of specs that depend on it
    dependents: Dict[str, List[str]] = field(default_factory=dict)

    # All spec names in the graph
    specs: Set[str] = field(default_factory=set)

    def add_spec(self, name: str, depends_on: List[str] = None):
        """Add a spec and its dependencies to the graph."""
        depends_on = depends_on or []
        self.specs.add(name)
        self.dependencies[name] = depends_on

        # Initialize dependents entry
        if name not in self.dependents:
            self.dependents[name] = []

        # Update reverse mapping
        for dep in depends_on:
            if dep not in self.dependents:
                self.dependents[dep] = []
            self.dependents[dep].append(name)
            self.specs.add(dep)

    def get_dependencies(self, name: str) -> List[str]:
        """Get direct dependencies of a spec."""
        return self.dependencies.get(name, [])

    def get_dependents(self, name: str) -> List[str]:
        """Get specs that directly depend on this spec."""
        return self.dependents.get(name, [])


class DependencyResolver:
    """
    Resolves dependencies between specs and computes build order.
    """

    def __init__(self, parser: SpecParser):
        self.parser = parser

    def build_graph(self, spec_names: List[str] = None) -> DependencyGraph:
        """
        Build a dependency graph from specs.

        Args:
            spec_names: List of spec names to include. If None, includes all specs.

        Returns:
            A DependencyGraph representing the relationships.

        Raises:
            MissingDependencyError: If a dependency references a non-existent spec.
        """
        if spec_names is None:
            spec_names = [s.replace(".spec.md", "") for s in self.parser.list_specs()]

        graph = DependencyGraph()

        for name in spec_names:
            spec = self.parser.parse_spec(name)
            deps = self._extract_dependencies(spec)
            graph.add_spec(name, deps)

        # Validate all dependencies exist
        for name in graph.specs:
            for dep in graph.get_dependencies(name):
                if dep not in spec_names:
                    # Check if it exists but wasn't in our list
                    if not self.parser.spec_exists(dep):
                        raise MissingDependencyError(name, dep)

        return graph

    def _extract_dependencies(self, spec: ParsedSpec) -> List[str]:
        """Extract dependency spec names from a parsed spec."""
        deps = []
        for dep in spec.metadata.dependencies:
            if isinstance(dep, dict) and "from" in dep:
                # Format: {name: "User", from: "types.spec.md"}
                from_spec = dep["from"].replace(".spec.md", "")
                if from_spec not in deps:
                    deps.append(from_spec)
            elif isinstance(dep, str):
                # Simple format: just the spec name
                from_spec = dep.replace(".spec.md", "")
                if from_spec not in deps:
                    deps.append(from_spec)
        return deps

    def resolve_build_order(self, spec_names: List[str] = None) -> List[str]:
        """
        Compute the build order for specs using topological sort.

        Specs with no dependencies come first, then specs that depend
        only on already-built specs, etc.

        Args:
            spec_names: List of spec names to build. If None, includes all specs.

        Returns:
            List of spec names in build order.

        Raises:
            CircularDependencyError: If a circular dependency is detected.
            MissingDependencyError: If a dependency references a non-existent spec.
        """
        graph = self.build_graph(spec_names)
        return self._topological_sort(graph)

    def _topological_sort(self, graph: DependencyGraph) -> List[str]:
        """
        Kahn's algorithm for topological sort.

        Returns specs in dependency order (dependencies before dependents).
        """
        # Calculate in-degree (number of dependencies) for each spec
        in_degree = {name: len(graph.get_dependencies(name)) for name in graph.specs}

        # Start with specs that have no dependencies
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            # Sort for deterministic output
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            # Reduce in-degree for dependents
            for dependent in graph.get_dependents(current):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # Check for cycles
        if len(result) != len(graph.specs):
            # Find the cycle for error reporting
            remaining = [name for name in graph.specs if name not in result]
            cycle = self._find_cycle(graph, remaining)
            raise CircularDependencyError(cycle)

        return result

    def _find_cycle(self, graph: DependencyGraph, remaining: List[str]) -> List[str]:
        """Find a cycle in the remaining nodes for error reporting."""
        # Simple DFS to find a cycle
        visited = set()
        path = []

        def dfs(node: str) -> List[str]:
            if node in path:
                # Found cycle
                cycle_start = path.index(node)
                return path[cycle_start:]
            if node in visited:
                return []

            visited.add(node)
            path.append(node)

            for dep in graph.get_dependencies(node):
                if dep in remaining:
                    cycle = dfs(dep)
                    if cycle:
                        return cycle

            path.pop()
            return []

        for node in remaining:
            cycle = dfs(node)
            if cycle:
                return cycle

        return remaining[:1]  # Fallback

    def get_parallel_build_order(self, spec_names: List[str] = None) -> List[List[str]]:
        """
        Compute build order grouped into parallelizable levels.

        Each level contains specs that only depend on specs from previous
        levels, so all specs within a level can be compiled in parallel.

        Args:
            spec_names: List of spec names to build. If None, includes all specs.

        Returns:
            List of levels, where each level is a list of spec names
            that can be compiled in parallel.

        Raises:
            CircularDependencyError: If a circular dependency is detected.
            MissingDependencyError: If a dependency references a non-existent spec.
        """
        graph = self.build_graph(spec_names)
        return self._topological_sort_levels(graph)

    def _topological_sort_levels(self, graph: DependencyGraph) -> List[List[str]]:
        """
        Modified Kahn's algorithm that returns specs grouped by levels.

        Level 0: specs with no dependencies
        Level 1: specs that only depend on level 0
        Level N: specs that only depend on levels 0..N-1
        """
        # Calculate in-degree (number of dependencies) for each spec
        in_degree = {name: len(graph.get_dependencies(name)) for name in graph.specs}

        # Start with specs that have no dependencies (level 0)
        current_level = sorted([name for name, degree in in_degree.items() if degree == 0])
        levels = []
        processed = set()

        while current_level:
            levels.append(current_level)
            processed.update(current_level)

            next_level = []
            for name in current_level:
                # Reduce in-degree for dependents
                for dependent in graph.get_dependents(name):
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        next_level.append(dependent)

            current_level = sorted(next_level)

        # Check for cycles
        if len(processed) != len(graph.specs):
            remaining = [name for name in graph.specs if name not in processed]
            cycle = self._find_cycle(graph, remaining)
            raise CircularDependencyError(cycle)

        return levels

    def get_affected_specs(self, changed_spec: str, graph: DependencyGraph = None) -> List[str]:
        """
        Get all specs that need to be rebuilt when a spec changes.

        This includes the changed spec and all specs that depend on it
        (transitively).

        Args:
            changed_spec: The spec that changed.
            graph: Pre-built graph, or None to build a new one.

        Returns:
            List of spec names that need rebuilding, in build order.
        """
        if graph is None:
            graph = self.build_graph()

        affected = set()
        queue = [changed_spec]

        while queue:
            current = queue.pop(0)
            if current in affected:
                continue
            affected.add(current)
            queue.extend(graph.get_dependents(current))

        # Return in build order
        full_order = self._topological_sort(graph)
        return [s for s in full_order if s in affected]
