# ADR 04 — Adotar o estoque da UnB e preços públicos como foco do projeto

- **Status:** aceito
- **Data:** 2026-09-28
- **Decisores:** Grupo 13 — Matheus Henrick Dutra dos Santos, Israel Thalles Dutra dos Santos, Samara Letícia Alves dos Santos e Magno Luiz Vale Vieira.

## Contexto

O escopo inicial reunia cinco datasets da UnB: estoque do almoxarifado, unidades acadêmicas, empenhos, gastos por unidade e requisições de serviços. As fontes de requisições e despesas não oferecem um vínculo confiável e suficientemente detalhado com os materiais do estoque. Com isso, seria difícil identificar quais itens foram comprados e produzir indicadores diretamente úteis à gestão de materiais.

A equipe decidiu concentrar a análise nos registros de estoque e enriquecê-los com duas fontes do Compras.gov.br: o Catálogo de Materiais (CATMAT), para apoiar a identificação dos itens, e os registros de pesquisa de preços públicos, para obter referências de compras. Essa escolha foi motivada pelo teste de viabilidade: verificar se era possível partir de descrições do estoque, encontrar candidatos CATMAT e consultar preços públicos para esses candidatos. O CATMAT não confirma automaticamente uma correspondência: descrições semelhantes precisam de validação, e os preços só são comparáveis quando item, unidade e período forem compatíveis.

É estimado aproximadamente 1.900 registros mensais de estoque, volume equivalente de dados de compras públicas e mais de 345 mil itens no catálogo CATMAT. A unidade da estimativa de compras não está especificada. A frequência prevista é em lote. O projeto deve usar ferramentas gratuitas e viáveis para a equipe. As consultas às APIs externas introduzem dependência de disponibilidade, estabilidade e formato das respostas.

## Alternativas consideradas

### A. Opção nula — manter o escopo original de requisições e despesas

Manter as cinco bases originalmente escolhidas aproveitaria o trabalho de levantamento e os scripts já produzidos e permitiria análises orçamentárias e de demanda das unidades. Porém, os dados disponíveis têm granularidades diferentes e não demonstram uma relação confiável entre despesas, requisições e materiais do estoque. O escopo também exigiria integrar várias bases sem garantir uma resposta direta sobre gestão de materiais.

### B. Usar estoque, CATMAT e pesquisa de preços públicos — escolhida

Usar o estoque da UnB como base principal, o CATMAT para propor códigos de materiais e a API de pesquisa de preços do Compras.gov.br para consultar compras comparáveis. Essa opção concentra o trabalho em materiais e oferece uma referência pública de preços sem tratar correspondências textuais como verdade confirmada.

O custo é implementar e validar a correspondência entre descrições do estoque e códigos CATMAT, além de compatibilizar unidades e datas. O volume indicado é superior a 345 mil itens no catálogo, portanto a busca deve ser controlada e reproduzível, em vez de comparar cada registro indiscriminadamente.

### C. Usar preços de lojas online, via Mercado Livre

Essa alternativa permitiria observar preços de varejo. No entanto o acesso para desenvolvedores exigia criar uma aplicação e usar autenticação por token, o que impedia compartilhar o acesso entre todos os membros e a professora. A alternativa não foi escolhida por essa barreira operacional e de acesso.

## Medição e evidências

O teste de viabilidade foi a evidência prática que sustentou a escolha: a equipe avaliou a obtenção do catálogo CATMAT, a geração de candidatos a partir dos materiais do estoque e a consulta de registros de compra por código candidato. O teste também orientou a comparação com a alternativa de preços de varejo, cujo acesso via Mercado Livre exigia aplicação e token, considerados inviáveis para o acesso compartilhado pela equipe e pela professora.

O procedimento e os scripts do teste estão no repositório:

- [Baixar o catálogo CATMAT](../../codigos/baixar_catalogo_catmat.py)
- [Gerar candidatos CATMAT](../../codigos/gerar_candidatos_catmat.py)
- [Validar candidatos e consultar preços públicos](../../codigos/validacao_e_cobertura_precos.py)
- [Procedimento do teste de viabilidade](../testes/teste-de-viabilidade.md)

O teste verificou a viabilidade do caminho escolhido, não certificou a qualidade das correspondências nem a cobertura de todos os materiais. O documento descreve a execução e a interpretação dos resultados.

| Alternativa | Fontes principais | Granularidade útil para materiais | Evidência disponível |
|---|---|---|---|
| A — escopo original | Cinco fontes de dados da UnB | Insuficiente para vincular despesas e requisições a itens do estoque com confiança | Inventário histórico de 453 recursos; não comprova integração semântica entre fontes |
| B — escolhida | Estoque, CATMAT e pesquisa de preços públicos | Material do estoque associado a candidato CATMAT e a compras consultadas, sujeito a validação | Teste de viabilidade executado e procedimento reproduzível; métricas agregadas da execução não preservadas |
| C — Mercado Livre | Estoque e API de varejo | Potencialmente por produto e anúncio, se o acesso funcionar | Não foi possível obter acesso à API. |

## Decisão

Adotamos o estoque do almoxarifado da UnB como fonte principal do projeto, enriquecido com o CATMAT e com preços de compras públicas consultados pela API do Compras.gov.br. O escopo deixa de priorizar as análises baseadas em requisições e despesas das cinco fontes originais.

A análise deve identificar e validar as correspondências entre materiais e CATMAT e comparar preços apenas quando houver compatibilidade suficiente de produto, unidade e período. Os preços consultados são referências de compras públicas; não serão descritos como cotações de lojas nem como prova automática de sobrepreço.

## Consequências

**O que ganhamos:**

- Uma pergunta mais diretamente relacionada à gestão de materiais e almoxarifados.
- Menos fontes centrais para a análise e uma função definida para cada uma das três fontes escolhidas.
- Uma forma de consultar preços públicos sem depender do acesso autenticado do Mercado Livre.
- Um fluxo de validação explícito, que permite separar candidatos de correspondências confirmadas.
- Uma decisão baseada em um teste de viabilidade do próprio domínio, em vez de somente na comparação teórica das fontes.

**O que perdemos e assumimos:**

- As análises de requisições de serviços, gastos por unidade, empenhos e unidades acadêmicas deixam de ser o foco.
- A qualidade da análise depende de correspondências entre descrições textuais e códigos CATMAT; correspondências erradas podem produzir comparações enganosas.
- A disponibilidade e a estabilidade das APIs do Compras.gov.br passam a ser dependências externas. Alterações de endpoint, paginação ou formato exigirão manutenção dos scripts.
- Nem todo material terá uma referência pública comparável; os resultados devem informar a cobertura e as exclusões.
- A prova de conceito não substitui uma avaliação de precisão, cobertura e desempenho em uma amostra representativa.



## Gatilho de revisão

Revisar esta decisão após duas execuções completas do piloto, ou antes se uma fonte deixar de estar acessível. Reabrir o escopo se:

- menos de **50%** dos materiais da amostra de validação tiverem simultaneamente uma correspondência CATMAT revisada e pelo menos um preço público comparável; ou
- a API do Compras.gov.br falhar em duas execuções completas consecutivas; ou
- os dados disponíveis não permitirem verificar unidade ou período em mais da metade dos preços que seriam usados na comparação.

O limiar de 50% é um critério inicial de viabilidade do piloto, não uma afirmação sobre a cobertura atual. Registrar cobertura, falhas e motivos de exclusão em cada execução antes de decidir manter ou rever o escopo.
