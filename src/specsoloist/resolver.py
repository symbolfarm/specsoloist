"""Dependency resolution for multi-spec builds.

Builds dependency graphs from specs and computes valid build orders.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Set

from .parser import SpecParser, ParsedSpec


class CircularDependencyError(Exception):
    """Raised when specs form a dependency cycle."""

    def __init__(self, cycle: List[str]):
        """Initialize with the detected cycle path.

        Args:
            cycle: Ordered list of spec names forming the cycle.
        """
        self.cycle = cycle
        path = " -> ".join(cycle + [cycle[0]])
        super().__init__(f"Circular dependency detected: {path}")


class MissingDependencyError(Exception):
    """Raised when a spec depends on one that doesn't exist."""

    def __init__(self, spec: str, missing: str):
        """Initialize with the spec and the missing dependency name.

        Args:
            spec: Name of the spec that has an unresolvable dependency.
            missing: Name of the dependency that could not be found.
        """
        self.spec = spec
        self.missing = missing
        super().__init__(f"Spec '{spec}' depends on '{missing}', which does not exist")


@dataclass
class DependencyGraph:
    """Represents dependency relationships between specs."""

    _forward: Dict[str, List[str]] = field(default_factory=dict)
    _reverse: Dict[str, List[str]] = field(default_factory=dict)
    specs: Set[str] = field(default_factory=set)

    def add_spec(self, name: str, depends_on: List[str] = None):
        """Register a spec and its dependencies in the graph.

        Args:
            name: Spec name to register.
            depends_on: List of spec names this spec depends on.
        """
        depends_on = depends_on or []
        self.specs.add(name)
        self._forward[name] = depends_on
        self._reverse.setdefault(name, [])
        for dep in depends_on:
            self.specs.add(dep)
            self._reverse.setdefault(dep, [])
            self._reverse[dep].append(name)

    def get_dependencies(self, name: str) -> List[str]:
        """Return the list of specs that the given spec depends on."""
        return self._forward.get(name, [])

    def get_dependents(self, name: str) -> List[str]:
        """Return the list of specs that depend on the given spec."""
        return self._reverse.get(name, [])


class DependencyResolver:
    """Resolves dependencies between specs and computes build orders."""

    def __init__(self, parser: SpecParser):
        """Initialize the resolver.

        Args:
            parser: SpecParser used to read spec frontmatter and list specs.
        """
        self.parser = parser

    def build_graph(self, spec_names: List[str] = None) -> DependencyGraph:
        """Build a DependencyGraph from spec frontmatter.

        Args:
            spec_names: Specs to include. Defaults to all specs in the src directory.

        Returns:
            DependencyGraph with all dependency relationships populated.

        Raises:
            MissingDependencyError: If a spec depends on a name that doesn't exist.
        """
        if spec_names is None:
            spec_names = [s.replace(".spec.md", "") for s in self.parser.list_specs()]

        graph = DependencyGraph()

        for name in spec_names:
            spec = self.parser.parse_spec(name)
            deps = self._extract_deps(spec)
            graph.add_spec(name, deps)

        # Validate all dependencies exist
        for name in graph.specs:
            for dep in graph.get_dependencies(name):
                if dep not in spec_names and not self.parser.spec_exists(dep):
                    raise MissingDependencyError(name, dep)

        return graph

    def _extract_deps(self, spec: ParsedSpec) -> List[str]:
        seen = set()
        result = []

        def add(name: str):
            clean = name.replace(".spec.md", "")
            if clean not in seen:
                seen.add(clean)
                result.append(clean)

        for dep in spec.metadata.dependencies:
            if isinstance(dep, dict) and "from" in dep:
                add(dep["from"])
            elif isinstance(dep, str):
                add(dep)

        if spec.schema and spec.schema.steps:
            for step in spec.schema.steps:
                add(step.spec)

        return result

    def resolve_build_order(self, spec_names: List[str] = None) -> List[str]:
        """Return a linear build order with dependencies before dependents.

        Raises:
            CircularDependencyError: If specs form a dependency cycle.
        """
        graph = self.build_graph(spec_names)
        return self._sorted_linear(graph)

    def get_parallel_build_order(self, spec_names: List[str] = None) -> List[List[str]]:
        """Return specs grouped into parallel build levels.

        Each level is a list of specs that can be compiled concurrently because
        all their dependencies appear in earlier levels.
        """
        graph = self.build_graph(spec_names)
        return self._sorted_levels(graph)

    def get_affected_specs(self, changed_spec: str, graph: DependencyGraph = None) -> List[str]:
        """Return all specs that transitively depend on changed_spec, in build order.

        Args:
            changed_spec: The spec that changed.
            graph: Pre-built dependency graph. Built from all specs if not provided.
        """
        if graph is None:
            graph = self.build_graph()

        affected = set()
        queue = deque([changed_spec])
        while queue:
            current = queue.popleft()
            if current in affected:
                continue
            affected.add(current)
            queue.extend(graph.get_dependents(current))

        # Return in valid build order
        full_order = self._sorted_linear(graph)
        return [s for s in full_order if s in affected]

    # -- internals --

    def _sorted_linear(self, graph: DependencyGraph) -> List[str]:
        in_deg = {s: len(graph.get_dependencies(s)) for s in graph.specs}
        ready = sorted(s for s, d in in_deg.items() if d == 0)
        order = []

        while ready:
            node = ready.pop(0)
            order.append(node)
            for dep in graph.get_dependents(node):
                in_deg[dep] -= 1
                if in_deg[dep] == 0:
                    ready.append(dep)
            ready.sort()

        if len(order) != len(graph.specs):
            cycle = self._detect_cycle(graph, set(graph.specs) - set(order))
            raise CircularDependencyError(cycle)

        return order

    def _sorted_levels(self, graph: DependencyGraph) -> List[List[str]]:
        in_deg = {s: len(graph.get_dependencies(s)) for s in graph.specs}
        current = sorted(s for s, d in in_deg.items() if d == 0)
        levels = []
        seen = set()

        while current:
            levels.append(current)
            seen.update(current)
            nxt = []
            for node in current:
                for dep in graph.get_dependents(node):
                    in_deg[dep] -= 1
                    if in_deg[dep] == 0:
                        nxt.append(dep)
            current = sorted(nxt)

        if len(seen) != len(graph.specs):
            cycle = self._detect_cycle(graph, set(graph.specs) - seen)
            raise CircularDependencyError(cycle)

        return levels

    def _detect_cycle(self, graph: DependencyGraph, candidates: Set[str]) -> List[str]:
        visited = set()
        path = []

        def walk(node: str) -> List[str]:
            if node in path:
                return path[path.index(node):]
            if node in visited:
                return []
            visited.add(node)
            path.append(node)
            for dep in graph.get_dependencies(node):
                if dep in candidates:
                    found = walk(dep)
                    if found:
                        return found
            path.pop()
            return []

        for node in sorted(candidates):
            result = walk(node)
            if result:
                return result

        return list(candidates)[:1]
