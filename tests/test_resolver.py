"""Tests for the dependency resolver."""

import pytest
import os
import shutil

from specsoloist.parser import SpecParser
from specsoloist.resolver import (
    DependencyResolver,
    CircularDependencyError,
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
