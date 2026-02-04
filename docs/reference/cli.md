# CLI Reference

The `sp` command-line tool is your primary interface for the framework.

| Command | Description |
| --- | --- |
| `sp list` | List all specifications in `src/` |
| `sp create <name> <desc>` | Create a new spec from the template |
| `sp compose <request>` | Draft architecture and specs from natural language |
| `sp validate <name>` | Check a spec for SRS compliance |
| `sp conduct` | Orchestrate a project build (parallel & incremental) |
| `sp compile <name>` | Compile a spec to implementation code and tests |
| `sp test <name>` | Execute the test suite for a component |
| `sp fix <name>` | Analyze failures and attempt an autonomous fix |
| `sp lift <file>` | Reverse engineer existing code into a spec |
| `sp perform <workflow>` | Execute an orchestration workflow |
| `sp build` | Alias for `conduct` |

## Build Options

-   `--incremental`: Only recompile specs that have changed since the last build.
-   `--parallel`: Compile independent specs concurrently.
-   `--workers <n>`: Set the number of parallel workers.
-   `--model <name>`: Override the default LLM model for a specific run.
