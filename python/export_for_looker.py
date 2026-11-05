"""
Export dashboard-ready CSV files for Looker Studio (File Upload connector): exports/looker/*.csv
Run from the repo root (after the analysis scripts):  python python/export_for_looker.py
"""
from pathlib import Path
import pandas as pd
from warehouse import query

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports" / "looker"; OUT.mkdir(parents=True, exist_ok=True)
tables = {
    "channel_weekly": "select * from marts.mart_channel_performance_weekly order by week, channel",
    "attribution": "select * from marts.mart_attribution order by model, channel",
    "business_weekly": "select * from marts.mart_business_weekly order by week",
    "geo_test_daily": "select * from marts.mart_geo_test_daily where period <> 'outside' order by date, region",
    "cohorts": "select * from marts.mart_cohorts order by first_order_month, months_since",
}
for name, sql in tables.items():
    df = query(sql); df.to_csv(OUT / f"{name}.csv", index=False); print(f"exports/looker/{name}.csv  {len(df):,} rows")
pd.read_csv(ROOT / "results" / "budget_scenarios.csv").to_csv(OUT / "budget_scenarios.csv", index=False)
print("exports/looker/budget_scenarios.csv")
