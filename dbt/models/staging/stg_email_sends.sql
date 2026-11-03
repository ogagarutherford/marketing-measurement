select cast(send_date as date) as spend_date, campaign, recipients, esp_cost_eur
from {{ source('raw', 'raw_email_sends') }}
