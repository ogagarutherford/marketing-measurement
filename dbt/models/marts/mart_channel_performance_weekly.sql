-- Grain: week x channel. Delivery KPIs and platform-claimed results next to GA4 last-click results.
with spend as (
    select date_trunc('week', spend_date) as week, channel,
           sum(spend_eur) as spend_eur, sum(impressions) as impressions, sum(clicks) as clicks,
           sum(platform_conversions) as platform_conversions, sum(platform_conversion_value_eur) as platform_conversion_value_eur
    from {{ ref('fct_marketing_spend_daily') }}
    group by 1, 2
),
ga4 as (
    select date_trunc('week', traffic_date) as week, channel,
           sum(sessions) as ga4_sessions, sum(purchases) as ga4_last_click_purchases, sum(purchase_revenue) as ga4_last_click_revenue_eur
    from {{ ref('stg_ga4_daily_traffic') }}
    group by 1, 2
)

select
    coalesce(s.week, g.week) as week,
    coalesce(s.channel, g.channel) as channel,
    coalesce(s.spend_eur, 0) as spend_eur, s.impressions, s.clicks,
    s.clicks * 1.0 / nullif(s.impressions, 0)                    as ctr,
    s.spend_eur / nullif(s.clicks, 0)                            as cpc_eur,
    s.spend_eur / nullif(s.impressions, 0) * 1000                as cpm_eur,
    s.platform_conversions, s.platform_conversion_value_eur,
    s.platform_conversion_value_eur / nullif(s.spend_eur, 0)     as platform_roas,
    g.ga4_sessions, g.ga4_last_click_purchases, g.ga4_last_click_revenue_eur,
    g.ga4_last_click_purchases * 1.0 / nullif(g.ga4_sessions, 0) as ga4_cvr,
    g.ga4_last_click_revenue_eur / nullif(s.spend_eur, 0)        as ga4_last_click_roas
from spend s
full outer join ga4 g on g.week = s.week and g.channel = s.channel
