-- Grain: week. Attribution-free efficiency: MER, blended CAC and contribution after marketing.
with o as (
    select order_week as week, sum(net_revenue_eur) as revenue_eur, sum(contribution_margin_eur) as cm_eur,
           count(*) filter (where is_new_customer) as new_customers,
           count(*) filter (where order_status <> 'cancelled') as orders,
           count(*) filter (where is_tracked_in_ga4) as ga4_tracked_orders
    from {{ ref('fct_orders') }} group by 1
),
s as (
    select date_trunc('week', spend_date) as week, sum(spend_eur) as marketing_cost_eur,
           sum(platform_conversions) as platform_claimed_conversions
    from {{ ref('fct_marketing_spend_daily') }} group by 1
)

select
    o.week, o.orders, o.revenue_eur, o.cm_eur, o.new_customers, s.marketing_cost_eur,
    o.revenue_eur / nullif(s.marketing_cost_eur, 0)          as mer,
    s.marketing_cost_eur / nullif(o.new_customers, 0)        as blended_cac_eur,
    o.cm_eur - s.marketing_cost_eur                          as contribution_after_marketing_eur,
    s.platform_claimed_conversions, o.ga4_tracked_orders
from o join s using (week)
