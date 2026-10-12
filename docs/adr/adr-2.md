# Adotar ELT: guardar o bruto do portal na bronze antes de qualquer transformação

- **Status:** proposto (passa a aceito quando a tabela de Medição estiver preenchida)
- **Data:** 2026-10-12
- **Decisores:** Squad SIGMA-UnB (confirmar nomes na revisão)

## Contexto

Na E1, o caminho do dado era um ETL: o `baixar_dados.py` grava os arquivos do
portal em `dados/bruto/`, e o `carregar.py` limpa, converte e grava direto no
PostgreSQL. A pasta `dados/bruto/` fica só na máquina de quem rodou e está no
`.gitignore`. Se uma regra de limpeza mudar, o único jeito de reprocessar é
baixar tudo de novo do portal.

Características da fonte que pesam na decisão:

- **Volume:** a primeira coleta baixa cerca de 850 MB, a maior parte de empenhos
  (README, seção "O que deve aparecer").
- **Disponibilidade:** o `dados.unb.br` responde `502` com frequência; o
  `baixar_dados.py` precisa de até 5 tentativas por arquivo.
- **Estabilidade:** o portal publica uma vez por mês e pode republicar um arquivo
  com o mesmo nome e conteúdo diferente. Não há garantia de que arquivos antigos
  continuem disponíveis.
- **Equipe:** domina SQL e Python; a E3 vai exigir transformações versionadas e
  testadas.

A disciplina e o mercado usam ELT com camadas (bronze, prata, ouro) justamente
pela rastreabilidade: o original fica guardado e qualquer transformação pode ser
refeita a partir dele.

## Alternativas consideradas

### A. Opção nula: manter o ETL da E1

Funciona hoje e é simples: um script baixa, outro carrega. O problema é que o
dado original só existe numa pasta local ignorada pelo git. Uma mudança de
regra exige baixar ~850 MB de um portal instável, e se o portal apagar ou trocar
um arquivo, a versão antiga se perde. Também não há como provar, depois, de qual
arquivo veio uma linha do banco.

### B. ELT com bronze no data lake

Os arquivos do portal sobem sem alteração para `bronze/portal/` no MinIO, com o
sha256 do conteúdo no caminho. O mesmo conteúdo nunca é enviado duas vezes, e uma
versão republicada fica ao lado da anterior. As tabelas do Postgres também chegam
à bronze em Parquet (lote e CDC, ver ADR 3 e ADR 4). A limpeza passa a ser SQL
versionado na E3 (prata e ouro).

### C. Guardar o bruto no git (ou Git LFS)

Dá versionamento de graça, mas ~850 MB por coleta num repositório público deixa
o `git clone` lento para todos, inclusive para a monitoria que corrige a partir
de um clone limpo. O Git LFS tem cota baixa no plano gratuito do GitHub.

## Medição

Medido com os dados reais do portal, depois de `docker compose up --build`:

```
docker compose run --rm extract python medir_e2.py
```

| Alternativa | Onde o original fica | Volume guardado | Reprocessar sem o portal |
|---|---|---|---|
| A — ETL atual | só em `dados/bruto/` local | _preencher_ | não é possível em outra máquina |
| B — ELT com bronze | `bronze/portal/` no MinIO | _preencher (seção ADR 2 da saída)_ | _preencher: tempo para ler tudo de volta_ |
| C — bruto no git | repositório | igual a B, por clone | tempo do `git clone` |

## Decisão

Escolhemos B: ELT, com a bronze guardando o original do portal e as fotos e
mudanças do Postgres em Parquet. A transformação sai do Python antes da carga
e vai para SQL versionado depois (E3).

## Consequências

**O que ganhamos:**

- Qualquer regra nova de limpeza pode ser refeita a partir da bronze, sem depender
  do portal estar no ar.
- Rastreabilidade: o manifesto de cada coleta (`bronze/portal/_manifestos/`) liga
  cada arquivo à URL e à data de modificação no portal.
- Versões republicadas pelo portal ficam guardadas lado a lado.

**O que perdemos:**

- Espaço: o bruto ocupa disco duas vezes na máquina (`dados/bruto/` e o volume do
  MinIO), e a bronze só cresce, porque nada é apagado.
- Um serviço a mais no compose (MinIO) para subir, monitorar e documentar.
- Na E2 o `carregar.py` ainda transforma em Python antes do Postgres. O ELT
  completo (bronze → prata → ouro em SQL) só fica pronto na E3. Até lá convivem
  os dois estilos.

**O que se torna irreversível:**

Pouco. A bronze é aditiva: voltar ao ETL puro é só parar de rodar o
`enviar_bruto.py`. O que não volta é a disciplina de "não transformar antes de
guardar": se ela for quebrada, o original daquele período se perde.

## Gatilho de revisão

- Revisar se o volume do MinIO passar de 5 GB na máquina de algum integrante.
- Revisar se ler a bronze/portal de volta levar mais de 10 minutos (aí o ganho
  sobre baixar do portal deixa de ser claro).
