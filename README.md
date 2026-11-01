# Velora — Marketing Measurement & Growth Intelligence

> Where should the next euro of marketing spend go? A measurement project for a D2C skincare brand: unified spend and
> channel KPIs, four attribution models, a pre-registered geo test on Meta, and contribution-margin economics.
> **Hands-on portfolio project on synthetic data** ([assumptions](docs/data_assumptions.md)), not production experience.

## The measurement problem
Three sources disagree by design: ad platforms claim more conversions than real orders, GA4 only sees consented visitors,
and only the order system knows what was actually sold. This project reconciles them and measures what marketing *causes*.

## Design before analysis
- [Business questions](docs/business_questions.md) · [Metric specification](docs/metric_spec.md)
- [Attribution approach](docs/attribution_approach.md): last-click, first-click, linear, position-based, and their limits
- [Geo test design](docs/geo_test_design.md): pre-registered Meta holdout in 8 of 16 states (MDE ≈ 8%)
- [Privacy and measurement](docs/privacy_and_measurement.md): GDPR consent, Consent Mode, DMA, SKAN
- [Data model](docs/data_model.md)

## Stack
DuckDB · dbt (dbt-duckdb) · SQL · Python (pandas, statsmodels) · Looker Studio · Git/GitHub

## Reproduce
```bash
pip install -r requirements.txt
python scripts/generate_data.py      # synthetic Parquet files in data/raw/
python scripts/load_to_duckdb.py     # loads warehouse/velora.duckdb and prints a measurement check
```

## Progress
- [x] Day 12 — business questions, metric spec, attribution approach, geo test design, privacy note, synthetic data, DuckDB load
- [ ] Day 13 — dbt models: unified spend, channel KPIs, attribution models, cohorts
- [ ] Day 14 — geo test analysis (difference-in-differences), ROAS vs iROAS, contribution economics
- [ ] Day 15 — Looker Studio dashboard, budget recommendation, README findings, v1.0
