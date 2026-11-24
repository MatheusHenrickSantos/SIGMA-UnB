# 0009 — Gravar respostas das APIs diretamente na camada raw

- **Status:** aceito
- **Data:** 2026-11-23
- **Decisores:** equipe SIGMA-UnB
- **Substitui parcialmente:** decisão I do [ADR 0006](0006-busca-hibrida-e-decisoes-por-agentes.md), que armazenava respostas de compras em arquivos antes da carga.

## Contexto

O Compose baixava os dados das APIs para arquivos JSON locais e, em uma etapa
separada, relia esses arquivos para inserir os documentos na raw. Isso exigia
montar a pasta `dados/` nos containers e deixava a retomada da coleta de
compras dependente de um cache no computador.

## Decisão

- Estoque, CATMAT e compras são gravados diretamente nas tabelas `raw` assim
  que a resposta completa da fonte está disponível.
- O conteúdo é mantido em memória somente durante o processamento. O hash do
  payload preserva a deduplicação idempotente que a carga por arquivos já
  oferecia.
- Cada código CATMAT consultado para compras recebe um checkpoint em
  `raw.compras_coleta`, inclusive quando a API não retorna registros. A
  resposta e o checkpoint são confirmados na mesma transação; execuções
  seguintes retomam pelos códigos pendentes.
- Dados não completos por limite de páginas não recebem checkpoint nem são
  gravados como resultado final.
- `dados/` deixa de ser dependência dos serviços de ingestão e compras no
  Compose. A classe de carga por arquivos permanece disponível para cargas
  manuais e compatibilidade.

## Consequências

- O PostgreSQL passa a ser o armazenamento durável e o ponto de retomada da
  ingestão automatizada.
- O CATMAT completo e a resposta de cada código de compras ainda são
  acumulados em memória antes da gravação, mantendo o grão atual da raw.
- Se o processo parar enquanto baixa um catálogo ou um código de compras, essa
  unidade lógica é baixada novamente; unidades já confirmadas permanecem no
  banco.
- Os documentos JSON existentes continuam compatíveis com os modelos Bronze.
- A instalação local do banco precisa ser versionada pela migração V7 para
  criar a tabela de checkpoints.
