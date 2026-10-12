# Dicionário de dados: Gastos por unidade

| | |
|---|---|
| **Fonte** | Portal de dados abertos da UnB ([dados.unb.br](https://dados.unb.br)), dataset `gastos-por-unidade` |
| **Documento original** | `despesas-e-orcamentos-gastos.pdf`, versão 1.0, autor CPDA, 09/09/2020 |
| **Descrição oficial** | Relação dos gastos por unidades da UnB. |
| **Dataset no SIGMA** | `gastos` (`dados/bruto/gastos/`, um arquivo por mês) |

## Campos, como publicados

Transcrição fiel do dicionário oficial.

| Campo | Tipo | Descrição | Obrigatório? |
|---|---|---|---|
| id_unidade | Inteiro | Identificador da unidade. | Sim |
| unidade | Texto | Nome da unidade. | Sim |
| natureza_despesa | Texto | Nome do elemento de despesa. | Sim |
| valor | Inteiro | Valor da operação. | Sim |

## Onde cada campo vai no SIGMA

| Campo do portal | Tabela.coluna no Postgres | Tratamento no `carregar.py` |
|---|---|---|
| id_unidade | `gasto.id_unidade` → `unidade.id_unidade` | Se a unidade não está no cadastro de unidades acadêmicas, é criada com `fonte = 'referencia'` |
| unidade | `unidade.nome` | Usado só para criar a unidade de referência |
| natureza_despesa | `natureza_despesa.descricao` → `gasto.id_natureza` | `id_natureza` é gerado na carga; a mesma tabela é usada pelos empenhos |
| valor | `gasto.valor` (NUMERIC 16,2) | Convertido para número |
| _(não vem no arquivo)_ | `gasto.data_referencia` | Ano e mês tirados do nome do arquivo |

## Diferenças entre o dicionário e o uso

- O dicionário declara `valor` como **Inteiro**; o SIGMA grava como decimal (valores em reais).
- O período não é um campo: só aparece no nome do arquivo mensal.
- Unidades administrativas aparecem aqui mas não no dataset de unidades acadêmicas.
