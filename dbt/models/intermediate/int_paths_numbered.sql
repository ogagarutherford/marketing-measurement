-- GA4 conversion paths with each touch's position and the path length.
select
    transaction_id, user_pseudo_id, touch_sequence, touch_timestamp, channel,
    count(*) over (partition by transaction_id) as path_length
from {{ ref('stg_ga4_conversion_paths') }}
