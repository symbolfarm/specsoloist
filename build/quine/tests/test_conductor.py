"""Tests for the conductor module."""

import os
import pytest
from unittest.mock import MagicMock, patch

from specsoloist.config import SpecSoloistConfig
from specsoloist.core import BuildResult
from spechestra.conductor import SpecConductor, VerifyResult


SIMPLE_SPEC = """---
name: myspec
description: A test spec
type: bundle
---

# Overview

A simple spec.

# Functions

```yaml:functions
do_thing:
  inputs:
    x: {type: string}
  outputs:
    result: {type: string}
  behavior: "Does a thing"
```
"""


@pytest.fixture
def spec_dir(tmp_path):
    (tmp_path / "myspec.spec.md").write_text(SIMPLE_SPEC)
    return tmp_path


@pytest.fixture
def conductor(tmp_path, spec_dir):
    config = SpecSoloistConfig(
        root_dir=str(tmp_path),
        src_dir=str(spec_dir),
        build_dir=str(tmp_path / "build"),
    )
    config.src_path = str(spec_dir)
    config.build_path = str(tmp_path / "build")
    os.makedirs(config.build_path, exist_ok=True)

    c = SpecConductor(project_dir=str(tmp_path), config=config)
    return c


@pytest.fixture
def empty_conductor(tmp_path):
    empty_src = tmp_path / "empty_specs"
    empty_src.mkdir()
    config = SpecSoloistConfig(
        root_dir=str(tmp_path),
        src_dir=str(empty_src),
        build_dir=str(tmp_path / "build"),
    )
    config.src_path = str(empty_src)
    config.build_path = str(tmp_path / "build")
    os.makedirs(config.build_path, exist_ok=True)

    return SpecConductor(project_dir=str(tmp_path), config=config)


class TestVerifyResult:
    def test_creation(self):
        result = VerifyResult(success=True)
        assert result.success is True
        assert result.results == {}

    def test_with_results(self):
        result = VerifyResult(
            success=False,
            results={"myspec": {"valid": False, "errors": ["missing section"]}}
        )
        assert result.success is False
        assert "myspec" in result.results


class TestSpecConductor:
    def test_init(self, conductor):
        assert os.path.isabs(conductor.project_dir)

    def test_has_parser(self, conductor):
        assert conductor.parser is not None

    def test_has_resolver(self, conductor):
        assert conductor.resolver is not None

    def test_verify_returns_verify_result(self, conductor):
        result = conductor.verify()
        assert isinstance(result, VerifyResult)
        assert isinstance(result.success, bool)

    def test_verify_empty_project(self, empty_conductor):
        result = empty_conductor.verify()
        assert result.success is True

    def test_get_build_order_empty(self, empty_conductor):
        order = empty_conductor.get_build_order()
        assert order == []

    def test_get_build_order_with_specs(self, conductor):
        order = conductor.get_build_order()
        assert "myspec" in order

    def test_get_dependency_graph(self, conductor):
        graph = conductor.get_dependency_graph()
        assert graph is not None

    def test_build_calls_core_compile(self, conductor):
        mock_result = BuildResult(
            success=True,
            specs_compiled=["myspec"],
        )
        with patch.object(conductor._core, "compile_project", return_value=mock_result) as mock:
            result = conductor.build(specs=["myspec"])
            assert mock.called
            assert result is mock_result

    def test_build_default_args(self, conductor):
        mock_result = BuildResult(success=True)
        with patch.object(conductor._core, "compile_project", return_value=mock_result) as mock:
            conductor.build()
            call_kwargs = mock.call_args[1]
            assert call_kwargs.get("parallel") is True
            assert call_kwargs.get("incremental") is True

    def test_build_with_arrangement_calls_provision(self, conductor):
        from specsoloist.schema import (
            Arrangement,
            ArrangementBuildCommands,
            ArrangementEnvironment,
            ArrangementOutputPaths,
        )

        arrangement = Arrangement(
            target_language="python",
            output_paths=ArrangementOutputPaths(
                implementation="src/{name}.py",
                tests="tests/test_{name}.py",
            ),
            environment=ArrangementEnvironment(
                config_files={"config.json": '{"key": "value"}'},
                setup_commands=[],
            ),
            build_commands=ArrangementBuildCommands(test="pytest tests/"),
        )

        mock_result = BuildResult(success=True)
        with patch.object(conductor._core, "compile_project", return_value=mock_result):
            with patch.object(conductor, "_provision_environment") as mock_provision:
                conductor.build(arrangement=arrangement)
                assert mock_provision.called

    def test_provision_environment_writes_config_files(self, conductor, tmp_path):
        from specsoloist.schema import (
            Arrangement,
            ArrangementBuildCommands,
            ArrangementEnvironment,
            ArrangementOutputPaths,
        )

        arrangement = Arrangement(
            target_language="python",
            output_paths=ArrangementOutputPaths(
                implementation="src/{name}.py",
                tests="tests/test_{name}.py",
            ),
            environment=ArrangementEnvironment(
                config_files={"myconfig.json": '{"test": true}'},
            ),
            build_commands=ArrangementBuildCommands(test="pytest"),
        )

        conductor._provision_environment(arrangement)
        config_file = os.path.join(conductor.config.build_path, "myconfig.json")
        assert os.path.exists(config_file)
        assert '{"test": true}' in open(config_file).read()

    def test_get_build_order_respects_dependencies(self, tmp_path):
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        # Create two specs with dependencies
        (spec_dir / "base.spec.md").write_text("""---
name: base
type: bundle
---

# Overview
Base.

# Functions

```yaml:functions
init:
  inputs: {}
  outputs: {}
  behavior: "Initialize"
```
""")
        (spec_dir / "derived.spec.md").write_text("""---
name: derived
type: bundle
dependencies:
  - base
---

# Overview
Derived.

# Functions

```yaml:functions
run:
  inputs: {}
  outputs: {}
  behavior: "Run"
```
""")

        config = SpecSoloistConfig(
            root_dir=str(tmp_path),
            src_dir=str(spec_dir),
            build_dir=str(tmp_path / "build"),
        )
        config.src_path = str(spec_dir)
        config.build_path = str(tmp_path / "build")
        os.makedirs(config.build_path, exist_ok=True)

        c = SpecConductor(project_dir=str(tmp_path), config=config)
        order = c.get_build_order()
        assert order.index("base") < order.index("derived")
