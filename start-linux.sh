#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
if [[ "${1:-}" == "--setup" ]]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install -r backend/requirements-desktop.txt 'pywebview[qt]'
  pnpm --dir frontend install --frozen-lockfile
  pnpm --dir frontend build
fi
export PYWEBVIEW_GUI=qt
exec .venv/bin/python desktop.py
