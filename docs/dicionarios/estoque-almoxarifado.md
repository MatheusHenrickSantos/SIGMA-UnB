# Dicionário de dados: Estoque do almoxarifado

| | |
|---|---|
| **Fonte** | Portal de dados abertos da UnB ([dados.unb.br](https://dados.unb.br)), dataset `estoque-do-almoxarifado` |
| **Documento original** | `materiais-estoque-de-almoxarifado.pdf`, versão 1.0, autor CPDA, 15/09/2020 |
| **Descrição oficial** | Relação com os estoques dos almoxarifados da UnB. |
| **Dataset no SIGMA** | `estoque` (`dados/bruto/estoque/`, um arquivo por mês) |

## Campos, como publicados

Transcrição fiel do dicionário oficial.

| Campo | Tipo | Descrição | Obrigatório? |
|---|---|---|---|
| material | Texto | Descrição resumida do material/serviço. | Sim |
| almoxarifado | Texto | Nome do almoxarifado. | Sim |
| saldo | Inteiro | Quantidade de itens em estoque. | Sim |
| preco | Inteiro | Preço praticado do material. | Sim |
| valor_total | Inteiro | Indica o valor total do material no estoque. | Não |

## Onde cada campo vai no SIGMA

| Campo do portal | Tabela.coluna no Postgres | Tratamento no `carregar.py` |
|---|---|---|
| material | `material.descricao` → `estoque_saldo.id_material` | Texto padronizado; a fonte não traz código, então `id_material` é gerado na carga |
| almoxarifado | `almoxarifado.nome` → `estoque_saldo.id_almoxarifado` | Idem: `id_almoxarifado` é gerado na carga |
| saldo | `estoque_saldo.saldo` (NUMERIC 14,3) | Convertido para número; registro sem saldo vai para `carga_rejeitado` |
| preco | `estoque_saldo.preco_unitario` (NUMERIC 14,4) | Convertido para número |
| valor_total | `estoque_saldo.valor_total` (NUMERIC 16,2) | Quando vem vazio, é calculado como saldo × preço |
| _(não vem no arquivo)_ | `estoque_saldo.data_referencia` | Mês de referência tirado do nome do arquivo |

## Diferenças entre o dicionário e o uso

- O dicionário declara `saldo`, `preco` e `valor_total` como **Inteiro**. O SIGMA grava como decimal, porque preço e valor em reais têm centavos.
- Não há código do material nem do almoxarifado: a ligação com empenhos e cotações depende da descrição em texto.
- Cada arquivo é uma foto do mês; o mesmo material no mesmo almoxarifado e mês só entra uma vez.
