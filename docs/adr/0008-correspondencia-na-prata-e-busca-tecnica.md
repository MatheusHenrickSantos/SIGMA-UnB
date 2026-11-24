# 0008 — Guardar correspondências na Prata e separar os artefatos técnicos da busca

- **Status:** aceito
- **Data:** 2026-11-23
- **Decisão:** manter candidatos e revisões como dados da Prata; mover vetores e metadados da busca para o schema técnico `busca`.

## Contexto

O schema `semantica` foi criado para a busca de similaridade entre materiais do
estoque e itens CATMAT. Seu conteúdo não é uma camada semântica analítica de
consumo. O projeto pode criar essa camada após a Ouro no futuro, então usar o
mesmo nome para o armazenamento operacional da busca causaria ambiguidade.

Além disso, os objetos misturavam dados com papéis diferentes: vetores e
execuções dependem do algoritmo; candidatos e decisões descrevem a relação de
negócio material–CATMAT. O diagrama da arquitetura já posiciona
`candidatoCatmat` na Prata.

## Decisão

- O schema `busca` guarda `descricao`, `modelo_embedding`, `embedding` e
  `execucao_correspondencia`. São registros técnicos usados pelo serviço Python
  e podem ser reconstruídos ou recalculados a partir das fontes da Prata.
- A Prata guarda `candidato_catmat`, `revisao_correspondencia` e
  `revisao_material`, além das visões de revisão e consumo. Candidatos são
  sugestões; revisões registram decisões de pessoas ou de agentes.
- `prata.v_item_aprovado` continua sendo a entrada da coleta de compras.
- O termo “camada semântica” fica disponível para a futura camada analítica
  posterior à Ouro. O serviço e o pacote Python podem continuar chamados
  `semantica`, pois implementam busca semântica.

## Consequências

- A migração V6 preserva os dados e move as tabelas existentes; migrações
  anteriores não são alteradas.
- Python escreve alguns objetos no schema `prata`, enquanto dbt escreve os
  modelos relacionais. Os nomes das relações permanecem separados para evitar
  colisões e cada processo continua dono dos objetos que cria.
- `busca.descricao` continua sendo um registro sincronizado das descrições e
  hashes usados para gerar embeddings e vincular revisões aos textos de origem.
- Código, fontes dbt, snapshots, documentação e consultas devem usar os novos
  schemas.

## Alternativa descartada

Mover todos os objetos para `prata` seria tecnicamente possível, mas colocaria
vetores específicos de modelo e histórico operacional junto aos dados de
correspondência. Por isso a separação é por responsabilidade, não apenas por
nome.
