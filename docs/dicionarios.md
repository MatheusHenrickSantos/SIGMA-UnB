# Dicionários de dados

Os cinco datasets do portal de dados abertos da UnB ([dados.unb.br](https://dados.unb.br)) que alimentam o SIGMA, com os campos transcritos dos dicionários oficiais (CPDA, versão 1.0, setembro de 2020) e, para cada campo, onde ele vai parar no Postgres.

| Dataset | Dicionário | Tabelas no SIGMA | Dado pessoal? |
|---|---|---|---|
| Estoque do almoxarifado | [estoque-almoxarifado](dicionarios/estoque-almoxarifado.md) | `estoque_saldo`, `material`, `almoxarifado` | Não |
| Gastos por unidade | [gastos-por-unidade](dicionarios/gastos-por-unidade.md) | `gasto`, `natureza_despesa`, `unidade` | Não |
| Empenhos | [empenhos](dicionarios/empenhos.md) | `empenho`, `credor`, `natureza_despesa`, `unidade` | Sim (`credor`) |
| Requisições de serviços | [requisicoes-de-servicos](dicionarios/requisicoes-de-servicos.md) | `requisicao_servico`, `unidade` | Sim (ver o dicionário) |
| Unidades acadêmicas | [unidades-academicas](dicionarios/unidades-academicas.md) | `unidade` | Não |

Os dicionários oficiais são de 2020 e nem sempre batem com o dado publicado hoje. Cada página tem uma seção "Diferenças entre o dicionário e o uso" com o que a Squad encontrou.

As cotações online (`cotacao_online`) não têm dicionário oficial: são geradas pelo próprio SIGMA.
