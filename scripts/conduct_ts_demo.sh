#!/bin/bash
set -e

# Detect the best uv to use
if command -v uv &> /dev/null; then
    UV_BIN="uv"
elif [ -f "./.uv/uv" ]; then
    UV_BIN="./.uv/uv"
    # Sandbox-specific: use local cache
    export UV_CACHE_DIR="${UV_CACHE_DIR:-.uv-cache}"
else
    echo "Error: 'uv' not found on PATH and ./.uv/uv does not exist."
    echo "Please install uv: https://github.com/astral-sh/uv"
    exit 1
fi

# Detect npm
if ! command -v npm &> /dev/null; then
    echo "Error: 'npm' not found on PATH."
    echo "Please install Node.js and npm: https://nodejs.org/"
    exit 1
fi

# Sandbox-friendly npm config if ~/.npm is not writable
# We check if $HOME exists and is writable, and if $HOME/.npm exists and is writable
if [ ! -w "$HOME" ] || ( [ -d "$HOME/.npm" ] && [ ! -w "$HOME/.npm" ] ); then
    export npm_config_cache="$(pwd)/.npm-cache"
fi

export PYTHONPATH="src"

echo "Using uv: $($UV_BIN --version)"
echo "Starting TypeScript demo build..."

$UV_BIN run python -m specsoloist.cli conduct examples/ts_demo/src/ \
    --arrangement arrangements/arrangement.typescript.yaml \
    "$@"
