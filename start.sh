#!/bin/bash
chmod +x download_data.sh
./download_data.sh
gunicorn --bind 0.0.0.0:10000 app:app