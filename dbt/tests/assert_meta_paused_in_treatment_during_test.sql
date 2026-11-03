-- Fails if any treatment state shows Meta spend during the geo test (the experiment was not implemented as designed).
select * from {{ ref('mart_geo_test_daily') }}
where geo_test_group = 'treatment' and period = 'test' and meta_spend_eur > 0
