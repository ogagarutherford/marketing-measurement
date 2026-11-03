select
    order_id, customer_id, order_timestamp, cast(order_timestamp as date) as order_date, region,
    gross_revenue_eur, discount_eur, cogs_eur, shipping_cost_eur, payment_fee_eur, order_status
from {{ source('raw', 'raw_orders') }}
