# SIGMA-UnB

**Sistema Integrado de Gestão de Materiais e Almoxarifado**

O SIGMA-UnB mostra os materiais disponíveis no almoxarifado da Universidade de Brasília e monitora seus preços em lojas online ao longo do tempo.

Ele foi feito para evitar compras acima do preço de mercado e facilitar o acompanhamento da disponibilidade e do custo dos materiais.

!!! question "Pergunta de gestão"
    _A definir pela Squad: uma frase com sujeito e recorte._

---

## Quem usa

- Gestores da UnB
- Chefes de departamento
- Centro Acadêmico

## Fontes de dados

Todos os dados vêm do portal de dados abertos da UnB, o [dados.unb.br](https://dados.unb.br). Os preços de mercado são coletados pelo próprio SIGMA.

| Fonte | Conteúdo | Dado pessoal? |
|---|---|---|
| Estoque de Materiais | Material, almoxarifado, saldo, preço e valor total | Não |
| Requisições de Serviços | Pedidos de manutenção, limpeza, transporte etc., com datas e situação | Sim |
| Gastos por Unidade | Gastos de cada unidade por natureza da despesa e período | Não |
| Empenhos | Notas de empenho: número, data, credor, valor e natureza da despesa | Sim |
| Unidades Acadêmicas | Código, sigla, nome, tipo e unidade superior | Não |
| Cotações online | Preço de cada material em lojas online, coletado toda semana | Não |

## Arquitetura em uma linha

**Portal da UnB** → camada bruta (JSON/CSV originais) → **banco transacional PostgreSQL** → camada analítica em **Parquet** (lida com DuckDB) → painéis e relatórios.

Tudo sobe com um único `docker compose up --build`. O passo a passo está no [README do repositório](https://github.com/samarawwleticia/SIGMA-UnB#readme).

## Modelagem

=== "Diagrama entidade-relacionamento"

    ![Diagrama entidade-relacionamento](assets/Diagrama%20entidade-relacionamento.v1.0.png)

=== "Modelo relacional"

    ![Modelo relacional](assets/Modelo%20relacional.v1.0.png)

## Entregas

| Entrega | Tema | Data |
|---|---|---|
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
