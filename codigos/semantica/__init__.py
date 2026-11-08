"""Busca semântica: correspondência entre materiais do estoque da UnB e o CATMAT.

Cada responsabilidade fica num módulo separado:

- normalizacao: limpa a descrição sem perder especificações;
- embeddings: transforma texto normalizado em vetor (modelo de linguagem);
- repositorio: lê e grava no PostgreSQL (schema semantica);
- processamento: junta os três acima em etapas incrementais.

Ver docs/semantica.md.
"""
