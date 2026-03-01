"""
Schema and completeness tests for agent definition files.

Covers three forms of each agent:
  - Skills:        src/specsoloist/skills/sp-<name>/SKILL.md  (agentskills format)
  - Claude agents: .claude/agents/<name>.md                   (Claude Code format)
  - Gemini agents: .gemini/agents/<name>.md                   (Gemini CLI format)

These tests validate structure only — not behavioral correctness.
"""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
SKILLS_DIR = ROOT / "src" / "specsoloist" / "skills"
CLAUDE_AGENTS_DIR = ROOT / ".claude" / "agents"
GEMINI_AGENTS_DIR = ROOT / ".gemini" / "agents"


def parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) for a Markdown file with YAML frontmatter."""
    content = path.read_text()
    if not content.strip().startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    fm = yaml.safe_load(parts[1].strip()) or {}
    return fm, parts[2].strip()


def skill_files() -> list[Path]:
    return sorted(SKILLS_DIR.glob("*/SKILL.md"))


def claude_agent_files() -> list[Path]:
    return sorted(CLAUDE_AGENTS_DIR.glob("*.md"))


def gemini_agent_files() -> list[Path]:
    return sorted(GEMINI_AGENTS_DIR.glob("*.md"))


# ---------------------------------------------------------------------------
# Skills (agentskills format)
# ---------------------------------------------------------------------------

SKILL_REQUIRED_FIELDS = ("name", "description", "license", "compatibility", "allowed-tools")


@pytest.mark.parametrize("path", skill_files(), ids=lambda p: p.parent.name)
def test_skill_required_fields(path):
    fm, _ = parse_frontmatter(path)
    missing = [f for f in SKILL_REQUIRED_FIELDS if f not in fm]
    assert not missing, f"{path.parent.name}/SKILL.md missing fields: {missing}"


@pytest.mark.parametrize("path", skill_files(), ids=lambda p: p.parent.name)
def test_skill_name_matches_directory(path):
    fm, _ = parse_frontmatter(path)
    assert fm.get("name") == path.parent.name, (
        f"name '{fm.get('name')}' does not match directory '{path.parent.name}'"
    )


@pytest.mark.parametrize("path", skill_files(), ids=lambda p: p.parent.name)
def test_skill_body_non_empty(path):
    _, body = parse_frontmatter(path)
    assert body, f"{path.parent.name}/SKILL.md has empty body"


# ---------------------------------------------------------------------------
# Claude agents (Claude Code format)
# ---------------------------------------------------------------------------

CLAUDE_REQUIRED_FIELDS = ("name", "description", "tools", "model")


@pytest.mark.parametrize("path", claude_agent_files(), ids=lambda p: p.stem)
def test_claude_agent_required_fields(path):
    fm, _ = parse_frontmatter(path)
    missing = [f for f in CLAUDE_REQUIRED_FIELDS if f not in fm]
    assert not missing, f".claude/agents/{path.name} missing fields: {missing}"


@pytest.mark.parametrize("path", claude_agent_files(), ids=lambda p: p.stem)
def test_claude_agent_tools_is_list(path):
    fm, _ = parse_frontmatter(path)
    assert isinstance(fm.get("tools"), list), (
        f".claude/agents/{path.name}: 'tools' must be a YAML list"
    )


@pytest.mark.parametrize("path", claude_agent_files(), ids=lambda p: p.stem)
def test_claude_agent_name_matches_filename(path):
    fm, _ = parse_frontmatter(path)
    assert fm.get("name") == path.stem, (
        f"name '{fm.get('name')}' does not match filename '{path.stem}'"
    )


@pytest.mark.parametrize("path", claude_agent_files(), ids=lambda p: p.stem)
def test_claude_agent_body_non_empty(path):
    _, body = parse_frontmatter(path)
    assert body, f".claude/agents/{path.name} has empty body"


# ---------------------------------------------------------------------------
# Gemini agents (Gemini CLI format)
# ---------------------------------------------------------------------------

GEMINI_REQUIRED_FIELDS = ("name", "description", "tools", "model", "max_turns")


@pytest.mark.parametrize("path", gemini_agent_files(), ids=lambda p: p.stem)
def test_gemini_agent_required_fields(path):
    fm, _ = parse_frontmatter(path)
    missing = [f for f in GEMINI_REQUIRED_FIELDS if f not in fm]
    assert not missing, f".gemini/agents/{path.name} missing fields: {missing}"


@pytest.mark.parametrize("path", gemini_agent_files(), ids=lambda p: p.stem)
def test_gemini_agent_tools_is_list(path):
    fm, _ = parse_frontmatter(path)
    assert isinstance(fm.get("tools"), list), (
        f".gemini/agents/{path.name}: 'tools' must be a YAML list"
    )


@pytest.mark.parametrize("path", gemini_agent_files(), ids=lambda p: p.stem)
def test_gemini_agent_max_turns_is_int(path):
    fm, _ = parse_frontmatter(path)
    assert isinstance(fm.get("max_turns"), int), (
        f".gemini/agents/{path.name}: 'max_turns' must be an integer"
    )


@pytest.mark.parametrize("path", gemini_agent_files(), ids=lambda p: p.stem)
def test_gemini_agent_name_matches_filename(path):
    fm, _ = parse_frontmatter(path)
    assert fm.get("name") == path.stem, (
        f"name '{fm.get('name')}' does not match filename '{path.stem}'"
    )


@pytest.mark.parametrize("path", gemini_agent_files(), ids=lambda p: p.stem)
def test_gemini_agent_body_non_empty(path):
    _, body = parse_frontmatter(path)
    assert body, f".gemini/agents/{path.name} has empty body"


# ---------------------------------------------------------------------------
# Completeness: all three forms must stay in sync
# ---------------------------------------------------------------------------

def test_claude_and_gemini_agent_sets_match():
    """Every Claude agent must have a Gemini counterpart and vice versa."""
    claude_names = {p.stem for p in claude_agent_files()}
    gemini_names = {p.stem for p in gemini_agent_files()}
    assert claude_names == gemini_names, (
        f"Claude-only: {claude_names - gemini_names}, "
        f"Gemini-only: {gemini_names - claude_names}"
    )


def test_skill_count_matches_agent_count():
    """Number of skills must match number of native agents.

    All skills in src/specsoloist/skills/ are expected to be agent-type
    skills with Claude and Gemini counterparts. If a non-agent skill is
    added, adjust this test accordingly.
    """
    n_skills = len(skill_files())
    n_claude = len(claude_agent_files())
    assert n_skills == n_claude, (
        f"Skill count ({n_skills}) != Claude agent count ({n_claude}). "
        "Add or remove the corresponding skill/agent file."
    )


def test_agent_directories_non_empty():
    """Sanity check: all three directories must contain files."""
    assert skill_files(), f"No skills found in {SKILLS_DIR}"
    assert claude_agent_files(), f"No Claude agents found in {CLAUDE_AGENTS_DIR}"
    assert gemini_agent_files(), f"No Gemini agents found in {GEMINI_AGENTS_DIR}"
