# Caracterização e volume da carga

Medições da carga dos dados abertos da UnB no PostgreSQL. Os números aqui embasam o [ADR 1](adr/adr-1.md) e o [ADR 0003](adr/0003-validacao-de-volume-na-carga.md).

| Campo | Valor |
|---|---|
| Data da medição | 19/10/2026 |
| Commit medido | `[hash — rode git rev-parse --short HEAD]` |
| Ambiente | GitHub Codespaces — `[nº de núcleos (nproc) / RAM (free -h)]` |
| Banco | PostgreSQL 16.15 (Docker), migração `V1__esquema_inicial.sql` |

## Como reproduzir

```bash
docker compose down -v                      # começa do zero
docker compose up --build                   # baixa e carrega
docker compose run --rm ingest python inspecionar_bruto.py
docker compose run --rm ingest python medir_adr0001.py
du -sh dados/bruto/*
```

## 1. Camada bruta (`dados/bruto/`)

| Dataset | Arquivos baixados | Registros brutos | Tamanho em disco | Formatos de colunas | Falhas de download |
|---|---:|---:|---:|---:|---:|
| Empenhos | 89 | 890.000 | 743 MB | 1 | 0 |
| Requisições de serviços | 83 | 103.311 | 39 MB | 1 | 0 |
| Gastos por unidade | 51 | 95.837 | 13 MB | 1 | 0 |
| Estoque do almoxarifado | 89 | 79.164 | 12 MB | 1 | 0 |
| Unidades acadêmicas | 141 | 14.231 | 6,1 MB | 1 | 0 |
| **Total** | **453** | **1.182.543** | **≈ 813 MB** | | **0** |

Os arquivos vêm em JSON. Nenhum dataset mudou de esquema ao longo do tempo (um único formato de colunas por dataset).

**Empenhos são 91% do volume em disco.** Os 89 arquivos têm exatamente 10.000 registros cada, o que sugere um limite de exportação do portal (ver [Qualidade dos dados](#_5-qualidade-dos-dados)).

## 2. Arquivos distintos e republicações

O portal republica o mesmo mês várias vezes, com sufixo (ex.: `_07c0e994`). A carga identifica os arquivos pelo sha256 e carrega um por mês.

| Dataset | Arquivos baixados | Arquivos distintos carregados |
|---|---:|---:|
| Unidades | 141 | 12 |
| Estoque | 89 | 40 |
| Gastos | 51 | 39 |
| Empenhos | 89 | 46 |
| Requisições | 83 | 44 |
| **Total** | **453** | **181** |

Exemplo: os 4 arquivos de estoque de 11/2022 têm o mesmo md5 (`7f251675ae5fcb4219fb4edc6749c4db`).

## 3. Carga no banco

### Resultado da carga

| Dataset | Arquivos | Linhas lidas | Gravadas | Rejeitadas |
|---|---:|---:|---:|---:|
| Empenhos | 46 | 460.000 | 460.000 | 0 |
| Gastos | 39 | 73.034 | 73.034 | 0 |
| Requisições | 44 | 53.341 | 53.341 | 0 |
| Estoque | 40 | 41.116 | 41.116 | 0 |
| Unidades | 12 | 1.203 | 1.203 | 0 |

Nenhuma linha foi rejeitada. "Gravadas" conta inserções e atualizações: empenhos e requisições chegam como fotografias acumuladas, então a mesma entidade é atualizada a cada mês (ver seção 4).

### Linhas e tamanho por tabela

| Tabela | Linhas | Tamanho (com índices) |
|---|---:|---:|
| `empenho` | 21.324 | 20 MB |
| `gasto` | 73.034 | 11 MB |
| `estoque_saldo` | 41.116 | 6,5 MB |
| `credor` | 7.020 | 1,2 MB |
| `material` | 2.382 | 0,6 MB |
| `requisicao_servico` | 1.853 | 0,5 MB |
| `unidade` | 733 | 0,2 MB |
| `carga_execucao` | — | 136 kB |
| `natureza_despesa` | 58 | 48 kB |
| `almoxarifado` | 2 | 48 kB |
| `cotacao_online` | 0 | 24 kB |
| `carga_rejeitado` | 0 | 16 kB |
| **Total** | **≈ 148 mil** | **≈ 40 MB** |

**Redução de ≈ 813 MB brutos para ≈ 40 MB no banco (≈ 20×).** Ela vem da eliminação das republicações e das fotografias repetidas.

### Linhas por mês de referência

| Tabela | Meses | Primeiro | Último | Mediana linhas/mês | Máx. linhas/mês |
|---|---:|---|---|---:|---:|
| `estoque_saldo` | 40 | 09/2020 | 12/2025 | 758 | 1.933 |
| `gasto` | 39 | 09/2020 | 12/2025 | 1.884 | 2.223 |
| `empenho` | 87 | 10/2018 | 12/2025 | 205 | 911 |
| `requisicao_servico` | 83 | 02/2019 | 12/2025 | 17 | 93 |

## 4. Perfil da carga de trabalho

| Característica | Observação |
|---|---|
| Frequência de publicação na origem | Mensal, com lacunas (ex.: sem arquivos de 08–10/2022, 05–06/2024, 04–05/2025, 09/2025) |
| Natureza dos arquivos | Fotografias (*snapshots*) do estado no mês, não eventos |
| Estoque | 89% das linhas são idênticas às do mês anterior (34.285 de 38.733); só 6% dos pares material/almoxarifado (148 de 2.383) mudaram de preço ao longo do tempo |
| Gastos | Valor **acumulado no ano**: em 62.321 de 62.334 pares de meses seguidos (≈ 100%) o valor não diminui |
| Entidades que mudam de estado | Empenhos: 60% (12.735 de 21.324) atualizados depois da primeira carga; requisições: 14%; unidades: 4% |
| Operação predominante | Inserção mensal em lote + atualização de estado; leitura analítica |
| Crescimento estimado | ≈ 700–800 linhas/mês de estoque; ≈ 2.000 de gastos; ≈ 200 de empenhos |

### Medição das alternativas de modelagem do estoque (ADR 1)

Consultas repetidas: Q4 300 vezes com materiais sorteados (semente 2026), Q7 30 vezes. Tempo medido no cliente.

| Alternativa | Linhas | Tamanho | Q4 mediana / p95 | Q7 mediana / p95 |
|---|---:|---:|---:|---:|
| A — CRUD (opção nula) | 2.383 | 0,3 MB | 0,17 / 0,22 ms | não responde (histórico perdido) |
| B — *insert-only* | 41.116 | 6,5 MB | 0,22 / 0,27 ms | 6,9 / 7,2 ms |
| C — CRUD + histórico | 41.116 | 3,7 MB | 0,18 / 0,23 ms | 7,8 / 13,6 ms |

Na alternativa A, os preços antigos dos 148 pares que mudaram de preço seriam sobrescritos. Isso impede responder à pergunta de gestão, que compara preços ao longo do tempo.

## 5. Qualidade dos dados

### Quebra de patamar no estoque em 11/2022

- O estoque cai de **1.800 linhas (07/2022) para 830 (11/2022)** e segue estável depois disso (830 → 680 até 12/2025).
- A queda está concentrada no almoxarifado **PRC (1.660 → 695)**. O **Central** praticamente não muda (140 → 135).
- Entre os dois meses, **991 materiais sumiram e 21 apareceram**.
- **Não são itens zerados**: os materiais que sumiram tinham saldo positivo em 07/2022 (ex.: 2.000 L de álcool etílico no Central).
- A mudança acontece dentro de uma lacuna da origem (não há arquivos de 08, 09 e 10/2022), por isso aparece como um salto.
- A causa não foi identificada (baixa/inventário no PRC, mudança no critério do relatório ou extração parcial).
- A validação original recusava os 30 meses a partir de 11/2022. A correção está no [ADR 0003](adr/0003-validacao-de-volume-na-carga.md).

### Empenhos: possível truncamento em 10.000 registros

- Todos os 89 arquivos de empenhos têm **exatamente 10.000 registros**.
- Isso indica um limite de exportação do portal, não o total real de empenhos do mês.
- **Consequência:** meses antigos podem estar incompletos. A cobertura de 10/2018 a 2020 deve ser vista com cautela.
- **A verificar:** comparar com a API do portal, se houver paginação.

### Outras observações

| Item | Observação | Tratamento |
|---|---|---|
| Preço como texto | Ex.: `"R$             4,42"` | `normalizar.py` converte para número |
| Republicações idênticas | Até 8 arquivos com o mesmo conteúdo no mesmo mês | Deduplicação por sha256 |
| Mês sem data no nome | `materiais-estoques-de-almoxarifado.json` foi carregado como 09/2020 | `[confirmar se a data de referência está correta]` |
| Empenhos repetidos entre UGs | 52 pares (ano, número) aparecem em mais de uma unidade gestora (4 UGs) | A chave do empenho inclui a UG |
| Unidades por origem | 101 do cadastro, 632 criadas a partir de referências em outros datasets | Hierarquia corrigida na carga |
| Portal instável | Respostas 502 intermitentes | Até 5 tentativas por arquivo; nenhuma falha nesta medição |

## 6. Conclusões

1. **O volume é pequeno para o PostgreSQL**: cerca de 40 MB e 148 mil linhas. Desempenho não é o fator decisivo nesta etapa.
2. **A origem publica fotografias, não eventos**, com muita repetição (89% das linhas de estoque repetem o mês anterior). Por isso a deduplicação por hash e a modelagem do ADR 1 reduzem o volume em ≈ 20×.
3. **O histórico é indispensável para a pergunta de gestão**: sem ele (alternativa A), os preços antigos se perdem.
4. **A origem tem mudanças de patamar e lacunas.** A validação de volume deve avisar, não recusar (ADR 0003).
5. **Gastos são acumulados no ano**: para obter o valor do mês, é preciso subtrair o mês anterior.
6. **Empenhos podem estar truncados em 10.000 registros por arquivo.** Isso precisa ser verificado antes de usar empenhos em análises de volume.
