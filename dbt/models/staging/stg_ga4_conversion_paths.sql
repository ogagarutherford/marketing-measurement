select
    transaction_id, user_pseudo_id, touch_sequence, touch_timestamp, source, medium, campaign,
    {{ channel_from_utm('source', 'medium', 'campaign') }} as channel
from {{ source('raw', 'raw_ga4_conversion_paths') }}
