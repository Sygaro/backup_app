# backup_app

Fleksibel backup av valgfri katalog, med valgfritt prosjektnavn, valgfri versjon, **.backupignore/--exclude**, **retention** og valgfri **Dropbox-opplasting**.

## Installasjon
```bash
sudo apt update && sudo apt install -y git python3-venv
git clone https://github.com/Sygaro/backup_app
cd backup_app
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```
Dropbox (valgfritt):

Opprett token: https://www.dropbox.com/developers/apps

Kopiér miljømal og sett token:

```bash
cp env_mal .env
nano .env   # sett DROPBOX_TOKEN=...
```
Bruk

Standard ZIP-backup uten versjon (dato i navn):
```bash
