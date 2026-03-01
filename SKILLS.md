# SpecSoloist Skills

SpecSoloist ships a set of [agent skills](https://agentskills.io) that teach Claude (and other compatible AI agents) to use the `sp` CLI commands. Each skill activates when you describe a matching task — no explicit invocation needed.

## Available Skills

| Skill | When it activates | CLI command |
|-------|------------------|-------------|
| `sp-compose` | "Design me a X system", "create specs for..." | `sp compose "<description>"` |
| `sp-conduct` | "Build the specs", "compile the project" | `sp conduct [dir]` |
| `sp-respec` | "Spec out this file", "reverse-engineer..." | `sp respec <file>` |
| `sp-fix` | "Fix the failing tests", "the tests are broken" | `sp fix <name>` |
| `sp-soloist` | "Compile this spec", "implement this component" | `sp compile <name>` |

## Installation

### Via Claude Code plugin marketplace

```
/plugin marketplace add symbolfarm/specsoloist
/plugin install specsoloist-skills@specsoloist
```

### Via the `sp` CLI

```bash
sp install-skills                        # Install to .claude/skills/ (current project)
sp install-skills --target ~/.claude/skills  # Install globally
```

## Skills vs. Subagents

SpecSoloist provides two complementary kinds of agent extensions:

| | Skills (`src/specsoloist/skills/`) | Subagents (`.claude/agents/`) |
|---|---|---|
| **Invoked by** | User mention / task description | System / orchestrator (Task tool) |
| **Scope** | User-facing workflows | Multi-agent delegation |
| **Use case** | "compose me a todo app" | Conductor spawning a soloist |

These are complementary. A skill may delegate to a subagent under the hood (e.g. `sp-conduct` triggers the conductor agent, which spawns soloist agents per spec).

## Skill source

Skills live in `src/specsoloist/skills/` and are included in the installed package. Each skill is a directory containing a `SKILL.md` with YAML frontmatter and instructions.
