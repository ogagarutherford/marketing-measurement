select cast(date as date) as spend_date, network_reported_orders, network_reported_revenue_eur, commission_eur
from {{ source('raw', 'raw_affiliate_costs') }}
