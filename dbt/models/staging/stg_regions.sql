select region, region_code, population_m, urban_share, geo_test_group, pair_id
from {{ source('raw', 'raw_regions') }}
