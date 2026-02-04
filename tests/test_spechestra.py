"""
Tests for Spechestra (SpecComposer and SpecConductor).
"""

import os
import tempfile
import pytest

from spechestra import SpecComposer, SpecConductor
from spechestra.composer import Architecture, ComponentDef, CompositionResult
from spechestra.conductor import PerformResult, StepResult, VerifyResult


def test_import():
    """Test that spechestra can be imported."""
    from spechestra import SpecComposer, SpecConductor
    assert SpecComposer is not None
    assert SpecConductor is not None


def test_composer_init():
    """Test SpecComposer initialization."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "src"))
        composer = SpecComposer(tmp_dir)
        assert composer.project_dir == os.path.abspath(tmp_dir)


def test_conductor_init():
    """Test SpecConductor initialization."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "src"))
        os.makedirs(os.path.join(tmp_dir, "build"))
        conductor = SpecConductor(tmp_dir)
        assert conductor.project_dir == os.path.abspath(tmp_dir)


def test_conductor_verify_empty_project():
    """Test verification on empty project."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "src"))
        os.makedirs(os.path.join(tmp_dir, "build"))
        conductor = SpecConductor(tmp_dir)
        result = conductor.verify()
        assert isinstance(result, VerifyResult)
        assert result.success is True  # Empty project is valid


def test_conductor_get_build_order_empty():
    """Test build order on empty project."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.makedirs(os.path.join(tmp_dir, "src"))
        os.makedirs(os.path.join(tmp_dir, "build"))
        conductor = SpecConductor(tmp_dir)
        order = conductor.get_build_order()
        assert order == []


def test_architecture_dataclass():
    """Test Architecture dataclass."""
    components = [
        ComponentDef(name="add", type="function", description="Adds numbers"),
        ComponentDef(name="calc", type="module", description="Calculator", dependencies=["add"])
    ]
    arch = Architecture(
        components=components,
        dependencies={"calc": ["add"]},
        build_order=["add", "calc"],
        description="A calculator"
    )
    assert len(arch.components) == 2
    assert arch.build_order == ["add", "calc"]


def test_step_result_dataclass():
    """Test StepResult dataclass."""
    result = StepResult(
        name="step1",
        spec="my_function",
        inputs={"x": 1},
        outputs={"y": 2},
        success=True,
        duration=0.5
    )
    assert result.success is True
    assert result.error is None


def test_perform_result_dataclass():
    """Test PerformResult dataclass."""
    result = PerformResult(
        success=True,
        workflow="test_workflow",
        steps=[],
        outputs={"result": 42},
        duration=1.0
    )
    assert result.success is True
    assert result.outputs == {"result": 42}


def test_composition_result_dataclass():
    """Test CompositionResult dataclass."""
    arch = Architecture(
        components=[],
        dependencies={},
        build_order=[]
    )
    result = CompositionResult(
        architecture=arch,
        spec_paths=["/path/to/spec.md"],
        ready_for_build=True
    )
    assert result.ready_for_build is True
    assert len(result.spec_paths) == 1
