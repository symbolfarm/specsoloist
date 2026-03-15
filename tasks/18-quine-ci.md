# Task 18: Quine CI — Scheduled Validation Workflow

## Why

The quine (`sp conduct score/`) is the canary for spec quality. If a source change
causes the quine to regress, we want to know immediately — not when someone manually
runs it weeks later. A scheduled CI workflow provides this automatically.

## Cost Management

- Use `--model haiku` (cheapest capable model, ~$0.50–2.00/run)
- Run on `schedule:` only — NOT on `push:` or `pull_request:` (prevents external forks
  from triggering it and avoids running on every commit)
- Weekly schedule (not nightly) — keeps monthly cost under ~$10
- Add a monthly spend cap on the API key at the provider level (external to this task)
- Use `--resume` flag so specs that haven't changed since last run are skipped

## Security

- API key stored as a GitHub Actions encrypted secret (`ANTHROPIC_API_KEY`)
- Workflow only runs on `schedule:` and manual `workflow_dispatch` — no external trigger
- Output (`build/quine/`) is uploaded as an artifact, not committed

## Files to Read

- `.github/workflows/publish.yaml` — existing workflow pattern to follow
- `.github/workflows/ci.yaml` — existing CI pattern
- `src/specsoloist/cli.py` — `sp conduct` flags (`--model`, `--auto-accept`, `--resume`)

## Steps

1. Create `.github/workflows/quine.yaml`:

```yaml
name: Quine Validation

on:
  schedule:
    - cron: '0 2 * * 0'   # Sunday 2am UTC (weekly)
  workflow_dispatch:        # allow manual trigger

jobs:
  quine:
    runs-on: ubuntu-latest
    timeout-minutes: 60

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Set up Python
        run: uv python install 3.10

      - name: Install dependencies
        run: uv sync --all-extras --dev

      - name: Install claude CLI
        run: npm install -g @anthropic-ai/claude-code

      - name: Run quine
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          uv run sp conduct score/ \
            --model claude-haiku-4-5-20251001 \
            --auto-accept \
            --resume

      - name: Run quine tests
        run: |
          PYTHONPATH=build/quine/src uv run python -m pytest build/quine/tests/ -q

      - name: Upload quine output
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: quine-output-${{ github.run_id }}
          path: build/quine/
          retention-days: 30
```

2. Update `tasks/README.md` to note that the quine CI is now running.
3. Add a note to `CONTRIBUTING.md` about the weekly quine run.

## Success Criteria

- `.github/workflows/quine.yaml` exists and is valid YAML
- Workflow triggers on schedule and `workflow_dispatch`
- Uses `ANTHROPIC_API_KEY` secret (not hardcoded)
- Quine output uploaded as artifact
- Does NOT trigger on push or pull_request
- Manual trigger works: `gh workflow run quine.yaml`

## Notes

The quine requires `claude` CLI to be installed in CI (for agent mode). If this proves
unreliable in CI, fall back to `--no-agent` mode with direct LLM API calls — it's slower
but more reproducible. `--no-agent` removes the need to install the claude CLI.
