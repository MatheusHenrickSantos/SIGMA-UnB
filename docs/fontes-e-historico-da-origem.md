# Fontes de dados e histórico da origem

## Fontes

| Dataset | URL no portal | Responsável na UnB | Formato | Atualização | Licença |
|---|---|---|---|---|---|
| Estoque do almoxarifado | [link dados.unb.br] | [..] | CSV | [..] | [..] |
| Unidades acadêmicas | [link] | [..] | CSV | [..] | [..] |
| Gastos por unidade | [link] | [..] | CSV | [..] | [..] |
| Empenhos | [link] | [..] | CSV | [..] | [..] |
| Requisições de serviços | [link] | [..] | CSV | [..] | [..] |
| Preços de mercado | [loja online / API] | — | [..] | Coleta própria | [termos de uso] |

O `dados/bruto/manifesto.json` guarda a URL, a data no portal e o sha256 de cada arquivo baixado.

## Dicionário de colunas da origem

[Resumo das colunas relevantes de cada dataset, como vêm do portal (antes da limpeza). O dicionário do modelo final está em [Dicionário de Dados](modelagem/dicionario-de-dados.md).]

## Histórico da origem

[Como a origem muda com o tempo: os arquivos são substituídos ou acumulados? Há versões por ano/mês? Já houve mudança de colunas?]

| Data da coleta | Dataset | Mudança observada | Impacto no pipeline |
|---|---|---|---|
| DD/MM/AAAA | [..] | [ex.: coluna renomeada] | [ex.: ajuste em `normalizar.py`] |

## Problemas conhecidos da fonte

- Portal responde 502 de forma intermitente (tratado com retry).
- [Outros: encoding, separador, datas em formatos diferentes, ..]
