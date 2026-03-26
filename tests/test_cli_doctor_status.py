"""Tests for sp doctor, sp status, and sp validate quality hints."""

import json
import os
import subprocess
import sys

import pytest

from specsoloist.cli import _check_spec_quality


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_sp(*args, env=None, cwd=None) -> subprocess.CompletedProcess:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "specsoloist.cli", *args],
        capture_output=True,
        text=True,
        env=merged_env,
        cwd=cwd,
    )


@pytest.fixture()
def tmp_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# sp doctor
# ---------------------------------------------------------------------------

class TestSpDoctor:
    def test_exits_0_when_api_key_present(self, tmp_cwd):
        result = run_sp("doctor", env={"ANTHROPIC_API_KEY": "test-key"})
        assert result.returncode == 0

    def test_exits_1_when_no_api_key(self, tmp_cwd):
        env = {k: v for k, v in os.environ.items()
               if k not in ("ANTHROPIC_API_KEY", "GEMINI_API_KEY")}
        result = subprocess.run(
            [sys.executable, "-m", "specsoloist.cli", "doctor"],
            capture_output=True, text=True, env=env, cwd=str(tmp_cwd),
        )
        assert result.returncode == 1

    def test_python_version_shown(self, tmp_cwd):
        result = run_sp("doctor", env={"ANTHROPIC_API_KEY": "test-key"})
        combined = result.stdout + result.stderr
        assert "Python" in combined

    def test_api_key_status_shown(self, tmp_cwd):
        result = run_sp("doctor", env={"ANTHROPIC_API_KEY": "test-key"})
        combined = result.stdout + result.stderr
        assert "ANTHROPIC_API_KEY" in combined

    def test_zero_specs_shown(self, tmp_cwd):
        result = run_sp("doctor", env={"ANTHROPIC_API_KEY": "test-key"})
        combined = result.stdout + result.stderr
        assert "spec" in combined.lower()

    def test_specs_count_when_specs_exist(self, tmp_cwd):
        src = tmp_cwd / "src"
        src.mkdir()
        (src / "foo.spec.md").write_text("# foo")
        (src / "bar.spec.md").write_text("# bar")
        result = run_sp("doctor", env={"ANTHROPIC_API_KEY": "test-key"})
        combined = result.stdout + result.stderr
        assert "2" in combined

    def test_gemini_key_warning_when_missing(self, tmp_cwd):
        env = {k: v for k, v in os.environ.items() if k != "GEMINI_API_KEY"}
        env["ANTHROPIC_API_KEY"] = "test-key"
        result = subprocess.run(
            [sys.executable, "-m", "specsoloist.cli", "doctor"],
            capture_output=True, text=True, env=env, cwd=str(tmp_cwd),
        )
        combined = result.stdout + result.stderr
        assert "GEMINI_API_KEY" in combined

    def test_both_keys_shown_as_set(self, tmp_cwd):
        result = run_sp(
            "doctor",
            env={"ANTHROPIC_API_KEY": "test-key", "GEMINI_API_KEY": "gemini-key"},
        )
        combined = result.stdout + result.stderr
        assert "ANTHROPIC_API_KEY" in combined
        assert "GEMINI_API_KEY" in combined
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# sp status
# ---------------------------------------------------------------------------

class TestSpStatus:
    def _make_project(self, tmp_path):
        """Create a minimal SpecSoloist project with one spec."""
        src = tmp_path / "src"
        src.mkdir()
        spec_content = """\
---
name: myspec
version: 1.0
description: A test spec
type: bundle
status: draft
dependencies: []
---

## Overview
A test spec.

## Test Scenarios

| Input | Output |
|-------|--------|
| a | b |
| c | d |
"""
        (src / "myspec.spec.md").write_text(spec_content)
        return tmp_path

    def test_status_no_specs(self, tmp_cwd):
        result = run_sp("status", env={"ANTHROPIC_API_KEY": "test-key"}, cwd=str(tmp_cwd))
        combined = result.stdout + result.stderr
        assert "No specs" in combined

    def test_status_shows_spec_name(self, tmp_cwd):
        self._make_project(tmp_cwd)
        result = run_sp("status", env={"ANTHROPIC_API_KEY": "test-key"}, cwd=str(tmp_cwd))
        combined = result.stdout + result.stderr
        assert "myspec" in combined

    def test_status_shows_never_when_no_manifest(self, tmp_cwd):
        self._make_project(tmp_cwd)
        result = run_sp("status", env={"ANTHROPIC_API_KEY": "test-key"}, cwd=str(tmp_cwd))
        combined = result.stdout + result.stderr
        assert "never" in combined

    def test_status_shows_built_time_when_manifest_exists(self, tmp_cwd):
        self._make_project(tmp_cwd)
        # Write a fake manifest
        from datetime import datetime, timezone, timedelta
        built_at = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
        build_dir = tmp_cwd / "build"
        build_dir.mkdir()
        manifest_data = {
            "version": "1.0",
            "specs": {
                "myspec": {
                    "spec_hash": "abc123",
                    "built_at": built_at,
                    "dependencies": [],
                    "output_files": [],
                }
            },
        }
        (build_dir / ".specsoloist-manifest.json").write_text(json.dumps(manifest_data))
        result = run_sp("status", env={"ANTHROPIC_API_KEY": "test-key"}, cwd=str(tmp_cwd))
        combined = result.stdout + result.stderr
        assert "ago" in combined

    def test_status_exits_0(self, tmp_cwd):
        self._make_project(tmp_cwd)
        result = run_sp("status", env={"ANTHROPIC_API_KEY": "test-key"}, cwd=str(tmp_cwd))
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# _check_spec_quality unit tests
# ---------------------------------------------------------------------------

FULL_SPEC = """\
---
name: mymodule
version: 1.0
description: A well-described module
type: bundle
status: draft
dependencies: []
---

## Overview
Does something.

## Test Scenarios

| Input | Output |
|-------|--------|
| 1 | 2 |
| 3 | 4 |

```yaml:schema
input: int
output: int
```
"""


class TestCheckSpecQuality:
    def test_no_warnings_for_complete_spec(self):
        warnings = _check_spec_quality(FULL_SPEC, "bundle")
        assert warnings == []

    def test_warns_missing_test_scenarios(self):
        spec = FULL_SPEC.replace("## Test Scenarios", "## Something Else")
        warnings = _check_spec_quality(spec, "bundle")
        assert any("test scenarios" in w.lower() for w in warnings)

    def test_warns_missing_schema_for_bundle(self):
        spec = FULL_SPEC.replace("```yaml:schema", "```yaml")
        warnings = _check_spec_quality(spec, "bundle")
        assert any("schema" in w.lower() for w in warnings)

    def test_warns_missing_schema_for_function(self):
        spec = FULL_SPEC.replace("```yaml:schema", "```yaml")
        warnings = _check_spec_quality(spec, "function")
        assert any("schema" in w.lower() for w in warnings)

    def test_no_schema_warning_for_type_spec(self):
        spec = FULL_SPEC.replace("```yaml:schema", "```yaml")
        warnings = _check_spec_quality(spec, "type")
        assert not any("schema" in w.lower() for w in warnings)

    def test_warns_short_description(self):
        spec = FULL_SPEC.replace(
            "description: A well-described module",
            "description: Short"
        )
        warnings = _check_spec_quality(spec, "bundle")
        assert any("description" in w.lower() for w in warnings)

    def test_no_description_warning_when_long_enough(self):
        warnings = _check_spec_quality(FULL_SPEC, "bundle")
        assert not any("description" in w.lower() for w in warnings)

    def test_warns_fewer_than_2_scenario_rows(self):
        # Only one data row in the table
        spec = """\
---
name: mymodule
version: 1.0
description: A well-described module
type: bundle
status: draft
dependencies: []
---

## Overview
Does something.

## Test Scenarios

| Input | Output |
|-------|--------|
| 1 | 2 |

```yaml:schema
input: int
output: int
```
"""
        warnings = _check_spec_quality(spec, "bundle")
        assert any("example" in w.lower() for w in warnings)

    def test_no_scenario_row_warning_when_2_or_more(self):
        warnings = _check_spec_quality(FULL_SPEC, "bundle")
        assert not any("example" in w.lower() for w in warnings)


# ---------------------------------------------------------------------------
# sp validate quality hints integration test
# ---------------------------------------------------------------------------

class TestValidateQualityHints:
    def _make_project_with_spec(self, tmp_path, spec_content: str):
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        (src / "myspec.spec.md").write_text(spec_content)

    # A structurally valid bundle spec (matches parser template) but no Test Scenarios
    _VALID_BUNDLE_NO_SCENARIOS = """\
---
name: myspec
type: bundle
---

# Overview

A well-described module that does something useful.

# Functions

```yaml:functions
do_thing:
  inputs: {x: integer}
  outputs: {result: integer}
  behavior: "Return x plus one"
```
"""

    def test_validate_shows_quality_warnings(self, tmp_cwd):
        self._make_project_with_spec(tmp_cwd, self._VALID_BUNDLE_NO_SCENARIOS)
        result = run_sp("validate", "myspec", env={"ANTHROPIC_API_KEY": "test-key"}, cwd=str(tmp_cwd))
        combined = result.stdout + result.stderr
        # Should still exit 0 (structural validity)
        assert result.returncode == 0
        # Should show quality warning about missing test scenarios
        assert "test scenarios" in combined.lower() or "scenario" in combined.lower()

    def test_validate_exits_0_with_warnings(self, tmp_cwd):
        self._make_project_with_spec(tmp_cwd, self._VALID_BUNDLE_NO_SCENARIOS)
        result = run_sp("validate", "myspec", env={"ANTHROPIC_API_KEY": "test-key"}, cwd=str(tmp_cwd))
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# _check_spec_quality: yaml:test_scenarios support (HK-17)
# ---------------------------------------------------------------------------

class TestYamlTestScenariosBlock:
    _SPEC_WITH_YAML_BLOCK = """\
---
name: mymodule
version: 1.0
description: A well-described module
type: bundle
status: draft
dependencies: []
---

## Overview
Does something.

```yaml:test_scenarios
- description: "basic case"
  inputs: {param: "value"}
  expected_output: "result"
```

```yaml:schema
input: str
output: str
```
"""

    _SPEC_WITH_TABLE = """\
---
name: mymodule
version: 1.0
description: A well-described module
type: bundle
status: draft
dependencies: []
---

## Overview
Does something.

## Test Scenarios

| Input | Output |
|-------|--------|
| 1 | 2 |
| 3 | 4 |

```yaml:schema
input: int
output: int
```
"""

    _SPEC_WITH_NEITHER = """\
---
name: mymodule
version: 1.0
description: A well-described module
type: bundle
status: draft
dependencies: []
---

## Overview
Does something.

```yaml:schema
input: int
output: int
```
"""

    def test_yaml_block_no_warning(self):
        """Spec with yaml:test_scenarios block does not warn about missing scenarios."""
        warnings = _check_spec_quality(self._SPEC_WITH_YAML_BLOCK, "bundle")
        assert not any("test scenarios" in w.lower() for w in warnings)

    def test_table_no_warning(self):
        """Spec with ## Test Scenarios table does not warn (existing behaviour preserved)."""
        warnings = _check_spec_quality(self._SPEC_WITH_TABLE, "bundle")
        assert not any("test scenarios" in w.lower() for w in warnings)

    def test_neither_warns_with_example_snippet(self):
        """Spec with neither table nor YAML block warns and includes the example snippet."""
        warnings = _check_spec_quality(self._SPEC_WITH_NEITHER, "bundle")
        assert any("test scenarios" in w.lower() for w in warnings)
        # Warning should include the yaml:test_scenarios example
        combined = "\n".join(warnings)
        assert "yaml:test_scenarios" in combined


# ---------------------------------------------------------------------------
# sp --version flag (HK-17)
# ---------------------------------------------------------------------------

class TestVersionFlag:
    def test_version_flag_exits_0(self, tmp_cwd):
        result = run_sp("--version")
        assert result.returncode == 0

    def test_short_version_flag_exits_0(self, tmp_cwd):
        result = run_sp("-V")
        assert result.returncode == 0

    def test_version_output_contains_specsoloist(self, tmp_cwd):
        result = run_sp("--version")
        combined = result.stdout + result.stderr
        assert "specsoloist" in combined


# ---------------------------------------------------------------------------
# sp install-skills: version marker (task 24)
# ---------------------------------------------------------------------------

class TestInstallSkillsVersionMarker:
    def test_installed_skill_starts_with_version_marker(self, tmp_cwd):
        """Installed SKILL.md files start with <!-- sp-version: X.Y.Z -->."""
        target = tmp_cwd / "skills_out"
        result = run_sp("install-skills", "--target", str(target))
        assert result.returncode == 0
        # Find any installed SKILL.md
        skill_files = list(target.rglob("SKILL.md"))
        assert skill_files, "No SKILL.md files installed"
        for skill_file in skill_files:
            first_line = skill_file.read_text().split("\n")[0]
            assert first_line.startswith("<!-- sp-version:"), (
                f"{skill_file.name} first line does not start with version marker: {first_line!r}"
            )

    def test_installed_skill_version_marker_contains_version(self, tmp_cwd):
        """Installed SKILL.md version marker contains a non-empty version string."""
        import importlib.metadata
        pkg_version = importlib.metadata.version("specsoloist")
        target = tmp_cwd / "skills_out"
        run_sp("install-skills", "--target", str(target))
        skill_files = list(target.rglob("SKILL.md"))
        assert skill_files
        first_line = skill_files[0].read_text().split("\n")[0]
        assert pkg_version in first_line


# ---------------------------------------------------------------------------
# sp doctor: skill staleness detection (task 24)
# ---------------------------------------------------------------------------

class TestDoctorSkillStaleness:
    def test_stale_skill_triggers_warning(self, tmp_cwd):
        """doctor warns when an installed skill has an older version marker."""
        skills_dir = tmp_cwd / ".claude" / "skills" / "sp-conduct"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("<!-- sp-version: 0.0.1 -->\n# old skill\n")
        result = run_sp("doctor", env={"ANTHROPIC_API_KEY": "test-key"}, cwd=str(tmp_cwd))
        combined = result.stdout + result.stderr
        assert "install-skills" in combined or "stale" in combined.lower() or "0.0.1" in combined

    def test_current_skill_no_staleness_warning(self, tmp_cwd):
        """doctor does not warn when installed skill version matches current package."""
        import importlib.metadata
        pkg_version = importlib.metadata.version("specsoloist")
        skills_dir = tmp_cwd / ".claude" / "skills" / "sp-conduct"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text(f"<!-- sp-version: {pkg_version} -->\n# current skill\n")
        result = run_sp("doctor", env={"ANTHROPIC_API_KEY": "test-key"}, cwd=str(tmp_cwd))
        combined = result.stdout + result.stderr
        # Should not complain about staleness for a matching version
        assert "0.0.1" not in combined

    def test_skill_without_marker_no_staleness_warning(self, tmp_cwd):
        """doctor silently ignores skill files that have no version marker."""
        skills_dir = tmp_cwd / ".claude" / "skills" / "sp-conduct"
        skills_dir.mkdir(parents=True)
        (skills_dir / "SKILL.md").write_text("# skill without marker\n")
        result = run_sp("doctor", env={"ANTHROPIC_API_KEY": "test-key"}, cwd=str(tmp_cwd))
        # Should not error out
        assert result.returncode == 0
