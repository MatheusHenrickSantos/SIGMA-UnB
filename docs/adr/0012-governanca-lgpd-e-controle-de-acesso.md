# 0012 — Minimizar dado pessoal na raw e controlar acesso por papéis com recorte de coluna e de linha

- **Status:** proposto (falta a revisão da Squad e a confirmação da base legal com o encarregado de dados da UnB)
- **Data:** 2026-11-24
- **Decisores:** [a definir pela Squad] — proposta preparada com assistente de IA (ver [Uso de IA](../gestao/ai-usage.md))

## Contexto

A API de pesquisa de preços devolve, em cada compra pública, o CNPJ ou CPF e o nome do fornecedor. Medimos as 41.522 compras reais (2025-07 a 2025-12, 6.908 fornecedores distintos) antes da minimização: **41.489 com CNPJ (14 dígitos), 11 com CPF (11 dígitos) e 22 sem número de 11 ou 14 dígitos**. Uma amostra anterior de 60 códigos (408 registros) só tinha CNPJ e dava a impressão de que não havia CPF. Além disso, empresário individual e MEI têm o nome da pessoa no nome empresarial. A análise de preço não usa esses campos. Além deles há nomes de revisores e de usuários de acesso. O estoque e o CATMAT não têm dado pessoal.

Antes desta decisão, o painel e o pipeline conectavam com um só usuário dono do banco, e o JSON bruto das compras ficava inteiro na raw. Restrições: projeto acadêmico em PostgreSQL, equipe sem DPO próprio, exigência de privilégio mínimo demonstrado em ao menos um recorte.

## Alternativas consideradas

### A. Opção nula — manter tudo na raw e um usuário só

Preserva o dado original para reprocessar e não cria papéis. Não escolhida: guarda dado pessoal sem finalidade (viola a necessidade, art. 6º, III) e dá a qualquer cliente leitura de tudo.

### B. Filtrar na aplicação (o painel esconde colunas e linhas)

Simples de fazer. O controle morre fora do painel: quem conecta ao banco vê tudo.

### C. Minimização na raw + papéis no banco, com recorte de coluna e de linha (RLS) — escolhida

A função `raw.remover_identificacao_fornecedor()` (V12) apaga os dois campos do JSON depois da bronze; `sigma_painel`, `sigma_compras` e `sigma_almoxarifado` (V11) só têm o que precisam; `GRANT` por coluna esconde `justificativa_agente`; RLS limita as chefias aos seus almoxarifados. Um teste do dbt impede coluna de fornecedor nas camadas analíticas.

### D. Mascarar na leitura (views com hash do fornecedor)

Mantém o dado na raw e só esconde a leitura. Hash de CNPJ é pseudonimização reversível por dicionário (o CNPJ tem poucos dígitos úteis); não elimina o dado pessoal.

## Medição

```bash
dbt build --select acesso_almoxarifado alerta_preco_compras sem_identificador_de_fornecedor
# roles e consultas: docs/governanca/acesso.md
python codigos/gerar_catalogo.py
```

| Verificação | Resultado |
|---|---|
| Fornecedor em 41.522 compras reais, antes da minimização | 41.489 CNPJ, **11 CPF**, 22 outros; 6.908 distintos |
| Minimização: arquivo com 2 itens com `niFornecedor` e `nomeFornecedor` | 1 arquivo alterado; depois, 0; segunda execução altera 0 (idempotente); ordem dos itens preservada |
| `compras_bronze` reconstruída depois da minimização | 8 testes passam |
| Teste de coluna de fornecedor nas camadas analíticas | passa |
| `ana_compras` lê `justificativa_agente` | `permission denied` |
| `joao_prc` (RLS) lê o alerta | 80 linhas, só `PRC` (o dono vê 91) |
| `joao_prc` lê `ouro` e `raw` | `permission denied for schema` |
| `sigma_painel` | lê `ouro`; não lê `raw` nem `reverso` |

## Decisão

Escolhemos C. A minimização liga por padrão (`remover_identificacao_fornecedor: true`) e é desligável por variável do dbt.

## Consequências

**O que ganhamos:** o dado pessoal que não serve à análise não fica guardado; o controle vale no banco, para qualquer cliente; a falha é fechada (usuário sem mapeamento não vê linha).

**O que perdemos:** a raw deixa de ser cópia fiel do que a fonte devolveu: não se recupera o fornecedor sem baixar de novo, e uma análise futura por fornecedor (a pergunta original do backlog, RF-03) exige baixar a API de novo com a variável desligada e rever esta decisão. O cache em disco (`dados/compras_cache`) segue com o JSON original até ser apagado, o que hoje é manual. Quem cria usuários e senhas passa a ser trabalho operacional fora do repositório. As chefias só são mapeadas por uma semente CSV, que não escala bem.

**O que se torna irreversível:** a remoção na raw. Reverte-se apenas baixando as compras de novo.

## Gatilho de revisão

- Aparecer **qualquer** `niFornecedor` com 11 dígitos (CPF) na raw antes da minimização: tratar como dado pessoal identificado, revisar a base legal e o prazo com o DPO. **Disparou em 24/11/2026** (11 compras com CPF). Efeito: a minimização deixa de ser só preventiva; o DPO precisa confirmar que a remoção feita já na raw é suficiente e se o dump `~/sigma-backups/sigma-real-pre-integracao.dump`, que guarda esses dados, deve ser apagado.
- A pergunta de gestão passar a exigir o fornecedor (RF-03): reabrir a minimização (reter só o CNPJ de pessoa jurídica, com acesso restrito).
- O painel for exposto **fora da rede da UnB** ou ganhar login por usuário: mapear linhas por usuário e a conexão do painel já usa `sigma_painel_app` (V13).
- Mais de **20 usuários** com mapeamento por almoxarifado: sair da semente CSV para uma tabela gerida.
- O encarregado de dados da UnB discordar da base legal ou do prazo: revisar a retenção.
