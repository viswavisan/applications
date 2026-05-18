# Flask Application Service Configuration

This guide outlines how to configure the Flask application as a system service on Linux using `systemd`.

## Installation

1. Copy the `flaskapp.service` file to the systemd directory:
   ```bash
   sudo cp flaskapp.service /etc/systemd/system/flaskapp.service
   ```
 or sudo nano /etc/systemd/system/flaskapp.service

## Service Management

### Initial Setup
Run the following commands to reload the daemon, enable the service on boot, and start it:
```bash
sudo systemctl daemon-reload
sudo systemctl enable flaskapp
sudo systemctl start flaskapp
```

### Check Status
journalctl -u flaskapp.service -f


### Redeployment
To apply updates, navigate to the project root, refresh the virtual environment, and restart the daemon:
```bash
cd /mnt/c/Users/viswa/PycharmProjects/applications
#git pull origin main #if project location is different and need auto code update
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart flaskapp
```

### Stop service
```bash
sudo systemctl stop flaskapp
```
