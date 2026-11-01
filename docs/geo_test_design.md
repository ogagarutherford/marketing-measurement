# Geo Test Design (pre-registered)

**Question:** how many orders does Meta advertising actually cause?
**Why a geo test:** platform-reported ROAS counts conversions Meta *touched*, not conversions it *caused*. Switching Meta
off in some regions and comparing them with similar regions where it stayed on measures the causal effect.

| Item | Decision |
|---|---|
| Units | Germany's 16 states |
| Assignment | States sorted by population and paired; one state per pair randomly assigned to **treatment** (8 states), the other to **control** (8 states). Stored in `raw_regions.geo_test_group` and `pair_id` |
| Treatment | All Meta campaigns paused in treatment states; all other channels unchanged everywhere |
| Test period | 5 May – 1 June 2025 (4 full weeks) |
| Pre-period | 10 March – 4 May 2025 (8 weeks) |
| **Primary metric** | **Orders per state per day, from the order system** (not GA4, which misses unconsented users; not Meta, which can’t see what it didn’t cause) |
| Secondary | Revenue and contribution margin per state per day |
| Method | Difference-in-differences on log orders with state and day fixed effects; standard errors clustered by state. Robustness: a simple pre/post ratio comparison and a placebo check |
| Translation | Incremental orders = treatment states’ counterfactual orders × estimated % drop. **iROAS** = incremental revenue ÷ Meta spend saved in treatment states |

## Precision (estimated before launch from historical data)
Nine placebo tests on earlier weeks, where nothing changed, gave estimates centred on zero with an average 95% interval
of about ±5.7%. That implies a **minimum detectable effect of about 8%** of orders at 80% power. Meta's own reporting
implies it drives around 40% of orders, so the test can clearly distinguish an effect near that claim from a much smaller one.

## Risks
- **Spillover:** people see ads in one state and order in another (understates the effect).
- **Other changes during the test:** any other channel change must be avoided or recorded.
- **Short-term only:** four weeks shows immediate effects, not longer-term brand building.

## Decision rule
Compare iROAS with platform ROAS and with break-even ROAS on contribution margin. Reallocate Meta budget only if iROAS
is clearly below break-even; scale it if clearly above; otherwise keep spend and test again.
