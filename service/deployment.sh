cd /mnt/Linux/applications
git pull origin main
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart flaskapp