"""Busca semântica: correspondência entre materiais do estoque da UnB e o CATMAT.

Cada responsabilidade fica num módulo separado:

- normalizacao: aplica as regras compartilhadas de limpeza e valida a descrição;
- embeddings: transforma texto normalizado em vetor (modelo de linguagem);
- repositorio: lê e grava os artefatos técnicos no schema busca;
- processamento: junta os três acima em etapas incrementais;
- especificacoes: regras que conferem medidas, unidades, cores e códigos;
- correspondencia: busca top-K por cosseno, grava candidatos e revisões;
- fontes: de quais tabelas da Prata vêm as descrições;
- __main__: linha de comando (python -m semantica).

Ver docs/dados-e-pipeline/semantica.md.
"""
