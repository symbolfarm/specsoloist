"""
Tests for SpecParser.
"""

import os
import tempfile
from specsoloist.parser import SpecParser


def test_parse_metadata_with_description():
    """Test that description is parsed from frontmatter."""
    content = """---
name: test_component
description: A explicit description from frontmatter.
---
# 1. Overview
This should be ignored since frontmatter has it.
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)
        
        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")
        
        assert parsed.metadata.name == "test_component"
        assert parsed.metadata.description == "A explicit description from frontmatter."


def test_extract_description_from_overview():
    """Test that description is extracted from Overview if missing in frontmatter."""
    content = """---
name: test_component
---
# 1. Overview
This is the extracted description.

# 2. Interface
...
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)
        
        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")
        
        assert parsed.metadata.description == "This is the extracted description."


def test_extract_description_ignores_empty_lines():
    """Test that the first non-empty line after Overview is used."""
    content = """---
name: test_component
---
# 1. Overview

   

This is the real description.
"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = os.path.join(tmp_dir, "test.spec.md")
        with open(path, 'w') as f:
            f.write(content)
        
        parser = SpecParser(tmp_dir)
        parsed = parser.parse_spec("test")
        
        assert parsed.metadata.description == "This is the real description."
