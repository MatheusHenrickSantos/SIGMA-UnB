{% macro gerar_identificador(prefixo, numero) %}
    CASE
        WHEN ({{ numero }}) BETWEEN 1 AND 9999 THEN
            (
                '{{ prefixo | lower }}'
                || LPAD(({{ numero }})::TEXT, 4, '0')
            )::CHAR(6)
        ELSE NULL
    END
{% endmacro %}