# Data Model

| Layer | Table | Grain |
|---|---|---|
| Dimensions | `dim_regions` | One row per state, with geo-test group and pair |
| | `dim_campaigns`, `dim_ads` | Campaign (platform, role) and ad (creative type) |
| | `dim_customers` | One row per customer: first order, home state, email opt-in |
| Facts | `fct_marketing_spend_daily` | Date × channel × campaign × state: spend, impressions, clicks, platform claims (paid media, affiliate commission and email cost unified) |
| | `fct_orders` | One row per order: revenue, costs, contribution margin, new vs returning |
| | `fct_touchpoints` | One row per GA4 touchpoint before a purchase (consented users) |
| Marts | `mart_channel_performance` | Channel × week: delivery KPIs, platform ROAS, GA4 conversions |
| | `mart_attribution` | Channel × attribution model: attributed orders and revenue |
| | `mart_geo_test_daily` | State × day: orders, revenue, contribution, Meta spend, test group |
| | `mart_cohorts` | First-order month × months since: retention, cumulative contribution (LTV, payback) |

The unified spend fact is the core: every channel's cost in one table, so MER and CAC never depend on a single platform's view.
