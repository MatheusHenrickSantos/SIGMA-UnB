# Catálogo de dados e linhagem

Quem olha um número no painel precisa conseguir seguir a coluna até a fonte pública. Esta página dá o caminho completo; o [catálogo gerado](governanca/catalogo-gerado.md) lista cada modelo, coluna documentada e dependência, direto do dbt.

## Do dado público ao consumo

```text
 FONTES PÚBLICAS                  RAW            BRONZE          PRATA              BUSCA / REVISÃO        OURO                       CONSUMO
┌───────────────────────┐       ┌────────┐     ┌──────────┐    ┌───────────────┐   ┌─────────────────┐   ┌──────────────────────┐   ┌────────────────────┐
│ dados.unb.br (CKAN)   │──────▶│ estoque│────▶│ estoque  │───▶│ estoque       │   │                 │   │ fato_comparacao_preco│──▶│ painel (Streamlit) │
│ estoque-do-almoxarif. │       └────────┘     └──────────┘    │ material      │   │                 │   │ dim_material (SCD 2) │   │  KPIs, séries,     │
├───────────────────────┤       ┌────────┐     ┌──────────┐    │ almoxarifado  │   │ embeddings,     │   │ dim_almoxarifado     │   │  busca de produto  │
│ Compras.gov.br        │──────▶│ catmat │────▶│ catmat   │───▶│ catmat_item.. │──▶│ candidatos,     │──▶│ dim_tempo            │   ├────────────────────┤
│ módulo material (CATMAT)│     └────────┘     └──────────┘    └───────────────┘   │ decisões (agente│   │ dim_item_catmat      │──▶│ ETL reverso        │
├───────────────────────┤       ┌────────┐     ┌──────────┐    ┌───────────────┐   │ ou pessoa)      │   │ metrica_mensal       │   │  reverso.alerta_.. │
│ Compras.gov.br        │──────▶│ compras│────▶│ compras  │───▶│ compra_publica│   └─────────────────┘   │ catalogo_metrica     │   │  CSV em dados/saida│
│ módulo pesquisa preço │       └────────┘     └──────────┘    └───────────────┘                         │ qualidade_dados      │   └────────────────────┘
└───────────────────────┘                                                                                  │ resumo_correspondencia│
                                                                                                           └──────────────────────┘
```

Detalhes que costumam ser esquecidos:

- **OLTP.** O pipeline atual **não passa** pelo OLTP da E1 (esquema da migração V1): a raw recebe direto da fonte pública. O OLTP continua como modelo transacional entregue na E1/E2, mas nenhum número do painel depende dele. A volta ao "operacional" da E4 é a tabela `reverso.alerta_preco_compras` e o CSV de [ETL reverso](dados-e-pipeline/consumo-e-etl-reverso.md).
- **A correspondência material × CATMAT** não vem de uma fonte: vem da busca (embeddings + trigramas) e das decisões de agentes de IA ou de pessoas, versionadas no snapshot `snap_correspondencia_material` (SCD tipo 2). Por isso toda linha do fato aponta para a **versão** da correspondência usada (`sk_material`).
- **As definições das métricas** ficam em `macros/metricas.sql` (versionadas) e saem em `ouro.catalogo_metrica`.

## Linhagem de coluna: do painel à fonte

| O que o painel mostra | Lê de | Calculado como | Origem na prata | Fonte pública |
|---|---|---|---|---|
| **Valor em estoque** | `ouro.metrica_mensal` (`valor_estoque`) | soma de `valor_estoque` do fato | `prata.estoque.quantidade × preco` | `dados.unb.br`, dataset `estoque-do-almoxarifado` (campos `saldo`, `preco`) |
| **Com item CATMAT / com preço público** | `metrica_mensal` (`cobertura_item_catmat_pct`, `cobertura_preco_publico_pct`) | razões entre contagens do fato | `dim_material.codigos_equivalentes` (snapshot da correspondência) e `prata.compra_publica` | estoque + CATMAT (`modulo-material/4_consultarItemMaterial`) + compras (`modulo-pesquisa-preco/1_consultarMaterial`) |
| **Valor comparável** | `metrica_mensal` (`valor_comparavel_pct`) | `valor_com_preco_publico ÷ valor_estoque` | idem | idem |
| **Economia potencial / Materiais alertados** | `metrica_mensal`; as mesmas linhas vão a `reverso.alerta_preco_compras` | `condicao_alerta` em `macros/metricas.sql` | `fato.preco_estoque`, `fato.preco_publico_mediano`, `fato.compras_publicas` | estoque (`preco`) e compras (`precoUnitario`, `idItemCompra`) |
| **Preço público (mediana)** | `fato_comparacao_preco.preco_publico_mediano` | `PERCENTILE_CONT(0,5)` de `compra_publica.preco_unitario` dos itens equivalentes | `prata.compra_publica` ← `bronze.compras` | `precoUnitario` da API de pesquisa de preços |
| **Diferença (%)** | `fato.diferenca_pct` | `(preco_estoque ÷ preco_publico_mediano − 1) × 100` | idem | idem |
| **Confiabilidade (selos)** | `ouro.qualidade_dados` | verificações com limites; as de comparação leem `metrica_mensal` | `bronze`, `prata`, `dim_tempo`, snapshot | todas |
| **Fila de conferência** | `ouro.resumo_correspondencia` | decisão vigente + valor em estoque do último mês | `prata.revisao_*`, `prata.candidato_catmat` | decisões de agentes (`decisoes_agentes.csv`) e de pessoas |

## Como reproduzir e manter

```bash
dbt parse --profiles-dir . --project-dir .
python codigos/gerar_catalogo.py        # atualiza docs/governanca/catalogo-gerado.md
```

- Cada modelo novo precisa de `description` no `.yml`; é o que aparece no catálogo.
- A coluna **Colunas documentadas** do catálogo mostra onde falta documentação.
- O `dbt docs generate` produz a versão navegável (grafo de linhagem por modelo) a partir do mesmo manifesto.

## Qualidade e frescor como parte do catálogo

`ouro.monitor_atualizacao` (SLA) e `ouro.qualidade_dados` (verificações) são tabelas do próprio catálogo: dizem se o dado que se está lendo é confiável *agora*. Os limites e a análise estão em [Confiabilidade dos dados](dados-e-pipeline/confiabilidade.md).
