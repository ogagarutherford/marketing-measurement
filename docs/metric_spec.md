# Metric Specification

Every metric is defined once, with its source. Three sources disagree by design, so the source is part of the definition.

| Source | What it is | Strength | Weakness |
|---|---|---|---|
| **Order system** (`raw_orders`) | Every real order, with revenue and costs | Complete ground truth for orders and money | Knows nothing about which ads a customer saw |
| **GA4** (`raw_ga4_*`) | Website sessions and conversion paths | Shows journeys and channels | Only consented users (~72% of orders) |
| **Ad platforms** (`raw_platform_geo_daily`) | Delivery, spend and the conversions each platform claims | Exact spend and delivery | Each platform claims credit generously, so claims overlap and exceed real orders |

## Delivery and efficiency (source: ad platforms)
| Metric | Definition |
|---|---|
| CTR | Clicks ÷ impressions |
| CPC | Spend ÷ clicks |
| CPM | Spend ÷ impressions × 1,000 |
| Platform ROAS | Platform-claimed conversion value ÷ spend (what the platform says) |

## Conversion (source: GA4, consented traffic)
| Metric | Definition |
|---|---|
| Sessions, engaged sessions | As reported by GA4 |
| CVR | Purchases ÷ sessions |
| Attributed revenue (by model) | Order revenue allocated to touchpoints by an attribution model (see attribution_approach.md) |

## Business outcomes (source: order system)
| Metric | Definition |
|---|---|
| Orders, revenue | Non-cancelled orders; revenue = gross revenue − discount |
| Contribution margin (CM) | Revenue − COGS − shipping − payment fees (returns: revenue and COGS reversed, shipping kept) |
| MER (marketing efficiency ratio) | Total revenue ÷ total marketing cost (all paid media + affiliate commission + email cost). Attribution-free |
| New-customer CAC (blended) | Total marketing cost ÷ new customers |
| LTV (6-month) | Cumulative contribution margin per customer within 180 days of first order |
| Payback | Months until cumulative contribution per new customer exceeds blended CAC |
| Repeat rate | Share of new customers ordering again within 90 days |

## Incrementality (source: geo test)
| Metric | Definition |
|---|---|
| Incremental orders | Orders caused by a channel, estimated from the geo test (difference-in-differences) |
| iROAS | Incremental revenue ÷ spend. Compare with platform ROAS: **ROAS ≠ iROAS** |
| Incremental CM ROAS | Incremental contribution margin ÷ spend: does the channel pay for itself after costs? |
