# Glossário

| Termo | Definição |
| ----- | --------- |
| Almoxarifado | Unidade que armazena e distribui materiais na UnB. |
| CATMAT | Catálogo de Materiais do Governo Federal, usado para identificar itens por código e descrição. |
| Correspondência CATMAT | Associação entre uma descrição do estoque e um código do catálogo. Uma sugestão automática precisa ser validada antes de ser usada na análise. |
| Compra pública | Registro de aquisição realizada pela Administração Pública. Os preços consultados no projeto são referências de compras, não cotações de lojas. |
| Preço registrado no estoque | Campo de preço informado na fonte de estoque. Sua escala, unidade e relação com o preço efetivamente pago devem ser verificadas. |
| Preço de compra pública | Preço registrado em uma compra pública para determinado item. Só é comparável ao preço do estoque quando produto, unidade e período forem compatíveis. |
| Diferença de preço | Resultado da comparação entre preço do estoque e preço de referência de compras públicas. Uma diferença positiva não comprova sobrepreço ou irregularidade. |
| Saldo de estoque | Quantidade informada para um material em um almoxarifado e uma data de referência. |
| Camada bruta (bronze) | Cópia dos dados recebidos da fonte, preservada antes das transformações. |
| OLTP | Banco transacional, otimizado para registrar e consultar operações correntes. |
| ADR | *Architecture Decision Record*: registro de uma decisão de arquitetura e seus motivos. |
| Migração | Arquivo SQL versionado (`V<n>__<descricao>.sql`) aplicado pelo Flyway para alterar o esquema do banco. |
| Idempotente | Propriedade de uma operação que pode ser repetida sem produzir efeitos adicionais indevidos. |
