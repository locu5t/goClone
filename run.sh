#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

python3 scripts/bootstrap_venv.py
"$ROOT/.venv/bin/python" scripts/build_goclone.py
"$ROOT/.venv/bin/python" -m ui.app
