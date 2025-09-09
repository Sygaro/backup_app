#!/usr/bin/env bash
set -euo pipefail

# Bruk: ./backup.sh [-p PROSJEKT] [-s KILDE] [-d DEST] [-v VERSJON] [-t TAG] [--no-version] [--dropbox-path /sti]
# Eksempel (samme semantikk som README viser i dag):
#   ./backup.sh -s /home/reidar/garage -p garasjeport -v 1.06 -t Frontend_OK --dropbox-path "/backup/garasjeport"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv/bin/python"

if [[ ! -x "$VENV" ]]; then
  echo "Fant ikke venv på $VENV. Har du kjørt 'python -m venv venv && source venv/bin/activate && pip install -r requirements.txt'?"
  exit 1
fi

# Send alt videre til Python-CLI
exec "$VENV" "$SCRIPT_DIR/backup.py" "$@"
