select c.*, count(a.ad_id) as ads
from {{ ref('stg_campaigns') }} c
left join {{ ref('stg_ads') }} a using (campaign_id)
group by all
