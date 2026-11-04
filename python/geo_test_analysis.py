"""
Meta geo test: analysis exactly as pre-registered in docs/geo_test_design.md.

1. Pre-period check: did treatment and control states move in parallel before the test?
2. Main estimate: difference-in-differences on log orders, state and day fixed effects, errors clustered by state
3. Same model for revenue, contribution margin and new customers
4. Robustness: simple ratio estimate, leave-one-pair-out, placebo tests on earlier weeks
5. Translation: incremental orders, iROAS, incremental CM ROAS, incremental CAC, compared with Meta's own ROAS

Outputs: results/geo_test_results.json, docs/images/geo_*.png
Run from the repo root:  python python/geo_test_analysis.py
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from warehouse import query

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "images"; IMG.mkdir(parents=True, exist_ok=True)
(ROOT / "results").mkdir(exist_ok=True)
NAVY, YELLOW, GREY, RED, GREEN = "#16213B", "#F2B705", "#9AA4B5", "#B3261E", "#1E7A4C"
TEST_START, TEST_END, PRE_START = "2025-05-05", "2025-06-01", "2025-03-10"
TEST_DAYS = 28

geo = query("select * from marts.mart_geo_test_daily")
geo["date"] = pd.to_datetime(geo["date"])
new = query("""select order_date as date, region, count(*) as new_customers
               from marts.fct_orders where is_new_customer group by 1, 2""")
new["date"] = pd.to_datetime(new["date"])
geo = geo.merge(new, on=["date", "region"], how="left").fillna({"new_customers": 0})
geo["treated"] = (geo.geo_test_group == "treatment").astype(int)
geo["post"] = (geo.period == "test").astype(int)
geo["treat_post"] = geo.treated * geo.post
win = geo[geo.period.isin(["pre", "test"])].copy()
R = {}


def did(df, outcome, log=True):
    d = df.copy()
    d["y"] = np.log(d[outcome].clip(lower=1)) if log else d[outcome]
    m = smf.ols("y ~ treat_post + C(region) + C(date)", d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.region)[0]})
    b, se = m.params["treat_post"], m.bse["treat_post"]
    return {"coef": b, "se": se, "pct": np.exp(b) - 1, "ci_low": np.exp(b - 1.96 * se) - 1,
            "ci_high": np.exp(b + 1.96 * se) - 1, "p_value": m.pvalues["treat_post"]}


# 1. Pre-period parallel trends: treatment x week interaction in the pre-period only
pre = win[win.period == "pre"].copy()
pre["week"] = ((pre.date - pd.Timestamp(PRE_START)).dt.days // 7).astype(int)
pre["ln"] = np.log(pre.orders.clip(lower=1))
m_pre = smf.ols("ln ~ treated:week + C(region) + C(date)", pre).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(pre.region)[0]})
R["pre_trend"] = {"weekly_divergence": m_pre.params["treated:week"], "p_value": m_pre.pvalues["treated:week"],
                  "parallel": bool(m_pre.pvalues["treated:week"] > 0.05)}

# 2-3. Main estimates
R["orders"] = did(win, "orders")
R["revenue"] = did(win, "net_revenue_eur")
R["contribution_margin"] = did(win, "contribution_margin_eur")
R["new_customers"] = did(win, "new_customers")

# 4. Robustness
g = win.groupby(["geo_test_group", "period"]).orders.mean().unstack()
ratio = (g.loc["treatment", "test"] / g.loc["treatment", "pre"]) / (g.loc["control", "test"] / g.loc["control", "pre"]) - 1
loo = []
for pid in sorted(win.pair_id.unique()):
    loo.append(did(win[win.pair_id != pid], "orders")["pct"])
placebo = []
hist = geo[(geo.date >= "2025-01-13") & (geo.date < TEST_START)].copy()
for start in pd.date_range("2025-02-10", "2025-04-07", freq="7D"):
    w = hist[(hist.date >= start - pd.Timedelta(weeks=4)) & (hist.date < start + pd.Timedelta(weeks=4))].copy()
    w["treat_post"] = w.treated * (w.date >= start).astype(int)
    placebo.append({"start": str(start.date()), **{k: v for k, v in did(w, "orders").items() if k in ("pct", "ci_low", "ci_high")}})
R["robustness"] = {"ratio_estimate": ratio, "leave_one_pair_out_min": min(loo), "leave_one_pair_out_max": max(loo),
                   "placebo": placebo, "placebo_mean": float(np.mean([p["pct"] for p in placebo]))}

# 5. Translation into money
t_test = win[(win.treated == 1) & (win.post == 1)]
t_pre_recent = geo[(geo.treated == 1) & (geo.date >= "2025-04-07") & (geo.date < TEST_START)]
spend_avoided = t_pre_recent.groupby("date").meta_spend_eur.sum().mean() * TEST_DAYS   # typical daily Meta spend in treatment states x 28 days


def lost(metric, est):
    actual = t_test[metric].sum()
    counterfactual = actual / (1 + est["pct"])
    lo = actual / (1 + est["ci_low"]); hi = actual / (1 + est["ci_high"])
    return counterfactual - actual, hi - actual, lo - actual          # point, low, high (positive = caused by Meta)


inc_orders = lost("orders", R["orders"])
inc_rev = lost("net_revenue_eur", R["revenue"])
inc_cm = lost("contribution_margin_eur", R["contribution_margin"])
inc_new = lost("new_customers", R["new_customers"])
meta = query("""select sum(spend_eur) spend, sum(platform_conversion_value_eur) value, sum(platform_conversions) conv
                from marts.fct_marketing_spend_daily where channel = 'Meta'""").iloc[0]
cm_rate = query("select sum(contribution_margin_eur) / sum(net_revenue_eur) r from marts.fct_orders").r.iloc[0]
ltv6 = query("""select cumulative_cm_per_customer_eur v from marts.mart_cohorts
                where first_order_month = '2025-01-01' and months_since = 5""").v.iloc[0]
first_cm = query("""select cumulative_cm_per_customer_eur v from marts.mart_cohorts
                    where first_order_month = '2025-01-01' and months_since = 0""").v.iloc[0]
R["money"] = {
    "meta_spend_avoided_eur": spend_avoided,
    "incremental_orders": inc_orders, "incremental_share_of_orders": -R["orders"]["pct"] / (1 + R["orders"]["pct"]),
    "incremental_revenue_eur": inc_rev, "incremental_cm_eur": inc_cm, "incremental_new_customers": inc_new,
    "iroas": [x / spend_avoided for x in inc_rev],
    "incremental_cm_roas": [x / spend_avoided for x in inc_cm],
    "incremental_cac_eur": [spend_avoided / x if x > 0 else None for x in inc_new],
    "platform_roas": meta.value / meta.spend,
    "platform_claimed_share_of_orders": None,
    "cm_rate": cm_rate, "breakeven_roas_on_cm": 1 / cm_rate,
    "ltv_6m_cm_eur": ltv6, "first_order_cm_eur": first_cm,
    "blended_cac_eur": query("select sum(marketing_cost_eur) / sum(new_customers) v from marts.mart_business_weekly").v.iloc[0],
}
claims_pre = query(f"""select sum(platform_conversions) c from marts.fct_marketing_spend_daily
                       where channel = 'Meta' and spend_date >= '2025-04-07' and spend_date < '{TEST_START}'""").c.iloc[0]
orders_pre = query(f"""select count(*) n from marts.fct_orders where order_status <> 'cancelled'
                       and order_date >= '2025-04-07' and order_date < '{TEST_START}'""").n.iloc[0]
R["money"]["platform_claimed_share_of_orders"] = claims_pre / orders_pre
(ROOT / "results" / "geo_test_results.json").write_text(json.dumps(R, indent=2, default=float))

# ---------------------------------------------------------------- charts
daily = geo[(geo.date >= PRE_START) & (geo.date <= "2025-06-15")].groupby(["date", "geo_test_group"]).orders.sum().unstack()
idx = daily / daily[daily.index < TEST_START].mean() * 100
roll = idx.rolling(7, center=True).mean()
fig, ax = plt.subplots(figsize=(9, 3.8))
ax.axvspan(pd.Timestamp(TEST_START), pd.Timestamp(TEST_END), color=YELLOW, alpha=0.18, label="Meta paused in treatment states")
ax.plot(roll.index, roll.control, color=GREY, lw=2, label="Control states (Meta on)")
ax.plot(roll.index, roll.treatment, color=NAVY, lw=2, label="Treatment states (Meta off)")
ax.set_ylabel("Orders, index (pre-period = 100)"); ax.set_title("Orders fell in treatment states when Meta was paused (7-day average)")
ax.legend(fontsize=8, loc="lower left"); plt.tight_layout(); plt.savefig(IMG / "geo_orders_index.png", dpi=150); plt.close()

fig, ax = plt.subplots(figsize=(8, 3.6))
for i, p in enumerate(placebo):
    ax.errorbar(i, p["pct"] * 100, yerr=[[(p["pct"] - p["ci_low"]) * 100], [(p["ci_high"] - p["pct"]) * 100]], fmt="o", color=GREY, capsize=3)
o = R["orders"]; j = len(placebo) + 1
ax.errorbar(j, o["pct"] * 100, yerr=[[(o["pct"] - o["ci_low"]) * 100], [(o["ci_high"] - o["pct"]) * 100]], fmt="o", color=RED, capsize=4, lw=2)
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(list(range(len(placebo))) + [j], [p["start"][5:] for p in placebo] + ["Real test"], rotation=45, fontsize=8)
ax.set_ylabel("Effect on orders (%)"); ax.set_title("The real test stands far outside the placebo tests")
plt.tight_layout(); plt.savefig(IMG / "geo_placebo.png", dpi=150); plt.close()

M = R["money"]
labels = ["Meta-reported\nROAS", "Incremental ROAS\n(geo test)", "Break-even ROAS\non contribution margin"]
vals = [M["platform_roas"], M["iroas"][0], M["breakeven_roas_on_cm"]]
fig, ax = plt.subplots(figsize=(7.5, 3.8))
bars = ax.bar(labels, vals, color=[GREY, NAVY, YELLOW])
ax.errorbar(1, M["iroas"][0], yerr=[[M["iroas"][0] - M["iroas"][1]], [M["iroas"][2] - M["iroas"][0]]], fmt="none", color="black", capsize=6)
for i, (b, v) in enumerate(zip(bars, vals)):
    x = b.get_x() + b.get_width() / 2 + (0.22 if i == 1 else 0)
    ax.text(x, v + 0.08, f"{v:.2f}×", ha="left" if i == 1 else "center", fontsize=10)
ax.set_ylim(0, max(vals) * 1.25); ax.set_ylabel("Revenue per € of Meta spend")
ax.set_title("Meta claims 3.2×; the geo test measures far less")
plt.tight_layout(); plt.savefig(IMG / "geo_roas_comparison.png", dpi=150); plt.close()

# ---------------------------------------------------------------- console summary
pt = R["pre_trend"]; print(f"Pre-period trends: weekly divergence {pt['weekly_divergence']:+.4f}, p = {pt['p_value']:.2f} -> {'parallel' if pt['parallel'] else 'NOT parallel'}")
for k in ("orders", "revenue", "contribution_margin", "new_customers"):
    e = R[k]; print(f"{k:20s} {e['pct']:+.1%}  95% CI [{e['ci_low']:+.1%}, {e['ci_high']:+.1%}]  p = {e['p_value']:.4f}")
rb = R["robustness"]; print(f"Ratio estimate {rb['ratio_estimate']:+.1%} | leave-one-pair-out {rb['leave_one_pair_out_min']:+.1%} to {rb['leave_one_pair_out_max']:+.1%} | placebo mean {rb['placebo_mean']:+.1%}")
print(f"Meta spend avoided in treatment states: EUR {M['meta_spend_avoided_eur']:,.0f}")
print(f"Incremental orders {M['incremental_orders'][0]:,.0f} ({M['incremental_share_of_orders']:.1%} of treatment-state orders; Meta claims ~{M['platform_claimed_share_of_orders']:.0%} of all orders)")
print(f"iROAS {M['iroas'][0]:.2f}x [{M['iroas'][1]:.2f}, {M['iroas'][2]:.2f}] vs Meta-reported ROAS {M['platform_roas']:.2f}x | break-even on CM {M['breakeven_roas_on_cm']:.2f}x")
print(f"Incremental CM ROAS {M['incremental_cm_roas'][0]:.2f}x | incremental CAC EUR {M['incremental_cac_eur'][0]:.0f} vs blended CAC EUR {M['blended_cac_eur']:.0f} | 6-month LTV (CM) EUR {M['ltv_6m_cm_eur']:.0f}")
