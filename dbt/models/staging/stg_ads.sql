select ad_id, campaign_id, ad_name, creative_type from {{ source('raw', 'raw_ads') }}
