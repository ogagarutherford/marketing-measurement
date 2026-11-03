select
    campaign_id,
    platform,
    campaign_name,
    campaign_role,
    case
        when platform = 'meta'        then 'Meta'
        when platform = 'tiktok'      then 'TikTok'
        when platform = 'dv360'       then 'DV360'
        when platform = 'affiliate'   then 'Affiliate'
        when campaign_role = 'brand_search' then 'Google Brand Search'
        else 'Google Non-Brand Search'
    end as channel,
    cast(start_date as date) as start_date
from {{ source('raw', 'raw_campaigns') }}
