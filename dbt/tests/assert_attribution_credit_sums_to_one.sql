-- Fails if any model gives an order more or less than 1.0 total credit.
with paths as (select * from {{ ref('int_paths_numbered') }}),
w as (
    select transaction_id, 'linear' as model, sum(1.0 / path_length) as credit from paths group by 1
    union all
    select transaction_id, 'position_based', sum(case when path_length = 1 then 1.0 when path_length = 2 then 0.5
                                                       when touch_sequence in (1, path_length) then 0.4
                                                       else 0.2 / (path_length - 2) end) from paths group by 1
)
select * from w where abs(credit - 1.0) > 0.0001
