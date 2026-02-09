"""
Dependency resolution for multi-spec builds.

Provides tools to build dependency graphs, compute build orders, detect cycles,
and determine which specs are affected by changes.
"""

from typing import List, Optional, Dict, Set
from dataclasses import dataclass, field


class CircularDependencyError(Exception):
    """Exception raised when specs form a dependency cycle."""

    def __init__(self, cycle: List[str]):
        """
        Initialize the error.

        Args:
            cycle: List of spec names forming the cycle.
        """
        self.cycle = cycle
        cycle_str = " -> ".join(cycle + [cycle[0]])
        super().__init__(f"Circular dependency detected: {cycle_str}")


class MissingDependencyError(Exception):
    """Exception raised when a spec depends on one that doesn't exist."""

    def __init__(self, spec: str, missing: str):
        """
        Initialize the error.

        Args:
            spec: Name of the spec that declared the dependency.
            missing: Name of the dependency that doesn't exist.
        """
        self.spec = spec
        self.missing = missing
        super().__init__(f"Spec '{spec}' depends on missing spec '{missing}'")


class DependencyGraph:
    """A data structure representing dependency relationships between specs."""

    def __init__(self):
        """Initialize an empty dependency graph."""
        self._dependencies: Dict[str, Set[str]] = {}
        self._dependents: Dict[str, Set[str]] = {}

    def add_spec(self, name: str, depends_on: Optional[List[str]] = None) -> None:
        """
        Add a spec and its dependencies to the graph.

        Args:
            name: The spec name.
            depends_on: Optional list of spec names this one depends on.
        """
        # Ensure the spec exists in both directions
        if name not in self._dependencies:
            self._dependencies[name] = set()
        if name not in self._dependents:
            self._dependents[name] = set()

        if depends_on:
            for dep in depends_on:
                self._dependencies[name].add(dep)
                if dep not in self._dependents:
                    self._dependents[dep] = set()
                self._dependents[dep].add(name)

    def get_dependencies(self, name: str) -> List[str]:
        """
        Get the direct dependencies of a spec.

        Args:
            name: The spec name.

        Returns:
            List of spec names this one depends on. Empty list if not in graph.
        """
        if name not in self._dependencies:
            return []
        return sorted(list(self._dependencies[name]))

    def get_dependents(self, name: str) -> List[str]:
        """
        Get specs that directly depend on this one.

        Args:
            name: The spec name.

        Returns:
            List of spec names that depend on this one. Empty list if not in graph.
        """
        if name not in self._dependents:
            return []
        return sorted(list(self._dependents[name]))

    def _get_all_specs(self) -> List[str]:
        """Internal method to get all specs in the graph."""
        return sorted(list(self._dependencies.keys()))


class DependencyResolver:
    """Main resolver for building graphs and computing build orders."""

    def __init__(self, parser):
        """
        Initialize the resolver.

        Args:
            parser: A SpecParser instance from specsoloist.parser
        """
        self.parser = parser

    def build_graph(self, spec_names: Optional[List[str]] = None) -> DependencyGraph:
        """
        Build a dependency graph from specs.

        Args:
            spec_names: List of spec names to include. If None, discover all from parser.

        Returns:
            A DependencyGraph object.

        Raises:
            MissingDependencyError: If a dependency doesn't exist.
        """
        if spec_names is None:
            # Discover all available specs from parser
            spec_list = self.parser.list_specs()
            spec_names = [s.replace(".spec.md", "") for s in spec_list]

        graph = DependencyGraph()

        # Add all specs first
        for spec_name in spec_names:
            graph.add_spec(spec_name)

        # Now parse each spec and add dependencies
        for spec_name in spec_names:
            try:
                parsed = self.parser.parse_spec(spec_name)
            except FileNotFoundError:
                raise MissingDependencyError(spec_name, spec_name)

            dependencies = []

            # Extract dependencies from metadata
            if parsed.metadata.dependencies:
                for dep in parsed.metadata.dependencies:
                    if isinstance(dep, str):
                        dep_name = dep.replace(".spec.md", "")
                        dependencies.append(dep_name)
                    elif isinstance(dep, dict) and "from" in dep:
                        dep_name = dep["from"].replace(".spec.md", "")
                        dependencies.append(dep_name)

            # Extract dependencies from workflow steps
            if parsed.steps:
                for step in parsed.steps:
                    step_spec = step.spec.replace(".spec.md", "")
                    dependencies.append(step_spec)

            # Remove duplicates while preserving as list
            dependencies = list(set(dependencies))

            # Validate all dependencies exist
            for dep_name in dependencies:
                if dep_name not in spec_names:
                    # Check if it exists in parser storage
                    if not self.parser.spec_exists(dep_name):
                        raise MissingDependencyError(spec_name, dep_name)

            graph.add_spec(spec_name, dependencies)

        return graph

    def resolve_build_order(self, spec_names: Optional[List[str]] = None) -> List[str]:
        """
        Compute a linear build order for specs.

        Args:
            spec_names: List of spec names to order. If None, use all specs.

        Returns:
            List of spec names in dependency order.

        Raises:
            CircularDependencyError: If a cycle is detected.
            MissingDependencyError: If a dependency doesn't exist.
        """
        graph = self.build_graph(spec_names)
        specs = graph._get_all_specs()

        result = []
        visited = set()
        visiting = set()

        def visit(spec: str) -> None:
            """Visit a spec in depth-first order, detecting cycles."""
            if spec in visited:
                return

            if spec in visiting:
                # Cycle detected - find it
                cycle = self._find_cycle(spec, graph)
                raise CircularDependencyError(cycle)

            visiting.add(spec)

            # Visit all dependencies first
            for dep in graph.get_dependencies(spec):
                visit(dep)

            visiting.remove(spec)
            visited.add(spec)
            result.append(spec)

        # Visit all specs in sorted order for determinism
        for spec in sorted(specs):
            visit(spec)

        return result

    def get_parallel_build_order(self, spec_names: Optional[List[str]] = None) -> List[List[str]]:
        """
        Compute build order grouped into parallelizable levels.

        Args:
            spec_names: List of spec names to order. If None, use all specs.

        Returns:
            List of levels, where each level is a list of specs that can be built concurrently.

        Raises:
            CircularDependencyError: If a cycle is detected.
            MissingDependencyError: If a dependency doesn't exist.
        """
        graph = self.build_graph(spec_names)
        specs = set(graph._get_all_specs())

        levels = []
        remaining = specs.copy()

        while remaining:
            # Find all specs with no unresolved dependencies
            current_level = []
            for spec in sorted(remaining):
                deps = set(graph.get_dependencies(spec))
                unresolved = deps & remaining
                if not unresolved:
                    current_level.append(spec)

            if not current_level:
                # No specs with resolved dependencies - must be a cycle
                cycle = self._find_cycle_in_set(remaining, graph)
                raise CircularDependencyError(cycle)

            levels.append(current_level)
            remaining -= set(current_level)

        return levels

    def get_affected_specs(
        self, changed_spec: str, graph: Optional[DependencyGraph] = None
    ) -> List[str]:
        """
        Determine which specs need rebuilding when a spec changes.

        Args:
            changed_spec: Name of the spec that changed.
            graph: Optional pre-built DependencyGraph. If None, builds one.

        Returns:
            List of all affected specs (including the changed spec) in build order.
        """
        if graph is None:
            graph = self.build_graph()

        affected = set()
        to_visit = [changed_spec]

        # BFS to find all transitive dependents
        while to_visit:
            spec = to_visit.pop(0)
            if spec in affected:
                continue
            affected.add(spec)
            # Add all specs that depend on this one
            for dependent in graph.get_dependents(spec):
                if dependent not in affected:
                    to_visit.append(dependent)

        # Sort affected specs in topological order
        # We need to build only a subgraph containing the affected specs
        affected_list = list(affected)
        result = []
        visited = set()
        visiting = set()

        def visit(spec: str) -> None:
            """Visit a spec in dependency order, only considering affected specs."""
            if spec in visited:
                return
            if spec in visiting:
                # Cycle in affected specs
                cycle = self._find_cycle(spec, graph)
                raise CircularDependencyError(cycle)

            visiting.add(spec)

            # Visit dependencies that are also affected
            for dep in graph.get_dependencies(spec):
                if dep in affected:
                    visit(dep)

            visiting.remove(spec)
            visited.add(spec)
            result.append(spec)

        # Visit all affected specs in sorted order for determinism
        for spec in sorted(affected_list):
            visit(spec)

        return result

    def _find_cycle(self, start_spec: str, graph: DependencyGraph) -> List[str]:
        """
        Find a cycle starting from a given spec.

        Args:
            start_spec: The spec where the cycle was detected.
            graph: The dependency graph.

        Returns:
            List of spec names forming the cycle.
        """
        visited = set()
        path = []

        def dfs(spec: str) -> bool:
            """DFS to find a cycle."""
            if spec in path:
                # Found the cycle
                idx = path.index(spec)
                return path[idx:] + [spec]
            if spec in visited:
                return None
            visited.add(spec)
            path.append(spec)

            for dep in graph.get_dependencies(spec):
                result = dfs(dep)
                if result:
                    return result

            path.pop()
            return None

        cycle = dfs(start_spec)
        if cycle:
            # Remove the duplicate at the end
            return cycle[:-1]
        return [start_spec]

    def _find_cycle_in_set(self, specs: Set[str], graph: DependencyGraph) -> List[str]:
        """
        Find a cycle within a set of specs.

        Args:
            specs: Set of spec names that form a cycle.
            graph: The dependency graph.

        Returns:
            List of spec names forming the cycle.
        """
        for spec in specs:
            try:
                cycle = self._find_cycle(spec, graph)
                if cycle:
                    return cycle
            except Exception:
                pass
        return list(specs)
