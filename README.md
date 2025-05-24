# backup_app
For backup av garasjeport prosjekt kode og filer med mulighet for flere versjoner og opplasting til Dropbox

## Installasjon
bash
```
sudo apt update && sudo apt install git -y
git clone https://github.com/Sygaro/backup_app
python -m venv backup_app/venv
cd backup_app
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..
cp backup_app/backup.sh .
```
Opprett token:
https://www.dropbox.com/developers/apps
```
cp backup_app/env_mal .env
nano backup_app/.env
```
### Start backup

Ingen parameter = alle versjoner
versjon + tag = opplasting til Dropbox

Ekesempel:

```
./backup.sh 1.06 Frontend_OK
```
