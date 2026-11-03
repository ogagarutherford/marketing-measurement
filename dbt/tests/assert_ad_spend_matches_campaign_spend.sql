-- Fails if ad-level spend doesn't match campaign-level spend on any day (two platform reports must agree).
with ads as (
    select a.spend_date, d.campaign_id, sum(a.spend_eur) as ad_spend
    from {{ ref('stg_ad_daily') }} a join {{ ref('stg_ads') }} d using (ad_id) group by 1, 2
),
camp as (select spend_date, campaign_id, sum(spend_eur) as campaign_spend from {{ ref('stg_platform_geo_daily') }} group by 1, 2)
select * from ads join camp using (spend_date, campaign_id)
where abs(ad_spend - campaign_spend) > 1.0
