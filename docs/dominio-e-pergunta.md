# Domínio e pergunta de gestão

## Domínio

O SIGMA-UnB trata da gestão de materiais de consumo dos almoxarifados da Universidade de Brasília (UnB). Nesse contexto, fornecedores (credores) estão associados aos empenhos de aquisição, enquanto os almoxarifados mantêm registros de materiais, preços unitários e saldos de estoque. As unidades acadêmicas e administrativas demandam materiais e podem acompanhar requisições e gastos. O fluxo específico de compra, recebimento, distribuição e vínculo entre empenho e item de material precisa ser confirmado na documentação dos dados de origem.

Os principais atores são os gestores da universidade e das áreas de compras e almoxarifado, que acompanham custos, fornecedores e disponibilidade; os chefes de departamento, interessados nos gastos e requisições de suas unidades; os fornecedores, relacionados aos empenhos; e os Centros Acadêmicos, interessados no acompanhamento do uso de recursos por unidade acadêmica.

O problema de gestão é identificar materiais cujos preços unitários registrados aumentaram mais rapidamente e verificar se seus empenhos estão concentrados em poucos fornecedores. A análise histórica pode apoiar a priorização de revisões de compras, o acompanhamento de custos e a avaliação de dependência de fornecedores. O SIGMA-UnB também prevê a consulta de saldos de estoque e, como complemento, o monitoramento de preços de lojas online.

## Pergunta de gestão

> Entre 2021 e 2025, quais materiais de consumo do almoxarifado da UnB apresentaram a maior taxa anualizada de aumento do preço unitário registrado?

**Objetivo futuro — fornecedores:** identificar quais fornecedores concentram os empenhos associados aos materiais de maior aumento de preço, conforme previsto no backlog. Na fase inicial há apenas um fornecedor previsto, e os dicionários atuais não demonstram a ligação entre empenhos e materiais. A análise de concentração será implementada quando houver dados de múltiplos fornecedores e uma associação confiável entre empenhos e itens de material. Esse objetivo deve permanecer registrado no backlog, README e página inicial como evolução planejada, sem ser apresentado como resultado disponível.

**Recorte complementar — mercado:** comparar preços com lojas online apenas quando houver base de cotações adequada e uma forma validada de vincular produtos e datas. Ainda não existe uma base integrada para isso.

### Quem usaria a resposta

| Público | Decisão que a resposta apoia |
|---|---|
| Gestores da UnB e áreas de compras | Priorizar a revisão de materiais com maiores aumentos de preço; consultar empenhos e credor apenas no nível de detalhe efetivamente suportado. |
| Gestores de almoxarifado | Acompanhar a evolução do custo registrado dos materiais e relacioná-la à disponibilidade em estoque. |
| Chefes de departamento | Acompanhar gastos e requisições por unidade, período e natureza da despesa, quando esse recorte estiver disponível. |
| Centros Acadêmicos | Acompanhar a demanda e os gastos das unidades acadêmicas, conforme a disponibilidade dos dados. |

### Como a pergunta se divide

| Subpergunta | Dados necessários | Dataset / fonte | Viabilidade atual |
|---|---|---|---|
| Como evoluiu o preço registrado de cada material de 2021 a 2025? | `material`, `almoxarifado`, `preco` e período de referência dos arquivos/snapshots. | Estoque almoxarifado. | Viável se os arquivos históricos permitirem datar e comparar os registros. |
| Quais materiais tiveram as maiores altas percentuais anualizadas? | Preços positivos de períodos comparáveis, datas das observações e identificação consistente de materiais. | Estoque almoxarifado e histórico de cargas. | Condicionada à qualidade e à cobertura da série. |
| Quais materiais e almoxarifados têm saldo e valor de estoque maiores? | `material`, `almoxarifado`, `saldo`, `valor_total`. | Estoque almoxarifado. | Suportada pelo esquema; depende da carga dos registros. |
| Qual credor consta nos empenhos e como evoluíram seus valores? | `credor`, `cod_empenho`, `ano`, `data`, `valor_empenho`, `saldo_empenho`. | Empenhos. | Possível em nível de empenho/credor, sem atribuição a materiais. |
| Quais empenhos estão vinculados a cada material? | Chave ou tabela de associação entre material e item do empenho. | Não identificada nos cinco dicionários. | **Não demonstrada**; não realizar associação apenas por suposição. |
| Como variam os gastos por unidade e natureza da despesa? | `id_unidade`, `unidade`, `natureza_despesa`, `valor`. | Gastos por unidade e unidades acadêmicas. | Recorte complementar, sujeito às dimensões temporais realmente presentes nos arquivos. |

**Outras bases recebidas:** requisições **de serviços** contêm número, ano, tipo, unidade requisitante, unidade de custo e status, mas não uma relação declarada de itens de material; unidades acadêmicas fornecem identificadores, nomes, siglas e hierarquia. Nenhuma das cinco especificações apresenta uma chave documentada de material para a tabela de empenhos.

## Indicadores

| Indicador | Fórmula / definição | Unidade | Status |
|---|---|---|---|
| Variação absoluta do preço | `preco_final - preco_inicial` para o mesmo material e base de comparação. | Unidade monetária da fonte por item | Complementar. |
| Variação percentual acumulada | `(preco_final / preco_inicial - 1) * 100`; exige `preco_inicial > 0`. | % | Complementar. |
| **Taxa anualizada de aumento do preço** | `((preco_final / preco_inicial) ** (1 / anos_decorridos) - 1) * 100`; exige preços positivos e datas válidas. | % ao ano | **Indicador principal confirmado.** |
| Saldo de estoque | `SUM(saldo)` por material/almoxarifado, sem somar snapshots de meses diferentes. | Itens | Complementar. |
| Valor de estoque | `SUM(valor_total)` por material/almoxarifado e data de referência, após validação. | Unidade monetária da fonte | Complementar. |
| Valor empenhado por credor | `SUM(valor_empenho)` por `credor` e período, respeitando a granularidade e evitando duplicidade. | Unidade monetária da fonte | Apenas no nível do credor/empenho; não por material. |
| Participação do credor nos empenhos de cada material | Dependeria da associação validada de empenhos aos materiais e da existência de mais de um credor. | % | **Não aplicável à fase inicial / não demonstrável com os dicionários atuais.** |
| Sobrepreço e economia potencial frente ao mercado | Dependem de cotação comparável, data, unidade de medida, quantidade e critério de equivalência. | Unidade monetária / % | **Não calculáveis atualmente** (sem base vinculada de preços de mercado). |

**Definições metodológicas:** o ranking priorizará a taxa anualizada, conforme confirmado. O cálculo deve utilizar as datas reais dos snapshots e não presumir que cada material tenha observações nos extremos de 2021 e 2025. Os dicionários de estoque rotulam `preco` como “preço praticado” (tipo inteiro), não explicitamente como preço efetivamente pago nem como preço de aquisição. Também não detalham escala monetária ou unidade de medida; ambas devem ser verificadas nos dados de origem antes de rotular o resultado em reais por unidade.

## Escopo e limitações

- **Dentro do escopo principal:** evolução histórica do campo `preco` dos materiais dos almoxarifados da UnB entre 2021 e 2025, ranking pela variação percentual anualizada, com identificação do almoxarifado e documentação da janela temporal efetivamente comparada.
- **Dentro do escopo complementar:** saldos e valores do estoque; análise agregada de empenhos por credor (inicialmente um fornecedor), sem vinculação presumida a itens; gastos por unidade; unidades acadêmicas e requisições de serviços, quando pertinentes e associáveis por campos documentados.
- **Objetivos futuros, ainda não operacionais:** análise da concentração de empenhos por fornecedor para cada material (dependente de associação entre empenhos e materiais e de múltiplos fornecedores); cotação de lojas online, comparação com o preço do estoque e estimativa de economia potencial.
- **Fora do escopo:** modificar dados da UnB; tempo real estrito; prever preços ou recomendar automaticamente compras; autenticação individual na interface do painel.
- **Limitações dos dados:** o dicionário de estoque traz `material`, `almoxarifado`, `saldo`, `preco`, `valor_total`, mas não data do registro, ID de material ou unidade de medida; a data deve vir dos arquivos históricos ou metadados de carga. O dicionário de empenhos possui `credor`, `cod_empenho`, `ano`, `data` e valores, mas não material ou itens do empenho. O dicionário de gastos por unidade também não descreve campo temporal. Os dicionários não confirmam cobertura contínua entre 2021–2025, escala monetária nem chave comum entre material e empenho.
- **Qualidade e governança:** validar duplicatas e alterações de descrição, saltos atípicos, preços nulos/zerados, meses sem carga, consistência do saldo, assim como eventuais dados pessoais em credores pessoa física.

## Hipóteses

- **H1:** os preços registrados apresentam taxas anualizadas de crescimento diferentes entre materiais de consumo, permitindo estabelecer um ranking no período disponível.
- **H2:** parte dos materiais apresenta oscilações ou aumentos expressivos que justificam revisão da qualidade dos registros e investigação pela gestão.
- **H3 (objetivo futuro, condicionada):** após incorporar mais fornecedores e estabelecer uma associação documentada entre empenhos e materiais, será possível investigar se os empenhos dos materiais que mais encareceram se concentram em determinados fornecedores. Essa concentração não pode ser inferida a partir dos campos atuais.

## Decisões confirmadas e pendências

**Confirmado pela equipe:** (1) usar a variação percentual anualizada no ranking; (2) considerar inicialmente apenas um fornecedor; (3) manter a concentração de fornecedores como **objetivo futuro do projeto**; (4) ainda não há base de preços de mercado conectada.

**A validar antes do painel:**

1. Verificar os arquivos de dados, as datas e a cobertura histórica de 2021–2025, incluindo os meses rejeitados apontados no backlog.
2. Confirmar a unidade/escala de `preco`, se o valor é unitário e como distinguir descrições iguais ou alteradas do mesmo material.
3. Definir se os preços serão comparados por material **e almoxarifado** ou agregados por material (e, no segundo caso, por qual regra).
4. Verificar se existe outra fonte ou mapeamento de item de empenho que permita relacioná-lo a material; até lá, não atribuir empenhos a materiais.
5. Alinhar a pergunta central da fase inicial com backlog, README e página inicial, **mantendo explicitamente a análise de concentração de fornecedores como objetivo futuro do projeto**.
6. Escolher se a integração de preços de mercado será implementada mais adiante, conforme prioridades e tempo disponível.

## Fontes documentais

- Dicionário de dados — **Estoque Almoxarifado** (UnB Dados Abertos, versão 1.0, 15/09/2020).
- Dicionário de dados — **Empenhos** (UnB Dados Abertos, versão 1.0, 15/09/2020).
- Dicionário de dados — **Gastos por Unidade** (UnB Dados Abertos, versão 1.0, 09/09/2020).
- Dicionário de dados — **Requisições de Serviços** (UnB Dados Abertos, versão 1.0, 15/09/2020).
- Dicionário de dados — **Unidade Acadêmica** (UnB Dados Abertos, versão 1.0, 15/09/2020).
- `backlog.md` — visão, requisitos e decisões previstas do SIGMA-UnB.
