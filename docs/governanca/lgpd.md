# Análise de LGPD

> Análise técnica da Squad sobre o que foi construído. **Não é parecer jurídico**: as bases legais e os prazos abaixo devem ser confirmados com o encarregado de dados (DPO) da UnB antes de qualquer uso fora do projeto acadêmico.

## Inventário: onde há dado pessoal

| Dado | Onde está | Pessoal? | Titular | Medição |
|---|---|---|---|---|
| `niFornecedor` (CNPJ ou CPF) e `nomeFornecedor` | `raw.compras` (JSON bruto da API de pesquisa de preços) | **Sim, potencialmente**: empresário individual e MEI têm nome da pessoa no nome empresarial; CPF seria pessoa física | Fornecedor da Administração | 60 códigos CATMAT sorteados, 408 registros: **408 CNPJ (14 dígitos), 0 CPF (11 dígitos)**. Amostra, não prova de ausência de CPF |
| Nome de quem revisou a correspondência | `semantica.revisao_correspondencia.revisor`, `revisao_material.revisor`, `ouro.resumo_correspondencia.revisor` | Sim (nome da pessoa da Squad) | Membros da Squad | Hoje todas as decisões são `agente:ia`; entra nome quando pessoas conferirem |
| Nome de usuário de banco | `reverso.acesso_almoxarifado.usuario` e papéis do PostgreSQL | Sim (login) | Chefias de almoxarifado e compras | 2 usuários de exemplo na semente |
| Estoque (material, almoxarifado, saldo, preço) | `raw.estoque` e camadas seguintes | Não | — | Nenhuma coluna de pessoa nos 39 arquivos mensais (06/2021 a 12/2025) |
| CATMAT | `raw.catmat` | Não | — | Catálogo de itens |
| Órgão comprador, UASG, município | `raw.compras` (JSON) | Não (pessoa jurídica de direito público) | — | — |
| `objetoCompra`, `descricaoDetalhadaItem` (texto livre) | `raw.compras` (JSON) | Improvável; texto livre pode conter nome | — | Não usado em nenhuma camada analítica |

**Fora do escopo atual, mas previsto no backlog (RD-25):** credores pessoa física e requisições de serviço dos datasets de empenho. Eles saíram do pipeline atual (`docker-compose.yml` só carrega estoque, CATMAT e compras). Se voltarem, o credor entra neste inventário com mascaramento do nome.

## Base legal, finalidade e minimização

| Tratamento | Finalidade | Base legal (a confirmar com o DPO) |
|---|---|---|
| Ler `niFornecedor`/`nomeFornecedor` da API pública e guardar na raw | Nenhuma além de poder reprocessar; a análise de preço **não usa** | Art. 7º, III e §3º da LGPD (tratamento pela administração pública de dado de acesso público, respeitada a finalidade) e Lei de Acesso à Informação. Como a finalidade não exige o campo, vale o **princípio da necessidade** (art. 6º, III): não guardar |
| Registrar quem revisou | Responsabilização e auditoria da decisão | Art. 7º, III e V (execução das atividades da instituição / do projeto) |
| Usuários de acesso | Controle de acesso e trilha | Art. 7º, III e art. 46 (segurança) |

## O que foi construído para cumprir

| Princípio | Mecanismo no repositório |
|---|---|
| **Necessidade / minimização** | `V12__minimizacao_fornecedor.sql`: `raw.remover_identificacao_fornecedor()` remove `niFornecedor` e `nomeFornecedor` do JSON da raw. O dbt a chama no post-hook de `compras_bronze` (desligável por `remover_identificacao_fornecedor: false`) |
| **Nenhum dado pessoal nas camadas analíticas** | Teste `tests/sem_identificador_de_fornecedor.sql` falha o build se bronze, prata, ouro ou reverso tiver coluna com fornecedor, CPF ou CNPJ |
| **Segurança / privilégio mínimo** | Papéis `sigma_painel`, `sigma_compras`, `sigma_almoxarifado` (V11), recorte de coluna e de linha: [Controle de acesso](governanca/acesso.md) |
| **Transparência** | Esta análise, o [catálogo e a linhagem](governanca/catalogo-e-linhagem.md) e o [ADR 0012](adr/0012-governanca-lgpd-e-controle-de-acesso.md) |

## Retenção e descarte

| Dado | Retenção | Descarte |
|---|---|---|
| Identificação do fornecedor em `raw.compras` | **Zero após a carga**: removido na mesma execução em que a bronze é construída | `raw.remover_identificacao_fornecedor()` (irreversível; idempotente) |
| Cache das páginas da API em `dados/compras_cache/` e `dados/compras/` (JSON original, com fornecedor) | Até a carga ser concluída; a pasta `dados/` não é versionada (`.gitignore`) | Apagar a pasta depois da carga: `rm -rf dados/compras_cache dados/compras`. **Hoje isso é manual** (pendência) |
| Nome de revisor e usuários | Duração do projeto acadêmico | Anonimizar `revisor` para `pessoa:<hash>` e remover a linha em `acesso_almoxarifado` ao encerrar o acesso |
| Estoque, CATMAT, preços públicos | Sem dado pessoal: sem prazo legal; guardados enquanto servirem à série histórica | — |

## Risco de reidentificação por cruzamento

Duas bases anonimizadas podem reidentificar quem nenhuma identificava sozinha. Os cruzamentos que analisamos:

1. **Compras × estoque.** O estoque não identifica ninguém; as compras (depois da minimização) não têm fornecedor. Sem fornecedor em nenhuma das duas, o cruzamento não liga pessoas. **Risco baixo.**
2. **Fornecedor pequeno × marca × município × data.** Enquanto `niFornecedor`/`nomeFornecedor` existiam, a combinação município + marca + data de uma compra poderia apontar para um empresário individual. A minimização elimina o identificador direto; `marca`, `municipio` e `dataCompra` continuam na raw (não são levados às camadas analíticas). **Risco residual na raw, mitigado pelo acesso restrito (o schema `raw` não é concedido a nenhum papel de consumo).**
3. **Alertas × fonte pública.** O CSV de alertas traz material, almoxarifado, preços e quantidades de um órgão público, sem pessoa. Quem tem o CSV poderia cruzar com a API pública, mas só reencontraria dados já públicos de pessoa jurídica.
4. **Nome de revisor × decisões.** Quando pessoas revisarem, `revisor` + `justificativa` permite atribuir cada decisão a uma pessoa: finalidade legítima de auditoria, mas é dado pessoal e por isso a coluna `justificativa_agente` e o nome ficam fora das concessões de coluna ao consumidor.

## Pendências

- Confirmar a base legal e os prazos com o DPO da UnB.
- Automatizar o descarte do cache em disco (`dados/compras_cache`).
- Amostra maior para confirmar a ausência de CPF: depois da carga completa, contar `length(regexp_replace(niFornecedor,'\D','','g')) = 11` **antes** de executar a minimização (a função apaga a evidência).
