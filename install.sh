#!/usr/bin/env bash
set -e

echo "==> Checking Python version"
python3 --version | grep -E "3\.(1[2-9]|[2-9][0-9])\." || {
    echo "Error: Python 3.12+ required"
    exit 1
}

echo "==> Installing uv (if not present)"
if ! command -v uv &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "==> Installing dependencies"
uv sync

echo "==> Done. Run the CLI with:"
echo "    uv run graphnetes build"
echo "    uv run graphnetes build --context <name> --namespace <name>"
echo "    uv run graphnetes inspect <Kind/namespace/name>"
echo "    uv run graphnetes path <source> <target>"
