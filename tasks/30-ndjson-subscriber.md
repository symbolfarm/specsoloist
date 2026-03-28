# Task 30: NDJSON subscriber and `--log-file` flag

**Effort**: Small

**Depends on**: Task 28 (event emission wired up)

## Motivation

The first concrete consumer of the event bus. Writes newline-delimited JSON to a file or
stdout, enabling post-hoc analysis with `jq`, Datadog, Grafana, or any log aggregator. This
is IDEAS.md §3a.

## Design Decisions (locked)

- **NDJSON format**: one JSON object per line, no wrapping array. Each line is a serialised
  `BuildEvent` with ISO 8601 timestamp.
- **CLI flag**: `sp conduct --log-file <path>` writes events to a file. `sp conduct --log-file -`
  writes to stdout (useful for piping). The flag also works on `sp build` and `sp compile`.
- **Subscriber class**: `NdjsonSubscriber(file_handle)` — receives a writable file object.
  The CLI opens the file and passes it in.
- **Also enable with `--json` flag**: when `--json` is passed to `sp conduct`, events stream
  to stdout as NDJSON in addition to the final JSON summary. This extends the existing `--json`
  behaviour rather than adding a conflicting mode.

## Implementation

### New file: `src/specsoloist/subscribers/ndjson.py`

```python
class NdjsonSubscriber:
    def __init__(self, file: IO[str]) -> None: ...
    def __call__(self, event: BuildEvent) -> None: ...  # json.dumps + write + flush
```

### Modified: `src/specsoloist/cli.py`

- Add `--log-file` argument to conduct/build/compile subparsers
- When `--log-file` is set: create `EventBus`, subscribe `NdjsonSubscriber`, pass bus to core
- When `--json` is set on conduct: also subscribe `NdjsonSubscriber(sys.stdout)`
- Wire `EventBus` lifecycle (close on completion)

### Spec

Add to `score/events.spec.md` or create a small `score/ndjson_subscriber.spec.md` — agent's
choice based on spec size.

### Tests

- `tests/test_ndjson_subscriber.py`
- Subscriber writes valid NDJSON to a StringIO
- Each line parses as valid JSON with expected fields
- Timestamps are ISO 8601
- Integration: `sp conduct --log-file /tmp/test.ndjson` produces a readable log file
  (can be a subprocess test or mocked)

## Files to Read Before Starting

- `src/specsoloist/events.py` — BuildEvent and EventBus
- `src/specsoloist/cli.py` — `cmd_conduct()`, `cmd_build()`, argument parsing
- Task 28 output — where events are emitted

## Success Criteria

- `uv run python -m pytest tests/test_ndjson_subscriber.py` passes
- `uv run python -m pytest tests/` — all tests pass
- `uv run ruff check src/` — clean
- `sp conduct score/ --log-file /tmp/test.ndjson` produces valid NDJSON
