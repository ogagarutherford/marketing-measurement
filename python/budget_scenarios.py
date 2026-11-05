"""
Meta budget scenarios built on the geo test, not on platform ROAS.

Response curve: incremental revenue = k * spend^b (diminishing returns, b = 0.75 by default).
k is calibrated so the AVERAGE incremental ROAS at current spend equals the geo-test estimate.
Profit view: contribution margin (CM) earned on incremental revenue minus Meta spend, in the short term
(first orders) and over 6 months (including repeat purchases, scaled by LTV / first-order CM).

Outputs: results/budget_scenarios.csv, docs/images/budget_scenarios.png
Run from the repo root (after geo_test_analysis.py):  python python/budget_scenarios.py
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from warehouse import query

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "results" / "geo_test_results.json").read_text())["money"]
B = 0.75
monthly = query("""select date_trunc('month', spend_date) m, sum(spend_eur) s from marts.fct_marketing_spend_daily
                   where channel = 'Meta' and month(spend_date) in (4, 6) group by 1""")
S0 = monthly.s.mean()                                        # current monthly Meta spend (normal months)
cm_rate, ltv_mult = M["cm_rate"], M["ltv_6m_cm_eur"] / M["first_order_cm_eur"]


def curve(iroas_at_s0, b=B):
    k = iroas_at_s0 * S0 / S0 ** b
    return lambda s: k * np.power(s, b)


rows = []
for label, share in [("Current", 1.0), ("Cut 30%", 0.7), ("Cut 50%", 0.5), ("Cut 70%", 0.3), ("Pause", 0.0)]:
    s = S0 * share
    for case, i in [("central", M["iroas"][0]), ("low", M["iroas"][1]), ("high", M["iroas"][2])]:
        rev = curve(i)(s)
        rows.append({"scenario": label, "case": case, "meta_spend_eur": s, "incremental_revenue_eur": rev,
                     "net_cm_short_term_eur": rev * cm_rate - s, "net_cm_6_months_eur": rev * cm_rate * ltv_mult - s,
                     "average_iroas": rev / s if s else None,
                     "marginal_iroas": B * curve(i)(s) / s if s else None})
df = pd.DataFrame(rows)
base = df[df.scenario == "Current"].set_index("case")
df["vs_current_short_term_eur"] = df.apply(lambda r: r.net_cm_short_term_eur - base.loc[r.case, "net_cm_short_term_eur"], axis=1)
df["vs_current_6_months_eur"] = df.apply(lambda r: r.net_cm_6_months_eur - base.loc[r.case, "net_cm_6_months_eur"], axis=1)
df["revenue_lost_vs_current_eur"] = df.apply(lambda r: base.loc[r.case, "incremental_revenue_eur"] - r.incremental_revenue_eur, axis=1)
df.round(2).to_csv(ROOT / "results" / "budget_scenarios.csv", index=False)

# sensitivity: does the conclusion survive a different curve shape?
sens = {b: (curve(M["iroas"][0], b)(S0 * 0.5) * cm_rate * ltv_mult - S0 * 0.5) - (curve(M["iroas"][0], b)(S0) * cm_rate * ltv_mult - S0)
        for b in (0.6, 0.75, 0.9)}
(ROOT / "results" / "budget_scenarios_meta.json").write_text(json.dumps(
    {"current_monthly_meta_spend_eur": S0, "curve_exponent": B, "ltv_multiplier": ltv_mult,
     "breakeven_monthly_spend_eur": None,
     "cut50_gain_6m_by_exponent": {str(k): v for k, v in sens.items()}}, indent=2))

# chart: monthly net contribution (6-month view) across spend levels
grid = np.linspace(0, S0 * 1.2, 121)
fine = np.linspace(S0 * 0.05, S0 * 1.2, 4000)
net_c = curve(M["iroas"][0])(fine) * cm_rate * ltv_mult - fine
breakeven = float(fine[net_c < 0][0]) if (net_c < 0).any() else None
fig, ax = plt.subplots(figsize=(8.5, 4))
for case, i, col, lw in [("low", M["iroas"][1], "#9AA4B5", 1), ("high", M["iroas"][2], "#9AA4B5", 1), ("central", M["iroas"][0], "#16213B", 2.2)]:
    ax.plot(grid / 1000, (curve(i)(grid) * cm_rate * ltv_mult - grid) / 1000, color=col, lw=lw,
            label={"central": "Central estimate", "low": "Uncertainty range", "high": None}[case])
c = df[df.case == "central"]
ax.scatter(c.meta_spend_eur / 1000, c.net_cm_6_months_eur / 1000, color="#F2B705", zorder=3, s=40)
for r in c.itertuples():
    ax.annotate(r.scenario, (r.meta_spend_eur / 1000, r.net_cm_6_months_eur / 1000), textcoords="offset points", xytext=(4, 6), fontsize=8)
ax.axhline(0, color="black", lw=0.8)
ax.set_xlabel("Monthly Meta spend (€k)"); ax.set_ylabel("Net contribution after Meta spend (€k / month)")
ax.set_title(f"Central estimate: Meta stops paying back above ~€{breakeven / 1000:.0f}k a month (wide uncertainty)")
ax.legend(fontsize=8); plt.tight_layout(); plt.savefig(ROOT / "docs" / "images" / "budget_scenarios.png", dpi=150); plt.close()

print(f"Current monthly Meta spend: EUR {S0:,.0f} | LTV multiplier {ltv_mult:.2f} | curve exponent {B}")
print(c[["scenario", "meta_spend_eur", "incremental_revenue_eur", "net_cm_6_months_eur", "vs_current_6_months_eur"]].round(0).to_string(index=False)); print("Marginal iROAS:", c.set_index("scenario").marginal_iroas.round(2).to_dict())
print("Cut-50% gain (6-month view) under different curve shapes:", {k: round(v) for k, v in sens.items()})
meta_path = ROOT / "results" / "budget_scenarios_meta.json"
meta_json = json.loads(meta_path.read_text()); meta_json["breakeven_monthly_spend_eur"] = breakeven
meta_path.write_text(json.dumps(meta_json, indent=2))
print(f"Break-even monthly Meta spend (central, 6-month view): EUR {breakeven:,.0f}")
