-- Fails if the unified spend fact doesn't add up to platform spend + affiliate commission + email cost.
with unified as (select sum(spend_eur) as v from {{ ref('fct_marketing_spend_daily') }}),
sources as (
    select (select sum(spend_eur) from {{ ref('stg_platform_geo_daily') }})
         + (select sum(commission_eur) from {{ ref('stg_affiliate_costs') }})
         + (select sum(esp_cost_eur) from {{ ref('stg_email_sends') }}) as v
)
select * from unified, sources where abs(unified.v - sources.v) > 0.01
