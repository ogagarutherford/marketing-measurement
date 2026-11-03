-- One row per customer, with the first-touch channel of their first order when GA4 tracked it.
with first_orders as (
    select customer_id, order_id, order_date from {{ ref('fct_orders') }} where customer_order_number = 1
),
first_touch as (
    select transaction_id, channel from {{ ref('int_paths_numbered') }} where touch_sequence = 1
)

select
    c.customer_id, c.first_order_date, date_trunc('month', c.first_order_date) as first_order_month,
    c.home_region, c.email_opt_in,
    coalesce(ft.channel, 'Untracked') as first_touch_channel
from {{ ref('stg_customers') }} c
left join first_orders fo using (customer_id)
left join first_touch ft on ft.transaction_id = fo.order_id
