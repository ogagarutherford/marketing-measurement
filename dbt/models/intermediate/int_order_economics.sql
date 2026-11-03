-- One row per order: net revenue and contribution margin.
-- Cancelled: no revenue, no costs. Returned: revenue and COGS reversed, shipping and payment fees still incurred.
select
    o.*,
    case when order_status = 'completed' then gross_revenue_eur - discount_eur else 0 end            as net_revenue_eur,
    case when order_status = 'completed' then cogs_eur else 0 end                                     as net_cogs_eur,
    case when order_status = 'cancelled' then 0 else shipping_cost_eur + payment_fee_eur end          as fulfilment_cost_eur
from {{ ref('stg_orders') }} o
