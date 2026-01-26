# CLI Reference

The `specular` command-line tool is your primary interface for the framework.

| Command | Description |
| --- | --- |
| `specular list` | List all specifications in `src/` |
| `specular create <name> <desc>` | Create a new spec from the template |
| `specular validate <name>` | Check a spec for SRS compliance |
| `specular compile <name>` | Compile a spec to implementation code and tests |
| `specular test <name>` | Execute the test suite for a component |
| `specular fix <name>` | Analyze failures and attempt an autonomous fix |
| `specular build` | Compile all specs in dependency order |

## Build Options

-   `--incremental`: Only recompile specs that have changed since the last build.
-   `--parallel`: Compile independent specs concurrently.
-   `--workers <n>`: Set the number of parallel workers.
-   `--model <name>`: Override the default LLM model for a specific run.
