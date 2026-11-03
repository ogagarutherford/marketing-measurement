select
    cast(date as date) as spend_date, campaign_id, region,
    impressions, clicks, spend_eur, platform_conversions, platform_conversion_value_eur
from {{ source('raw', 'raw_platform_geo_daily') }}
