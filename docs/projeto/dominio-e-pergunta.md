# Domínio e pergunta de gestão

## Projeto

O SIGMA-UnB é uma plataforma de dados para apoiar a gestão de materiais e as decisões de compra da Universidade de Brasília. A pergunta atual combina o estoque dos almoxarifados, o Catálogo de Materiais (CATMAT) e registros de preços de compras públicas. O CATMAT ajuda a localizar itens correspondentes; a comparação só é válida quando a identificação do produto, a unidade de medida e o período forem compatíveis.

## Pergunta de gestão

> Para quais materiais do estoque da UnB é possível encontrar um item correspondente no CATMAT e em compras públicas comparáveis, e quais apresentam as maiores diferenças entre o preço registrado no estoque e os preços dessas compras, por almoxarifado e período?

Essa pergunta orienta a investigação, não presume que todos os materiais possam ser comparados nem que diferenças indiquem sobrepreço. O vínculo sugerido por semelhança de descrição deve ser validado antes de usar um código CATMAT; preços sem unidade ou período comparáveis devem ser excluídos ou apresentados separadamente.

## Fontes e papel na análise

| Fonte | Papel | Limitação importante |
| :---- | ----- | -------------------- |
| Estoque do almoxarifado da UnB | Fornece material, almoxarifado, saldo e preço registrado. | A descrição não é um identificador estável; validar a data de referência, a unidade e a escala do preço. |
| CATMAT | Fornece códigos e descrições para apoiar a identificação de materiais. | Um candidato encontrado por similaridade textual não é, por si só, uma correspondência confirmada. |
| Pesquisa de preços públicos | Fornece registros de preços observados em compras públicas para itens consultados. | Nem todo item consultado terá uma compra no período. |

O preço de uma compra pública funciona como referência observada em compras da Administração; não é uma cotação de loja nem necessariamente o preço de mercado atual.

## Quem usa a resposta

| Público | Decisão que a análise pode apoiar |
|---|---|
| Gestores da UnB e áreas de compras | Investigar diferenças de preço entre registros do estoque e compras públicas comparáveis. |
| Gestores de almoxarifado | Acompanhar preço registrado e saldo por material e almoxarifado. |
| Chefes de departamento e Centros Acadêmicos | Consultar informações de materiais e apoiar o acompanhamento da gestão, conforme os dados disponíveis. |

## Indicadores e critérios

| Indicador | Definição | Condição de uso |
| :-------- | :-------- | :-------------- |
| Diferença absoluta de preço | Preço registrado no estoque menos preço de referência da compra pública. | Mesma base de unidade e produto; a escolha do preço de referência deve ser documentada. |
| Diferença percentual | `(preço do estoque / preço de referência - 1) * 100`. | Preço de referência positivo e unidades comparáveis. |
| Saldo de estoque | Saldo do material em um almoxarifado e data de referência. | Não somar snapshots de datas diferentes como se fossem movimentos. |

O critério para resumir vários preços públicos — por exemplo, mediana ou outra estatística — deve ser definido e documentado antes de publicar rankings. Uma diferença positiva é um sinal para análise, não prova de irregularidade nem estimativa de economia.

## Escopo e limitações

- **Escopo atual:** explorar correspondências entre materiais do estoque e códigos CATMAT; consultar preços de compras públicas desses códigos; comparar preços somente quando produto, unidade e período forem compatíveis; apresentar a disponibilidade por almoxarifado.
- **Não presumir:** que todo material tenha correspondência CATMAT; que o preço do estoque seja necessariamente preço efetivamente pago; que todo preço público seja comparável; ou que uma diferença corresponda a sobrepreço.
- **Fora da pergunta atual:** cotações em lojas online, previsão de preços, recomendações automáticas de compra e atribuição de empenhos a materiais sem vínculo documentado.
- **Limitações a validar:** estabilidade das descrições do estoque, cobertura temporal, unidade de medida, escala monetária, duplicatas e revisões dos registros públicos.

## Próximas validações

1. Confirmar os campos e a granularidade dos dados retornados pelas fontes atuais.
2. Validar os candidatos CATMAT com evidência suficiente, sem aceitar apenas similaridade textual.
3. Definir o período de análise e a estatística usada para resumir vários preços públicos.
4. Conferir se os preços comparados têm unidade de medida e condições de compra equivalentes.
5. Documentar cobertura, exclusões e limitações junto aos resultados.

## Fontes documentais

- [Fontes e histórico da origem](fontes-e-historico-da-origem.md).
- [Teste de viabilidade CATMAT e cobertura de preços públicos](../testes/teste-de-viabilidade.md).
- [Backlog do produto](../gestao/backlog.md), que ainda deve ser alinhado à pergunta atual.
