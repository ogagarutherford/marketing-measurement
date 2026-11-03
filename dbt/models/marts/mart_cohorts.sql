-- Grain: first-order month x months since first order. Retention and cumulative contribution per customer (LTV),
-- next to blended CAC (all marketing cost in the month / new customers), for payback.
with c as (select customer_id, first_order_month from {{ ref('dim_customers') }}),
o as (
    select f.customer_id, c.first_order_month,
           datediff('month', c.first_order_month, date_trunc('month', f.order_date)) as months_since,
           f.contribution_margin_eur, f.order_status
    from {{ ref('fct_orders') }} f join c using (customer_id)
),
sizes as (select first_order_month, count(*) as cohort_customers from c group by 1),
cac as (
    select date_trunc('month', spend_date) as first_order_month, sum(spend_eur) as marketing_cost_eur
    from {{ ref('fct_marketing_spend_daily') }} group by 1
),
monthly as (
    select first_order_month, months_since,
           count(distinct customer_id) filter (where order_status <> 'cancelled') as active_customers,
           sum(contribution_margin_eur) as contribution_margin_eur
    from o group by 1, 2
)

select
    m.first_order_month, m.months_since, s.cohort_customers, m.active_customers,
    m.active_customers * 1.0 / s.cohort_customers                                        as active_rate,
    sum(m.contribution_margin_eur) over (partition by m.first_order_month order by m.months_since)
        / s.cohort_customers                                                             as cumulative_cm_per_customer_eur,
    k.marketing_cost_eur / s.cohort_customers                                            as blended_cac_eur
from monthly m
join sizes s using (first_order_month)
join cac k using (first_order_month)
