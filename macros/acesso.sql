{#- Reaplica as permissões do painel depois de cada execução do dbt (as tabelas
    são recriadas e perdem os GRANTs). Só age se o papel existir (V11). -#}
{% macro conceder_leitura_painel() %}
  {% if execute %}
    {% set sql %}
      DO $$
      BEGIN
        IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sigma_painel') THEN
          GRANT USAGE ON SCHEMA ouro TO sigma_painel;
          GRANT SELECT ON ALL TABLES IN SCHEMA ouro TO sigma_painel;
        END IF;
      END
      $$;
    {% endset %}
    {% do run_query(sql) %}
  {% endif %}
{% endmacro %}
