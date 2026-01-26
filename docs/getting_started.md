# Getting Started

## Installation

```bash
pip install specular-ai
```

Or for development:

```bash
git clone https://github.com/symbolfarm/specular.git
cd specular
uv sync
```

## Quick Start

### 1. Set your API key
Specular defaults to Google Gemini.

```bash
export GEMINI_API_KEY="your-key-here"
```

### 2. Create a new spec
```bash
specular create calculator "A simple calculator with add and multiply"
```

### 3. Compile to code
```bash
specular compile calculator
```

### 4. Run tests
```bash
specular test calculator
```

### 5. Auto-fix if needed
```bash
specular fix calculator
```
