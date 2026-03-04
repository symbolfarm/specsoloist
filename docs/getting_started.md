# Getting Started

## Installation

```bash
pip install specsoloist-ai
```

Or for development:

```bash
git clone https://github.com/symbolfarm/specsoloist.git
cd specsoloist
uv sync
```

## Quick Start

### 1. Set your API key
SpecSoloist defaults to Google Gemini.

```bash
export GEMINI_API_KEY="your-key-here"
```

### 2. Create a new spec
```bash
specsoloist create calculator "A simple calculator with add and multiply"
```

### 3. Compile to code
```bash
specsoloist compile calculator
```

### 4. Run tests
```bash
specsoloist test calculator
```

### 5. Auto-fix if needed
```bash
specsoloist fix calculator
```
