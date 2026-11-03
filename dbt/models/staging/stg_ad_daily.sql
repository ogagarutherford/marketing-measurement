select cast(date as date) as spend_date, ad_id, impressions, clicks, spend_eur
from {{ source('raw', 'raw_ad_daily') }}
