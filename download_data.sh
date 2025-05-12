#!/bin/bash
source venv/bin/activate

# Create a data directory
mkdir -p data

url="https://github.com/Statophobia/deutsche-bahn-data/raw/refs/heads/main/monthly_data_releases/recent_data.parquet"
output_file="data/recent_data.parquet"
    
echo "Downloading $url"
curl -L "$url" -o "$output_file"

echo "Download complete"

python3 llm/load_data.py

echo "Data loaded into DuckDB"
