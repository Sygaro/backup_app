# Fil: dropbox_opplasting.py
# Formål: Laster opp en fil til Dropbox ved hjelp av en token lagret i .env

import os
import dropbox
from dotenv import load_dotenv

# Last inn DROPBOX_TOKEN fra .env
load_dotenv()
TOKEN = os.getenv("DROPBOX_TOKEN")

if not TOKEN:
    raise ValueError("❌ DROPBOX_TOKEN mangler i .env-filen.")

def last_opp_til_dropbox(filsti, dropbox_sti=None):
    """Laster opp filen til Dropbox"""
    if not os.path.isfile(filsti):
        raise FileNotFoundError(f"Filen finnes ikke: {filsti}")
    
    dbx = dropbox.Dropbox(TOKEN)
    filnavn = os.path.basename(filsti)
    dropbox_mål = dropbox_sti if dropbox_sti else f"/{filnavn}"

    with open(filsti, "rb") as f:
        try:
            dbx.files_upload(f.read(), dropbox_mål, mode=dropbox.files.WriteMode.overwrite)
            print(f"☁️ Opplastet til Dropbox: {dropbox_mål}")
        except Exception as e:
            print(f"❌ Feil under opplasting til Dropbox: {e}")
