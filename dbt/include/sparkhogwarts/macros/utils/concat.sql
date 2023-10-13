{% macro sparkhogwarts__concat(fields) -%}
    concat({{ fields|join(', ') }})
{%- endmacro %}
