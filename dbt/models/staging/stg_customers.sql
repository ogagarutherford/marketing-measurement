select customer_id, cast(first_order_date as date) as first_order_date, home_region, email_opt_in
from {{ source('raw', 'raw_customers') }}
