# Fontes de dados e histórico da origem

## Fontes

Os cinco datasets foram coletados do [Portal de Dados Abertos da UnB](https://dados.unb.br/). **Esta versão documenta o conteúdo exato de `manifesto (3).json`**, produzido em **19/10/2026 às 14:31:48 UTC** (`coletado_em`). O manifesto relaciona recursos **JSON**; não há evidência nesse arquivo de que a coleta auditada tenha sido em CSV. A presença de recurso no manifesto comprova seu inventário com metadados, não a carga aceita no PostgreSQL. A CPDA consta como autora de quatro dicionários, mas isso não confirma a unidade institucional mantenedora de cada dataset.

| Dataset | URL no portal | Responsável identificado | Formato inventariado | Atualização / histórico no manifesto | Licença |
|---|---|---|---|---|---|
| Estoque do almoxarifado | https://dados.unb.br/dataset/estoque-do-almoxarifado | UnB (CPDA autora do dicionário quando informada; responsável operacional não confirmado) | **JSON** | 39 competências nomeadas (2021-06 a 2025-12); 89 recursos JSON; atualizações irregulares no recorte | A confirmar nos metadados de licença do portal |
| Unidades acadêmicas | https://dados.unb.br/dataset/unidades-academicas | UnB (CPDA autora do dicionário quando informada; responsável operacional não confirmado) | **JSON** | 35 competências nomeadas (2022-02 a 2025-12); 141 recursos JSON; atualizações irregulares no recorte | A confirmar nos metadados de licença do portal |
| Empenhos | https://dados.unb.br/dataset/empenhos | UnB (CPDA autora do dicionário quando informada; responsável operacional não confirmado) | **JSON** | 37 competências nomeadas (2021-06 a 2025-12); 89 recursos JSON; atualizações irregulares no recorte | A confirmar nos metadados de licença do portal |
| Gastos por unidade | https://dados.unb.br/dataset/gastos-por-unidade | UnB (CPDA autora do dicionário quando informada; responsável operacional não confirmado) | **JSON** | 38 competências nomeadas (2021-07 a 2025-12); 51 recursos JSON; atualizações irregulares no recorte | A confirmar nos metadados de licença do portal |
| Requisições de serviços | https://dados.unb.br/dataset/requisicoes-de-servicos | UnB (CPDA autora do dicionário quando informada; responsável operacional não confirmado) | **JSON** | 39 competências nomeadas (2021-07 a 2025-12); 83 recursos JSON; atualizações irregulares no recorte | A confirmar nos metadados de licença do portal |
| Preços de mercado (**fonte futura**) | Não definida | A definir | A definir | Coleta semanal prevista, sem base conectada | A definir conforme fonte |

**Rastreabilidade por recurso:** cada entrada de `datasets.<dataset>.arquivos[]` inclui `arquivo` (caminho relativo), `nome_no_portal`, `formato`, `url` direta, `modificado_no_portal`, `bytes` e `sha256`. Cada dataset contém a lista `falhas`, vazia neste manifesto. Isso **não equivale** a zero erros de parsing, validação ou carga relacional. O manifesto registra um único instante global de coleta, não uma data individual de download por arquivo. O inventário completo de URLs e hashes permanece no próprio JSON, evitando reproduzir centenas de registros aqui.

## Dicionário de colunas da origem

As colunas abaixo reproduzem os **nomes e tipos descritos nos cinco dicionários fornecidos** (versão 1.0, setembro de 2020), antes de normalizações do pipeline. O dicionário do modelo final está em [Dicionário de Dados](modelagem/dicionario-de-dados.md).

### Estoque do almoxarifado

| Coluna | Tipo declarado | Significado / atenção |
|---|---|---|
| `material` | Texto | Descrição resumida do material/serviço; não é identificador estável documentado. |
| `almoxarifado` | Texto | Nome do almoxarifado. |
| `saldo` | Inteiro | Quantidade em estoque. |
| `preco` | Inteiro | Preço praticado do material; confirmar escala monetária e caráter unitário em dados reais. |
| `valor_total` | Inteiro; opcional | Valor total do material em estoque; verificar a relação com preço e saldo. |

**Granularidade a validar:** item descrito por `material` em um `almoxarifado` e um arquivo de referência. **Não há coluna de data ou código único do material no dicionário**; a competência temporal precisa vir do nome/metadados do recurso ou de outra fonte validada. É a principal série para o ranking de variação percentual anualizada de 2021–2025.

### Unidades acadêmicas

| Coluna(s) | Tipo declarado | Significado |
|---|---|---|
| `id_unidade` | Inteiro | Identificador da unidade. |
| `nome`, `sigla`, `sigla_academica` | Texto | Denominações e siglas. |
| `id_unidade_responsavel`, `unidade_responsavel` | Inteiro, Texto; opcionais | Vínculo hierárquico da unidade responsável. |
| `id_unidade_gestora`, `unidade_gestora` | Inteiro, Texto; opcionais | Unidade gestora. |
| `id_gestora_academica`, `unidade_gestora_academica` | Inteiro, Texto; opcionais | Gestão acadêmica. |
| `tipo_organizacional`, `tipo_academica` | Texto | Classificação da unidade. |

**Atenção:** sem campos de início/fim de vigência no dicionário; o histórico de mudanças de nome, sigla ou hierarquia depende da preservação de versões de extração.

### Gastos por unidade

| Coluna | Tipo declarado | Significado |
|---|---|---|
| `id_unidade` | Inteiro | Identificador da unidade. |
| `unidade` | Texto | Nome da unidade. |
| `natureza_despesa` | Texto | Elemento/natureza da despesa. |
| `valor` | Inteiro | Valor da operação; confirmar escala/unidade monetária. |

**Atenção:** o dicionário não informa data, ano nem código de empenho/material. Não atribuir temporalidade ao registro sem evidência dos recursos publicados.

### Empenhos

| Coluna(s) | Tipo declarado | Significado |
|---|---|---|
| `cod_empenho` | Inteiro | Identificação do empenho no SIAFE. |
| `ano` | Inteiro | Ano de emissão. |
| `modalidade` | Texto | Modalidade do empenho. |
| `id_unidade_gestora`, `nome_unidade_gestora` | Inteiro, Texto | Unidade gestora. |
| `data` | Data | Data de emissão. |
| `programa_trabalho_resumido`, `fonte_recurso`, `plano_interno`, `esfera`, `natureza_despesa` | Texto | Classificações orçamentárias. |
| `credor` | Texto | Credor/fornecedor do empenho. |
| `valor_empenho`, `saldo_empenho` | Decimal | Valor e saldo do empenho. |
| `valor_reforcado`, `valor_anulado`, `valor_cancelado` | Decimal; opcionais | Ajustes do empenho. |
| `processo`, `documento_associado`, `licitacao`, `convenio`, `observacoes` | Texto; opcionais | Referências administrativas e observações. |

**Atenção:** não existe campo `material` nem chave de item do almoxarifado no dicionário. A análise inicial prevê somente um fornecedor; a **concentração dos empenhos por fornecedor e por material é objetivo futuro**, dependente de vários fornecedores e vínculo demonstrado entre as bases. Recursos mensais podem trazer registros históricos repetidos: não somar snapshots do mesmo empenho como novas operações sem verificar sua semântica.

### Requisições de serviços

| Coluna(s) | Tipo declarado | Significado |
|---|---|---|
| `numero`, `ano` | Inteiro | Número e ano de cadastro da requisição. |
| `tipo`, `status` | Texto | Tipo e situação. |
| `id_unidade_requisitante`, `nome_unidade_requisitante` | Inteiro, Texto | Unidade solicitante. |
| `id_unidade_custo`, `nome_unidade_custo` | Inteiro, Texto | Unidade responsável pelo custo. |
| `data_envio` | Texto; opcional | Data do último envio (tipo declarado como texto). |
| `data_autorizacao_chefe` | Data; opcional | Data de autorização. |
| `observacoes` | Texto; opcional | Observações. |

**Atenção:** trata de **serviços**, não de uma lista de itens de material do almoxarifado. Não usar como relação direta entre material e empenho.

## Histórico da origem

### Inventário reproduzível da coleta de 19/10/2026

O manifesto fornecido contém **453 recursos JSON** no total. As competências foram extraídas do padrão `MM-AAAA` do caminho dos arquivos; são **competências indicadas pelo nome**, não datas de observação comprovadas no conteúdo. Recursos de uma mesma competência podem ter hashes iguais (cópias idênticas) ou diferentes (versões distintas). Os totais de hashes únicos abrangem todo o dataset, e não apenas os recursos de uma mesma competência.

| Dataset | Recursos | Competências distintas no nome | SHA-256 distintos | Recursos adicionais de competências repetidas | Competências com versões de hash diferentes | Sem competência no nome |
|---|---:|---:|---:|---:|---:|---:|
| Estoque do almoxarifado | 89 | 39 | 49 | 49 | 4 | 1 |
| Unidades acadêmicas | 141 | 35 | 12 | 106 | 1 | 0 |
| Empenhos | 89 | 37 | 46 | 52 | 5 | 0 |
| Gastos por unidade | 51 | 38 | 48 | 12 | 4 | 1 |
| Requisições de serviços | 83 | 39 | 44 | 44 | 4 | 0 |
| **Total** | **453** | — | — | — | — | **2** |

**Cobertura da fonte para o objetivo 2021–2025:** no estoque há **39 competências identificadas**, de **junho/2021 a dezembro/2025**, distribuídas em 2021: 4, 2022: 6, 2023: 10, 2024: 10 e 2025: 9. Portanto, o inventário **não apresenta todos os 60 meses** do recorte; são 21 meses sem recurso nomeado correspondente, além do recurso legado `materiais-estoques-de-almoxarifado.json`, sem competência explícita. As ausências no manifesto não demonstram, por si, inexistência absoluta do recurso no portal. Verificar também os **30 meses rejeitados na carga de estoque**, conforme backlog: é outro problema, distinto das lacunas do inventário.

**Competências não encontradas no inventário de estoque (2021–2025):**

- 2021: janeiro–maio, julho, novembro e dezembro.
- 2022: janeiro, abril, agosto–outubro e dezembro.
- 2023: janeiro e fevereiro.
- 2024: maio e junho.
- 2025: abril, maio e setembro.

### Histórico de versões e mudanças observáveis

- **Estoque do almoxarifado:** `2023-03` (4 hashes, 8 recursos), `2024-07` (5 hashes, 6 recursos), `2025-06` (2 hashes, 6 recursos), `2025-10` (2 hashes, 4 recursos).
- **Unidades acadêmicas:** `2024-07` (2 hashes, 12 recursos).
- **Empenhos:** `2022-11` (2 hashes, 5 recursos), `2023-03` (4 hashes, 8 recursos), `2024-07` (3 hashes, 11 recursos), `2025-06` (2 hashes, 8 recursos), `2025-10` (3 hashes, 6 recursos).
- **Gastos por unidade:** `2023-03` (6 hashes, 8 recursos), `2024-07` (3 hashes, 3 recursos), `2025-06` (2 hashes, 3 recursos), `2025-10` (2 hashes, 2 recursos).
- **Requisições de serviços:** `2023-03` (2 hashes, 8 recursos), `2024-07` (3 hashes, 6 recursos), `2025-06` (2 hashes, 5 recursos), `2025-10` (2 hashes, 4 recursos).

**Exemplos verificáveis de versão:**

- Estoque de **agosto/2021** aparece em dois recursos com o mesmo SHA-256 `115ec67e0641884800875ae1882754cfd1d4e0c1e2d5fdb578aa4a4fef803174` (duplicação idêntica).
- Estoque de **março/2023** aparece com quatro conteúdos distintos por SHA-256 na mesma competência (versões efetivamente diferentes, não somar todas como quatro meses).
- Estoque de **julho/2024** tem cinco hashes diferentes entre seis recursos; a seleção de uma versão mensal precisa de regra documentada e preservação das anteriores.
- Estoque de **outubro/2025** também apresenta duas versões de conteúdo; a data `modificado_no_portal` auxilia na ordenação, mas não substitui a interpretação da competência nem demonstra quando o dado foi gerado internamente.

**Estratégia recomendada (a implementar/confirmar):** preservar os arquivos por URL/ID e SHA-256, registrar a competência extraída e a data de modificação, identificar equivalências por hash e definir **uma versão canônica por competência para cada análise**, com regra auditável (por exemplo, versão mais recente no portal após validação). Guardar revisões anteriores como histórico e nunca somar snapshots completos de meses diferentes como transações.

### Linha do tempo da plataforma (informada pelo backlog)

| Referência | Evento | Situação e consequência |
|---|---|---|
| E1 (tag `e1`) | Inventário e carga OLTP com PostgreSQL/Flyway e rejeitados | Concluído segundo o backlog; este manifesto não comprova a integridade do banco. |
| 19/10/2026 às 14:31:48 UTC | Manifesto de coleta dos cinco datasets | 453 recursos JSON, todos com `sha256`, URL e tamanho; listas `falhas` vazias. |
| E2 (prazo 19/10/2026) | Carga histórica de estoque | Parcial: 30 meses rejeitados pela trava de queda de 30%, segundo backlog; investigar quais competências e versões. |
| E2 em andamento | Destino analítico, CDC e reprocessamento | Ainda não demonstrados no material enviado; preservar metadados de origem e regras de idempotência. |

**Distinções fundamentais:** `coletado_em` = instante global do manifesto; `modificado_no_portal` = metadado do recurso no portal; `MM-AAAA` = referência nominal no arquivo; `ano`/`data` de empenhos = campos do registro. Nenhum desses metadados deve ser automaticamente tratado como data de aquisição/compra ou como data efetiva do preço.

## Problemas conhecidos da fonte

- **Disponibilidade:** há menção anterior a HTTP 502 intermitente, sem logs de requisição anexados. No manifesto atual, as cinco listas `falhas` estão vazias; isso não comprova ausência de falhas transitórias anteriores.
- **Cobertura histórica incompleta na carga:** 30 meses de estoque rejeitados pela proteção contra queda de 30%, conforme backlog (RD-03).
- **Versões verificadas:** o manifesto contém competências repetidas, incluindo hashes distintos para a mesma competência (ex.: estoque 2023-03, 2024-07, 2025-06 e 2025-10). Diferenciar por URL, identificador e SHA-256; evitar perda de versões ou dupla contagem.
- **Ausência de data no registro de estoque:** usar a competência validada do arquivo, sem confundi-la com a data em que o SIGMA-UnB baixou os dados.
- **Identificação de material:** `material` é uma descrição textual, sem código persistente ou unidade de medida documentados; descrições semelhantes podem corresponder a produtos distintos.
- **Escala e semântica monetária:** `preco`, `valor_total` e `valor` aparecem como inteiros nos dicionários, sem especificação explícita da escala. Não presumir centavos/reais nem preço efetivamente pago antes de validar amostras.
- **Relacionamento entre bases:** não há chave documentada para associar materiais aos empenhos; a concentração de fornecedores **permanece objetivo futuro**. `id_unidade` e `id_unidade_gestora` exigem validação de domínio antes do cruzamento.
- **Qualidade temporal:** recursos ausentes, duplicados ou atrasados podem distorcer a taxa anualizada de crescimento. Registrar lacunas e janela efetiva de cada material.
- **Campos opcionais e dados pessoais:** `observacoes`, `credor` e outras informações textuais exigem verificação de conteúdo e análise LGPD antes de exposição.
- **Formato da coleta:** todos os recursos do manifesto estão em JSON. Validar estrutura, esquema, representação de datas e escala monetária nos arquivos reais; o manifesto não fornece linhas, tipos efetivos ou resultados de parsing.
- **Mercado:** não há base conectada de preços de lojas online; a coleta semanal está apenas parcialmente preparada, e comparações de sobrepreço/economia potencial não estão disponíveis.

## Pendências de verificação

1. **Concluído parcialmente com `manifesto (3).json`:** inventariados links diretos, hashes, metadados e competências nominais. **Ainda falta** comparar o inventário aos logs/tabelas da carga para identificar arquivos aceitos, rejeitados e versões canônicas.
2. Conferir, no portal, licença e responsável institucional por dataset e recurso; esses atributos não constam do manifesto fornecido.
3. Comparar cabeçalhos e tipos entre arquivos antigos e recentes, registrar mudanças reais e padronizações feitas no pipeline.
4. Investigar os 30 meses rejeitados pela regra de queda de 30%, distinguindo falha de carga, competência não listada, arquivo vazio e variantes de mesmo mês com conteúdo divergente.
5. Validar a chave de identidade dos materiais entre meses, o significado e a escala do campo `preco` e a regra para comparar diferentes almoxarifados.
6. Identificar eventual fonte de itens de empenho; só então associar fornecedor a material. A existência inicial de apenas um fornecedor não permite análise de concentração.
7. Definir a origem de preços de mercado, termos de uso e política de coleta caso a análise complementar entre no escopo.

## Referências

- Portal de Dados Abertos da UnB: páginas oficiais dos cinco datasets listadas na tabela.
- Dicionários de dados recebidos: Estoque Almoxarifado, Unidade Acadêmica, Gastos por Unidade, Empenhos e Requisições de Serviços (versões 1.0, 2020).
- `backlog.md` — requisitos RD-01 a RD-10, RF-11 a RF-13 e decisões de ADR.
- `dominio-e-pergunta.md` — recorte de 2021–2025, indicador anualizado, limitações e objetivos futuros.
- `manifesto (3).json` — coleta declarada de 19/10/2026, URLs, datas `modificado_no_portal`, SHA-256, tamanhos, inventário de versões e listas de falhas dos cinco datasets.
