# Dicionário de dados: Unidades acadêmicas

| | |
|---|---|
| **Fonte** | Portal de dados abertos da UnB ([dados.unb.br](https://dados.unb.br)), dataset `unidades-academicas` |
| **Documento original** | `dicionario-de-dados-unidade-academica.pdf`, versão 1.0, autor CPDA, 15/09/2020 |
| **Descrição oficial** | Relação das Unidades Acadêmicas. |
| **Dataset no SIGMA** | `unidades` (`dados/bruto/unidades/`) |

## Campos, como publicados

Transcrição fiel do dicionário oficial.

| Campo | Tipo | Descrição | Obrigatório? |
|---|---|---|---|
| id_unidade | Inteiro | Identificador da unidade. | Sim |
| nome | Texto | Descrição nominal da unidade acadêmica. | Sim |
| sigla | Texto | Sigla destinada a unidade. | Sim |
| sigla_academica | Texto | Sigla destinada a unidade, quando utilizada em vínculos acadêmicos. | Sim |
| id_unidade_responsavel | Inteiro | Identificador da unidade responsável pela unidade acadêmica. | Não |
| unidade_responsavel | Texto | Unidade responsável hierarquicamente. | Não |
| id_unidade_gestora | Inteiro | Identificador da unidade gestora da unidade acadêmica. | Não |
| unidade_gestora | Texto | Unidade gestora academicamente. | Não |
| id_gestora_academica | Inteiro | Identificador da unidade gestora acadêmica da unidade acadêmica. | Não |
| unidade_gestora_academica | Texto | Unidade gestora acadêmica da unidade acadêmica. | Não |
| tipo_organizacional | Texto | Forma de organização da unidade. | Sim |
| tipo_academica | Texto | Tipo da unidade acadêmica. | Sim |

## Onde cada campo vai no SIGMA

| Campo do portal | Tabela.coluna no Postgres | Tratamento no `carregar.py` |
|---|---|---|
| id_unidade | `unidade.id_unidade` (chave primária) | Registro sem id ou sem nome vai para `carga_rejeitado` |
| nome, sigla, sigla_academica, tipo_organizacional, tipo_academica | colunas de mesmo nome | Texto padronizado; `fonte = 'cadastro'` |
| id_unidade_responsavel, id_unidade_gestora, id_gestora_academica | colunas de mesmo nome (autorrelacionamento) | Superior inexistente no cadastro fica em branco, com aviso no log |
| unidade_responsavel, unidade_gestora, unidade_gestora_academica | `unidade.nome` da unidade superior | Usados só para criar a superior se ela ainda não foi lida |

## Diferenças entre o dicionário e o uso

- O dataset só traz unidades **acadêmicas**. Unidades administrativas citadas em gastos, empenhos e requisições entram no SIGMA com `fonte = 'referencia'`, só com id e nome.
- A hierarquia tem 2 a 3 níveis, resolvida com autorrelacionamento (ver planilha, aba 3).
- Nome e sigla podem mudar: é a dimensão de variação lenta da E3, e o CDC da E2 guarda cada versão em `bronze/cdc/unidade/`.
