# Task: Add `--resume` Flag to `sp conduct`

## Context

SpecSoloist is a spec-driven AI coding framework. Read `AGENTS.md` for full project context.

`sp conduct` compiles all specs in a project in dependency order, spawning soloists level
by level. For a 15-spec web app this might take 10–20 minutes. If the run is interrupted
mid-way — API rate limit, network error, the user closing the terminal — the current
behaviour is to restart from scratch.

The build manifest (`BuildManifest` in `src/specsoloist/manifest.py`) already tracks which
specs were successfully compiled, including their output files and content hashes. The
information needed for resume is already there. `--resume` adds a flag that reads the
manifest and skips already-compiled specs.

See `PROPOSALS.md §5b` for the original proposal.

## What to Build

### 1. `--resume` flag in CLI (`src/specsoloist/cli.py`)

Add `--resume` to the `conduct` subcommand:

```bash
sp conduct specs/ --arrangement arrangement.yaml --resume
```

When `--resume` is set:
1. Load the build manifest before starting
2. For each spec in the dependency graph, check if it's already compiled:
   - It has an entry in the manifest
   - Its content hash matches the current spec file
   - Its listed output files exist on disk
3. Skip specs that pass all three checks; mark them as `SKIPPED (cached)` in the output
4. Compile only the specs that need rebuilding
5. Ensure dependency levels still respect ordering — if spec A was skipped but spec B
   (which depends on A) was NOT skipped, B should still be compiled normally

### 2. Hash checking

The manifest stores `spec_hash` per compiled spec. The existing `compute_file_hash()`
function in `manifest.py` can recompute it. A spec needs recompilation if any of:
- Not in manifest
- `spec_hash` doesn't match current file hash
- Any declared output file is missing from disk
- Any dependency was recompiled this run (cascade)

The cascade case is critical: if spec `state` was recompiled (because its spec changed),
then `routes` (which depends on `state`) must also be recompiled even if `routes.spec.md`
is unchanged.

### 3. Output during resume

Display clearly which specs were cached vs compiled:

```
Resuming build from manifest...

  Level 0:  fasthtml_interface  SKIPPED (cached)
            state               COMPILING...
  Level 1:  layout              SKIPPED (cached)
            routes              COMPILING... (dep state changed)

  1 compiled, 3 skipped
```

### 4. Conductor agent instruction

The conductor agent (`.claude/agents/conductor.md`) drives `sp conduct`. Update the conductor
agent's instructions to explain `--resume` behaviour so that when the conductor is deciding
what to compile, it correctly interprets the manifest state.

Alternatively: expose `--resume` logic at the CLI/Python layer so the conductor agent doesn't
need to understand it — `sp conduct --resume` just does the right thing from the agent's
perspective. This is the preferred approach (simpler agent prompt).

### 5. `--force` flag (complement to `--resume`)

While implementing `--resume`, also add `--force` as the explicit "ignore manifest, recompile
everything" flag. This makes the default behaviour (no flag) explicit: recompile anything
that the manifest says is stale, skip what is fresh. `--resume` and `--force` are mutually
exclusive.

The current "always recompile" behaviour should become the default only when the manifest
shows staleness. In other words, move toward making incremental builds the default, with
`--force` to override.

## Files to Read First

- `src/specsoloist/cli.py` — `cmd_conduct()`, `_run_agent_oneshot()`
- `src/specsoloist/manifest.py` — `BuildManifest`, `SpecBuildInfo`, `compute_file_hash()`
- `src/specsoloist/resolver.py` — dependency graph, build order computation
- `.claude/agents/conductor.md` — conductor agent instructions
- `PROPOSALS.md §5b` — original proposal

## Success Criteria

1. `sp conduct --resume` skips specs whose hash and output files match the manifest.
2. `sp conduct --resume` recompiles specs whose spec file has changed since last build.
3. `sp conduct --resume` recompiles a spec if any of its dependencies were recompiled
   this run (cascade).
4. `sp conduct --force` recompiles all specs regardless of manifest state.
5. Default `sp conduct` (no flags) uses manifest staleness to decide — equivalent to
   `--resume` for fresh specs, recompiles stale ones.
6. Output clearly distinguishes SKIPPED vs COMPILING specs.
7. All existing tests pass: `uv run python -m pytest tests/`
8. Ruff passes: `uv run ruff check src/`
9. New tests in `tests/test_conduct_resume.py` covering: all-cached, partial-cached,
   cascade recompile, missing output file triggers recompile.
