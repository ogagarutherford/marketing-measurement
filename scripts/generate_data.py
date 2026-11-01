"""
Synthetic marketing dataset: "Velora", a fictional D2C skincare brand selling across Germany's 16 states.
Period: 2025-01-01 to 2025-06-30. All data is SYNTHETIC (seed 7). Assumptions: docs/data_assumptions.md

What the data is built to show (the true effects are NOT stored in any table):
- Ad platforms over-claim conversions (their totals exceed real orders).
- GA4 only sees consented visitors, so it under-counts orders.
- Brand search looks excellent on last-click but is mostly non-incremental.
- A geo test: Meta was paused in 8 of 16 states for four weeks (see docs/geo_test_design.md).

Usage:  python scripts/generate_data.py      -> Parquet files in data/raw/
"""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

DAYS = pd.date_range("2025-01-01", "2025-06-30", freq="D")
ND = len(DAYS)
TEST_START, TEST_END = pd.Timestamp("2025-05-05"), pd.Timestamp("2025-06-01")   # inclusive, 4 weeks
in_test = np.asarray((DAYS >= TEST_START) & (DAYS <= TEST_END))

# ---------------------------------------------------------------- regions and geo-test assignment
REG = [("Nordrhein-Westfalen", 18.1), ("Bayern", 13.4), ("Baden-Württemberg", 11.3), ("Niedersachsen", 8.1),
       ("Hessen", 6.4), ("Rheinland-Pfalz", 4.2), ("Sachsen", 4.1), ("Berlin", 3.8), ("Schleswig-Holstein", 3.0),
       ("Brandenburg", 2.6), ("Sachsen-Anhalt", 2.2), ("Thüringen", 2.1), ("Hamburg", 1.9),
       ("Mecklenburg-Vorpommern", 1.6), ("Saarland", 1.0), ("Bremen", 0.7)]
regions = pd.DataFrame(REG, columns=["region", "population_m"])
regions["region_code"] = ["NW", "BY", "BW", "NI", "HE", "RP", "SN", "BE", "SH", "BB", "ST", "TH", "HH", "MV", "SL", "HB"]
regions["urban_share"] = [0.55, 0.45, 0.48, 0.42, 0.52, 0.38, 0.45, 1.0, 0.40, 0.35, 0.38, 0.36, 1.0, 0.33, 0.45, 1.0]
# matched pairs by population: one of each consecutive pair is randomly assigned to treatment (Meta paused)
grp = []
for i in range(0, 16, 2):
    t = rng.integers(0, 2)
    grp += (["treatment", "control"] if t == 0 else ["control", "treatment"])
regions["geo_test_group"] = grp
regions["pair_id"] = np.repeat(np.arange(1, 9), 2)
pop_share = (regions.population_m / regions.population_m.sum()).values
urban = regions.urban_share.values
NR = len(regions)

# ---------------------------------------------------------------- campaigns and ads
CAMP = [  # platform, campaign, role, share of platform budget, claim weight, CPM or CPC, CTR
    ("meta", "META_Prospecting_Broad", "prospecting", 0.45, 0.8, 9.0, 0.011),
    ("meta", "META_Prospecting_Lookalike", "prospecting", 0.30, 0.9, 10.0, 0.012),
    ("meta", "META_Retargeting", "retargeting", 0.25, 1.9, 14.0, 0.016),
    ("tiktok", "TT_Prospecting_Spark", "prospecting", 0.55, 1.0, 6.0, 0.009),
    ("tiktok", "TT_Prospecting_UGC", "prospecting", 0.45, 1.0, 6.5, 0.010),
    ("google_ads", "GADS_Brand", "brand_search", 1.00, 1.0, 0.35, 0.28),
    ("google_ads", "GADS_NonBrand_Generic", "nonbrand_search", 0.70, 1.0, 0.95, 0.055),
    ("google_ads", "GADS_NonBrand_Competitor", "nonbrand_search", 0.30, 1.0, 1.20, 0.045),
    ("dv360", "DV360_Prospecting_Display", "prospecting", 0.60, 1.0, 3.5, 0.0025),
    ("dv360", "DV360_Prospecting_YouTube", "prospecting", 0.40, 1.0, 6.0, 0.004),
    ("affiliate", "AWIN_Network", "affiliate", 1.00, 1.0, None, None),
]
campaigns = pd.DataFrame(CAMP, columns=["platform", "campaign_name", "campaign_role", "budget_share", "claim_weight", "cost_unit", "ctr"])
campaigns.insert(0, "campaign_id", [f"C{i:03d}" for i in range(1, len(campaigns) + 1)])
campaigns["start_date"] = pd.Timestamp("2024-11-01").date()

CREATIVES = {"meta": ["UGC video", "Static image", "Carousel", "Founder story"], "tiktok": ["Spark ad", "UGC video", "Tutorial"],
             "google_ads": ["Responsive search ad A", "Responsive search ad B"], "dv360": ["Banner 300x250", "Video 15s"],
             "affiliate": ["Voucher partner", "Content partner"]}
ads_rows = []
for _, c in campaigns.iterrows():
    for j, cr in enumerate(CREATIVES[c.platform][:4 if c.platform == "meta" else 3], 1):
        ads_rows.append({"ad_id": f"{c.campaign_id}_A{j}", "campaign_id": c.campaign_id,
                         "ad_name": f"{c.campaign_name}_{cr.replace(' ', '')}", "creative_type": cr})
ads = pd.DataFrame(ads_rows)

# ---------------------------------------------------------------- daily national budgets by channel
t = np.arange(ND)
weekday = DAYS.dayofweek.values
season = 1 + 0.10 * np.sin((t - 30) / 365 * 2 * np.pi) + np.where(DAYS.month == 5, 0.06, 0)   # spring skincare lift
wk = np.where(weekday >= 5, 0.92, 1.03)
budget_level = np.where(DAYS.month >= 4, 1.12, 1.0)          # budgets raised from April
BUDGET = {"meta": 3000, "tiktok": 1500, "google_ads": 2000, "dv360": 1000}
GADS_SPLIT = {"GADS_Brand": 0.40, "GADS_NonBrand_Generic": 0.42, "GADS_NonBrand_Competitor": 0.18}

# spend[platform] -> array (ND, NR), allocated by population with mild noise
spend = {}
for p, b in BUDGET.items():
    nat = b * budget_level * wk * rng.normal(1, 0.06, ND)
    alloc = pop_share[None, :] * rng.normal(1, 0.08, (ND, NR))
    alloc = alloc / alloc.sum(1, keepdims=True)
    spend[p] = nat[:, None] * alloc
treat = (regions.geo_test_group == "treatment").values
spend["meta"][np.ix_(in_test, treat)] = 0.0                      # the geo test: Meta paused in treatment states

# ---------------------------------------------------------------- true demand model (hidden)
AOV = 42.0
base_orders = 360 * season * np.where(weekday >= 5, 1.06, 0.98)  # organic, direct, brand demand, email, affiliate
# incremental orders per channel = k * spend^0.75 (diminishing returns), calibrated to national targets
TARGET_IROAS = {"meta": 1.30, "tiktok": 0.95, "gads_nonbrand": 1.80, "gads_brand": 0.35, "dv360": 0.45}
def calibrate(s_by_region, iroas):
    """k such that average incremental revenue / spend = iroas on normal (non-test) days."""
    s = s_by_region[~in_test]
    return iroas * s.sum(1).mean() / AOV / (s ** 0.75).sum(1).mean()
gads = spend["google_ads"]
s_ch = {"meta": spend["meta"], "tiktok": spend["tiktok"], "dv360": spend["dv360"],
        "gads_brand": gads * GADS_SPLIT["GADS_Brand"], "gads_nonbrand": gads * (1 - GADS_SPLIT["GADS_Brand"])}
k = {c: calibrate(s_ch[c], TARGET_IROAS[c]) for c in s_ch}
incr = {c: k[c] * s_ch[c] ** 0.75 for c in s_ch}
baseline = base_orders[:, None] * pop_share[None, :] * (0.9 + 0.2 * urban[None, :]) / np.mean(0.9 + 0.2 * urban)
expected = baseline + sum(incr.values())
orders_rd = rng.poisson(np.clip(expected, 0, None))

# ---------------------------------------------------------------- orders, customers, journeys
BASE_MIX = {"direct": 0.30, "organic_search": 0.24, "brand_search_intent": 0.20, "email": 0.14, "affiliate": 0.12}
order_rows, path_rows = [], []
cust_first, cust_region, cust_optin = [], [], []
oid = 0
mean_driver = {}
for d in range(ND):
    for r in range(NR):
        n = orders_rd[d, r]
        if n == 0: continue
        parts = {"baseline": baseline[d, r], **{c: incr[c][d, r] for c in incr}}
        names = list(parts); w = np.array([parts[x] for x in names]); w = w / w.sum()
        drivers = rng.choice(names, n, p=w)
        for drv in drivers:
            oid += 1
            if drv == "baseline":
                drv = rng.choice(list(BASE_MIX), p=list(BASE_MIX.values()))
            # customer: returning with probability rising over time
            p_ret = min(0.38, 0.12 + 0.0016 * d)
            if cust_first and rng.random() < p_ret:
                cid = int(rng.integers(0, len(cust_first)))
            else:
                cid = len(cust_first); cust_first.append(DAYS[d].date()); cust_region.append(regions.region[r])
                cust_optin.append(bool(rng.random() < 0.58))
            ts = DAYS[d] + pd.Timedelta(minutes=int(rng.integers(7 * 60, 23 * 60)))
            rev = round(float(np.clip(rng.lognormal(np.log(AOV) - 0.08, 0.38), 12, 220)), 2)
            disc = round(rev * 0.10, 2) if drv == "affiliate" and rng.random() < 0.7 else 0.0
            order_rows.append((f"O{oid:07d}", f"CU{cid + 1:06d}", ts, regions.region[r], rev, disc, drv))
            # journey (only stored for consented users, in GA4 paths)
            if rng.random() < 0.72:
                path = {"meta": [["meta", "brand"], ["meta"], ["meta", "direct"], ["meta", "meta_rt"]],
                        "tiktok": [["tiktok", "brand"], ["tiktok"], ["tiktok", "direct"]],
                        "dv360": [["dv360", "brand"], ["dv360", "direct"], ["dv360", "organic"]],
                        "gads_nonbrand": [["nonbrand"], ["nonbrand", "brand"], ["nonbrand", "direct"]],
                        "gads_brand": [["brand"]],
                        "direct": [["direct"], ["meta", "direct"], ["organic", "direct"]],
                        "organic_search": [["organic"], ["organic", "direct"]],
                        "brand_search_intent": [["brand"], ["direct", "brand"], ["meta", "brand"]],
                        "email": [["email"], ["direct", "email"], ["email", "direct"]],
                        "affiliate": [["affiliate"], ["meta", "affiliate"], ["organic", "affiliate"]]}[drv]
                pw = {"meta": [0.35, 0.30, 0.20, 0.15], "tiktok": [0.40, 0.35, 0.25], "dv360": [0.4, 0.35, 0.25],
                      "gads_nonbrand": [0.55, 0.25, 0.20], "gads_brand": [1.0], "direct": [0.7, 0.18, 0.12],
                      "organic_search": [0.75, 0.25], "brand_search_intent": [0.6, 0.2, 0.2], "email": [0.6, 0.2, 0.2],
                      "affiliate": [0.6, 0.25, 0.15]}[drv]
                chosen = path[rng.choice(len(path), p=pw)]
                if rng.random() < 0.25 and chosen[0] != "direct":
                    chosen = [rng.choice(["direct", "organic", "email", "meta", "tiktok"])] + chosen
                n_t = len(chosen)
                gaps = np.sort(rng.uniform(0, 14 * 24 * 60, n_t - 1))[::-1] if n_t > 1 else []
                for s, tp in enumerate(chosen, 1):
                    when = ts - pd.Timedelta(minutes=float(gaps[s - 1])) if s < n_t else ts - pd.Timedelta(minutes=int(rng.integers(2, 25)))
                    path_rows.append((f"O{oid:07d}", f"U{cid + 1:07d}", s, when, tp))

orders = pd.DataFrame(order_rows, columns=["order_id", "customer_id", "order_timestamp", "region", "gross_revenue_eur", "discount_eur", "_driver"])
orders["cogs_eur"] = (orders.gross_revenue_eur * rng.uniform(0.24, 0.30, len(orders))).round(2)
orders["shipping_cost_eur"] = np.where(orders.gross_revenue_eur >= 39, 4.20, 4.90)
orders["payment_fee_eur"] = (orders.gross_revenue_eur * 0.019 + 0.25).round(2)
orders["order_status"] = rng.choice(["completed", "returned", "cancelled"], len(orders), p=[0.93, 0.04, 0.03])
orders = orders.drop(columns="_driver")

customers = pd.DataFrame({"customer_id": [f"CU{i + 1:06d}" for i in range(len(cust_first))],
                          "first_order_date": cust_first, "home_region": cust_region, "email_opt_in": cust_optin})

UTM = {"meta": ("facebook", "paid_social", "META_Prospecting_Broad"), "meta_rt": ("facebook", "paid_social", "META_Retargeting"),
       "tiktok": ("tiktok", "paid_social", "TT_Prospecting_Spark"), "dv360": ("dv360", "display", "DV360_Prospecting_Display"),
       "nonbrand": ("google", "cpc", "GADS_NonBrand_Generic"), "brand": ("google", "cpc", "GADS_Brand"),
       "affiliate": ("awin", "affiliate", "AWIN_Network"), "email": ("newsletter", "email", "crm_weekly"),
       "organic": ("google", "organic", "(not set)"), "direct": ("(direct)", "(none)", "(not set)")}
paths = pd.DataFrame(path_rows, columns=["transaction_id", "user_pseudo_id", "touch_sequence", "touch_timestamp", "_tp"])
# spread campaign names realistically within platforms
pick = lambda tp, n: {"meta": rng.choice(["META_Prospecting_Broad", "META_Prospecting_Lookalike"], n, p=[0.6, 0.4]),
                      "tiktok": rng.choice(["TT_Prospecting_Spark", "TT_Prospecting_UGC"], n),
                      "dv360": rng.choice(["DV360_Prospecting_Display", "DV360_Prospecting_YouTube"], n, p=[0.6, 0.4]),
                      "nonbrand": rng.choice(["GADS_NonBrand_Generic", "GADS_NonBrand_Competitor"], n, p=[0.72, 0.28])}.get(tp)
paths["source"] = paths._tp.map(lambda x: UTM[x][0]); paths["medium"] = paths._tp.map(lambda x: UTM[x][1])
paths["campaign"] = paths._tp.map(lambda x: UTM[x][2])
for tp in ["meta", "tiktok", "dv360", "nonbrand"]:
    m = paths._tp == tp
    paths.loc[m, "campaign"] = pick(tp, m.sum())
paths = paths.drop(columns="_tp")

# ---------------------------------------------------------------- GA4 daily traffic (consented sessions only)
last = paths.sort_values("touch_sequence").groupby("transaction_id").tail(1)
last = last.merge(orders[["order_id", "region", "gross_revenue_eur"]], left_on="transaction_id", right_on="order_id")
last["date"] = pd.to_datetime(last.touch_timestamp).dt.date
CVR = {"paid_social": 0.012, "display": 0.006, "cpc": 0.045, "affiliate": 0.05, "email": 0.035, "organic": 0.03, "(none)": 0.04}
g = last.groupby(["date", "region", "source", "medium", "campaign"]).agg(purchases=("order_id", "count"), purchase_revenue=("gross_revenue_eur", "sum")).reset_index()
g["sessions"] = (g.purchases / g.medium.map(CVR) * rng.uniform(0.85, 1.15, len(g))).round().astype(int)
g["engaged_sessions"] = (g.sessions * rng.uniform(0.45, 0.70, len(g))).round().astype(int)
g["add_to_carts"] = np.maximum(g.purchases, (g.sessions * rng.uniform(0.05, 0.09, len(g))).round()).astype(int)
ga4_daily = g[["date", "region", "source", "medium", "campaign", "sessions", "engaged_sessions", "add_to_carts", "purchases", "purchase_revenue"]]

# ---------------------------------------------------------------- platform delivery and platform-reported conversions
# Platforms claim credit with generous windows (incl. view-through), so claims exceed true influence.
CLAIM_SHARE = {"meta": 0.40, "tiktok": 0.13, "google_ads_brand": 0.36, "google_ads_nonbrand": 0.12, "dv360": 0.09}
geo_rows, ad_rows = [], []
for _, c in campaigns.iterrows():
    if c.platform == "affiliate":
        continue
    if c.platform == "google_ads":
        s = spend["google_ads"] * GADS_SPLIT[c.campaign_name]
        claim_key = "google_ads_brand" if c.campaign_role == "brand_search" else "google_ads_nonbrand"
        share_in_platform = 1.0 if c.campaign_role == "brand_search" else (0.70 if "Generic" in c.campaign_name else 0.30)
    else:
        s = spend[c.platform] * c.budget_share
        claim_key = c.platform
        w = campaigns[campaigns.platform == c.platform]
        share_in_platform = c.budget_share * c.claim_weight / (w.budget_share * w.claim_weight).sum()
    active = (s > 0).astype(float)
    claims = rng.poisson(orders_rd * CLAIM_SHARE[claim_key] * share_in_platform * active * rng.uniform(0.85, 1.15, s.shape))
    if c.platform == "google_ads":
        clicks = s / c.cost_unit; impressions = clicks / c.ctr
    else:
        impressions = s / c.cost_unit * 1000; clicks = impressions * c.ctr
    for d in range(ND):
        for r in range(NR):
            geo_rows.append((DAYS[d].date(), c.campaign_id, regions.region[r], int(impressions[d, r]), int(clicks[d, r]),
                             round(float(s[d, r]), 2), int(claims[d, r]), round(float(claims[d, r] * AOV * rng.uniform(0.95, 1.08)), 2)))
    # ad-level daily (national), split of campaign totals across ads
    my_ads = ads[ads.campaign_id == c.campaign_id].ad_id.values
    wts = rng.dirichlet(np.ones(len(my_ads)) * 3)
    for d in range(ND):
        for a, wa in zip(my_ads, wts):
            ad_rows.append((DAYS[d].date(), a, int(impressions[d].sum() * wa), int(clicks[d].sum() * wa), round(float(s[d].sum() * wa), 2)))
platform_geo = pd.DataFrame(geo_rows, columns=["date", "campaign_id", "region", "impressions", "clicks", "spend_eur", "platform_conversions", "platform_conversion_value_eur"])
ad_daily = pd.DataFrame(ad_rows, columns=["date", "ad_id", "impressions", "clicks", "spend_eur"])

# affiliate: commission = 10% of revenue on orders where the affiliate is the last click (all users, not only consented)
aff_orders = orders.merge(paths[paths.medium == "affiliate"][["transaction_id"]].drop_duplicates(), left_on="order_id", right_on="transaction_id")
aff_rate = 1 / 0.72                                              # scale up for unconsented users the network still tracks
affiliate_costs = (aff_orders.assign(date=pd.to_datetime(aff_orders.order_timestamp).dt.date)
                   .groupby("date").agg(network_reported_orders=("order_id", "count"), network_reported_revenue_eur=("gross_revenue_eur", "sum")).reset_index())
affiliate_costs["network_reported_orders"] = (affiliate_costs.network_reported_orders * aff_rate).round().astype(int)
affiliate_costs["network_reported_revenue_eur"] = (affiliate_costs.network_reported_revenue_eur * aff_rate).round(2)
affiliate_costs["commission_eur"] = (affiliate_costs.network_reported_revenue_eur * 0.10).round(2)

email_sends = pd.DataFrame({"send_date": [d.date() for d in DAYS if d.dayofweek in (1, 4)]})
email_sends["campaign"] = "crm_weekly"; email_sends["recipients"] = rng.integers(38000, 52000, len(email_sends))
email_sends["esp_cost_eur"] = (email_sends.recipients * 0.0012).round(2)

tables = {"regions": regions, "campaigns": campaigns.drop(columns=["budget_share", "claim_weight", "cost_unit", "ctr"]),
          "ads": ads, "platform_geo_daily": platform_geo, "ad_daily": ad_daily, "affiliate_costs": affiliate_costs,
          "email_sends": email_sends, "ga4_daily_traffic": ga4_daily, "ga4_conversion_paths": paths,
          "orders": orders, "customers": customers}
for name, df in tables.items():
    df.to_parquet(OUT / f"raw_{name}.parquet", index=False)
    print(f"raw_{name:22s} {len(df):>9,d} rows")
