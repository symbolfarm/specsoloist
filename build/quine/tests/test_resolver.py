"""
Comprehensive tests for the dependency resolver module.

Tests cover:
- Dependency graph construction
- Build order computation
- Parallel build levels
- Affected spec detection
- Circular dependency detection
- Missing dependency detection
"""

import os
import pytest
import tempfile
from pathlib import Path
from specsoloist.parser import SpecParser
from specsoloist.resolver import (
    DependencyGraph,
    DependencyResolver,
    CircularDependencyError,
    MissingDependencyError,
)


@pytest.fixture
def temp_spec_dir():
    """Create a temporary directory for test specs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def create_spec(spec_dir: str, name: str, dependencies: list = None) -> None:
    """Helper to create a test spec file."""
    spec_content = f"""---
name: {name}
type: bundle"""

    if dependencies:
        # Format dependencies for YAML list
        deps_yaml = "\ndependencies:"
        for dep in dependencies:
            deps_yaml += f"\n  - {dep}"
        spec_content += deps_yaml

    spec_content += """
---

# Overview

Test spec for {}.

# Functions

```yaml:functions
test_func:
  inputs: {{a: integer}}
  outputs: {{result: integer}}
  behavior: "Test function"
```
""".format(name)

    path = os.path.join(spec_dir, f"{name}.spec.md")
    with open(path, 'w') as f:
        f.write(spec_content)


def create_workflow_spec(spec_dir: str, name: str, steps: list) -> None:
    """Helper to create a workflow spec with steps."""
    spec_content = f"""---
name: {name}
type: workflow
---

# Overview

Workflow test spec for {name}.

# Interface

```yaml:schema
inputs:
  input_param:
    type: string
    description: Input parameter
outputs:
  result:
    type: string
    description: Output result
```

# Steps

```yaml:steps
"""

    for step in steps:
        spec_content += f"""- name: {step}
  spec: {step}
  inputs: {{}}

"""

    spec_content += "```\n"

    path = os.path.join(spec_dir, f"{name}.spec.md")
    with open(path, 'w') as f:
        f.write(spec_content)


class TestDependencyGraph:
    """Tests for DependencyGraph class."""

    def test_add_spec_no_dependencies(self):
        """Test adding a spec with no dependencies."""
        graph = DependencyGraph()
        graph.add_spec("auth")

        assert graph.get_dependencies("auth") == []
        assert graph.get_dependents("auth") == []

    def test_add_spec_with_dependencies(self):
        """Test adding a spec with dependencies."""
        graph = DependencyGraph()
        graph.add_spec("auth", ["types", "utils"])

        deps = graph.get_dependencies("auth")
        assert "types" in deps
        assert "utils" in deps

    def test_get_dependencies_unknown_spec(self):
        """Test getting dependencies for unknown spec."""
        graph = DependencyGraph()
        assert graph.get_dependencies("unknown") == []

    def test_get_dependents_unknown_spec(self):
        """Test getting dependents for unknown spec."""
        graph = DependencyGraph()
        assert graph.get_dependents("unknown") == []

    def test_dependency_tracking_bidirectional(self):
        """Test that dependencies are tracked both ways."""
        graph = DependencyGraph()
        graph.add_spec("types")
        graph.add_spec("auth", ["types"])

        # auth depends on types
        assert "types" in graph.get_dependencies("auth")

        # types has auth as dependent
        assert "auth" in graph.get_dependents("types")

    def test_add_spec_multiple_times(self):
        """Test that adding the same spec multiple times accumulates dependencies."""
        graph = DependencyGraph()
        graph.add_spec("auth", ["types"])
        graph.add_spec("auth", ["utils"])

        deps = graph.get_dependencies("auth")
        # Adding dependencies multiple times accumulates them
        assert "types" in deps
        assert "utils" in deps

    def test_specs_returns_sorted_list(self):
        """Test that _get_all_specs() returns a sorted list."""
        graph = DependencyGraph()
        graph.add_spec("zebra")
        graph.add_spec("alpha")
        graph.add_spec("beta")

        specs = graph._get_all_specs()
        assert specs == ["alpha", "beta", "zebra"]


class TestDependencyResolver:
    """Tests for DependencyResolver class."""

    def test_build_graph_single_spec(self, temp_spec_dir):
        """Test building a graph with a single spec."""
        create_spec(temp_spec_dir, "auth")
        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        graph = resolver.build_graph(["auth"])
        assert "auth" in graph._get_all_specs()

    def test_build_graph_with_dependencies(self, temp_spec_dir):
        """Test building a graph with dependencies."""
        create_spec(temp_spec_dir, "types")
        create_spec(temp_spec_dir, "auth", ["types"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        graph = resolver.build_graph(["types", "auth"])

        assert "types" in graph.get_dependencies("auth")
        assert "auth" in graph.get_dependents("types")

    def test_build_graph_discover_all_specs(self, temp_spec_dir):
        """Test discovering all specs when spec_names is None."""
        create_spec(temp_spec_dir, "types")
        create_spec(temp_spec_dir, "auth", ["types"])
        create_spec(temp_spec_dir, "users", ["types"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        graph = resolver.build_graph()
        specs = graph._get_all_specs()

        assert "types" in specs
        assert "auth" in specs
        assert "users" in specs

    def test_build_graph_missing_dependency(self, temp_spec_dir):
        """Test that missing dependencies raise MissingDependencyError."""
        create_spec(temp_spec_dir, "auth", ["nonexistent"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        with pytest.raises(MissingDependencyError) as exc_info:
            resolver.build_graph(["auth"])

        assert exc_info.value.spec == "auth"
        assert exc_info.value.missing == "nonexistent"

    def test_resolve_build_order_no_dependencies(self, temp_spec_dir):
        """Test build order with no dependencies."""
        create_spec(temp_spec_dir, "auth")
        create_spec(temp_spec_dir, "users")

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        order = resolver.resolve_build_order(["auth", "users"])
        assert len(order) == 2
        assert set(order) == {"auth", "users"}

    def test_resolve_build_order_respects_dependencies(self, temp_spec_dir):
        """Test that build order respects dependencies."""
        create_spec(temp_spec_dir, "types")
        create_spec(temp_spec_dir, "auth", ["types"])
        create_spec(temp_spec_dir, "users", ["types"])
        create_spec(temp_spec_dir, "api", ["auth", "users"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        order = resolver.resolve_build_order()

        # types should come before auth and users
        assert order.index("types") < order.index("auth")
        assert order.index("types") < order.index("users")

        # auth and users should come before api
        assert order.index("auth") < order.index("api")
        assert order.index("users") < order.index("api")

    def test_resolve_build_order_alphabetical_for_unordered(self, temp_spec_dir):
        """Test that unordered specs are sorted alphabetically."""
        create_spec(temp_spec_dir, "zebra")
        create_spec(temp_spec_dir, "alpha")
        create_spec(temp_spec_dir, "beta")

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        order = resolver.resolve_build_order()
        assert order == ["alpha", "beta", "zebra"]

    def test_resolve_build_order_circular_dependency(self, temp_spec_dir):
        """Test detection of circular dependencies."""
        create_spec(temp_spec_dir, "a", ["b"])
        create_spec(temp_spec_dir, "b", ["a"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        with pytest.raises(CircularDependencyError) as exc_info:
            resolver.resolve_build_order()

        cycle = exc_info.value.cycle
        assert "a" in cycle
        assert "b" in cycle

    def test_resolve_build_order_three_way_cycle(self, temp_spec_dir):
        """Test detection of a three-way circular dependency."""
        create_spec(temp_spec_dir, "a", ["b"])
        create_spec(temp_spec_dir, "b", ["c"])
        create_spec(temp_spec_dir, "c", ["a"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        with pytest.raises(CircularDependencyError):
            resolver.resolve_build_order()

    def test_get_parallel_build_order_no_deps(self, temp_spec_dir):
        """Test parallel order with no dependencies."""
        create_spec(temp_spec_dir, "a")
        create_spec(temp_spec_dir, "b")
        create_spec(temp_spec_dir, "c")

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        levels = resolver.get_parallel_build_order()

        # All specs can be built together
        assert len(levels) == 1
        assert set(levels[0]) == {"a", "b", "c"}

    def test_get_parallel_build_order_with_dependencies(self, temp_spec_dir):
        """Test parallel order with dependencies."""
        create_spec(temp_spec_dir, "types")
        create_spec(temp_spec_dir, "unrelated")
        create_spec(temp_spec_dir, "auth", ["types"])
        create_spec(temp_spec_dir, "users", ["types"])
        create_spec(temp_spec_dir, "api", ["auth", "users"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        levels = resolver.get_parallel_build_order()

        # Level 0: types and unrelated (no dependencies)
        assert set(levels[0]) == {"types", "unrelated"}

        # Level 1: auth and users (depend on types)
        assert set(levels[1]) == {"auth", "users"}

        # Level 2: api (depends on auth and users)
        assert set(levels[2]) == {"api"}

    def test_get_parallel_build_order_alphabetical_within_level(self, temp_spec_dir):
        """Test that specs within a level are alphabetically sorted."""
        create_spec(temp_spec_dir, "zebra")
        create_spec(temp_spec_dir, "alpha")
        create_spec(temp_spec_dir, "beta")

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        levels = resolver.get_parallel_build_order()

        assert levels[0] == ["alpha", "beta", "zebra"]

    def test_get_parallel_build_order_circular_dependency(self, temp_spec_dir):
        """Test that circular dependencies are detected in parallel order."""
        create_spec(temp_spec_dir, "a", ["b"])
        create_spec(temp_spec_dir, "b", ["a"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        with pytest.raises(CircularDependencyError):
            resolver.get_parallel_build_order()

    def test_get_affected_specs_no_dependents(self, temp_spec_dir):
        """Test affected specs when the changed spec has no dependents."""
        create_spec(temp_spec_dir, "types")
        create_spec(temp_spec_dir, "auth", ["types"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        affected = resolver.get_affected_specs("auth")
        assert affected == ["auth"]

    def test_get_affected_specs_with_dependents(self, temp_spec_dir):
        """Test affected specs when the changed spec has dependents."""
        create_spec(temp_spec_dir, "types")
        create_spec(temp_spec_dir, "auth", ["types"])
        create_spec(temp_spec_dir, "users", ["types"])
        create_spec(temp_spec_dir, "api", ["auth", "users"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        affected = resolver.get_affected_specs("types")

        # types, auth, users, and api all need rebuilding
        assert set(affected) == {"types", "auth", "users", "api"}

    def test_get_affected_specs_partial_impact(self, temp_spec_dir):
        """Test that only affected specs are included."""
        create_spec(temp_spec_dir, "types")
        create_spec(temp_spec_dir, "auth", ["types"])
        create_spec(temp_spec_dir, "users", ["types"])
        create_spec(temp_spec_dir, "api", ["auth"])
        create_spec(temp_spec_dir, "unrelated")

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        # When users changes, only users and api are affected (api depends on auth, not users)
        # Wait, api depends on auth which depends on types, not users
        # So when users changes, only users should be affected
        affected = resolver.get_affected_specs("users")
        assert affected == ["users"]

    def test_get_affected_specs_with_provided_graph(self, temp_spec_dir):
        """Test get_affected_specs with a provided graph."""
        create_spec(temp_spec_dir, "types")
        create_spec(temp_spec_dir, "auth", ["types"])
        create_spec(temp_spec_dir, "api", ["auth"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        graph = resolver.build_graph()
        affected = resolver.get_affected_specs("types", graph=graph)

        # All should be affected
        assert set(affected) == {"types", "auth", "api"}

    def test_get_affected_specs_transitive_dependents(self, temp_spec_dir):
        """Test transitive dependent tracking."""
        create_spec(temp_spec_dir, "base")
        create_spec(temp_spec_dir, "level1", ["base"])
        create_spec(temp_spec_dir, "level2", ["level1"])
        create_spec(temp_spec_dir, "level3", ["level2"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        affected = resolver.get_affected_specs("base")
        assert set(affected) == {"base", "level1", "level2", "level3"}

    def test_get_affected_specs_build_order(self, temp_spec_dir):
        """Test that affected specs are returned in valid build order."""
        create_spec(temp_spec_dir, "types")
        create_spec(temp_spec_dir, "auth", ["types"])
        create_spec(temp_spec_dir, "api", ["auth"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        affected = resolver.get_affected_specs("types")

        # types should come before auth
        assert affected.index("types") < affected.index("auth")

        # auth should come before api
        assert affected.index("auth") < affected.index("api")

    def test_circular_dependency_error_attributes(self, temp_spec_dir):
        """Test CircularDependencyError has correct attributes."""
        create_spec(temp_spec_dir, "a", ["b"])
        create_spec(temp_spec_dir, "b", ["a"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        with pytest.raises(CircularDependencyError) as exc_info:
            resolver.resolve_build_order()

        error = exc_info.value
        assert hasattr(error, "cycle")
        assert isinstance(error.cycle, list)
        assert len(error.cycle) > 0

    def test_missing_dependency_error_attributes(self, temp_spec_dir):
        """Test MissingDependencyError has correct attributes."""
        create_spec(temp_spec_dir, "auth", ["missing"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        with pytest.raises(MissingDependencyError) as exc_info:
            resolver.build_graph()

        error = exc_info.value
        assert error.spec == "auth"
        assert error.missing == "missing"

    def test_workflow_spec_dependencies(self, temp_spec_dir):
        """Test extracting dependencies from workflow step specs."""
        create_spec(temp_spec_dir, "step1")
        create_spec(temp_spec_dir, "step2")
        create_workflow_spec(temp_spec_dir, "workflow", ["step1", "step2"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        graph = resolver.build_graph()

        # Workflow should depend on both steps
        deps = graph.get_dependencies("workflow")
        assert "step1" in deps
        assert "step2" in deps

    def test_spec_extension_stripping(self, temp_spec_dir):
        """Test that .spec.md extensions are properly stripped."""
        create_spec(temp_spec_dir, "types")
        create_spec(temp_spec_dir, "auth", ["types.spec.md"])  # Include extension

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        graph = resolver.build_graph()

        # Should handle both with and without extension
        deps = graph.get_dependencies("auth")
        assert "types" in deps

    def test_complex_dependency_scenario(self, temp_spec_dir):
        """Test a complex real-world scenario."""
        # Create a complex dependency tree
        specs = {
            "types": [],
            "utils": [],
            "auth": ["types", "utils"],
            "users": ["types", "utils"],
            "api": ["auth", "users"],
            "server": ["api"],
            "cli": ["auth"],
            "docs": [],
        }

        for name, deps in specs.items():
            create_spec(temp_spec_dir, name, deps)

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        # Get build order
        order = resolver.resolve_build_order()

        # Verify all specs are present
        assert len(order) == len(specs)
        assert set(order) == set(specs.keys())

        # Verify order constraints
        for spec_name, deps in specs.items():
            for dep in deps:
                assert order.index(dep) < order.index(spec_name)

        # Get parallel levels
        levels = resolver.get_parallel_build_order()

        # types and utils should be in level 0
        assert "types" in levels[0]
        assert "utils" in levels[0]

        # Affected specs for types change
        affected = resolver.get_affected_specs("types")
        assert "types" in affected
        assert "auth" in affected
        assert "users" in affected
        assert "api" in affected
        assert "server" in affected
        # docs is not affected as it has no dependencies


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_graph(self):
        """Test operations on an empty graph."""
        graph = DependencyGraph()
        assert graph._get_all_specs() == []

    def test_self_loop_detection(self, temp_spec_dir):
        """Test that self-loops are detected as circular."""
        # A depends on itself
        create_spec(temp_spec_dir, "a", ["a"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        with pytest.raises(CircularDependencyError):
            resolver.resolve_build_order()

    def test_duplicate_dependencies(self, temp_spec_dir):
        """Test handling of duplicate dependencies."""
        create_spec(temp_spec_dir, "types")
        # List types twice as a dependency
        spec_content = """---
name: auth
type: bundle
dependencies:
  - types
  - types
---

# Overview

Auth spec.

# Functions

```yaml:functions
test:
  inputs: {a: integer}
  outputs: {result: integer}
  behavior: "Test"
```
"""
        with open(os.path.join(temp_spec_dir, "auth.spec.md"), 'w') as f:
            f.write(spec_content)

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        # Should handle duplicates gracefully
        graph = resolver.build_graph()
        deps = graph.get_dependencies("auth")
        assert deps.count("types") == 1  # Should be deduplicated

    def test_deep_dependency_chain(self, temp_spec_dir):
        """Test handling of deep dependency chains."""
        # Create a chain: a <- b <- c <- d <- e
        for i, name in enumerate(["a", "b", "c", "d", "e"]):
            if i == 0:
                create_spec(temp_spec_dir, name)
            else:
                create_spec(temp_spec_dir, name, [["a", "b", "c", "d"][i-1]])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        order = resolver.resolve_build_order()

        # Should be in order a, b, c, d, e
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")
        assert order.index("c") < order.index("d")
        assert order.index("d") < order.index("e")

    def test_diamond_dependency(self, temp_spec_dir):
        """Test the diamond dependency pattern."""
        #     base
        #    /    \
        #   a      b
        #    \    /
        #      c
        create_spec(temp_spec_dir, "base")
        create_spec(temp_spec_dir, "a", ["base"])
        create_spec(temp_spec_dir, "b", ["base"])
        create_spec(temp_spec_dir, "c", ["a", "b"])

        parser = SpecParser(temp_spec_dir)
        resolver = DependencyResolver(parser)

        order = resolver.resolve_build_order()

        # base before a and b
        assert order.index("base") < order.index("a")
        assert order.index("base") < order.index("b")

        # a and b before c
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("c")

        # Get parallel levels
        levels = resolver.get_parallel_build_order()
        assert "base" in levels[0]
        assert set(levels[1]) == {"a", "b"}
        assert "c" in levels[2]
