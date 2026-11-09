# <img src="https://raw.githubusercontent.com/MatheusHenrickSantos/SIGMA-UnB/refs/heads/main/docs/assets/icone.png" alt="icone" width="50"> SIGMA-UnB

**Sistema Integrado de Gestão de Materiais e Almoxarifado**

O SIGMA-UnB é uma plataforma de dados para apoiar a gestão de materiais e as decisões de compra da Universidade de Brasília. Ela reúne informações do estoque dos almoxarifados, do catálogo CATMAT e de compras públicas para identificar materiais, acompanhar sua disponibilidade e analisar preços.

As comparações de preços dependem de identificar correspondências confiáveis entre os itens e de comparar unidades e períodos equivalentes.

> **Pergunta de gestão**
>
> Para quais materiais do estoque da UnB é possível encontrar um item correspondente no CATMAT e em compras públicas comparáveis, e quais apresentam as maiores diferenças entre o preço registrado no estoque e os preços dessas compras, por almoxarifado e período?

---

## Quem usa

- Gestores da UnB
- Chefes de departamento
- Centro Acadêmico

## Fontes de dados

O Estoque de Materiais vem do portal de [Dados Abertos da UnB](https://dados.unb.br) e representa os itens de almoxarifado da UnB.  

O Catálogo de Materiais, do Sistema Integrado de Administração e Serviços Gerais – SIASG, é uma base de dados que identifica todos os materiais licitados e adquiridos pela Administração Pública Federal. Já o serviço de consulta de preços permite acesso aos dados e informações de itens comprados por meio da Administração, o qual tem como objetivo auxiliar os órgãos governamentais na etapa de pesquisa de preços, que é um passo crucial no planejamento de compras e contratações públicas. Ambos são extraídos por meio da [API de Dados Abertos do Compras.gov.br](Comprashttps://dadosabertos.compras.gov.br/swagger-ui/index.html).

| Fonte | Conteúdo | Dado pessoal? |
| :---: | :------- | :-----------: |
| Estoque de Materiais | Material, almoxarifado, saldo, preço e valor total. | Não |
| Catálogo de Materiais (CATMAT) | Códigos que identificam a família do item e os respectivos nomes. | Não |
| Compras Públicas | Dados como data da compra, item comprado, quantidade, preço e comprador. | Sim |



## Entregas

| Entrega | Tema | Data |
| :-----: | :--- | :--: |
| E1 | Fonte transacional modelada e populada | 22/09/2026 |
| E2 | Ingestão em lote e captura de mudanças | 13/10/2026 |
| E3 | Camada analítica transformada, testada e orquestrada | 03/11/2026 |
| E4 | Plataforma completa, governada e defendida | 24/11/2026 |

## Equipe

- Israel Thalles Dutra dos Santos
- Magno Luiz Vale Vieira
- Matheus Henrick Dutra dos Santos
- Samara Letícia Alves dos Santos

_Sistemas de Banco de Dados 2 · Turma 03 · 2026.2 · FCTE/UnB_
