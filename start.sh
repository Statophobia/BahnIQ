#!/bin/bash
chmod +x download_data.sh
./download_data.sh

cd ~/app || exit

# Activate virtual environment (or create if not exist)
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies inside venv
pip3 install -r requirements.txt

gunicorn --bind 0.0.0.0:10000 app:app