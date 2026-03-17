# CLI Reference

The `sp` command-line tool is your primary interface for the framework.

## Global Flags

These flags apply to all commands:

| Flag | Description |
| --- | --- |
| `--quiet` | Suppress all non-error output (useful for CI and scripting) |
| `--json` | Emit machine-readable JSON instead of Rich terminal output (where supported) |

## Commands

### Spec Authoring

| Command | Description |
| --- | --- |
| `sp list` | List all specification files in `src/` |
| `sp create <name> <desc>` | Create a new spec from template (`--type`: function, class, module, typedef) |
| `sp validate <name>` | Validate a spec's structure and frontmatter |
| `sp verify` | Verify all specs for orchestration readiness (dependencies, types) |
| `sp graph` | Export the dependency graph as Mermaid markup |
| `sp diff <name>` | Detect drift between a spec and its compiled code |

### Building

| Command | Description |
| --- | --- |
| `sp compile <name>` | Compile a single spec to implementation code and tests |
| `sp build` | Compile all specs in dependency order (non-agent, direct API) |
| `sp conduct [src_dir]` | Orchestrate a full project build using agents (parallel & incremental) |
| `sp vibe [brief]` | Single-command pipeline: compose specs from a brief, then build |

### Testing & Fixing

| Command | Description |
| --- | --- |
| `sp test [name]` | Run tests for a spec; `--all` runs tests for every compiled spec |
| `sp fix <name>` | Analyze failing tests and attempt an autonomous fix |

### Reverse Engineering

| Command | Description |
| --- | --- |
| `sp respec <file>` | Reverse-engineer existing code into a spec |

### Project Setup

| Command | Description |
| --- | --- |
| `sp init [name]` | Scaffold a new project with an arrangement file |
| `sp install-skills` | Install SpecSoloist agent skills to your project or global skills directory |

### Inspection

| Command | Description |
| --- | --- |
| `sp status` | Show the compilation state of each spec |
| `sp doctor` | Check environment health (API keys, CLIs, tools) |

---

## Command Details

### `sp conduct`

```
sp conduct [src_dir] [options]
```

Orchestrates a full project build by spawning agent soloists in dependency order.

| Option | Description |
| --- | --- |
| `--arrangement FILE` | Path to arrangement YAML (auto-discovers `arrangement.yaml`) |
| `--model MODEL` | Override the LLM model |
| `--resume` | Skip specs already compiled (checks manifest + output files); recompile stale or missing |
| `--force` | Recompile all specs regardless of manifest state |
| `--incremental` | Only recompile specs that have changed |
| `--parallel` | Compile independent specs concurrently |
| `--workers N` | Max parallel workers (default: 4) |
| `--no-agent` | Use direct LLM API instead of agent CLI |
| `--auto-accept` | Skip interactive review prompts |

### `sp vibe`

```
sp vibe [brief] [options]
```

Compose + conduct in a single command. Pass a `.md` file path or a plain string description.

| Option | Description |
| --- | --- |
| `--template NAME` | Arrangement template (e.g. `python-fasthtml`, `nextjs-vitest`) |
| `--pause-for-review` | Pause after composing specs so you can review and edit before building |
| `--resume` | Skip already-compiled specs; treats brief as an addendum to an existing project |
| `--model MODEL` | Override LLM model for both compose and conduct steps |
| `--no-agent` | Use direct LLM API |
| `--auto-accept` | Skip interactive review |

### `sp diff`

```
sp diff <name>           # spec-drift mode: compare spec to compiled code
sp diff <left> <right>   # build-diff mode: compare two build directories
sp diff --runs N         # build-diff mode: compare the last N build runs
```

In **spec-drift mode**, reports `MISSING` (spec defines, code lacks), `UNDOCUMENTED` (code has, spec lacks), and `TEST_GAP` (spec defines, no test covers). Add `--json` for machine-readable output.

### `sp build`

Non-agent build: compiles all specs via direct LLM API calls in dependency order. Useful when running outside a Claude/Gemini session.

| Option | Description |
| --- | --- |
| `--arrangement FILE` | Path to arrangement YAML |
| `--model MODEL` | Override LLM model |
| `--incremental` | Only recompile changed specs |
| `--parallel` | Compile concurrently |
| `--workers N` | Max parallel workers (default: 4) |
| `--no-tests` | Skip test generation |

### `sp init`

```
sp init [name] [options]
```

Scaffold a new project. Without `--template`, creates a basic `arrangement.yaml`.

| Option | Description |
| --- | --- |
| `--template NAME` | Named arrangement template (see below) |
| `--list-templates` | List all available templates |
| `--arrangement {python,typescript}` | Generic arrangement type (default: python) |

Available templates:

| Template | Description |
| --- | --- |
| `python-fasthtml` | FastHTML + uv + pytest |
| `nextjs-vitest` | Next.js App Router + TypeScript + vitest |
| `nextjs-playwright` | Next.js + Playwright E2E |

### `sp doctor`

```
sp doctor [--arrangement FILE]
```

Checks API keys, installed CLIs, and tool availability. With `--arrangement`, also verifies that all declared `env_vars` are set in the environment.

### `sp compile`

```
sp compile <name> [options]
```

| Option | Description |
| --- | --- |
| `--arrangement FILE` | Path to arrangement YAML |
| `--model MODEL` | Override LLM model |
| `--no-tests` | Skip test generation |
| `--json` | Emit machine-readable JSON output |

---

## Agents

By default, `sp conduct`, `sp compose`, `sp vibe`, `sp fix`, and `sp respec` delegate to a Claude or Gemini CLI agent for multi-step reasoning and tool use. Pass `--no-agent` to fall back to direct LLM API calls.

See the [Agents guide](../guide/agents.md) for details.

## Arrangement

An Arrangement file (`arrangement.yaml`) configures the build environment: output paths, language, tools, and setup commands. It is auto-discovered from the current working directory, or specified with `--arrangement`.

See the [Arrangement guide](../guide/arrangement.md) for full documentation.
