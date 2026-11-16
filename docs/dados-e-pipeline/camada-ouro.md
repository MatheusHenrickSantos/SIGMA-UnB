# Camada ouro: modelo analítico

A camada ouro responde à pergunta de gestão da E1: para quais materiais do
estoque existe preço de compras públicas comparável e quais têm as maiores
diferenças, por almoxarifado e período. Decisão e alternativas:
[ADR 0007](adr/0007-modelo-estrela-para-comparacao-de-precos.md).

Tudo em dbt (`models/ouro/`, `snapshots/`), construído pelo serviço
`transformar_ouro` depois da busca semântica e das compras.

## Modelo estrela

```text
                      dim_tempo (mes_referencia)
                               │
dim_almoxarifado ──── fato_comparacao_preco ──── dim_material (SCD tipo 2)
                                                     │  codigos_equivalentes
                                                     └─ dim_item_catmat (codigo_item)
```

| Tabela | Grão | Linhas (10/11/2026) |
|---|---|---|
| `ouro.fato_comparacao_preco` | **uma linha por material, por almoxarifado, por mês de referência publicado** | 39.176 |
| `ouro.dim_material` | uma linha por versão da correspondência material × CATMAT | 2.306 + versões |
| `ouro.dim_almoxarifado` | um almoxarifado | 2 |
| `ouro.dim_tempo` | um mês, do primeiro ao último com estoque (`publicado` indica se há arquivo) | 55 |
| `ouro.dim_item_catmat` | um item CATMAT com PDM, classe e grupo | 346.140 |
| `ouro.monitor_atualizacao` | uma tabela de consumo (freshness e SLA) | 2 |

Medidas do fato: `quantidade`, `preco_estoque` (média ponderada pela
quantidade), `valor_estoque`, `preco_publico_mediano` (mediana das compras
públicas dos itens equivalentes), `compras_publicas`,
`unidade_fornecimento_predominante`, `diferenca_absoluta`, `diferenca_pct` e
`tipo_revisor_correspondencia` (pessoa, agente ou sem decisão).

**Cuidado com a soma.** `quantidade` e `valor_estoque` são saldos (fotografia
do mês): somam entre almoxarifados no mesmo mês, **nunca entre meses**.

## Dimensão de variação lenta: correspondência material × CATMAT

A correspondência muda: um agente de IA sugere, uma pessoa confirma ou
corrige. Sobrescrever apagaria qual item sustentava uma comparação já
publicada. `snapshots/snap_correspondencia_material.sql` (dbt snapshot,
estratégia `check` sobre itens equivalentes, "sem correspondente" e tipo de
revisor) guarda cada versão com `dbt_valid_from`/`dbt_valid_to`;
`dim_material` expõe `sk_material`, `valido_de`, `valido_ate` e `atual`.

O fato é **incremental por mês**: uma execução comum só insere meses novos, e
cada linha guarda o `sk_material` da versão vigente quando foi carregada.

### Demonstração (banco do compose, dados reais, 10/11/2026)

Registramos, no banco de teste, uma decisão de pessoa que acrescenta um item
equivalente ao material `ma0092` (álcool etílico 70% gel, galão 5 L), cuja
correspondência tinha sido decidida por agente. Depois do `dbt build`:

```text
--- dim_material: versões do material ma0092
 codigos_equivalentes | tipo_revisor |         valido_de          |         valido_ate         | atual
----------------------+--------------+----------------------------+----------------------------+-------
 269943               | agente       | 2026-11-10 14:28:12.681729 | 2026-11-10 14:29:06.996259 | f
 269943|273231        | pessoa       | 2026-11-10 14:29:06.996259 | 9999-12-31 00:00:00        | t

--- fato: linhas do ma0092 (execução incremental: nenhum mês novo, INSERT 0 0)
 mes_referencia | codigos_equivalentes | tipo_revisor | preco_publico_mediano | compras_publicas
----------------+----------------------+--------------+-----------------------+------------------
 2025-10-01     | 269943               | agente       |                7.5400 |              305
 2025-11-01     | 269943               | agente       |                7.5400 |              305
 2025-12-01     | 269943               | agente       |                7.5400 |              305
```

A versão antiga foi fechada, não apagada, e as linhas já carregadas seguem
apontando para ela. Para recalcular um mês com a correspondência atual, faz-se
o **backfill** daquele mês:

```bash
dbt build --select fato_comparacao_preco --vars '{mes_referencia: "2025-12-01"}'
# 1 of 13 OK created sql incremental model ouro.fato_comparacao_preco ... [INSERT 0 680]
```

```text
 mes_referencia | codigos_equivalentes | tipo_revisor | preco_publico_mediano | compras_publicas
----------------+----------------------+--------------+-----------------------+------------------
 2025-10-01     | 269943               | agente       |                7.5400 |              305
 2025-11-01     | 269943               | agente       |                7.5400 |              305
 2025-12-01     | 269943|273231        | pessoa       |                7.5200 |              328
```

Só 12/2025 foi refeito (680 linhas, delete+insert); outubro e novembro
mantiveram a versão com que foram calculados. O backfill pela orquestração
está em [Orquestração](dados-e-pipeline/orquestracao.md).

## Testes de dados

Além dos testes de esquema, unicidade e integridade referencial dos modelos
(`models/**/*.yml`), os testes singulares em `tests/` verificam o que o
domínio tem de sujo. Ocorrências já investigadas ficam em
`seeds/excecoes_qualidade.csv`, com o motivo; qualquer outra derruba o build.

| Teste | Tipo | O que pega | Resultado em 10/11/2026 |
|---|---|---|---|
| `volume_estoque_mensal` | volume | linhas de um almoxarifado variando mais de 30% entre meses publicados | 1 ocorrência (PRC 11/2022: 1.660 → 695), registrada como exceção |
| `distribuicao_salto_preco_estoque` | distribuição | preço do mesmo material multiplicado ou dividido por 5+ entre meses | 2 ocorrências reais (máscara 18,00 → 2,60; papel almaço 7,15 → 63,56), registradas |
| `distribuicao_preco_compra_publica` | distribuição | mais de 8% das compras a mais de 10× da mediana do próprio código | 5,86% (passa) |
| `preco_estoque_positivo` | domínio | preço ≤ 0 no estoque (aviso a partir de 1, erro acima de 5) | 1 aviso (avental, 07/2022) |
| `serie_material_some_e_volta` | domínio | material que some num mês e reaparece no seguinte (aviso; erro acima de 200) | 55 avisos |
| `unique_combination` no fato | grão | uma linha por material × almoxarifado × mês | passa |
| `relationships` do fato | integridade | fato → `dim_material` (versão), `dim_almoxarifado`, `dim_tempo` | passa |
| `accepted_range` no fato | domínio | `preco_estoque > 0`, `quantidade >= 0` | passa |

## Freshness e SLA

**SLA declarado:** o estoque do mês M deve estar em `ouro.fato_comparacao_preco`
até **45 dias** depois do fim de M (o portal publica o arquivo do mês no mês
seguinte). As compras públicas, até 60 dias depois do fim da janela.

Duas medições:

- `dbt source freshness` sobre `raw` (`models/fontes.yml`): estoque avisa a 45
  e falha a 75 dias; CATMAT e compras pela data de inserção (35/60 dias);
- a tabela `ouro.monitor_atualizacao`, recalculada a cada carga, com último
  dado, atraso em dias e situação diante do SLA (é o que o painel mostra).

Medição de 10/11/2026:

```text
 freshness of raw.catmat  ... PASS
 freshness of raw.compras ... PASS
 freshness of raw.estoque ... ERROR STALE

           tabela           | ultimo_dado | atraso_dias | sla_dias | situacao_sla
----------------------------+-------------+-------------+----------+--------------
 prata.compra_publica       | 2025-12-31  |         314 |       60 | fora do SLA
 ouro.fato_comparacao_preco | 2025-12-31  |         314 |       45 | fora do SLA
```

O alerta é verdadeiro e vem da origem: o conjunto "Estoque do Almoxarifado"
do portal dados.unb.br foi modificado pela última vez em 17/12/2025 e o
arquivo mais recente é o de 12/2025. Sem a métrica, o painel mostraria 12/2025
como se fosse o dado atual.
