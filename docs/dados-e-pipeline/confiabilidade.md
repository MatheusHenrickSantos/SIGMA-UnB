# Confiabilidade dos dados

Análise de quanto se pode confiar na comparação entre o preço do estoque e o das compras públicas. As medidas do estoque foram feitas sobre os 39 arquivos mensais reais (06/2021 a 12/2025, 39.191 linhas); as demais vêm dos arquivos versionados em `codigos/semantica/`. As verificações contínuas ficam em `ouro.qualidade_dados` (modelo `models/ouro/qualidade_dados.sql`) e aparecem na aba **Qualidade** do painel.

## O que está sólido

| Verificação | Resultado |
|---|---|
| Preço nulo, zero ou negativo | 1 linha em 39.191 |
| Saldo negativo ou nulo | 0 |
| Chave (mês, material, almoxarifado) repetida | 0 |
| Linhas descartadas na passagem bronze → prata (material fora da semente) | 2 linhas (R$ 12,8 mil de R$ 47,8 milhões; luvas de procedimento M e P) |
| Saltos de preço mês a mês acima de 5× | 2 em 36.860 pares, ambos já registrados em `seeds/excecoes_qualidade.csv` |
| Valor total do portal × saldo × preço | diferença líquida de R$ 11,7 mil em R$ 47,8 milhões (0,05%) |

## O que limita a confiança

1. **A correspondência material × CATMAT não foi conferida por nenhuma pessoa.** Todas as 2.306 decisões vêm de agentes de IA (554 com confiança alta, 1.216 média, 536 baixa). Por isso 100% do valor comparável está sob correspondência não conferida. A concordância medida (80%, 119/149) compara IA com IA: os 150 rótulos de referência também foram feitos por IA. O arquivo `rotulos_referencia.csv` coincide em 98,7% com `decisoes_agentes.csv`, então medir um contra o outro não é validação independente. **Ação:** uma pessoa confere, por prioridade (`ouro.resumo_correspondencia.prioridade_revisao`), e esse conjunto vira a referência.
2. **A série mensal tem buracos.** O portal não publicou 16 dos 55 meses entre 06/2021 e 12/2025 (29%). Há queda de ~1.830 para ~830 linhas em 11/2022 (já em `excecoes_qualidade`). Gráficos de série devem mostrar só meses publicados, sem interpolar.
3. **O estoque mais recente é de 12/2025**, com mais de 300 dias de atraso diante do SLA de 45 dias; o painel avisa.
4. **A unidade de fornecimento não existe no estoque.** O estoque não informa unidade; só se vê a das compras. Diferenças extremas costumam ser galão × frasco ou caixa × unidade, não sobrepreço.
5. **Cobertura de preço público de 50,9% do valor** (3.528 códigos aprovados, 70% com compra na janela). Metade do valor do estoque não tem referência.
6. **`valor_total` diverge de saldo × preço em 4,5% das linhas** (1.748), mas só 154 em mais de 1%. O fato recalcula o valor, então o efeito financeiro é pequeno; ainda vale pedir correção à fonte.

## Ordem do pipeline

Corrigida nesta rodada: `transformar` não constrói mais `compras_bronze` e dependentes (rodavam sobre `raw.compras` vazia); `semantica tudo` executa `sincronizar → embeddings → corresponder → importar → validar`, e `validar` falha o serviço se algo ficou pela metade.

## Limitações desta análise

Não rodamos o pipeline completo com o CATMAT e as compras reais nesta análise; as métricas de compras e de correspondência acima vêm da documentação e dos arquivos versionados, e os limites de `qualidade_dados` devem ser recalibrados depois da primeira carga completa.
