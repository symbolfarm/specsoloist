# sp conduct Reference

`sp conduct` orchestrates a full project build: it reads all specs, resolves the
dependency graph, and compiles specs in parallel (by level) using agent soloists.

---

## Basic usage

```bash
sp conduct                         # build specs in src/ (auto-discovers arrangement.yaml)
sp conduct specs/                  # build specs in a specific directory
sp conduct specs/ --arrangement arrangement.yaml
sp conduct --resume                # skip already-compiled specs (incremental)
sp conduct --force                 # recompile everything regardless of manifest
sp conduct --no-agent              # use direct LLM API instead of spawning agent CLIs
sp conduct --model claude-haiku-4-5-20251001   # override model
```

---

## Key flags

| Flag | Description |
|------|-------------|
| `src_dir` (positional) | Spec directory. Overrides `specs_path` from arrangement. |
| `--arrangement FILE` | Path to arrangement YAML. Auto-discovers `arrangement.yaml` if omitted. |
| `--resume` | Skip specs whose spec hash and output files match the build manifest. |
| `--force` | Recompile all specs, ignoring the manifest. |
| `--no-agent` | Use direct LLM API calls. Required when running inside an active agent session. |
| `--auto-accept` | Skip interactive review prompts (useful for CI). |
| `--model MODEL` | Override LLM model. Takes precedence over arrangement's `model` field. |
| `--parallel` | Enable concurrent compilation within each dependency level. |
| `--workers N` | Max parallel workers (default: 4). Used with `--parallel`. |

---

## How it works

1. Discovers all `*.spec.md` files in `src_dir` (or `specs_path` from arrangement).
2. Reads frontmatter from each spec to extract `name`, `type`, and `dependencies`.
3. Builds a dependency graph and groups specs into parallelizable levels.
4. Compiles each level in order; specs within a level are compiled in parallel.
5. Runs the test command from `arrangement.yaml` (`build_commands.test`) to verify.

Each spec is compiled by a soloist agent that: reads the spec, writes implementation
and test files, runs tests, and retries up to 3 times on failure.

---

## Arrangement integration

`sp conduct` loads `arrangement.yaml` automatically and uses:
- `specs_path` — spec discovery directory (overridden by the positional `src_dir` arg)
- `output_paths` — where to write implementation and test files
- `target_language` — injected into every soloist prompt
- `environment.setup_commands` — run before compilation starts
- `build_commands.test` — run at the end to verify the full build
- `model` — LLM model (overridden by `--model` flag)

---

## Incremental builds

The build manifest (`build/.specsoloist-manifest.json`) tracks spec hashes and output
files. With `--resume`, a spec is skipped when:
- Its content hash matches the manifest, AND
- All its output files exist on disk

Use `--resume` when adding specs to an existing project. Use `--force` to recompile
everything from scratch (e.g. after changing the arrangement or a shared reference spec).

---

## Running inside a Claude Code session

`sp conduct` spawns a subprocess, which is blocked when already inside an active Claude
Code session. Instead, use the `conductor` agent directly:

```
Agent(subagent_type="conductor", prompt="Build specs in specs/ using arrangement.yaml")
```

Or use `sp conduct --no-agent`, which calls the LLM API directly with no subprocess.

---

## See also

- `sp help arrangement` — full arrangement.yaml reference
- `sp status` — show compilation state of each spec
- `sp vibe` — compose + conduct in one command
