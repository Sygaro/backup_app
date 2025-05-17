#!/bin/bash
# backup.sh – kjører backup fra venv i backup_app

# Aktiver virtuelt miljø
source /home/reidar/backup_app/venv/bin/activate

# Kjør Python-backup med evt. argumenter
python3 /home/reidar/backup_app/backup_zip.py "$@"

# (valgfritt) Deaktiver etterpå
deactivate
