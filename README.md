# SpecSoloist

<!-- TODO: Replace with actual logo -->
<p align="center">
  <img src="docs/assets/logo.svg" alt="SpecSoloist logo" width="120">
</p>

<p align="center">
  <strong>Spec-as-Source AI coding framework</strong><br>
  Write specs. Compile to code. Detect drift.
</p>

<p align="center">
  <a href="https://pypi.org/project/specsoloist/"><img src="https://img.shields.io/pypi/v/specsoloist" alt="PyPI"></a>
  <a href="https://pypi.org/project/specsoloist/"><img src="https://img.shields.io/pypi/pyversions/specsoloist" alt="Python"></a>
  <a href="https://github.com/symbolfarm/specsoloist/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/specsoloist" alt="License"></a>
  <a href="https://github.com/symbolfarm/specsoloist/actions/workflows/ci.yaml"><img src="https://github.com/symbolfarm/specsoloist/actions/workflows/ci.yaml/badge.svg" alt="CI"></a>
  <a href="https://symbolfarm.github.io/specsoloist/"><img src="https://img.shields.io/badge/docs-mkdocs-blue" alt="Docs"></a>
</p>

---

**SpecSoloist** treats specifications as the source of truth and uses AI agents to compile
them into executable code. Compose systems from natural language, conduct parallel builds,
and detect spec-vs-code drift.

> **Code is a build artifact. Specs are the source of truth.**

<!-- TODO: Replace with actual demo recording (asciinema or GIF) -->
<!-- Suggested: record `sp vibe` or `sp conduct --tui` in action -->
<p align="center">
  <em>Demo: <code>sp conduct --tui</code> building a project from specs</em><br>
  <code>[demo GIF placeholder — record after TUI file viewer is complete]</code>
</p>

## Quick Start

```bash
pip install specsoloist
export GEMINI_API_KEY="your-key"   # or ANTHROPIC_API_KEY
```

### Vibe-code a project from a brief

```bash
sp init my-app --template python-fasthtml
cd my-app
sp vibe "A todo app with auth"
```

This drafts specs, then builds them into working code and tests. Add `--pause-for-review`
to edit specs before building.

### Or work step by step

```bash
sp compose "A todo app with auth"   # draft architecture + specs
sp conduct specs/                   # build all specs via agents
```

### Single spec workflow

```bash
sp create calculator "A simple calculator with add and multiply"
sp compile calculator
sp test calculator
sp fix calculator   # auto-fix if tests fail
```

### Add specs to an existing project

```bash
sp respec src/mymodule.py            # extract a spec from existing code
sp conduct specs/mymodule.spec.md    # rebuild from spec
```

See the [Incremental Adoption Guide](https://symbolfarm.github.io/specsoloist/incremental-adoption/) for a full walkthrough.

## How It Works

```
Brief or spec (Markdown)
        |
        v
  SpecComposer         -> drafts architecture + specs
        |
  [Optional review]    -> edit specs before building
        |
        v
  SpecConductor        -> resolves dependencies, spawns soloists in parallel
        |
        v
  Working code + tests -> ready to run
```

Specs define **what** the code should do — public API, behavior, edge cases, examples.
The **Arrangement** file defines **how** — output paths, language, tools. AI agents handle
the implementation. If tests fail, `sp fix` analyzes the failure and patches the code.

## Key Commands

| Command | Description |
| :--- | :--- |
| `sp vibe [brief]` | Compose + build in one command |
| `sp conduct [dir]` | Build specs via agent orchestration |
| `sp compose [brief]` | Draft architecture & specs |
| `sp respec <file>` | Reverse-engineer code into a spec |
| `sp fix <name>` | Auto-fix failing tests |
| `sp diff` | Detect spec-vs-code drift |
| `sp doctor` | Check environment health |

See the full [CLI Reference](https://symbolfarm.github.io/specsoloist/reference/cli/) for
all commands and flags.

## Configuration

SpecSoloist works with **Google Gemini**, **Anthropic Claude**, or any model via **Pydantic AI**
(OpenAI, OpenRouter, Ollama, etc.). Set one environment variable:

```bash
export GEMINI_API_KEY="..."      # Google Gemini (default)
export ANTHROPIC_API_KEY="..."   # Anthropic Claude
```

For model selection, arrangement files, and advanced configuration, see the
[Getting Started](https://symbolfarm.github.io/specsoloist/getting_started/) and
[Arrangement Guide](https://symbolfarm.github.io/specsoloist/guide/arrangement/).

## Documentation

- [Getting Started](https://symbolfarm.github.io/specsoloist/getting_started/) — installation, first project, `sp doctor`
- [The Workflow](https://symbolfarm.github.io/specsoloist/guide/workflow/) — compose, conduct, fix loop
- [Arrangement Guide](https://symbolfarm.github.io/specsoloist/guide/arrangement/) — build configuration
- [Agents Guide](https://symbolfarm.github.io/specsoloist/guide/agents/) — Claude & Gemini subagents
- [CLI Reference](https://symbolfarm.github.io/specsoloist/reference/cli/) — all commands and flags
- [Spec Types](https://symbolfarm.github.io/specsoloist/reference/spec-types/) — bundle, function, type, reference, workflow
- [Examples](https://symbolfarm.github.io/specsoloist/examples/fasthtml_app/) — FastHTML, Next.js, incremental adoption

## Contributing

```bash
git clone https://github.com/symbolfarm/specsoloist.git
cd specsoloist && uv sync
uv run python -m pytest tests/    # run tests
uv run ruff check src/             # lint
```

See [CONTRIBUTING.md](https://github.com/symbolfarm/specsoloist/blob/main/CONTRIBUTING.md)
for guidelines, release process, and the Score (SpecSoloist's own specs).

## License

[MIT](https://github.com/symbolfarm/specsoloist/blob/main/LICENSE)
