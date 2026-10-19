# Domínio e pergunta de gestão

## Domínio

[Descreva o contexto: almoxarifado da UnB, como funciona a compra e a distribuição de materiais, quem são os atores (unidades acadêmicas, almoxarifados, fornecedores), e por que isso importa para a gestão da universidade.]

## Pergunta de gestão

> Quais materiais do almoxarifado da UnB tiveram o preço unitário registrado acima do preço de mercado em lojas online entre 2026 e 2027, em quais almoxarifados, e quanto a UnB gastaria a menos se tivesse pago o preço de mercado?

### Quem usaria a resposta

| Público | Decisão que a resposta apoia |
|---|---|
| [ex.: Decanato de Administração] | [ex.: renegociar contratos] |
| [público] | [decisão] |

### Como a pergunta se divide

| Subpergunta | Dados necessários | Dataset / fonte |
|---|---|---|
| Quais materiais estão acima do mercado? | Preço unitário UnB × preço de mercado | Estoque + coleta de preços |
| Em quais almoxarifados? | Almoxarifado de cada item | Estoque + unidades |
| Quanto se economizaria? | (preço UnB − preço mercado) × quantidade | Estoque / empenhos + coleta |

## Indicadores

| Indicador | Fórmula | Unidade |
|---|---|---|
| Sobrepreço unitário | `preco_unb - preco_mercado` | R$ |
| Sobrepreço % | `(preco_unb / preco_mercado - 1) * 100` | % |
| Economia potencial | `Σ (preco_unb - preco_mercado) * quantidade` onde `preco_unb > preco_mercado` | R$ |

## Escopo e limitações

- **Dentro do escopo:** [..]
- **Fora do escopo:** [..]
- **Limitações conhecidas:** [ex.: casamento entre descrição do material e o produto da loja online; frete e impostos não incluídos; variação de preço ao longo do tempo]

## Hipóteses

- [H1: ..]
- [H2: ..]
