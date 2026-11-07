{% macro gerar_identificador(prefixo, numero) %}
    CASE
        WHEN ({{ numero }}) BETWEEN 1 AND 999 THEN
            (
                '{{ prefixo | lower }}'
                || LPAD(({{ numero }})::TEXT, 3, '0')
            )::CHAR(6)
        ELSE NULL
    END
{% endmacro %}