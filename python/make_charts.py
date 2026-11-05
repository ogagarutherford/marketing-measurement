"""
README charts: attribution by model, weekly MER and spend, cohort LTV against CAC.
Run from the repo root:  python python/make_charts.py
"""
from pathlib import Path
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from warehouse import query

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "docs" / "images"
NAVY, YELLOW, GREY, RED, GREEN = "#16213B", "#F2B705", "#9AA4B5", "#B3261E", "#1E7A4C"

# 1. Attribution: share of orders by channel under each model
a = query("select model, channel, share_of_orders from marts.mart_attribution").pivot(index="channel", columns="model", values="share_of_orders")
a = a[["last_click", "first_click", "linear", "position_based"]].sort_values("last_click", ascending=False)
fig, ax = plt.subplots(figsize=(9.5, 4.2)); x = np.arange(len(a)); w = 0.2
for i, (m, col) in enumerate(zip(a.columns, [NAVY, YELLOW, GREY, GREEN])):
    ax.bar(x + (i - 1.5) * w, a[m] * 100, w, label=m.replace("_", " ").capitalize(), color=col)
ax.set_xticks(x, a.index, rotation=25, ha="right", fontsize=8); ax.set_ylabel("Share of attributed orders (%)")
ax.set_title("The attribution model decides who looks like the winner"); ax.legend(fontsize=8, ncol=4, frameon=False)
plt.tight_layout(); plt.savefig(IMG / "attribution_by_model.png", dpi=150); plt.close()

# 2. Weekly MER and marketing cost
b = query("select week, mer, marketing_cost_eur from marts.mart_business_weekly order by week")
b = b.iloc[1:-1]                                              # drop partial first and last weeks
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.bar(b.week, b.marketing_cost_eur / 1000, width=5, color=GREY, label="Marketing cost (€k)")
ax2 = ax.twinx(); ax2.plot(b.week, b.mer, color=NAVY, lw=2, label="MER")
ax.axvspan(np.datetime64("2025-05-05"), np.datetime64("2025-06-01"), color=YELLOW, alpha=0.2)
ax.set_ylabel("Marketing cost per week (€k)"); ax2.set_ylabel("MER (revenue ÷ marketing cost)")
ax.set_title("Attribution-free view: weekly MER (shaded: geo test)")
plt.tight_layout(); plt.savefig(IMG / "mer_weekly.png", dpi=150); plt.close()

# 3. Cohort LTV against CAC
c = query("select first_order_month, months_since, cumulative_cm_per_customer_eur, blended_cac_eur from marts.mart_cohorts order by 1, 2")
M = json.loads((ROOT / "results" / "geo_test_results.json").read_text())["money"]
fig, ax = plt.subplots(figsize=(8, 3.8))
for (m, g), col in zip(c.groupby("first_order_month"), ["#16213B", "#2E4A7A", "#4F6FA8", "#7C93C4", "#AEBEDD", "#D3DCEE"]):
    ax.plot(g.months_since, g.cumulative_cm_per_customer_eur, marker="o", ms=3, color=col, label=str(m)[:7])
ax.axhline(M["blended_cac_eur"], color=GREEN, ls="--", label=f"Blended CAC €{M['blended_cac_eur']:.0f}")
ax.axhline(M["incremental_cac_eur"][0], color=RED, ls="--", label=f"Meta incremental CAC €{M['incremental_cac_eur'][0]:.0f}")
ax.set_xlabel("Months since first order"); ax.set_ylabel("Cumulative contribution per customer (€)")
ax.set_title("Customers pay back blended CAC immediately, but not Meta's incremental CAC")
ax.legend(fontsize=7, ncol=2); plt.tight_layout(); plt.savefig(IMG / "ltv_vs_cac.png", dpi=150); plt.close()
print("Charts written: attribution_by_model, mer_weekly, ltv_vs_cac")
