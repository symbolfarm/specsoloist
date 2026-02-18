# CLI Reference

The `sp` command-line tool is your primary interface for the framework.

| Command | Description |
| --- | --- |
| `sp list` | List all specifications in `src/` |
| `sp create <name> <desc>` | Create a new spec from the template |
| `sp compose <request>` | Draft architecture and specs from natural language |
| `sp validate <name>` | Check a spec for SRS compliance |
| `sp conduct [src_dir]` | Orchestrate a project build (parallel & incremental) |
| `sp compile <name>` | Compile a spec to implementation code and tests |
| `sp test <name>` | Execute the test suite for a component |
| `sp fix <name>` | Analyze failures and attempt an autonomous fix |
| `sp respec <file>` | Reverse engineer existing code into a spec |
| `sp perform <workflow>` | Execute an orchestration workflow |
| `sp build` | Alias for `conduct` |

## Build Options

- `--incremental`: Only recompile specs that have changed since the last build.
- `--parallel`: Compile independent specs concurrently.
- `--workers <n>`: Set the number of parallel workers.
- `--model <name>`: Override the default LLM model for a specific run.
- `--auto-accept`: Run non-interactively (agent mode). For `sp conduct score/`, also enables `bypassPermissions`.
- `--no-agent`: Use direct LLM calls instead of delegating to a Claude/Gemini CLI agent.
- `--arrangement <path>`: Load an Arrangement config file. Auto-discovers `arrangement.yaml` if omitted.

## Arrangement

An Arrangement file (`arrangement.yaml`) configures the build environment: output paths, language, tools, and setup commands. It is auto-discovered from the current working directory, or specified explicitly with `--arrangement`.

See the [Arrangement guide](../guide/arrangement.md) for full documentation.

## Agents

By default, `sp compose`, `sp conduct`, `sp fix`, and `sp respec` delegate to a Claude or Gemini CLI agent for multi-step reasoning and tool use. Pass `--no-agent` to fall back to direct LLM calls.

See the [Agents guide](../guide/agents.md) for details.
