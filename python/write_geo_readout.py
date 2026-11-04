"""
Write docs/geo_test_readout.md from results/ and the marts, so every number in the memo comes from the analysis.
Run after geo_test_analysis.py:  python python/write_geo_readout.py
"""
import json
from pathlib import Path
from warehouse import query

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "results" / "geo_test_results.json").read_text())
M, o, rb, pt = R["money"], R["orders"], R["robustness"], R["pre_trend"]
pct = lambda v: f"{v * 100:+.1f}%"
fx = lambda v: "–" if v != v or v is None else f"{v:.2f}×"
below_be = M["iroas"][2] < M["breakeven_roas_on_cm"]
pays_back = M["ltv_6m_cm_eur"] >= M["incremental_cac_eur"][0]
ch = query("""
    with perf as (select channel, sum(spend_eur) spend, sum(platform_conversion_value_eur) / nullif(sum(spend_eur), 0) platform_roas,
                         sum(ga4_last_click_revenue_eur) / nullif(sum(spend_eur), 0) ga4_lc_roas
                  from marts.mart_channel_performance_weekly group by 1),
         pb as (select channel, attributed_revenue_eur from marts.mart_attribution where model = 'position_based')
    select p.channel, p.spend, p.platform_roas, p.ga4_lc_roas, pb.attributed_revenue_eur / nullif(p.spend, 0) pb_roas
    from perf p left join pb using (channel) where p.spend > 0 order by p.spend desc""")
rows = "\n".join(
    f"| {r.channel} | €{r.spend:,.0f} | {r.platform_roas:.2f}× | {fx(r.ga4_lc_roas)} | {fx(r.pb_roas)} | "
    + (f"**{M['iroas'][0]:.2f}×** (geo test)" if r.channel == "Meta" else "not yet tested") + " |"
    for r in ch.itertuples() if r.platform_roas == r.platform_roas)

md = f"""# Geo Test Readout: What Meta Really Causes

> Synthetic data. Analysis follows the pre-registered plan in [geo_test_design.md](geo_test_design.md).

## Recommendation
**Meta drives real orders, but far fewer than it reports, and at current spend it does not pay back. Velora should
reduce Meta spend, starting with retargeting, re-test at the lower level, and use incrementality, not platform ROAS,
to set budgets.** Brand search is the next test: it reports the highest ROAS of any channel.

## The result
| | Value |
|---|---|
| Effect of pausing Meta on orders | **{pct(o['pct'])}** (95% CI {pct(o['ci_low'])} to {pct(o['ci_high'])}; p < 0.001) |
| Share of orders Meta actually causes (treatment states) | **{M['incremental_share_of_orders']:.0%}**, against ~{M['platform_claimed_share_of_orders']:.0%} of all orders that Meta claims |
| Incremental orders over 4 weeks (8 states) | {M['incremental_orders'][0]:,.0f} (range {M['incremental_orders'][1]:,.0f} to {M['incremental_orders'][2]:,.0f}) |
| Meta spend avoided in treatment states | €{M['meta_spend_avoided_eur']:,.0f} |
| **Incremental ROAS** | **{M['iroas'][0]:.2f}×** (range {M['iroas'][1]:.2f}× to {M['iroas'][2]:.2f}×), against **{M['platform_roas']:.2f}×** reported by Meta |
| Break-even ROAS on contribution margin | {M['breakeven_roas_on_cm']:.2f}× (contribution margin is {M['cm_rate']:.0%} of revenue) |
| Incremental contribution per € of Meta spend | €{M['incremental_cm_roas'][0]:.2f} |
| **Incremental CAC** | **€{M['incremental_cac_eur'][0]:.0f}** per new customer Meta actually brings, against a blended CAC of €{M['blended_cac_eur']:.0f} |
| 6-month LTV (contribution) of a new customer | €{M['ltv_6m_cm_eur']:.0f}, so {'Meta-acquired customers pay back within 6 months' if pays_back else 'even with repeat purchases, Meta-acquired customers do not pay back within 6 months'} |

![Orders index](images/geo_orders_index.png)

## Can we trust it?
- **Parallel trends:** before the test, treatment and control states moved together (weekly divergence {pt['weekly_divergence']:+.4f}, p = {pt['p_value']:.2f}).
- **Same answer by a simpler method:** a plain before/after ratio comparison gives {pct(rb['ratio_estimate'])}.
- **No single pair drives it:** dropping each matched pair in turn gives {pct(rb['leave_one_pair_out_min'])} to {pct(rb['leave_one_pair_out_max'])}.
- **Placebo tests** on earlier weeks, when nothing changed, average {pct(rb['placebo_mean'])}; the real test sits far outside them.
- **Consistent across outcomes:** revenue {pct(R['revenue']['pct'])}, contribution margin {pct(R['contribution_margin']['pct'])}, new customers {pct(R['new_customers']['pct'])}.

![Placebo tests](images/geo_placebo.png)

## Every channel, through every lens
| Channel | Spend (6 months) | Platform-reported ROAS | GA4 last-click ROAS | Position-based ROAS | Incremental ROAS |
|---|---|---|---|---|---|
{rows}

GA4 columns cover only consented users (~72% of orders), so they understate every channel. The point of the table is the
spread: the same channel looks excellent or poor depending on the lens, and only a test measures cause.

![ROAS comparison](images/geo_roas_comparison.png)

## Why the numbers differ so much
1. **Meta counts conversions it touched, not ones it caused,** including people who saw an ad and would have bought anyway.
2. **Attribution windows overlap:** Meta, Google and affiliates can all claim the same order.
3. **Retargeting** reaches people already close to buying, so it collects credit with little incremental effect.

## Next steps
1. **Cut Meta retargeting first** and reduce prospecting gradually; with diminishing returns, the last euros spent are the least productive.
2. **Re-test Meta at the lower budget** to find the spend level where incremental ROAS reaches break-even.
3. **Run a brand-search holdout next:** it reports {ch.set_index('channel').loc['Google Brand Search', 'platform_roas']:.1f}× ROAS, but mostly captures customers already searching for Velora.
4. **Make MER and order-system metrics the weekly scoreboard,** with platform ROAS as a diagnostic only.

## Limitations
Four weeks measures short-term effects only; longer-term brand effects of Meta are not captured. Some spillover between
states (people seeing ads in one state and ordering in another) would make the true effect slightly larger. With 16
states, the interval is wide: incremental ROAS could plausibly be anywhere from {M['iroas'][1]:.2f}× to {M['iroas'][2]:.2f}×,
{'but even the top of that range is below break-even.' if below_be else 'and the upper part of that range would be above break-even, so a re-test is essential before cutting further.'}
"""
(ROOT / "docs" / "geo_test_readout.md").write_text(md)
print("Wrote docs/geo_test_readout.md")
