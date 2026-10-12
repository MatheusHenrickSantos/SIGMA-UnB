# Dicionário de dados: Empenhos

| | |
|---|---|
| **Fonte** | Portal de dados abertos da UnB ([dados.unb.br](https://dados.unb.br)), dataset `empenhos` |
| **Documento original** | `despesas-e-orcamentos-empenhos.pdf`, versão 1.0, autor não informado, 15/09/2020 |
| **Descrição oficial** | Relação de empenhos da UnB. |
| **Dataset no SIGMA** | `empenhos` (`dados/bruto/empenhos/`); o maior volume do projeto |

## Campos, como publicados

Transcrição fiel do dicionário oficial.

| Campo | Tipo | Descrição | Obrigatório? |
|---|---|---|---|
| cod_empenho | Inteiro | Código que identifica o empenho no SIAFE. | Sim |
| ano | Inteiro | Ano de emissão do empenho. | Sim |
| modalidade | Texto | Modalidade do empenho. | Sim |
| id_unidade_gestora | Inteiro | Identificador da unidade gestora. | Sim |
| nome_unidade_gestora | Texto | Nome da unidade gestora. | Sim |
| data | Data | Data da emissão do empenho. | Sim |
| programa_trabalho_resumido | Texto | Ação da instituição que direciona recursos para uma determinada área. | Sim |
| fonte_recurso | Texto | Representa a origem dos recursos do orçamento. | Sim |
| plano_interno | Texto | Representa o plano interno do orçamento. | Sim |
| esfera | Texto | Representa a esfera do orçamento. | Sim |
| natureza_despesa | Texto | Representa a naturaza da despesa. | Sim |
| credor | Texto | Credor a quem o empenho pertence. | Sim |
| valor_empenho | Decimal | Valor do empenho. | Sim |
| valor_reforcado | Decimal | Representa o reforço do valor do empenho. | Não |
| valor_anulado | Decimal | Valor anulado. | Não |
| valor_cancelado | Decimal | Valor cancelado. | Não |
| saldo_empenho | Decimal | Saldo atual do empenho. | Sim |
| processo | Texto | Representa o processo protocolado. | Não |
| documento_associado | Texto | Número do protocolo. | Não |
| licitacao | Texto | Licitação – Gestora da licitação. | Não |
| convenio | Texto | Número do convênio associado. | Não |
| observacoes | Texto | Observações adicionais sobre o empenho. | Não |

## Onde cada campo vai no SIGMA

| Campo do portal | Tabela.coluna no Postgres | Tratamento no `carregar.py` |
|---|---|---|
| cod_empenho, ano, id_unidade_gestora | `empenho` (chave primária composta) | Registro sem algum dos três vai para `carga_rejeitado` |
| nome_unidade_gestora | `unidade.nome` | Usado só para criar a unidade gestora com `fonte = 'referencia'` se ela não estiver no cadastro |
| data | `empenho.data_emissao` (DATE) | Convertida para data |
| modalidade, programa_trabalho_resumido, fonte_recurso, plano_interno, esfera, processo, documento_associado, licitacao, convenio, observacoes | colunas de mesmo nome em `empenho` | Texto padronizado |
| natureza_despesa | `natureza_despesa.descricao` → `empenho.id_natureza` | Mesma tabela usada pelos gastos |
| credor | `credor.nome` → `empenho.id_credor` | Separado em tabela própria (ver LGPD abaixo) |
| valor_empenho, valor_reforcado, valor_anulado, valor_cancelado, saldo_empenho | colunas de mesmo nome em `empenho` (NUMERIC 16,2) | Convertidos para número |

## Diferenças entre o dicionário e o uso

- O dicionário sugere que `cod_empenho` + `ano` identificam o empenho, mas o SIGMA usa também `id_unidade_gestora` na chave.
- O portal **republica** empenhos com valores anulados, reforçados ou cancelados alterados. É a principal "história que muda" do projeto: o upsert do `carregar.py` atualiza a linha e o CDC da E2 guarda cada versão em `bronze/cdc/empenho/`.
- Não há código de material: o casamento com o estoque e com as cotações precisa usar o texto de `observacoes`.

## LGPD

`credor` pode ser pessoa física, e aí o nome é dado pessoal. A fonte não traz CPF nem CNPJ. O nome fica só na tabela `credor`, o que facilita mascarar ou restringir o acesso na E4.
