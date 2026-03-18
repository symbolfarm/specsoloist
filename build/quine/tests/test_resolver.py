"""Tests for the resolver module."""

import pytest
from unittest.mock import MagicMock

from specsoloist.resolver import (
    CircularDependencyError,
    DependencyGraph,
    DependencyResolver,
    MissingDependencyError,
)


class TestCircularDependencyError:
    def test_creation(self):
        err = CircularDependencyError(["a", "b", "a"])
        assert err.cycle == ["a", "b", "a"]
        assert "a" in str(err)
        assert "circular" in str(err).lower() or "cycle" in str(err).lower() or "a" in str(err)

    def test_is_exception(self):
        with pytest.raises(CircularDependencyError):
            raise CircularDependencyError(["x", "y"])


class TestMissingDependencyError:
    def test_creation(self):
        err = MissingDependencyError("auth", "users")
        assert err.spec == "auth"
        assert err.missing == "users"
        assert "auth" in str(err)
        assert "users" in str(err)

    def test_is_exception(self):
        with pytest.raises(MissingDependencyError):
            raise MissingDependencyError("foo", "bar")


class TestDependencyGraph:
    def test_add_spec_no_deps(self):
        graph = DependencyGraph()
        graph.add_spec("foo")
        assert graph.get_dependencies("foo") == []
        assert graph.get_dependents("foo") == []

    def test_add_spec_with_deps(self):
        graph = DependencyGraph()
        graph.add_spec("bar")
        graph.add_spec("foo", depends_on=["bar"])
        assert graph.get_dependencies("foo") == ["bar"]
        assert "foo" in graph.get_dependents("bar")

    def test_get_dependencies_missing(self):
        graph = DependencyGraph()
        assert graph.get_dependencies("nonexistent") == []

    def test_get_dependents_missing(self):
        graph = DependencyGraph()
        assert graph.get_dependents("nonexistent") == []

    def test_multiple_dependents(self):
        graph = DependencyGraph()
        graph.add_spec("base")
        graph.add_spec("a", depends_on=["base"])
        graph.add_spec("b", depends_on=["base"])
        dependents = graph.get_dependents("base")
        assert "a" in dependents
        assert "b" in dependents


def _make_parser(specs: dict) -> object:
    """Create a mock parser with given specs."""
    parser = MagicMock()

    def parse(name):
        if name not in specs:
            raise ValueError(f"Spec '{name}' not found")
        spec = MagicMock()
        spec.metadata.name = name
        spec.metadata.dependencies = specs[name]
        spec.schema = None
        return spec

    parser.parse = parse
    parser.list_specs = MagicMock(return_value=list(specs.keys()))
    return parser


class TestDependencyResolver:
    def test_build_graph_simple(self):
        parser = _make_parser({
            "types": [],
            "auth": ["types"],
            "users": ["types"],
        })
        resolver = DependencyResolver(parser=parser)
        graph = resolver.build_graph(["types", "auth", "users"])
        assert "types" in graph.get_dependencies("auth")
        assert "types" in graph.get_dependencies("users")

    def test_build_graph_missing_dep_raises(self):
        parser = _make_parser({
            "auth": ["nonexistent"],
        })
        # Make parser.parse raise for nonexistent
        original_parse = parser.parse
        def parse_raising(name):
            if name == "nonexistent":
                raise ValueError(f"Spec '{name}' not found")
            return original_parse(name)
        parser.parse = parse_raising

        resolver = DependencyResolver(parser=parser)
        with pytest.raises(MissingDependencyError) as exc_info:
            resolver.build_graph(["auth"])
        assert exc_info.value.spec == "auth"
        assert exc_info.value.missing == "nonexistent"

    def test_resolve_build_order_deps_first(self):
        parser = _make_parser({
            "types": [],
            "auth": ["types"],
            "api": ["auth"],
        })
        resolver = DependencyResolver(parser=parser)
        order = resolver.resolve_build_order(["types", "auth", "api"])
        assert order.index("types") < order.index("auth")
        assert order.index("auth") < order.index("api")

    def test_resolve_build_order_alphabetical_for_peers(self):
        parser = _make_parser({
            "types": [],
            "aaa": ["types"],
            "bbb": ["types"],
        })
        resolver = DependencyResolver(parser=parser)
        order = resolver.resolve_build_order(["types", "aaa", "bbb"])
        # types must come first
        assert order[0] == "types"
        # aaa and bbb are peers, alphabetical order
        assert order.index("aaa") < order.index("bbb")

    def test_resolve_build_order_circular_raises(self):
        parser = _make_parser({
            "a": ["b"],
            "b": ["c"],
            "c": ["a"],
        })
        resolver = DependencyResolver(parser=parser)
        with pytest.raises(CircularDependencyError) as exc_info:
            resolver.resolve_build_order(["a", "b", "c"])
        assert len(exc_info.value.cycle) > 0

    def test_get_parallel_build_order_levels(self):
        parser = _make_parser({
            "types": [],
            "unrelated": [],
            "auth": ["types"],
            "users": ["types"],
            "api": ["auth", "users"],
        })
        resolver = DependencyResolver(parser=parser)
        levels = resolver.get_parallel_build_order(
            ["types", "unrelated", "auth", "users", "api"]
        )
        assert len(levels) == 3
        # Level 0: types and unrelated
        assert "types" in levels[0]
        assert "unrelated" in levels[0]
        # Level 1: auth and users
        assert "auth" in levels[1]
        assert "users" in levels[1]
        # Level 2: api
        assert "api" in levels[2]

    def test_get_parallel_build_order_alphabetical_within_level(self):
        parser = _make_parser({
            "bbb": [],
            "aaa": [],
            "ccc": [],
        })
        resolver = DependencyResolver(parser=parser)
        levels = resolver.get_parallel_build_order(["bbb", "aaa", "ccc"])
        assert len(levels) == 1
        assert levels[0] == ["aaa", "bbb", "ccc"]

    def test_get_parallel_build_order_circular_raises(self):
        parser = _make_parser({
            "a": ["b"],
            "b": ["a"],
        })
        resolver = DependencyResolver(parser=parser)
        with pytest.raises(CircularDependencyError):
            resolver.get_parallel_build_order(["a", "b"])

    def test_get_affected_specs_direct_change(self):
        parser = _make_parser({
            "types": [],
            "auth": ["types"],
            "users": ["types"],
            "api": ["auth", "users"],
            "unrelated": [],
        })
        resolver = DependencyResolver(parser=parser)
        affected = resolver.get_affected_specs(
            "types",
            graph=resolver.build_graph(
                ["types", "auth", "users", "api", "unrelated"]
            ),
        )
        assert "types" in affected
        assert "auth" in affected
        assert "users" in affected
        assert "api" in affected
        assert "unrelated" not in affected

    def test_get_affected_specs_leaf_change(self):
        parser = _make_parser({
            "types": [],
            "auth": ["types"],
            "api": ["auth"],
        })
        resolver = DependencyResolver(parser=parser)
        affected = resolver.get_affected_specs(
            "api",
            graph=resolver.build_graph(["types", "auth", "api"]),
        )
        assert affected == ["api"]

    def test_get_affected_specs_valid_order(self):
        parser = _make_parser({
            "types": [],
            "auth": ["types"],
            "api": ["auth"],
        })
        resolver = DependencyResolver(parser=parser)
        affected = resolver.get_affected_specs(
            "types",
            graph=resolver.build_graph(["types", "auth", "api"]),
        )
        assert affected.index("types") < affected.index("auth")
        assert affected.index("auth") < affected.index("api")

    def test_uses_none_to_discover_all(self):
        parser = _make_parser({
            "a": [],
            "b": ["a"],
        })
        resolver = DependencyResolver(parser=parser)
        # Should use parser.list_specs() when spec_names is None
        order = resolver.resolve_build_order()
        assert "a" in order
        assert "b" in order
