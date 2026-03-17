# Getting Started

## Installation

```bash
pip install specsoloist
```

Or for development:

```bash
git clone https://github.com/symbolfarm/specsoloist.git
cd specsoloist
uv sync
```

## Quick Start

### 1. Set your API key

SpecSoloist works with Google Gemini, Anthropic Claude, or any model via Pydantic AI.

```bash
# Google Gemini (default)
export GEMINI_API_KEY="your-key-here"

# Or Anthropic Claude
export ANTHROPIC_API_KEY="your-key-here"
```

### 2. Create a new spec

```bash
sp create calculator "A simple calculator with add and multiply"
```

### 3. Compile to code

```bash
sp compile calculator
```

### 4. Run tests

```bash
sp test calculator
```

### 5. Auto-fix if needed

```bash
sp fix calculator
```

---

## Vibe-Coding: Build from a brief

For a new project, skip writing specs by hand and let SpecSoloist draft them:

```bash
sp vibe "A todo app with user auth and REST API"
```

This runs `sp compose` (drafts architecture and specs) followed by `sp conduct` (builds all specs). Add `--pause-for-review` to inspect and edit the generated specs before building.

For an existing project layout, use a template:

```bash
sp init myapp --template python-fasthtml
cd myapp
sp vibe "A task manager with tags and due dates" --template python-fasthtml
```

---

## Check your environment

```bash
sp doctor
```

Reports which API keys, CLIs, and tools are available. Pass `--arrangement arrangement.yaml` to also verify all declared environment variables are set.
