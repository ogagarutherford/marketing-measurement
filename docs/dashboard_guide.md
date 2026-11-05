# Building the Velora dashboard in Looker Studio

Free, in the browser. Data comes from `exports/looker/*.csv` (created by `python python/export_for_looker.py`).

## 1. Get the files
In the Codespace Explorer, open `exports/looker`, select the six CSV files, right-click → **Download**.

## 2. Create the data sources
Go to **lookerstudio.google.com** → **Create → Data source → File Upload**. Upload `business_weekly.csv` and click
**Connect**. Repeat for each CSV (one data source per file). Check that date columns (`week`, `date`,
`first_order_month`) are typed as **Date**, and euro columns as **Currency (EUR)**.

## 3. Build one report with four pages
**Create → Report**, add the data sources.

**Page 1 · Overview** (business_weekly)
- Scorecards: total `revenue_eur`, total `marketing_cost_eur`, a calculated field `MER = SUM(revenue_eur) / SUM(marketing_cost_eur)`, total `new_customers`.
- Time series: `week` × `MER`, with `marketing_cost_eur` as a second metric on the right axis.

**Page 2 · Channels** (channel_weekly)
- Table: `channel` with SUM of `spend_eur`, `clicks`, `impressions`, and calculated fields
  `Platform ROAS = SUM(platform_conversion_value_eur) / SUM(spend_eur)` and `GA4 last-click ROAS = SUM(ga4_last_click_revenue_eur) / SUM(spend_eur)`.
- Add a date-range control on `week`.

**Page 3 · Attribution** (attribution)
- Bar chart: dimension `channel`, breakdown dimension `model`, metric `share_of_orders` (format as percent).
- Title: *The model decides who looks like the winner*.

**Page 4 · Meta geo test** (geo_test_daily and budget_scenarios)
- Time series: `date` × SUM(`orders`), breakdown `geo_test_group`.
- Table from budget_scenarios: filter `case = central`, columns `scenario`, `meta_spend_eur`, `net_cm_6_months_eur`, `vs_current_6_months_eur`.
- A text box with the headline: *Meta claims 3.2× ROAS; the geo test measures about 0.93×.*

## 4. Share
**Share → Manage access → Anyone with the link can view**. Copy the link and replace `LOOKER_LINK` in the README.
