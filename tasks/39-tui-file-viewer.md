# Task 39: TUI file viewer (spec, code, tests)

**Effort**: Small–Medium

**Depends on**: Task 31c (spec detail panel)

## Motivation

The TUI dashboard shows build progress — status icons, log lines, token counts — but
you can't see the actual artifacts: the spec that drove compilation, the code that was
generated, or the tests that were run. To investigate a failure or review output, you
have to leave the TUI and open files manually.

Adding a file viewer to the TUI makes it a self-contained investigation tool. Select a
spec, press a key, and read the spec source, implementation, or tests — all without
leaving the dashboard.

This also lays groundwork for the Spechestra web dashboard (task S-03), which will need
the same file-serving capability over HTTP.

## Design Decisions (locked)

- **Keybindings**: `s` = view spec source, `c` = view generated code, `t` = view
  generated tests, `l` = back to log view (default). These cycle the right panel content.
- **Read-only**: The viewer is display-only. No editing.
- **File resolution**: Derive paths from the spec name + arrangement. The arrangement's
  `output_paths` pattern (`src/specsoloist/{path}.py`, `tests/test_{name}.py`) plus any
  overrides give the exact file paths. The spec file path comes from the parser's
  `src_dir` + spec name + `.spec.md`.
- **SSE server endpoint** (for `sp dashboard` remote mode): Add `GET /files?path=<relative>`
  to the SSE server. Returns file contents as `text/plain`. Only serves files under the
  project root (path traversal guard). This lets the remote dashboard fetch files on demand.
- **Syntax highlighting**: Use Rich's built-in syntax highlighting via `RichLog.write(Syntax(...))`.
  Detect language from file extension.

## Implementation

### Modified: `src/specsoloist/tui.py`

- Add a `FileViewerWidget` (or repurpose `LogPanel`) that displays file contents with
  syntax highlighting. It replaces the log panel content when a file view key is pressed.
- Add keybindings `s`, `c`, `t`, `l` to `DashboardApp`.
- The app needs to know file paths. Options:
  - **Simple**: Pass a `file_resolver` callable to the app that takes `(spec_name, file_type)`
    and returns a file path or content string. For local mode (`--tui`), this reads files
    directly. For remote mode (`sp dashboard`), it fetches from the SSE server.
  - The resolver can be a simple function or a protocol/dataclass.

### Modified: `src/specsoloist/subscribers/sse.py`

- Add `GET /files?path=<relative>` endpoint to `SSEHandler`.
- Path traversal guard: resolve the requested path against the project root, verify the
  resolved path is still under the project root (`os.path.commonpath` check).
- Returns `text/plain` with CORS headers. 404 if file not found.

### Modified: `src/specsoloist/cli.py`

- When wiring up `--tui` mode: pass a local file resolver to the app.
- When wiring up `sp dashboard`: pass an HTTP-based file resolver that fetches from
  the SSE server's `/files` endpoint.

### Tests

- `tests/test_tui.py`: Add tests for keybinding behavior (mock file resolver).
- `tests/test_sse_server.py`: Add tests for `GET /files` — valid path, missing file,
  path traversal blocked, CORS headers.

## Files to Read Before Starting

Read these files in order. They contain everything you need to understand the current
architecture:

1. `AGENTS.md` — project overview, conventions, working principles
2. `tasks/README.md` — current project state, key commands (`uv run python -m pytest tests/`,
   `uv run ruff check src/`)
3. `src/specsoloist/tui.py` — the full TUI: `DashboardApp`, `SpecListWidget`,
   `SpecDetailWidget`, `LogPanel`, `StatusBar`. Understand the widget tree and how
   `refresh_state()` updates everything.
4. `src/specsoloist/subscribers/sse.py` — `SSEServer`, `SSEHandler`, `SSESubscriber`.
   The `/events` and `/status` endpoints. You'll add `/files` here.
5. `src/specsoloist/subscribers/build_state.py` — `BuildState`, `SpecState`. The state
   model that flows through the system.
6. `src/specsoloist/cli.py` — look at `_run_with_tui()` (~line 949) for local TUI wiring,
   and `cmd_dashboard()` (~line 1044) for remote SSE wiring. Both patterns need a file
   resolver injected.
7. `src/specsoloist/schema.py` — `Arrangement`, `OutputPathConfig`. The `resolve_implementation()`
   and `resolve_tests()` methods give you file paths from spec names.
8. `score/arrangement.yaml` — concrete example of output path patterns and overrides.

## Architectural Notes

- The `LogPanel` already uses `RichLog` which supports `write(Syntax(...))`. You likely
  don't need a new widget — just swap what gets written to the log panel based on the
  active view mode.
- `SpecState` doesn't currently store file paths. You'll need either (a) a side-channel
  to resolve paths (the file resolver callable), or (b) extend `SpecState` with path
  fields populated during build events. Option (a) is simpler and doesn't change the
  event/state model.
- For the local TUI case, the arrangement might not be available (user ran `sp build --tui`
  without `--arrangement`). In that case, fall back to the default output path patterns
  from `SpecSoloistCore.config`.

## Success Criteria

- `sp conduct --tui --no-agent`: press `s`/`c`/`t` to view spec/code/tests for selected spec
- `sp dashboard`: same keybindings work, fetching files from SSE server
- `GET /files?path=src/specsoloist/config.py` returns file contents with CORS headers
- Path traversal attempts (e.g., `../../../etc/passwd`) return 403
- `uv run python -m pytest tests/` — all tests pass
- `uv run ruff check src/` — clean
