"""
Load data/raw/*.parquet into a local DuckDB warehouse (warehouse/velora.duckdb), schema RAW,
then print a quick measurement check.  Usage:  python scripts/load_to_duckdb.py
"""
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "warehouse" / "velora.duckdb"
DB.parent.mkdir(exist_ok=True)
con = duckdb.connect(str(DB))
con.execute("create schema if not exists raw")
for f in sorted((ROOT / "data" / "raw").glob("raw_*.parquet")):
    con.execute(f"create or replace table raw.{f.stem} as select *, now() as _loaded_at from read_parquet('{f.as_posix()}')")
    print(f"raw.{f.stem:26s} {con.execute(f'select count(*) from raw.{f.stem}').fetchone()[0]:>9,d} rows")

orders = con.execute("select count(*) from raw.raw_orders").fetchone()[0]
claims = con.execute("select sum(platform_conversions) from raw.raw_platform_geo_daily").fetchone()[0]
tracked = con.execute("select count(distinct transaction_id) from raw.raw_ga4_conversion_paths").fetchone()[0]
print(f"\nMeasurement check: {orders:,} real orders | ad platforms claim {claims:,} conversions | GA4 tracked {tracked / orders:.1%} of orders")
con.close()
print("Warehouse ready: warehouse/velora.duckdb")
