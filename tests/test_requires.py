"""Tests for the requires: field in spec frontmatter (task 36)."""

import os
import tempfile

from specsoloist.core import SpecSoloistCore, _requirement_satisfied, _basic_version_check
from specsoloist.parser import SpecParser


# ---------------------------------------------------------------------------
# Parser: requires field parsing
# ---------------------------------------------------------------------------

def test_parse_requires_field():
    """requires: list is parsed from frontmatter."""
    content = """---
name: tui
type: bundle
requires:
  - textual>=1.0
  - rich>=13.0.0
---
# Overview
A TUI dashboard.

## Functions
Some function docs.
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "tui.spec.md")
        with open(path, "w") as f:
            f.write(content)
        parser = SpecParser(tmp)
        parsed = parser.parse_spec("tui")
        assert parsed.metadata.requires == ["textual>=1.0", "rich>=13.0.0"]


def test_parse_no_requires_field():
    """Missing requires: defaults to empty list."""
    content = """---
name: config
type: bundle
---
# Overview
Config module.

## Functions
Some function docs.
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "config.spec.md")
        with open(path, "w") as f:
            f.write(content)
        parser = SpecParser(tmp)
        parsed = parser.parse_spec("config")
        assert parsed.metadata.requires == []


def test_validate_accepts_requires():
    """sp validate should not error on specs with requires: field."""
    content = """---
name: tui
type: bundle
requires:
  - textual>=1.0
---
# Overview
A TUI dashboard.

## Functions
Some function docs.
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "tui.spec.md")
        with open(path, "w") as f:
            f.write(content)
        parser = SpecParser(tmp)
        result = parser.validate_spec("tui")
        assert result["valid"], result["errors"]


# ---------------------------------------------------------------------------
# _requirement_satisfied helper
# ---------------------------------------------------------------------------

def test_requirement_satisfied_installed_package():
    """A package we know is installed (pyyaml) should be satisfied."""
    assert _requirement_satisfied("pyyaml") is True


def test_requirement_satisfied_with_version():
    """pyyaml>=6.0 should be satisfied (we require it in pyproject.toml)."""
    assert _requirement_satisfied("pyyaml>=6.0") is True


def test_requirement_not_satisfied_missing():
    """A made-up package should not be satisfied."""
    assert _requirement_satisfied("nonexistent-package-xyz-12345") is False


def test_requirement_not_satisfied_version_too_high():
    """A package with an impossibly high version requirement should fail."""
    assert _requirement_satisfied("pyyaml>=999.0.0") is False


# ---------------------------------------------------------------------------
# _basic_version_check helper
# ---------------------------------------------------------------------------

def test_basic_version_check_gte():
    assert _basic_version_check("1.2.3", ">=1.0.0") is True
    assert _basic_version_check("1.2.3", ">=2.0.0") is False


def test_basic_version_check_eq():
    assert _basic_version_check("1.2.3", "==1.2.3") is True
    assert _basic_version_check("1.2.3", "==1.2.4") is False


def test_basic_version_check_neq():
    assert _basic_version_check("1.2.3", "!=1.2.4") is True
    assert _basic_version_check("1.2.3", "!=1.2.3") is False


def test_basic_version_check_compound():
    assert _basic_version_check("1.5.0", ">=1.0,<2.0") is True
    assert _basic_version_check("2.0.0", ">=1.0,<2.0") is False


# ---------------------------------------------------------------------------
# Core: check_requirements integration
# ---------------------------------------------------------------------------

def test_check_requirements_all_satisfied():
    """Specs requiring installed packages should return empty dict."""
    content = """---
name: mymod
type: bundle
requires:
  - pyyaml>=6.0
---
# Overview
Uses pyyaml.

## Functions
Some function docs.
"""
    with tempfile.TemporaryDirectory() as tmp:
        specdir = os.path.join(tmp, "src")
        os.makedirs(specdir)
        with open(os.path.join(specdir, "mymod.spec.md"), "w") as f:
            f.write(content)

        core = SpecSoloistCore(root_dir=tmp)
        core.parser.src_dir = specdir
        core.resolver.parser.src_dir = specdir
        missing = core.check_requirements()
        assert missing == {}


def test_check_requirements_missing():
    """Specs requiring a nonexistent package should appear in missing dict."""
    content = """---
name: exotic
type: bundle
requires:
  - nonexistent-package-xyz>=1.0
---
# Overview
Needs a fake package.

## Functions
Some function docs.
"""
    with tempfile.TemporaryDirectory() as tmp:
        specdir = os.path.join(tmp, "src")
        os.makedirs(specdir)
        with open(os.path.join(specdir, "exotic.spec.md"), "w") as f:
            f.write(content)

        core = SpecSoloistCore(root_dir=tmp)
        core.parser.src_dir = specdir
        core.resolver.parser.src_dir = specdir
        missing = core.check_requirements()
        assert "nonexistent-package-xyz>=1.0" in missing
        assert "exotic" in missing["nonexistent-package-xyz>=1.0"]


def test_check_requirements_deduplicates_across_specs():
    """Same requirement from multiple specs should list all declaring specs."""
    spec_a = """---
name: a
type: bundle
requires:
  - nonexistent-xyz
---
# Overview
Module A.

## Functions
Some function docs.
"""
    spec_b = """---
name: b
type: bundle
requires:
  - nonexistent-xyz
---
# Overview
Module B.

## Functions
Some function docs.
"""
    with tempfile.TemporaryDirectory() as tmp:
        specdir = os.path.join(tmp, "src")
        os.makedirs(specdir)
        with open(os.path.join(specdir, "a.spec.md"), "w") as f:
            f.write(spec_a)
        with open(os.path.join(specdir, "b.spec.md"), "w") as f:
            f.write(spec_b)

        core = SpecSoloistCore(root_dir=tmp)
        core.parser.src_dir = specdir
        core.resolver.parser.src_dir = specdir
        missing = core.check_requirements()
        assert "nonexistent-xyz" in missing
        assert sorted(missing["nonexistent-xyz"]) == ["a", "b"]
