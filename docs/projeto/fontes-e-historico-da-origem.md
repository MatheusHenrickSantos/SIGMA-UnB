# Fontes de dados e histórico da origem

## Fontes atuais

O escopo atual usa três fontes: o estoque vem do [Portal de Dados Abertos da UnB](https://dados.unb.br/); o CATMAT e os registros de pesquisa de preços são consultados pela [API de Dados Abertos do Compras.gov.br](https://dadosabertos.compras.gov.br/swagger-ui/index.html).

| Fonte | Origem / acesso | Conteúdo e papel | Limitações |
|---|---|---|---|
| Estoque do almoxarifado | [Dataset da UnB](https://dados.unb.br/dataset/estoque-do-almoxarifado) | Material, almoxarifado, saldo e preço registrado. | A descrição não é um código estável; validar data de referência, unidade e escala do preço. |
| Catálogo de Materiais (CATMAT) | API de Materiais (`modulo-material/4_consultarItemMaterial`) | Códigos e descrições para apoiar a identificação dos materiais. | Correspondência sugerida por texto precisa ser validada. |
| Pesquisa de preços públicos | API de Pesquisa de Preços (`modulo-pesquisa-preco/1_consultarMaterial`) | Registros de preços observados em compras da Administração Pública. | Não equivale a cotação de loja ou preço de mercado atual; comparar somente itens, unidades e períodos compatíveis. |

O script de download do CATMAT e a consulta de preços são separados do `docker compose` atual; veja [Como executar](como-executar.md) e o [teste de viabilidade](../testes/teste-de-viabilidade.md). A associação entre estoque e preços públicos ainda depende de validação.

## Histórico das fontes anteriores

O motivo da mudança de escopo está registrado na [ADR 04 — Adotar o estoque da UnB e preços públicos como foco do projeto](../adr/0004-adotar-dados-de-estoque-e-precos-publicos.md).

O desenho anterior incluía cinco datasets do portal da UnB: **Estoque do almoxarifado**, **Unidades acadêmicas**, **Empenhos**, **Gastos por unidade** e **Requisições de serviços**. A coleta documentada em 19/10/2026 inventariou 453 recursos JSON. Esse registro é histórico e não comprova quais arquivos foram aceitos na carga.

O estoque continua entre as fontes atuais. Os outros quatro datasets não fazem parte da pergunta de gestão vigente. Consulte [Como executar](como-executar.md) para os limites do pipeline atual.
