#!/bin/bash

# Activate virtual environment (or create if not exist)
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies inside venv
pip3 install -r requirements.txt

chmod +x refresh_data.sh
./refresh_data.sh

# Restart systemd service
echo "Restarting systemd service..."
sudo systemctl restart bahniq

echo "✅ Deployment complete."