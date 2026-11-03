-- Grain: one row per order. Contribution margin before marketing; new vs returning; tracked in GA4 or not.
with numbered as (
    select *, row_number() over (partition by customer_id order by order_timestamp, order_id) as customer_order_number
    from {{ ref('int_order_economics') }}
),
tracked as (select distinct transaction_id from {{ ref('stg_ga4_conversion_paths') }})

select
    n.order_id, n.customer_id, n.order_timestamp, n.order_date, date_trunc('week', n.order_date) as order_week,
    n.region, n.order_status, n.gross_revenue_eur, n.discount_eur, n.net_revenue_eur, n.net_cogs_eur, n.fulfilment_cost_eur,
    n.net_revenue_eur - n.net_cogs_eur - n.fulfilment_cost_eur      as contribution_margin_eur,
    n.customer_order_number,
    n.customer_order_number = 1                                     as is_new_customer,
    t.transaction_id is not null                                    as is_tracked_in_ga4
from numbered n
left join tracked t on t.transaction_id = n.order_id
