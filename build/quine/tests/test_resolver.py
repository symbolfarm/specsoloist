"""Tests for the dependency resolver."""

import pytest
import os
import shutil

from specsoloist.parser import SpecParser
from specsoloist.resolver import (
    DependencyResolver,
    CircularDependencyError,
    MissingDependencyError,
    DependencyGraph,
)


@pytest.fixture
def test_env():
    """Sets up a temporary directory for testing."""
    env_dir = "test_resolver_env"
    src_dir = os.path.join(env_dir, "src")
    if os.path.exists(env_dir):
        shutil.rmtree(env_dir)
    os.makedirs(src_dir)

    yield env_dir

    if os.path.exists(env_dir):
        shutil.rmtree(env_dir)


def create_spec(src_dir: str, name: str, deps: list = None):
    """Helper to create a minimal spec file with dependencies."""
    deps = deps or []
    deps_yaml = "\n".join([f'  - name: X\n    from: {d}.spec.md' for d in deps])
    if deps_yaml:
        deps_yaml = f"dependencies:\n{deps_yaml}"
    else:
        deps_yaml = "dependencies: []"

    content = f"""---
name: {name}
type: module
language_target: python
status: draft
{deps_yaml}
---

# 1. Overview
Test spec for {name}.

# 2. Interface Specification
## 2.1 Inputs
None.
## 2.2 Outputs
None.

# 3. Functional Requirements
*   **FR-01**: Test requirement.

# 4. Non-Functional Requirements
*   **NFR-Test**: Test constraint.

# 5. Design Contract
*   **Invariant**: Test invariant.
"""
    path = os.path.join(src_dir, f"{name}.spec.md")
    with open(path, 'w') as f:
        f.write(content)


def test_no_dependencies(test_env):
    """Test resolver with specs that have no dependencies."""
    src_dir = os.path.join(test_env, "src")
    create_spec(src_dir, "alpha")
    create_spec(src_dir, "beta")

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    order = resolver.resolve_build_order()

    # Both specs should be in the order (alphabetically since no deps)
    assert len(order) == 2
    assert "alpha" in order
    assert "beta" in order


def test_simple_dependency(test_env):
    """Test resolver with a simple A -> B dependency."""
    src_dir = os.path.join(test_env, "src")
    create_spec(src_dir, "types")
    create_spec(src_dir, "service", deps=["types"])

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    order = resolver.resolve_build_order()

    # types must come before service
    assert order.index("types") < order.index("service")


def test_diamond_dependency(test_env):
    """Test resolver with diamond dependency pattern."""
    src_dir = os.path.join(test_env, "src")
    #     types
    #    /     \
    # auth     users
    #    \     /
    #      api
    create_spec(src_dir, "types")
    create_spec(src_dir, "auth", deps=["types"])
    create_spec(src_dir, "users", deps=["types"])
    create_spec(src_dir, "api", deps=["auth", "users"])

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    order = resolver.resolve_build_order()

    # types must be first
    assert order[0] == "types"
    # api must be last
    assert order[-1] == "api"
    # auth and users must come before api
    assert order.index("auth") < order.index("api")
    assert order.index("users") < order.index("api")


def test_circular_dependency_detected(test_env):
    """Test that circular dependencies raise an error."""
    src_dir = os.path.join(test_env, "src")
    create_spec(src_dir, "a", deps=["b"])
    create_spec(src_dir, "b", deps=["c"])
    create_spec(src_dir, "c", deps=["a"])

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    with pytest.raises(CircularDependencyError) as exc_info:
        resolver.resolve_build_order()

    # Should report the cycle
    assert len(exc_info.value.cycle) > 0


def test_missing_dependency(test_env):
    """Test that missing dependencies raise an error."""
    src_dir = os.path.join(test_env, "src")
    create_spec(src_dir, "auth", deps=["nonexistent"])

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    with pytest.raises(MissingDependencyError) as exc_info:
        resolver.build_graph()

    assert exc_info.value.spec == "auth"
    assert exc_info.value.missing == "nonexistent"


def test_affected_specs(test_env):
    """Test getting specs affected by a change."""
    src_dir = os.path.join(test_env, "src")
    create_spec(src_dir, "types")
    create_spec(src_dir, "validation", deps=["types"])
    create_spec(src_dir, "service", deps=["types", "validation"])
    create_spec(src_dir, "unrelated")

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    # Changing types affects types, validation, and service (not unrelated)
    affected = resolver.get_affected_specs("types")
    assert "types" in affected
    assert "validation" in affected
    assert "service" in affected
    assert "unrelated" not in affected

    # Changing service only affects service
    affected = resolver.get_affected_specs("service")
    assert affected == ["service"]


def test_build_graph_structure(test_env):
    """Test the structure of the dependency graph."""
    src_dir = os.path.join(test_env, "src")
    create_spec(src_dir, "types")
    create_spec(src_dir, "service", deps=["types"])

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    graph = resolver.build_graph()

    # Check dependencies
    assert graph.get_dependencies("types") == []
    assert graph.get_dependencies("service") == ["types"]

    # Check dependents (reverse mapping)
    assert "service" in graph.get_dependents("types")
    assert graph.get_dependents("service") == []


def test_parallel_build_order_levels(test_env):
    """Test that parallel build order groups specs into levels correctly."""
    src_dir = os.path.join(test_env, "src")
    #     types    utils
    #       \      /
    #        service
    #          |
    #         api
    create_spec(src_dir, "types")
    create_spec(src_dir, "utils")
    create_spec(src_dir, "service", deps=["types", "utils"])
    create_spec(src_dir, "api", deps=["service"])

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    levels = resolver.get_parallel_build_order()

    # Level 0: types and utils (no dependencies, can be parallel)
    assert set(levels[0]) == {"types", "utils"}
    # Level 1: service (depends on level 0)
    assert levels[1] == ["service"]
    # Level 2: api (depends on level 1)
    assert levels[2] == ["api"]


def test_parallel_build_order_diamond(test_env):
    """Test parallel build order with diamond dependency pattern."""
    src_dir = os.path.join(test_env, "src")
    #     types
    #    /     \
    # auth     users
    #    \     /
    #      api
    create_spec(src_dir, "types")
    create_spec(src_dir, "auth", deps=["types"])
    create_spec(src_dir, "users", deps=["types"])
    create_spec(src_dir, "api", deps=["auth", "users"])

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    levels = resolver.get_parallel_build_order()

    # Level 0: types only
    assert levels[0] == ["types"]
    # Level 1: auth and users can be parallel
    assert set(levels[1]) == {"auth", "users"}
    # Level 2: api
    assert levels[2] == ["api"]


def test_dependency_graph_add_spec():
    """Test DependencyGraph.add_spec method."""
    graph = DependencyGraph()
    graph.add_spec("a", ["b", "c"])
    graph.add_spec("b")
    graph.add_spec("c")

    # Check specs are recorded
    assert "a" in graph.specs
    assert "b" in graph.specs
    assert "c" in graph.specs

    # Check dependencies
    assert set(graph.get_dependencies("a")) == {"b", "c"}
    assert graph.get_dependencies("b") == []

    # Check reverse mapping
    assert "a" in graph.get_dependents("b")
    assert "a" in graph.get_dependents("c")


def test_dependency_graph_empty():
    """Test DependencyGraph with empty specs."""
    graph = DependencyGraph()
    assert graph.get_dependencies("nonexistent") == []
    assert graph.get_dependents("nonexistent") == []


def test_circular_error_cycle_attribute(test_env):
    """Test that CircularDependencyError has proper cycle attribute."""
    src_dir = os.path.join(test_env, "src")
    create_spec(src_dir, "x", deps=["y"])
    create_spec(src_dir, "y", deps=["z"])
    create_spec(src_dir, "z", deps=["x"])

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    try:
        resolver.resolve_build_order()
        pytest.fail("Should have raised CircularDependencyError")
    except CircularDependencyError as e:
        # Cycle should contain at least 3 elements in some order
        assert len(e.cycle) >= 3
        # All cycle elements should be part of the detected cycle
        assert set(e.cycle) <= {"x", "y", "z"}
        # Error message should mention the cycle
        assert "Circular" in str(e)


def test_missing_dependency_error_attributes(test_env):
    """Test that MissingDependencyError has proper attributes."""
    src_dir = os.path.join(test_env, "src")
    create_spec(src_dir, "client", deps=["database"])

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    try:
        resolver.build_graph()
        pytest.fail("Should have raised MissingDependencyError")
    except MissingDependencyError as e:
        assert e.spec == "client"
        assert e.missing == "database"
        assert "client" in str(e)
        assert "database" in str(e)


def test_build_order_deterministic(test_env):
    """Test that build order is deterministic with same input."""
    src_dir = os.path.join(test_env, "src")
    for i in range(5):
        create_spec(src_dir, f"spec{i}")

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    order1 = resolver.resolve_build_order()
    order2 = resolver.resolve_build_order()

    assert order1 == order2


def test_affected_specs_transitive(test_env):
    """Test that affected specs includes transitive dependents."""
    src_dir = os.path.join(test_env, "src")
    # a -> b -> c -> d
    create_spec(src_dir, "a")
    create_spec(src_dir, "b", deps=["a"])
    create_spec(src_dir, "c", deps=["b"])
    create_spec(src_dir, "d", deps=["c"])

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    # Changing a affects all downstream specs
    affected = resolver.get_affected_specs("a")
    assert set(affected) == {"a", "b", "c", "d"}

    # Changing c affects c and d only
    affected = resolver.get_affected_specs("c")
    assert set(affected) == {"c", "d"}


def test_multiple_dependencies_ordering(test_env):
    """Test that specs with multiple dependencies are ordered correctly."""
    src_dir = os.path.join(test_env, "src")
    create_spec(src_dir, "log")
    create_spec(src_dir, "config")
    create_spec(src_dir, "db", deps=["config", "log"])

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    order = resolver.resolve_build_order()

    # Both log and config must come before db
    assert order.index("log") < order.index("db")
    assert order.index("config") < order.index("db")


def test_get_parallel_build_order_with_none():
    """Test get_parallel_build_order with empty graph."""
    # Create a test environment with no specs
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        parser = SpecParser(tmpdir)
        resolver = DependencyResolver(parser)

        # Should handle empty specs gracefully
        levels = resolver.get_parallel_build_order()
        assert levels == []


def test_resolve_build_order_with_specific_specs(test_env):
    """Test resolving build order with a specific subset of specs."""
    src_dir = os.path.join(test_env, "src")
    create_spec(src_dir, "a")
    create_spec(src_dir, "b", deps=["a"])
    create_spec(src_dir, "c")

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    # Resolve order for only a and b
    order = resolver.resolve_build_order(spec_names=["a", "b"])

    assert order == ["a", "b"]
    assert "c" not in order


def test_get_affected_specs_with_provided_graph(test_env):
    """Test get_affected_specs with a pre-built graph."""
    src_dir = os.path.join(test_env, "src")
    create_spec(src_dir, "x", deps=["y"])
    create_spec(src_dir, "y")
    create_spec(src_dir, "z")

    parser = SpecParser(src_dir)
    resolver = DependencyResolver(parser)

    # Build graph once and reuse it
    graph = resolver.build_graph()
    affected = resolver.get_affected_specs("y", graph=graph)

    assert "y" in affected
    assert "x" in affected
    assert "z" not in affected
