select
    cast(date as date) as traffic_date, region, source, medium, campaign,
    {{ channel_from_utm('source', 'medium', 'campaign') }} as channel,
    sessions, engaged_sessions, add_to_carts, purchases, purchase_revenue
from {{ source('raw', 'raw_ga4_daily_traffic') }}
