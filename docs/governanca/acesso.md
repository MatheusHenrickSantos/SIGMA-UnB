# Controle de acesso

Privilégio mínimo demonstrado em **um recorte de coluna e um de linha**, mais o isolamento por schema. Tudo é criado por migração (V11) e reaplicado pelo dbt a cada carga, porque o dbt recria as tabelas e elas perdem os `GRANT`.

## Papéis

Os papéis são grupos (`NOLOGIN`). Cada pessoa ou aplicação tem o seu usuário, que entra no grupo.

| Papel | Quem | Enxerga | Não enxerga |
|---|---|---|---|
| `sigma_painel` | O painel (Streamlit) | Schema `ouro`, só leitura | `raw`, `bronze`, `prata`, `semantica`, `reverso` |
| `sigma_compras` | Setor de compras | Todas as linhas de `reverso.alerta_preco_compras` | A coluna `justificativa_agente` (**recorte de coluna**); qualquer outro schema |
| `sigma_almoxarifado` | Chefias de almoxarifado | Só as linhas dos almoxarifados que o seu usuário tem em `reverso.acesso_almoxarifado` (**recorte de linha, RLS**) | A coluna `justificativa_agente`; qualquer outro schema |

O dono (usuário do dbt) escreve tudo e não é afetado pelas políticas de linha. Em produção ele não deve ser o usuário do painel nem dos consumidores.

## Como cada recorte é feito

```sql
-- coluna: GRANT por coluna, sem justificativa_agente (macros no post_hook de models/reverso/alerta_preco_compras.sql)
GRANT SELECT (mes_referencia, identificador_material, material, almoxarifado, ...)
  ON reverso.alerta_preco_compras TO sigma_compras, sigma_almoxarifado;

-- linha: RLS
ALTER TABLE reverso.alerta_preco_compras ENABLE ROW LEVEL SECURITY;
CREATE POLICY compras_ve_tudo ON reverso.alerta_preco_compras FOR SELECT TO sigma_compras USING (true);
CREATE POLICY almoxarifado_ve_o_seu ON reverso.alerta_preco_compras FOR SELECT TO sigma_almoxarifado
  USING (almoxarifado IN (SELECT almoxarifado FROM reverso.acesso_almoxarifado WHERE usuario = current_user));
```

Quem entra em `sigma_almoxarifado` mas não está em `seeds/acesso_almoxarifado.csv` não vê nenhuma linha (falha fechada).

## Demonstração

Executada em 24/11/2026, banco com o estoque real e compras sintéticas (ver [Consumo e ETL reverso](dados-e-pipeline/consumo-e-etl-reverso.md#medicoes)). Usuários `ana_compras` (em `sigma_compras`) e `joao_prc` (em `sigma_almoxarifado`, mapeado a `PRC`):

| Consulta | Usuário | Resultado |
|---|---|---|
| `SELECT count(*), count(DISTINCT almoxarifado) FROM reverso.alerta_preco_compras` | dono (dbt) | 91 linhas, 2 almoxarifados |
| idem | `ana_compras` | 91 linhas, 2 almoxarifados |
| `SELECT justificativa_agente FROM reverso.alerta_preco_compras` | `ana_compras` | `ERROR: permission denied for table alerta_preco_compras` |
| `SELECT count(*), min(almoxarifado), max(almoxarifado) FROM ...` | `joao_prc` | 80 linhas, só `PRC` |
| `SELECT count(*) FROM ouro.fato_comparacao_preco` | `joao_prc` | `ERROR: permission denied for schema ouro` |
| `SELECT count(*) FROM raw.estoque` | `joao_prc` | `ERROR: permission denied for schema raw` |
| `has_table_privilege('sigma_painel', ...)` | — | `ouro.fato_comparacao_preco`: sim; `raw.compras`: não; `reverso.alerta_preco_compras`: não |

Reproduzir (com o Compose no ar e a camada ouro construída):

```bash
docker compose exec db psql -U sigma -d sigma -c "
  CREATE ROLE ana_compras LOGIN PASSWORD 'troque' IN ROLE sigma_compras;
  CREATE ROLE joao_prc    LOGIN PASSWORD 'troque' IN ROLE sigma_almoxarifado;"
PGPASSWORD=troque psql -h localhost -U joao_prc -d sigma -c "SELECT almoxarifado, count(*) FROM reverso.alerta_preco_compras GROUP BY 1"
```

## O que ainda não está no privilégio mínimo

- O painel conecta como `sigma_painel_app` (V13, membro de `sigma_painel`), com senha em `SENHA_DO_PAINEL`. Testado: lê `ouro`; `prata` e `reverso` dão `permission denied`. Troque a senha padrão fora do ambiente local.
- As senhas dos usuários não são geridas pelo repositório (de propósito): criar fora da migração, com segredo do ambiente.
- `acesso_almoxarifado` é uma semente em CSV. Acima de ~20 usuários ou com rotatividade, mover para tabela mantida por aplicação (gatilho do [ADR 0012](adr/0012-governanca-lgpd-e-controle-de-acesso.md)).
