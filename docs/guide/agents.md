# Agents Guide

SpecSoloist uses **native subagents** — agent definitions for Claude Code and Gemini CLI — to perform multi-step, tool-using compilation tasks. This is the default mode for most commands.

## What Are Native Subagents?

Native subagents are Markdown files that define an agent's role, tools, and behaviour:

- **Claude Code**: `.claude/agents/` directory
- **Gemini CLI**: `.gemini/agents/` directory

When you run `sp conduct`, `sp compose`, `sp fix`, or `sp respec`, SpecSoloist detects which CLI is installed (Claude preferred) and delegates the task to the appropriate agent.

## Available Agents

| Agent | File | Role |
| --- | --- | --- |
| **compose** | `.claude/agents/compose.md` | Draft architecture and specs from natural language |
| **conductor** | `.claude/agents/conductor.md` | Orchestrate builds, resolve dependencies, spawn soloists |
| **soloist** | `.claude/agents/soloist.md` | Compile a single spec into working code and tests |
| **respec** | `.claude/agents/respec.md` | Reverse-engineer existing code into specs |
| **fix** | `.claude/agents/fix.md` | Analyze test failures, patch code, re-test |

## How sp Commands Use Agents

```
sp conduct src/
    └── Conductor agent
            ├── Reads all *.spec.md files
            ├── Resolves dependency order
            └── Spawns soloist agents per spec (parallel)
                    ├── soloist: config
                    ├── soloist: resolver
                    └── soloist: parser ...

sp compose "build a todo app with auth"
    └── Compose agent
            ├── Drafts architecture
            └── Writes spec files to src/

sp fix mymodule
    └── Fix agent
            ├── Reads failing tests
            ├── Patches implementation
            └── Re-runs tests (up to 3 retries)

sp respec src/mymodule.py
    └── Respec agent
            ├── Reads existing code
            └── Writes spec to src/mymodule.spec.md
```

## Usage with Claude Code

```bash
# Default: delegates to Claude agent
sp conduct src/

# Fully automated (no permission prompts) — for CI or quine runs
sp conduct score/ --auto-accept

# Override model
sp conduct src/ --model claude-haiku-4-5-20251001
```

## Usage with Gemini CLI

If `claude` is not installed but `gemini` is, SpecSoloist automatically falls back to Gemini:

```bash
sp conduct src/
# → delegates to gemini agent
```

## --no-agent Fallback

Pass `--no-agent` to skip the agent entirely and use direct LLM API calls. This is faster for simple single-spec compilation but loses the multi-step reasoning and tool-use capabilities:

```bash
sp compile mymodule --no-agent
sp conduct src/ --no-agent
```

Note: `--no-agent` requires an API key (`GEMINI_API_KEY` or `ANTHROPIC_API_KEY`).

## The Quine

`sp conduct score/ --auto-accept` runs the **quine** — it uses the conductor agent to regenerate SpecSoloist's own source code from its own specs. This validates that all specs are complete and correct.

Output goes to `build/quine/`. Run the generated tests with:

```bash
PYTHONPATH=build/quine/src uv run python -m pytest build/quine/tests/ -v
```
