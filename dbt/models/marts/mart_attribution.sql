-- Grain: channel x attribution model. Credit per touch under four rule-based models (GA4-tracked orders only).
with paths as (select * from {{ ref('int_paths_numbered') }}),
orders as (select order_id, net_revenue_eur, contribution_margin_eur from {{ ref('fct_orders') }}),
weights as (
    select transaction_id, channel, 'last_click' as model, case when touch_sequence = path_length then 1.0 else 0 end as credit from paths
    union all
    select transaction_id, channel, 'first_click', case when touch_sequence = 1 then 1.0 else 0 end from paths
    union all
    select transaction_id, channel, 'linear', 1.0 / path_length from paths
    union all
    select transaction_id, channel, 'position_based',
           case when path_length = 1 then 1.0
                when path_length = 2 then 0.5
                when touch_sequence in (1, path_length) then 0.4
                else 0.2 / (path_length - 2) end
    from paths
)

select
    w.model, w.channel,
    sum(w.credit)                         as attributed_orders,
    sum(w.credit * o.net_revenue_eur)     as attributed_revenue_eur,
    sum(w.credit) / sum(sum(w.credit)) over (partition by w.model) as share_of_orders
from weights w
join orders o on o.order_id = w.transaction_id
group by 1, 2
