{{ config(
    materialized = 'incremental',
    incremental_strategy = 'append',
    file_format = 'iceberg',
    tblproperties = { 'write.parquet.compression-codec': 'zstd' },
) }}

{% if not is_incremental() %}

select cast(1 as bigint) as id, 'hello' as msg
union all
select cast(2 as bigint) as id, 'goodbye' as msg

{% else %}

select cast(2 as bigint) as id, 'yo' as msg
union all
select cast(3 as bigint) as id, 'anyway' as msg

{% endif %}
