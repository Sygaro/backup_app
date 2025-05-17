# Fil: lag_backup_zip.py
# Formål: Zip-backup med robust feilhåndtering, notat i filnavn og opplasting til Dropbox hvis notat er angitt
import os
import zipfile
import fnmatch
import sys
from datetime import datetime
from dropbox_opplasting import last_opp_til_dropbox
from dotenv import load_dotenv

load_dotenv()

ROT = "/home/reidar"
backup_rot = "/home/reidar/Backup"
dato = datetime.now().strftime("%Y-%m-%d")
tid = datetime.now().strftime("%H%M%S")
backupmappe = os.path.join(backup_rot, dato)
os.makedirs(backupmappe, exist_ok=True)

ekskluder_mapper = ['venv', '__pycache__', '.git', 'backups', 'logs']
ekskluder_filmønstre = ['*.pyc', '*.log', '*.zip', '._*', '.DS_Store']

def skal_utelates(filsti):
    for eks_mapp in ekskluder_mapper:
        if eks_mapp in filsti:
            return True
    filnavn = os.path.basename(filsti)
    for mønster in ekskluder_filmønstre:
        if fnmatch.fnmatch(filnavn, mønster):
            return True
    return False

def lag_backup_for_mappe(mappe_navn, notat=""):
    prosjektmappe = os.path.join(ROT, mappe_navn)
    versjon = mappe_navn.replace("garasjeport_v", "")
    safe_note = f"_{notat}" if notat else ""
    filnavn = f"garasjeprosjekt_v{versjon}_{dato}_{tid}{safe_note}.zip"
    stifull = os.path.join(backupmappe, filnavn)

    antall_filer = 0
    feilede_filer = []
    loggfil = os.path.join(backupmappe, f"feil_v{versjon}_{dato}_{tid}{safe_note}.log")

    with zipfile.ZipFile(stifull, 'w', zipfile.ZIP_DEFLATED) as backupzip:
        for mappe, _, filer in os.walk(prosjektmappe):
            for fil in filer:
                fullsti = os.path.join(mappe, fil)
                relsti = os.path.relpath(fullsti, prosjektmappe)
                if not skal_utelates(fullsti):
                    try:
                        if os.path.isfile(fullsti):
                            backupzip.write(fullsti, arcname=relsti)
                            antall_filer += 1
                    except Exception as e:
                        filinfo = {
                            "sti": relsti,
                            "feil": str(e),
                            "tid": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "størrelse": os.path.getsize(fullsti) if os.path.exists(fullsti) else 0
                        }
                        feilede_filer.append(filinfo)

    filstørrelse = os.path.getsize(stifull)
    filstørrelse_kb = filstørrelse / 1024

    if filstørrelse < 100:
        print(f"⚠️ Advarsel: Backup-fil for {versjon} er kun {filstørrelse} byte – kan være tom!")

    print(f"✅ Backup for v{versjon} fullført:")
    print(f"   📄 Fil: {stifull}")
    print(f"   📦 Størrelse: {filstørrelse_kb:.1f} KB")
    print(f"   📂 Antall filer i backup: {antall_filer}")

    if feilede_filer:
        print(f"   ⚠️ {len(feilede_filer)} filer ble hoppet over pga. feil:")
        with open(loggfil, "w", encoding="utf-8") as log:
            for feil in feilede_filer:
                log.write(f"{feil['tid']} – {feil['sti']} ({feil['størrelse']} B) → {feil['feil']}\n")
                print(f"      - {feil['sti']} → {feil['feil']}")
        print(f"   📝 Feillogg: {loggfil}")

    if notat:
        print("☁️ Laster opp til Dropbox...")
        last_opp_til_dropbox(stifull)

    print()

# Bruk: python3 lag_backup_zip.py <versjon> [notat]
if len(sys.argv) >= 2:
    versjon = sys.argv[1]
    notat = sys.argv[2] if len(sys.argv) >= 3 else ""
    mappe_navn = f"garasjeport_v{versjon}"
    if os.path.isdir(os.path.join(ROT, mappe_navn)):
        lag_backup_for_mappe(mappe_navn, notat)
    else:
        print(f"❌ Mappe {mappe_navn} finnes ikke i {ROT}")
else:
    print("📦 Ingen versjon spesifisert – kjører backup for ALLE versjoner:")
    for navn in os.listdir(ROT):
        if navn.startswith("garasjeport_v") and os.path.isdir(os.path.join(ROT, navn)):
            lag_backup_for_mappe(navn)
