# 0005 — Sugerir candidatos CATMAT por similaridade de embeddings no PostgreSQL (pgvector), com busca exata

- **Status:** proposto (falta a revisão da Squad e a medição com vetores reais; ver *Gatilho de revisão*)
- **Data:** 2026-11-08
- **Decisores:** [a definir pela Squad] — proposta preparada com assistente de IA (ver [Uso de IA](../ai-usage.md))

## Contexto

O [ADR 04](0004-adotar-dados-de-estoque-e-precos-publicos.md) (ainda na branch `documentação`) põe o estoque da
UnB no centro do projeto e usa o CATMAT para chegar aos preços de compras
públicas. O estoque não tem código de item: cada material é uma descrição
livre. Para comparar preço é preciso saber a qual item CATMAT cada descrição
corresponde.

Hoje isso é feito pelo [teste de viabilidade](../testes/teste-de-viabilidade.md):
`gerar_candidatos_catmat.py` ranqueia o catálogo por semelhança de caracteres
(rapidfuzz) e `validacao_e_cobertura_precos.py` aponta conflitos de
especificação. Os scripts rodam fora do Docker, leem e gravam CSV e
recomeçam do zero a cada execução.

Caracterização da carga:

| Item | Valor | Fonte |
|---|---|---|
| Materiais distintos no estoque | ~2.400 (2.382 na tabela `material`) | [Caracterização da carga](../caracterizacao-da-carga.md) |
| Linhas novas de estoque por mês | ~700–800 | idem |
| Itens no CATMAT | mais de 345 mil | ADR 04 |
| Frequência | lote mensal (o portal publica uma vez por mês) | |
| Latência tolerada | minutos por execução | não há consulta interativa hoje |

O casamento por caracteres falha quando o mesmo material é escrito de jeitos
diferentes: o estoque usa texto livre e abreviado ("CANETA ESFEROGR. AZUL
PONTA MEDIA"), o CATMAT usa o padrão "NOME, ATRIBUTO: VALOR, ..." ("CANETA
ESFEROGRÁFICA, MATERIAL: PLÁSTICO, TIPO ESCRITA: MÉDIA, COR TINTA: AZUL").

Restrições: ferramentas gratuitas; só CPU (máquinas da equipe e Codespaces);
a plataforma precisa subir do zero com `docker compose up`; a equipe domina
SQL e PostgreSQL. E a restrição do ADR 04: **semelhança de texto não confirma
equivalência**, e toda correspondência passa por revisão humana.

## Alternativas consideradas

### A. Opção nula — manter o ranking por caracteres (rapidfuzz) em CSV

É viável: já existe, é barato, explica por que um candidato apareceu (tokens
em comum) e não depende de modelo nem de internet. Não foi escolhida como
mecanismo principal porque não aproxima descrições com palavras diferentes e
mesmo sentido, roda fora do banco e do Docker, recalcula tudo a cada vez e não
guarda proveniência nem decisões. Continua útil como sinal complementar (ver
*Consequências*).

### B. Embeddings + pgvector no PostgreSQL existente, busca exata — escolhida

Um modelo multilíngue gera um vetor por descrição; o PostgreSQL guarda os
vetores (extensão pgvector) e ordena por distância de cosseno, varrendo todos
os vetores do CATMAT para cada material. Usa o banco que já existe, junta
direto com a Prata, é exata e determinística. Cobra o tempo da varredura.

### C. Embeddings + pgvector com índice HNSW (busca aproximada)

Mesmo armazenamento, com um índice de vizinhos aproximados. Consultas de
milissegundos; cobra espaço, tempo de inserção e resultados aproximados
(recall abaixo de 1, que precisa ser medido).

### D. Banco vetorial dedicado (Qdrant, Milvus) ou FAISS em arquivo

Desempenho e recursos de busca vetorial maiores, mas mais um serviço (ou
arquivo) para manter, os dados saem do PostgreSQL e cada junção com a Prata
vira código de aplicação. Para ~345 mil vetores, o PostgreSQL atende (ver
medição).

### Escolhas dentro de B

| Escolha | Opção adotada | Alternativas | Motivo |
|---|---|---|---|
| Modelo | `intfloat/multilingual-e5-small` (384 dim.) | MiniLM-L12 multilíngue (384), e5-base (768), bge-m3 (1024) | treinado para recuperação, inclui português, 512 tokens, viável em CPU; MiniLM corta em 128 tokens; os maiores são 3× ou mais lentos em CPU |
| Métrica | cosseno (`<=>`) | produto interno, L2 | com vetores de norma 1 a ordem é a mesma; cosseno é a métrica de treino do e5 e dá nota legível (1 = idêntico) |
| Onde guardar | schema `semantica`, separado da Prata | tabelas na Prata | escrito por Python, não pelo dbt; depende do modelo; não se reconstrói só com SQL |
| Plausibilidade | regras de especificação do teste de viabilidade | só a nota | o embedding pesa pouco números e unidades (AA × AAA) |

## Medição

O que foi medido: latência da busca, recall da HNSW, custo de carga e espaço,
com o volume do domínio (345 mil vetores CATMAT de 384 dimensões e 2.400
materiais), em PostgreSQL 16.15 + pgvector 0.8.7, numa máquina de 2 CPUs e
7 GB de RAM.

**Limite desta medição:** o ambiente em que ela foi feita não tinha acesso ao
Hugging Face nem ao Compras.gov.br, então os vetores são **aleatórios**
(normalizados), não vetores do modelo sobre descrições reais. O volume e a
dimensão são os do domínio; a distribuição não. Vetores aleatórios são o pior
caso para a HNSW (as distâncias ficam quase todas iguais), por isso o recall
abaixo não prevê o recall real. A medição com dados reais é o primeiro item do
gatilho de revisão.

Como reproduzir:

```bash
# vetores aleatórios no volume do domínio (schema temporário, apagado no fim)
docker compose run --rm semantica python medir_adr0005.py sintetico --catmat 345000 --materiais 2400 --amostra 100

# vetores reais, depois de `docker compose up` (cria um índice temporário e o apaga)
docker compose run --rm semantica python medir_adr0005.py real --amostra 100
```

| Alternativa | Latência por material (mediana / p95) | 2.400 materiais | Recall@10 | Carga de 345 mil vetores | Espaço extra |
|---|---|---|---|---|---|
| A — rapidfuzz em CSV | não medido nesta rodada | — | — | — | — |
| B — pgvector, busca exata | 107 / 134 ms | **451 s** pelo pipeline completo¹ | 1 (exata) | ~7.200 vetores/s (< 1 min)² | 0 |
| C — pgvector, HNSW (m=16, ef_construction=64) | 4 / 5 ms (ef_search 40) · 19 / 25 ms (ef_search 200) | 11,6 s (LATERAL pelo índice) | 0,03 (ef 40) a 0,10 (ef 200), **com vetores aleatórios** | ~111 vetores/s com o índice (~52 min, extrapolado) ou 203 s de `CREATE INDEX` após carga | índice de 691 MB (tabela: 547 MB) |
| D — banco dedicado | não medido | — | — | — | novo serviço |

¹ `python -m semantica corresponder --top-k 10` sobre o schema `semantica`
com os vetores sintéticos: busca, checagem de especificações dos 24.000
candidatos e gravação.
² `repositorio.gravar_vetores` em lotes de 256, sem índice.

Tempo do modelo (o mesmo para B, C e D): ~260 textos/s em 2 threads, medido
com a arquitetura do e5-small e pesos aleatórios (o tempo não depende dos
pesos) — ~22 min para 345 mil itens, uma vez; depois, só o que mudar.

## Decisão

Escolhemos **B**: embeddings de `intfloat/multilingual-e5-small`, guardados em
`vector(384)` no schema `semantica` do PostgreSQL existente, comparados por
distância de cosseno com **busca exata** (a migração V3 remove o índice HNSW
que a V2 havia criado antes da medição). Para cada material são guardados os
10 itens CATMAT mais próximos, com a nota de similaridade e a checagem de
especificações; nenhum é aprovado automaticamente, e as decisões humanas
ficam em `revisao_correspondencia`. Não há limiar padrão de similaridade
até haver pares revisados para calibrá-lo.

## Consequências

**O que ganhamos:**

- correspondência por sentido, não só por caracteres, dentro do banco e do
  `docker compose up`, juntável por SQL com a Prata;
- processamento incremental (só textos novos ou alterados vão ao modelo) e
  proveniência completa: texto original, versão da normalização, modelo e
  commit, parâmetros de cada execução;
- resultado exato e reprodutível: a mesma entrada gera os mesmos candidatos;
- decisões humanas que sobrevivem aos reprocessamentos.

**O que perdemos:**

- **Imagem e download:** o serviço `semantica` tem ~1 GB (PyTorch de CPU) e
  baixa ~0,5 GB do Hugging Face na primeira execução. Sem acesso a esse site a
  etapa não roda; o volume `modelos` evita baixar de novo.
- **Tempo de CPU:** a primeira execução completa soma ~22 min de modelo e
  ~7,5 min de busca nas máquinas da equipe; cada execução mensal repete a
  busca (~7,5 min), mesmo que pouca coisa tenha mudado.
- **Espaço:** ~550 MB de vetores no banco. Não caberia no plano gratuito do
  Supabase (500 MB) citado na planilha de acompanhamento (bloco 4, cargas e
  engines); no PostgreSQL do Docker não é problema.
- **Acoplamento à dimensão:** `vector(384)` amarra o esquema ao modelo; trocar
  por um de outra dimensão exige migração e recalcular todos os vetores.
- **Qualidade desconhecida:** nada aqui mede se os candidatos estão certos.
  Isso só se sabe revisando uma amostra; até lá os candidatos não devem ser
  usados para comparar preços.
- O sinal lexical do teste de viabilidade não entra na nota. Uma combinação
  (híbrida) pode ser avaliada depois da primeira revisão.

**O que se torna irreversível:**

Pouco. O schema `semantica` é derivado da Prata e pode ser apagado e
recalculado (~30 min), **exceto** `revisao_correspondencia`, que deve ser
exportada antes. Voltar ao índice HNSW é uma migração com o comando de
`correspondencia.SQL_INDICE_HNSW` (~3–4 min para construir).

## Gatilho de revisão

1. **Medição com vetores reais** (antes de mudar o status para aceito): rodar
   `medir_adr0005.py real` depois da primeira execução completa e registrar os
   números aqui.
2. **Criar o índice HNSW** (nova migração) se a etapa `corresponder` passar de
   **30 min**, se o número de consultas por execução passar de **~10 mil**
   (por exemplo, com as descrições de compras públicas) ou se surgir uma
   consulta interativa que precise responder em **menos de 100 ms** — e só se
   a medição real der **recall@10 ≥ 0,95** com algum `ef_search ≤ 200`.
3. **Rever o modelo** (e5-base ou combinação com o ranking por caracteres) se,
   na revisão de uma amostra de **100 materiais sorteados**, menos de **70%**
   tiverem um item equivalente entre os 10 candidatos. O limiar é um critério
   inicial proposto, a confirmar pela Squad.
