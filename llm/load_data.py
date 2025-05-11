import duckdb
import pandas as pd
from pathlib import Path

# Load your Deutsche Bahn CSV file (replace with your actual filename)

data_folder = Path('data')
df = pd.read_parquet(data_folder/"recent_data.parquet")

# Connect to DuckDB and create table
con = duckdb.connect(data_folder/"db_data.db")
con.execute("DROP TABLE IF EXISTS db_data")
con.execute("CREATE TABLE db_data AS SELECT * FROM df")
con.close()