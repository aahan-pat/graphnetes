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

echo ""
echo "==> Choose install type:"
echo "    1) Local  — installed into .venv, use 'uv run graphnetes' or activate the venv"
echo "    2) Global — installed system-wide, use 'graphnetes' from anywhere"
echo ""
read -rp "Enter choice [1/2]: " choice

case "$choice" in
    1)
        echo "==> Installing into .venv"
        uv sync
        echo ""
        echo "==> Done. Run the CLI with:"
        echo "    uv run graphnetes build"
        echo "    uv run graphnetes build --context <name> --namespace <name>"
        echo "    uv run graphnetes inspect <Kind/namespace/name>"
        echo "    uv run graphnetes path <source> <target>"
        echo ""
        echo "    Or activate the venv first:"
        echo "    source .venv/bin/activate"
        ;;
    2)
        echo "==> Installing globally via uv tool"
        uv tool install .
        uv tool update-shell
        echo ""
        echo "==> Done. Run the CLI with:"
        echo "    graphnetes build"
        echo "    graphnetes build --context <name> --namespace <name>"
        echo "    graphnetes inspect <Kind/namespace/name>"
        echo "    graphnetes path <source> <target>"
        echo ""
        echo "    If 'graphnetes' is not found, restart your terminal."
        ;;
    *)
        echo "Error: invalid choice '$choice' — expected 1 or 2"
        exit 1
        ;;
esac
