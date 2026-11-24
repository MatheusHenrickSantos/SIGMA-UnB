# Catálogo de dados (gerado)

> Gerado por `codigos/gerar_catalogo.py` a partir do manifesto do dbt. **Não edite à mão**: mude a descrição no `.yml` do modelo e gere de novo.

Modelos, sementes e snapshots: **26**. Fontes (tabelas escritas fora do dbt): **10**.

## Camada `bronze`

| Objeto | Tipo | Descrição | Colunas documentadas | Lê de | Lido por |
|---|---|---|:-:|---|---|
| `catmat_bronze` | model | Catálogo de Materiais (CATMAT), contendo informações de identificação, classificação e descrição dos materiais, além de seus atributos complementares. | 12 | `raw.catmat` | `catmat_classe_prata`, `catmat_grupo_prata`, `catmat_item_prata`, `catmat_pdm_prata` |
| `compras_bronze` | model | Compras públicas dos itens CATMAT aprovados na busca semântica, uma linha por registro da API de pesquisa de preços do Compras.gov.br, deduplicadas por id_item_compra. Mantém todas as datas baixadas. | 7 | `raw.compras` | `compra_publica_prata` |
| `estoque_bronze` | model | Dados de estoque dos almoxarifados da UnB, extraídos dos arquivos disponibilizados no portal de dados abertos e organizados em formato tabular. | 8 | `raw.estoque` | `almoxarifado_prata`, `estoque_prata`, `material_prata`, `qualidade_dados` |
| `excecoes_qualidade` | seed | Anomalias de dados já investigadas, que os testes singulares de qualidade (tests/) deixam passar. Cada linha diz qual teste, a chave da ocorrência e o motivo. Acrescente aqui só depois de conferir na origem. | 3 | — | — |
| `materiais_normalizados` | seed | Tabela auxiliar que relaciona as descrições originais dos materiais com suas respectivas descrições normalizadas. Gerada por um script Python a partir dos dados da Bronze. | 2 | — | `estoque_prata`, `material_prata` |

## Camada `prata`

| Objeto | Tipo | Descrição | Colunas documentadas | Lê de | Lido por |
|---|---|---|:-:|---|---|
| `almoxarifado_prata` | model | Cadastro dos almoxarifados identificados nos arquivos de estoque da UnB. | 2 | `estoque_bronze` | `dim_almoxarifado`, `estoque_prata` |
| `catmat_classe_prata` | model | Classes de materiais do CATMAT. | 3 | `catmat_bronze` | `dim_item_catmat` |
| `catmat_grupo_prata` | model | Grupos de materiais do CATMAT. | 2 | `catmat_bronze` | `dim_item_catmat` |
| `catmat_item_prata` | model | Itens do catálogo de materiais do CATMAT. | 4 | `catmat_bronze` | `dim_item_catmat` |
| `catmat_pdm_prata` | model | Padrões Descritivos de Materiais do CATMAT. | 3 | `catmat_bronze` | `dim_item_catmat` |
| `compra_publica_prata` | model | Compras públicas dos itens CATMAT aprovados, na janela de análise (vars compras_inicio e compras_fim) e com preço unitário positivo (Tabela 15 do dicionário de dados). | 6 | `compras_bronze` | `fato_comparacao_preco`, `monitor_atualizacao`, `qualidade_dados` |
| `estoque_prata` | model | Fotografia mensal da quantidade e do preço praticado para cada material em cada almoxarifado da UnB. | 6 | `estoque_bronze`, `materiais_normalizados`, `material_prata`, `almoxarifado_prata` | `dim_tempo`, `fato_comparacao_preco`, `qualidade_dados` |
| `material_prata` | model | Cadastro de materiais identificados a partir das descrições normalizadas encontradas nos arquivos de estoque da UnB. As descrições são obtidas por meio de uma tabela auxiliar de correspondências gerada por um script Pyth… | 4 | `estoque_bronze`, `materiais_normalizados` | `dim_material`, `estoque_prata` |

## Camada `ouro`

| Objeto | Tipo | Descrição | Colunas documentadas | Lê de | Lido por |
|---|---|---|:-:|---|---|
| `catalogo_metrica` | model | Definição de cada métrica (nome, tipo, unidade, versão, descrição e fórmula). | 0 | — | — |
| `dim_almoxarifado` | model | — | 0 | `almoxarifado_prata` | `alerta_preco_compras`, `metrica_mensal` |
| `dim_item_catmat` | model | Item CATMAT com PDM, classe e grupo. | 0 | `catmat_item_prata`, `catmat_pdm_prata`, `catmat_classe_prata`, `catmat_grupo_prata` | — |
| `dim_material` | model | Material com a correspondência ao CATMAT em SCD tipo 2: uma linha por versão (snap_correspondencia_material). Uma versão nova nasce quando mudam os itens equivalentes, a decisão "sem correspondente" ou quem decidiu. | 2 | `snap_correspondencia_material`, `material_prata` | `fato_comparacao_preco`, `metrica_mensal`, `qualidade_dados`, `resumo_correspondencia` |
| `dim_tempo` | model | Um mês por linha, do primeiro ao último mês com estoque. | 0 | `estoque_prata` | `qualidade_dados` |
| `fato_comparacao_preco` | model | GRÃO: uma linha por material, por almoxarifado, por mês de referência publicado. Preço registrado no estoque comparado com a mediana do preço das compras públicas dos itens CATMAT equivalentes (versão da correspondência … | 9 | `estoque_prata`, `dim_material`, `compra_publica_prata` | `alerta_preco_compras`, `metrica_mensal`, `monitor_atualizacao`, `qualidade_dados`, `resumo_correspondencia` |
| `metrica_mensal` | model | Camada semântica de métricas: uma linha por (métrica, mês, almoxarifado), com almoxarifado = 'TODOS' para o total. As fórmulas moram em macros/metricas.sql, versionadas; painel, qualidade_dados e ETL reverso leem daqui e… | 0 | `fato_comparacao_preco`, `dim_almoxarifado`, `dim_material` | `alerta_preco_compras`, `qualidade_dados` |
| `monitor_atualizacao` | model | Métrica de freshness e SLA das tabelas de consumo. Uma linha por tabela: último dado disponível, atraso em dias e situação diante do SLA declarado. | 0 | `fato_comparacao_preco`, `compra_publica_prata` | `qualidade_dados` |
| `qualidade_dados` | model | Registro de confiabilidade: uma linha por verificação (estoque, compras públicas, comparação e correspondência CATMAT) com valor medido, limites e situação (ok, atencao, critico, sem_dado). Não derruba o build; mede o qu… | 0 | `semantica.revisao_correspondencia`, `semantica.candidato_catmat`, `semantica.execucao_correspondencia`, `semantica.descricao`, `fato_comparacao_preco`, `metrica_mensal`, `estoque_bronze`, `estoque_prata`, `dim_tempo`, `compra_publica_prata`, `dim_material`, `monitor_atualizacao` | — |
| `resumo_correspondencia` | model | Uma linha por material (versão vigente): tipo de revisor, confiança, itens CATMAT, melhor candidato da busca, valor em estoque e prioridade de revisão. | 0 | `semantica.revisao_material`, `semantica.descricao`, `semantica.execucao_correspondencia`, `semantica.candidato_catmat`, `fato_comparacao_preco`, `dim_material` | `alerta_preco_compras` |
| `snap_correspondencia_material` | snapshot | — | 0 | `semantica.descricao`, `semantica.revisao_correspondencia`, `semantica.revisao_material` | `dim_material` |

## Camada `reverso`

| Objeto | Tipo | Descrição | Colunas documentadas | Lê de | Lido por |
|---|---|---|:-:|---|---|
| `acesso_almoxarifado` | seed | Quais almoxarifados cada usuário do grupo sigma_almoxarifado pode ver em reverso.alerta_preco_compras (recorte de linha por RLS). Um usuário sem linha aqui não vê nenhuma linha. | 0 | — | `alerta_preco_compras` |
| `alerta_preco_compras` | model | ETL reverso. Materiais do último mês com preço do estoque acima da mediana pública (referência robusta, correspondência não marcada como palpite). Lida pelo setor de compras e pelas chefias de almoxarifado; a coluna just… | 0 | `fato_comparacao_preco`, `metrica_mensal`, `dim_almoxarifado`, `resumo_correspondencia`, `acesso_almoxarifado` | — |

## Fontes escritas fora do dbt

| Fonte | Descrição |
|---|---|
| `raw.catmat` | — |
| `raw.compras` | — |
| `raw.estoque` | — |
| `semantica.candidato_catmat` | — |
| `semantica.descricao` | — |
| `semantica.embedding` | — |
| `semantica.execucao_correspondencia` | — |
| `semantica.modelo_embedding` | — |
| `semantica.revisao_correspondencia` | — |
| `semantica.revisao_material` | — |
