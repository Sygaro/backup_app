#!/usr/bin/env bash
set -euo pipefail
# Bruk: ./backup.sh [--project NAVN] --source STIDIR [flagg...]
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$SCRIPT_DIR/venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "Fant ikke venv på $PY"
  echo "Tips: cd $(basename "$SCRIPT_DIR") && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi
exec "$PY" "$SCRIPT_DIR/backup.py" "$@"