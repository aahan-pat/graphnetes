#Requires -Version 5.1
$ErrorActionPreference = "Stop"

Write-Host "==> Checking Python version"
$ver = python --version 2>&1
if ($ver -notmatch "Python 3\.(1[2-9]|[2-9]\d)\.") {
    Write-Error "Error: Python 3.12+ required (found: $ver)"
    exit 1
}

Write-Host "==> Installing uv (if not present)"
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
}

Write-Host ""
Write-Host "==> Choose install type:"
Write-Host "    1) Local  — installed into .venv, use 'uv run graphnetes' or activate the venv"
Write-Host "    2) Global — installed system-wide, use 'graphnetes' from anywhere"
Write-Host ""
$choice = Read-Host "Enter choice [1/2]"

switch ($choice) {
    "1" {
        Write-Host "==> Installing into .venv"
        uv sync
        Write-Host ""
        Write-Host "==> Done. Run the CLI with:"
        Write-Host "    uv run graphnetes build"
        Write-Host "    uv run graphnetes build --context <name> --namespace <name>"
        Write-Host "    uv run graphnetes inspect <Kind/namespace/name>"
        Write-Host "    uv run graphnetes path <source> <target>"
        Write-Host ""
        Write-Host "    Or activate the venv first:"
        Write-Host "    .venv\Scripts\Activate.ps1"
    }
    "2" {
        Write-Host "==> Installing globally via uv tool"
        uv tool install .
        uv tool update-shell
        Write-Host ""
        Write-Host "==> Done. Run the CLI with:"
        Write-Host "    graphnetes build"
        Write-Host "    graphnetes build --context <name> --namespace <name>"
        Write-Host "    graphnetes inspect <Kind/namespace/name>"
        Write-Host "    graphnetes path <source> <target>"
        Write-Host ""
        Write-Host "    If 'graphnetes' is not found, restart your terminal."
    }
    default {
        Write-Error "Error: invalid choice '$choice' — expected 1 or 2"
        exit 1
    }
}
