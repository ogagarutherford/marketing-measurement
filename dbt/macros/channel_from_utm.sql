{#- One channel definition for every source. GA4 sees source / medium / campaign; this maps them to the same
    channel names the spend data uses, so attribution and spend can be joined. -#}
{% macro channel_from_utm(source, medium, campaign) -%}
    case
        when {{ medium }} = 'paid_social' and {{ source }} = 'facebook' then 'Meta'
        when {{ medium }} = 'paid_social' and {{ source }} = 'tiktok'   then 'TikTok'
        when {{ medium }} = 'cpc' and {{ campaign }} = 'GADS_Brand'      then 'Google Brand Search'
        when {{ medium }} = 'cpc'                                        then 'Google Non-Brand Search'
        when {{ medium }} = 'display'                                    then 'DV360'
        when {{ medium }} = 'affiliate'                                  then 'Affiliate'
        when {{ medium }} = 'email'                                      then 'Email'
        when {{ medium }} = 'organic'                                    then 'Organic Search'
        when {{ source }} = '(direct)'                                   then 'Direct'
        else 'Other'
    end
{%- endmacro %}
