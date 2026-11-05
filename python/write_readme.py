"""
Write README.md from results/ and the marts, so every number in it comes from the analysis.
Run last:  python python/write_readme.py
"""
import json
from pathlib import Path
from warehouse import query

ROOT = Path(__file__).resolve().parents[1]
G = json.loads((ROOT / "results" / "geo_test_results.json").read_text())
S = json.loads((ROOT / "results" / "budget_scenarios_meta.json").read_text())
M, o = G["money"], G["orders"]
import pandas as pd
sc = pd.read_csv(ROOT / "results" / "budget_scenarios.csv")
cut50 = sc[(sc.scenario == "Cut 50%") & (sc.case == "central")].iloc[0]
tot = query("""select count(*) filter (where order_status <> 'cancelled') orders, sum(net_revenue_eur) rev,
                      count(*) filter (where is_tracked_in_ga4) * 1.0 / count(*) ga4 from marts.fct_orders""").iloc[0]
cost = query("select sum(marketing_cost_eur) c from marts.mart_business_weekly").c.iloc[0]
claims = query("select sum(platform_conversions) c from marts.fct_marketing_spend_daily").c.iloc[0]
att = query("select model, channel, share_of_orders s from marts.mart_attribution").pivot(index="channel", columns="model", values="s")
proas = query("""select channel, sum(platform_conversion_value_eur) / sum(spend_eur) r from marts.fct_marketing_spend_daily
                 where channel in ('Google Brand Search', 'Meta') group by 1""").set_index("channel").r
mer = query("""select case when week >= '2025-05-05' and week < '2025-06-02' then 'test' else 'other' end p,
                      sum(revenue_eur) / sum(marketing_cost_eur) m
               from marts.mart_business_weekly where week >= '2025-03-10' and week < '2025-06-02' group by 1""").set_index("p").m
gains = S["cut50_gain_6m_by_exponent"]

md = f"""# Velora — Marketing Measurement & Growth Intelligence

> Where should the next euro of marketing spend go? A measurement project for a D2C skincare brand selling across
> Germany's 16 states: unified spend and channel KPIs, four attribution models, a pre-registered geo test on Meta,
> contribution-margin economics and budget scenarios.
> **Hands-on portfolio project on synthetic data** ([assumptions](docs/data_assumptions.md)), not production experience.

**Dashboard:** [Looker Studio](LOOKER_LINK) · **Decision memo:** [geo test readout](docs/geo_test_readout.md)

## The measurement problem
Velora (fictional, January–June 2025) took {tot.orders:,.0f} orders worth €{tot.rev / 1e6:.2f}M on €{cost / 1e6:.2f}M of marketing.
Three sources disagree by design: ad platforms claimed **{claims:,.0f} conversions** (more than the real orders), GA4 saw only
**{tot.ga4:.0%}** of orders because of consent, and only the order system knew what was actually sold.

## Recommendation
**Cut Meta spend by about half, starting with retargeting, then re-test. Run a brand-search holdout next. Judge budgets on
incrementality and contribution margin, with MER as the weekly scoreboard, not on platform ROAS.**

## Key findings

**1. Meta drives real orders, but far fewer than it claims.** Pausing Meta in 8 of 16 states cut orders by
{-o['pct'] * 100:.1f}% (95% CI {-o['ci_high'] * 100:.1f}% to {-o['ci_low'] * 100:.1f}%). Meta causes about {M['incremental_share_of_orders']:.0%} of orders while
claiming about {M['platform_claimed_share_of_orders']:.0%}. Incremental ROAS is **{M['iroas'][0]:.2f}×** (range {M['iroas'][1]:.2f}–{M['iroas'][2]:.2f}) against
**{M['platform_roas']:.2f}×** reported by Meta, and below the **{M['breakeven_roas_on_cm']:.2f}×** break-even on contribution margin. [Full readout](docs/geo_test_readout.md)

![ROAS comparison](docs/images/geo_roas_comparison.png)

**2. Blended CAC hides the problem.** Blended CAC is €{M['blended_cac_eur']:.0f}, which customers repay on their first order. But
each new customer Meta actually brings costs **€{M['incremental_cac_eur'][0]:.0f}**, more than the €{M['ltv_6m_cm_eur']:.0f} contribution a customer generates in six months.

![LTV vs CAC](docs/images/ltv_vs_cac.png)

**3. Halving Meta spend improves profit.** On the central estimate, cutting Meta by 50% improves contribution after
marketing by about **€{cut50.vs_current_6_months_eur / 1000:.0f}k a month** (€{min(gains.values()) / 1000:.0f}k–€{max(gains.values()) / 1000:.0f}k across response-curve assumptions); Meta
stops paying back above roughly €{S['breakeven_monthly_spend_eur'] / 1000:.0f}k a month. The uncertainty is wide, hence cut, then re-test.
During the test itself, weekly MER rose to {mer['test']:.2f} from {mer['other']:.2f}: revenue fell less than spend.

![Budget scenarios](docs/images/budget_scenarios.png)

**4. The attribution model decides who looks like the winner.** Meta receives {att.loc['Meta', 'first_click']:.0%} of credit under
first-click but {att.loc['Meta', 'last_click']:.0%} under last-click; brand search jumps from {att.loc['Google Brand Search', 'first_click']:.0%} to
{att.loc['Google Brand Search', 'last_click']:.0%}. Google reports a **{proas['Google Brand Search']:.1f}×** ROAS for brand search, mostly from customers already
searching for Velora. Attribution shows channel roles; only tests show cause.

![Attribution by model](docs/images/attribution_by_model.png)

## Method
| Stage | What was done |
|---|---|
| Design first | [Metric spec](docs/metric_spec.md) with a source per metric, [attribution approach](docs/attribution_approach.md), [pre-registered geo test](docs/geo_test_design.md) with an MDE from placebo tests, [privacy note](docs/privacy_and_measurement.md) (GDPR, Consent Mode, DMA, SKAN) |
| Data model | dbt on DuckDB: 23 models, one channel-mapping macro, 65 tests including spend reconciliation and attribution credit checks |
| Geo test | Difference-in-differences with state and day fixed effects, clustered errors; parallel trends, ratio, leave-one-pair-out and placebo checks |
| Economics | Contribution margin per order; incremental ROAS, CAC and contribution; budget scenarios on a diminishing-returns curve with sensitivity |
| Communication | Memo and README generated from results; Looker Studio dashboard |

## Stack
DuckDB · dbt (dbt-duckdb, dbt_utils) · SQL · Python (pandas, statsmodels, matplotlib) · Looker Studio · Git/GitHub

## Reproduce
```bash
pip install -r requirements.txt
python scripts/generate_data.py && python scripts/load_to_duckdb.py
cd dbt && dbt deps && dbt build && cd ..        # 65 tests
python python/geo_test_analysis.py && python python/write_geo_readout.py
python python/budget_scenarios.py && python python/make_charts.py
python python/export_for_looker.py && python python/write_readme.py
```

## Limitations
- Synthetic data with stylised behaviour: it demonstrates method, not benchmarks.
- One four-week test measures short-term effects; brand-building effects of Meta are not captured.
- Budget scenarios extrapolate from one tested spend level using an assumed curve shape; re-testing is essential.
- Only Meta was tested; other channels' incremental value is unknown.

## Progress
- [x] Day 12 — business questions, metric spec, attribution approach, geo test design, privacy note, synthetic data, DuckDB load
- [x] Day 13 — dbt models: unified spend, channel KPIs, attribution models, cohorts
- [x] Day 14 — geo test analysis (difference-in-differences), ROAS vs iROAS, contribution economics
- [x] Day 15 — budget scenarios, Looker Studio dashboard, README findings, v1.0
"""
(ROOT / "README.md").write_text(md)
print("Wrote README.md")
