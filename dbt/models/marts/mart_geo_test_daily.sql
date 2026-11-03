-- Grain: state x day. Input to the geo test: orders and economics from the order system, Meta spend from the platform.
with orders as (
    select order_date as d, region, count(*) filter (where order_status <> 'cancelled') as orders,
           sum(net_revenue_eur) as net_revenue_eur, sum(contribution_margin_eur) as contribution_margin_eur
    from {{ ref('fct_orders') }} group by 1, 2
),
spend as (
    select spend_date as d, region,
           sum(spend_eur) filter (where channel = 'Meta') as meta_spend_eur,
           sum(spend_eur) as paid_media_spend_eur
    from {{ ref('fct_marketing_spend_daily') }} where region <> 'National' group by 1, 2
)

select
    o.d as date, o.region, r.geo_test_group, r.pair_id, r.population_m,
    case when o.d >= cast('{{ var("geo_test_start") }}' as date) and o.d <= cast('{{ var("geo_test_end") }}' as date) then 'test'
         when o.d >= cast('{{ var("geo_pre_start") }}' as date) and o.d < cast('{{ var("geo_test_start") }}' as date) then 'pre'
         else 'outside' end as period,
    o.orders, o.net_revenue_eur, o.contribution_margin_eur,
    coalesce(s.meta_spend_eur, 0) as meta_spend_eur, coalesce(s.paid_media_spend_eur, 0) as paid_media_spend_eur
from orders o
join {{ ref('dim_regions') }} r using (region)
left join spend s on s.d = o.d and s.region = o.region
