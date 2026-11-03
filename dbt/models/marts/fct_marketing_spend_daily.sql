-- Grain: date x channel x campaign x region. Every marketing cost in one table.
-- Paid media is reported by region; affiliate commission and email cost are national (region = 'National').
select
    p.spend_date, c.channel, p.campaign_id, c.campaign_name, c.campaign_role, p.region,
    p.spend_eur, p.impressions, p.clicks, p.platform_conversions, p.platform_conversion_value_eur
from {{ ref('stg_platform_geo_daily') }} p
join {{ ref('stg_campaigns') }} c using (campaign_id)

union all

select spend_date, 'Affiliate', 'C011', 'AWIN_Network', 'affiliate', 'National',
       commission_eur, null, null, network_reported_orders, network_reported_revenue_eur
from {{ ref('stg_affiliate_costs') }}

union all

select spend_date, 'Email', null, campaign, 'crm', 'National',
       esp_cost_eur, null, null, null, null
from {{ ref('stg_email_sends') }}
