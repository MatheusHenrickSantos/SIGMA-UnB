# 0011 — Devolver os alertas de preço a compras por arquivo CSV e por tabela, com o destino puxando

- **Status:** proposto (falta a revisão da Squad e a confirmação de uso pelo setor de compras)
- **Data:** 2026-11-24
- **Decisores:** [a definir pela Squad] — proposta preparada com assistente de IA (ver [Uso de IA](../gestao/ai-usage.md))

## Contexto

O painel informa; para o dado mudar o que acontece, ele precisa chegar a quem decide a próxima compra. Consumidor: setor de compras e chefias de almoxarifado da UnB. Ação: conferir unidade e preço do material antes de comprar de novo e, se confirmado, renegociar.

Carga: o estoque muda **uma vez por mês** (o portal publica no mês seguinte; SLA de 45 dias); a lista tem ordem de **dezenas a poucas centenas** de linhas por mês. Latência tolerada: dias. Restrições: não conhecemos um sistema operacional da UnB com API para receber alertas de preço; a equipe não opera filas nem serviços de longa duração; dados de pessoas não saem (ver [LGPD](../governanca/lgpd.md)).

## Alternativas consideradas

### A. Opção nula — CSV agendado

Um arquivo por mês numa pasta, lido por quem quiser. É a opção forte e foi **mantida como um dos dois caminhos**: sem integração, sem dependência de o destino estar no ar, abre no Excel.

### B. Tabela no banco lida pelo consumidor (o destino puxa)

`reverso.alerta_preco_compras`, com papéis do banco e recorte de linha e coluna (RLS). Serve quem tem uma aplicação ou planilha conectada ao PostgreSQL. Cobra criar e manter usuários.

### C. Empurrar para um sistema (API, webhook, fila)

Faz sentido quando o destino tem API e alguém age dentro dele. Não conhecemos esse destino; escrever o cliente seria integração por reflexo. Exigiria política de reenvio e idempotência no destino.

### D. Federação de consultas (o consumidor lê o warehouse por foreign data wrapper de outro banco)

Acopla o destino ao nosso esquema e ao nosso banco; descartada.

## Medição

Banco local com estoque real e compras sintéticas (a carga real das compras não rodou nesta medição; mede forma e custo, não a lista final).

```bash
docker compose run --rm exportar            # CSV + manifesto
dbt test --select consistencia_metricas_e_alertas
```

| Alternativa | Custo medido | Se o destino cai | Acoplamento |
|---|---|---|---|
| A — CSV | 0,14 s para 91 linhas; arquivo de poucos KB | Nada se perde: regrava o mesmo nome | Nenhum |
| B — tabela com RLS | leitura direta; sem etapa extra | Nada se perde: a tabela é a fonte | Usuário de banco por consumidor |
| C — push | não medido (sem destino) | Precisa de reenvio e idempotência | Alto |

Consistência: 91 alertas na tabela = 91 em `materiais_alertados` (teste passa). Latência do mês: o arquivo sai depois de `transformar_ouro` na mesma execução do Dagster.

## Decisão

Entregar por **A e B**: `exportar` grava CSV atômico com manifesto (linhas, sha256, mês, versão das métricas) e `reverso.alerta_preco_compras` fica legível pelos papéis `sigma_compras` e `sigma_almoxarifado`. O **destino puxa**; a frequência é mensal. Se o destino estiver fora do ar, nada é perdido; se o `exportar` falhar, o Dagster refaz a etapa até 3 vezes (30, 60, 120 s) e o arquivo anterior permanece.

## Consequências

**O que ganhamos:** nenhuma dependência de sistema externo, nenhum estado de entrega a reconciliar; o consumidor decide quando ler; o mesmo conjunto de linhas vale para o arquivo e para a tabela.

**O que perdemos:** não sabemos se alguém leu. Sem um retorno (alerta conferido, descartado por unidade, renegociado), o alerta pode virar "mais uma tabela". Quem lê o arquivo vê o dado do mês, não o do dia. O CSV leva o que o grupo `sigma_compras` vê: não serve para chefias que só podem ver o próprio almoxarifado (para elas, B).

**O que se torna irreversível:** nada em dado. Quem passar a depender do nome do arquivo (`alertas_preco_atual.csv`) e das colunas cria um contrato: mudar as colunas passa a ser mudança de interface.

## Gatilho de revisão

- Compras **não abrir nem consultar** o alerta em 2 ciclos mensais seguidos: remover o ETL reverso (é mais uma tabela) ou trocar de consumidor.
- Surgir um sistema de destino com API **e** alguém agindo dentro dele: avaliar o push (alternativa C) com reenvio e idempotência.
- Mais de **500 alertas por mês**: a lista deixa de ser acionável; subir `limiar_diferenca_pct` ou ordenar por valor e cortar.
- Passar de mensal para **mais de uma carga por dia** (ADR 0007): rever arquivo único e nome estável.
- Medir com a carga real (CATMAT e compras completos) e registrar a taxa de alertas descartados por unidade diferente; se passar de **50%**, o alerta precisa converter unidade antes de sair.
