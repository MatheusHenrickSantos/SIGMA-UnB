# Dicionário de dados: Requisições de serviços

| | |
|---|---|
| **Fonte** | Portal de dados abertos da UnB ([dados.unb.br](https://dados.unb.br)), dataset `requisicoes-de-servicos` |
| **Documento original** | `dicionario-de-dados-requisicao-de-servico.pdf`, versão 1.0, autor CPDA, 15/09/2020 |
| **Descrição oficial** | Relação de requisições de serviços da instituição. |
| **Dataset no SIGMA** | `requisicoes` (`dados/bruto/requisicoes/`) |

## Campos, como publicados

Transcrição fiel do dicionário oficial.

| Campo | Tipo | Descrição | Obrigatório? |
|---|---|---|---|
| numero | Inteiro | Número da requisição | Sim |
| ano | Inteiro | Ano em que a requisição foi cadastrada. | Sim |
| tipo | Texto | Tipo da Requisição. | Sim |
| id_unidade_requisitante | Inteiro | Identificador da unidade requisitante. | Sim |
| nome_unidade_requisitante | Texto | Nome da unidade requisitante. | Sim |
| id_unidade_custo | Inteiro | Identificador da unidade que pagará a requisição | Sim |
| nome_unidade_custo | Texto | Nome da unidade que pagará a requisição | Sim |
| data_envio | Texto | Data do último envio da requisição. | Não |
| data_autorizacao_chefe | Data | Data em que o chefe imediato autorizou a requisição. | Não |
| status | Texto | Status da requisição. | Sim |
| observacoes | Texto | Observações referentes à requisição. | Não |

## Onde cada campo vai no SIGMA

| Campo do portal | Tabela.coluna no Postgres | Tratamento no `carregar.py` |
|---|---|---|
| numero, ano | `requisicao_servico` (chave primária composta) | Registro sem algum dos dois vai para `carga_rejeitado` |
| tipo, status, observacoes | colunas de mesmo nome | Texto padronizado |
| id_unidade_requisitante, id_unidade_custo | colunas de mesmo nome → `unidade.id_unidade` | Unidade fora do cadastro é criada com `fonte = 'referencia'` |
| nome_unidade_requisitante, nome_unidade_custo | `unidade.nome` | Usados só para criar a unidade de referência |
| data_envio | `requisicao_servico.data_envio` (DATE) | Convertida de texto para data |
| data_autorizacao_chefe | `requisicao_servico.data_autorizacao_chefe` (DATE) | Autorização anterior ao envio é rejeitada |

## Diferenças entre o dicionário e o uso

- `data_envio` é declarada como **Texto** no dicionário, embora seja uma data; o SIGMA converte.
- Não há data de conclusão: o tempo de atendimento só pode ser medido até a autorização do chefe.
- `status` e `data_autorizacao_chefe` mudam ao longo do tempo; o CDC da E2 guarda cada versão.

## LGPD

A planilha da Squad marca esta fonte como contendo dado pessoal. O motivo ainda precisa ser registrado na análise de LGPD da E4; o candidato mais provável é o texto livre de `observacoes`.
