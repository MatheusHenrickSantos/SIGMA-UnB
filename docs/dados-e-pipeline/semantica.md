# Busca semântica: materiais do estoque × CATMAT

O estoque da UnB descreve materiais em texto livre, sem código. Para comparar
preços com compras públicas é preciso saber a qual item do CATMAT cada
material corresponde. Esta etapa sugere, para cada material, os itens CATMAT
de descrição mais parecida, com uma nota de similaridade e uma checagem de
especificações. **Ela não decide equivalência**: o resultado é uma fila de
candidatos para revisão humana.

Decisões e alternativas: [ADR 0005](adr/0005-busca-semantica-com-pgvector.md)
(pgvector, modelo, busca exata) e [ADR 0006](adr/0006-busca-hibrida-e-decisoes-por-agentes.md)
(busca híbrida, decisões sugeridas por agentes de IA e compras públicas).

## Onde fica na arquitetura

```text
 raw (JSONB)  ──dbt──▶  bronze  ──dbt──▶  prata                      ──python──▶  semantica
 raw.estoque            bronze.estoque     prata.material                          descricao
 raw.catmat             bronze.catmat      prata.catmat_item                       embedding (vector(384))
                                                                                   candidato_catmat
                                                                                   revisao_correspondencia
```

O schema `semantica` é separado da Prata porque:

- quem escreve nele é o Python (`codigos/semantica`), não o dbt;
- os vetores dependem do modelo e da versão das regras de normalização e
  não podem ser refeitos só com SQL a partir da Bronze;
- tudo nele é derivado e pode ser recalculado a partir da Prata, **exceto**
  `revisao_correspondencia`, que guarda decisões humanas.

A visão `semantica.v_candidato_catmat` faz o papel da entidade
`candidatoCatmat` do [diagrama de arquitetura](modelagem/diagrama-de-arquitetura.md).

## Etapas

`python -m semantica` (no Docker: serviço `semantica`). Cada etapa pode rodar
sozinha e é segura para repetir.

| Etapa | Lê | Grava | O que evita refazer |
|---|---|---|---|
| `sincronizar` | `prata.material` (`descricao_normalizada`), `prata.catmat_item` (ativos) | `semantica.descricao` | Linhas sem mudança não são tocadas |
| `embeddings` | descrições válidas sem vetor atual | `semantica.embedding` | Texto já vetorizado (mesmo hash) não volta ao modelo |
| `corresponder` | vetores e textos normalizados do estoque e do CATMAT | `execucao_correspondencia`, `candidato_catmat` | — (cada execução é uma fotografia completa) |
| `tudo` | as três acima, em ordem | | |
| `revisar` | um par material × item CATMAT | `revisao_correspondencia` | |
| `importar` | CSV de decisões (agentes ou planilha da squad) | `revisao_correspondencia`, `revisao_material` | Reimportar substitui, não duplica |
| `fila` | `v_fila_revisao` | CSV em `dados/semantica/` | |

Proveniência: cada linha de `descricao` guarda a origem (`estoque`/`catmat`),
a chave na Prata, o texto original sem alteração e seu sha256. Cada execução
guarda o modelo, os parâmetros da busca e as versões das regras.

## 1. Normalização

`codigos/semantica/normalizacao.py`, aplicada igual nos dois lados. Desfaz
entidades HTML e mojibake, aplica Unicode NFKC, põe em minúsculas sem acento,
expande abreviações de cadastro (`c/` → `com`, `cx` → `caixa`, `pct` →
`pacote`...), separa número de unidade (`500ml` → `500 ml`) e arruma
pontuação e espaços.

**Não remove** números, unidades, medidas, frações (`1/4 w`, `26/6`),
percentuais nem códigos de modelo (`cf283a`): é isso que distingue materiais
parecidos. O texto original fica guardado ao lado do normalizado.

Descrição nula ou em branco vira `vazia`; só símbolos, só números ou menos de
3 caracteres vira `invalida`; as duas ficam registradas com o motivo e não
recebem vetor.

Mudou uma regra? Incremente `VERSAO_NORMALIZACAO`: o hash do texto
normalizado muda e só os vetores afetados são recalculados.

Conferido com as 2.327 descrições reais de `seeds/materiais_normalizados.csv`
(`testes/teste_normalizacao_dados_reais.py`): todas válidas, normalização
idempotente, nenhuma sequência de dígitos perdida, 16 grupos de variações de
escrita convergindo para o mesmo texto.

**Duas normalizações no repositório.** `codigos/normalizar/` (camada Bronze)
gera a descrição canônica legível, em maiúsculas, da semente
`materiais_normalizados.csv`, com correção de erros de digitação
(`FEVERDOR` → `FERVEDOR`). Esta aqui gera a entrada do modelo (minúsculas,
abreviações expandidas). Os objetivos são diferentes, mas parte das regras se
sobrepõe (HTML, acentos, unidades); consolidar as duas — e usar aqui o
dicionário de correções — fica para a Squad decidir.

## 2. Modelo de embeddings

Padrão: [`intfloat/multilingual-e5-small`](https://huggingface.co/intfloat/multilingual-e5-small)
— 384 dimensões, ~118 M de parâmetros, licença MIT.

Por que este modelo para descrições de materiais em português:

- foi treinado para **recuperação** (achar o documento certo para uma
  consulta) em ~100 línguas, incluindo português — exatamente a tarefa aqui;
- aceita até 512 tokens: descrições longas do CATMAT não são cortadas (o
  pipeline conta e avisa quando alguma passa disso);
- roda em CPU: medimos ~260 textos/s em 2 threads com a mesma arquitetura
  (pesos aleatórios), o que dá ~22 min para ~345 mil itens do CATMAT, uma
  vez só; depois, só o que mudou.

Custos e limites:

- é um modelo de domínio geral: abreviações de almoxarifado e jargão de
  compras podem não ser bem entendidos (a normalização expande algumas);
- números e unidades são mal representados por qualquer embedding: "pilha AA"
  e "pilha AAA" ficam muito próximos — por isso a checagem de especificações;
- as notas de cosseno da família e5 ficam concentradas numa faixa alta
  (pares sem relação costumam passar de 0,7), então **não existe limiar
  universal**: ele precisa ser calibrado com pares revisados;
- exige os prefixos `query: ` (material do estoque) e `passage: ` (item CATMAT),
  aplicados num só lugar e registrados com o modelo.

| Alternativa | Dimensões | Por que não é o padrão |
|---|---|---|
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | Mais rápido, mas corta em 128 tokens e foi treinado para paráfrase, não recuperação |
| `multilingual-e5-base` | 768 | Melhor qualidade, ~3× mais lento em CPU; exige nova migração (dimensão) |
| `BAAI/bge-m3` | 1024 | Melhor qualidade, ~2,2 GB; pesado demais para CPU em 345 mil itens |

Trocar de modelo: `SEMANTICA_MODELO`. Se a dimensão for outra, crie uma
migração para a coluna `vetor`; o pipeline recusa gravar vetor de dimensão
diferente da coluna.

## 3. Similaridade de cosseno

A busca usa a distância de cosseno do pgvector (`<=>`), e a nota gravada é
`similaridade = 1 − distância` (1 = mesma direção). O cosseno compara a
direção dos vetores, que é o que o e5 aprende a alinhar no treino; os vetores
são normalizados (norma 1), então a ordem seria a mesma com produto interno
ou distância euclidiana — o cosseno só deixa a nota legível.

## 4. Armazenamento e versionamento

| Tabela | Chave | Guarda |
|---|---|---|
| `modelo_embedding` | `id_modelo` | nome, revisão (commit no Hugging Face), dimensão, prefixos, versões das bibliotecas |
| `descricao` | (`origem`, `chave_origem`) | texto original + sha256, texto normalizado + hash, versão da normalização, situação e motivo, `ativa` |
| `embedding` | (`id_descricao`, `id_modelo`) | `vector(384)` e o hash do texto que o gerou |
| `execucao_correspondencia` | `id_execucao` | modelo, top-K, limiar, exata/HNSW, `ef_search`, versões, totais |
| `candidato_catmat` | (`id_execucao`, material, posição) | similaridade, situação das especificações e detalhes (JSONB) |
| `revisao_correspondencia` | (hash do texto original do material, `codigo_item`) | decisão, revisor, `tipo_revisor` (pessoa ou agente), observação |
| `revisao_material` | hash do texto original do material | decisão sobre o material todo: `sem_correspondente`, confiança, justificativa, revisor e `tipo_revisor` |

Um vetor só existe enquanto é atual: quando o texto ou a regra mudam, quando
a descrição fica inválida ou some da Prata, o vetor é apagado na
sincronização e recalculado na próxima etapa `embeddings`. Vetores de
modelos diferentes nunca são comparados.

## 5. Busca exata (sem índice)

Para cada material, a etapa `corresponder` compara o vetor com **todos** os
vetores do CATMAT e fica com os 10 mais próximos. Medição com 345 mil vetores
de 384 dimensões (aleatórios; detalhes e limites no
[ADR 0005](adr/0005-busca-semantica-com-pgvector.md#medição)):

| | Busca exata (adotada) | Índice HNSW |
|---|---|---|
| Por material | 107 ms (p95 134 ms) | 4–19 ms |
| 2.400 materiais, pelo pipeline | 451 s | ~12 s |
| Recall@10 | 1 | 0,03–0,10 com vetores aleatórios; com vetores reais, a medir |
| Gravar 345 mil vetores | < 1 min | ~52 min com o índice (ou 203 s para criá-lo depois) |
| Espaço extra | 0 | 691 MB |

Para uma execução mensal com ~2.400 materiais, minutos de varredura valem
mais que um resultado aproximado. A V2 criou um índice HNSW antes desta
medição; a V3 o removeu.

Para voltar a usar o índice (gatilho no ADR 0005): crie uma migração com o
comando de `correspondencia.SQL_INDICE_HNSW`. O pipeline passa a usá-lo sem
outra mudança; `--ef-search` regula precisão × velocidade e `--busca-exata`
proíbe o índice numa execução. Antes, meça o recall com os vetores reais:

```bash
docker compose run --rm semantica python medir_adr0005.py real
```

## 6. Candidatos, especificações e revisão humana

Por que similaridade alta não basta: dois textos podem ser quase iguais e
diferir justamente no que importa — pilha AA × AAA, resistor 10 kΩ × 1 kΩ,
papel 75 × 90 g/m², álcool líquido × gel, caixa com 100 × pacote com 4. O
modelo vê a frase inteira e pesa pouco esses detalhes. Além disso, o estoque
não tem unidade de fornecimento nem código, e o CATMAT tem itens quase
duplicados.

Cada candidato passa pela checagem de especificações herdada do
[teste de viabilidade](testes/teste-de-viabilidade.md)
(`codigos/semantica/especificacoes.py`): resistência, capacitância, potência,
massa, volume, tensão, duração, dimensões, cor, apresentação, formato de pilha
e identificadores. A situação vai para `situacao_especificacao`:

| Situação | Significa |
|---|---|
| `conflito_tecnico` | uma especificação explícita diverge — provavelmente não é o mesmo material |
| `sem_conflito_mas_incompleto` | nada diverge, mas o CATMAT não traz algo que o estoque traz |
| `sem_conflito_detectado` | as categorias reconhecidas batem (não garante equivalência) |
| `sem_especificacoes_verificaveis` | o texto do estoque não tem especificação que as regras reconheçam |

A similaridade **não é alterada** pela checagem: as duas informações ficam
lado a lado para quem revisa.

### Fluxo de revisão

```bash
# 1. exportar a fila (materiais ainda sem item marcado como equivalente)
docker compose run --rm semantica python -m semantica fila
#    -> dados/semantica/fila_revisao.csv

# 2. registrar decisões (equivalente | nao_equivalente | incerto)
docker compose run --rm semantica python -m semantica revisar \
    --material ma0012 --codigo 461775 --decisao equivalente --revisor "Nome" --observacao "conferido no catálogo"
```

A decisão é chaveada pelo hash do **texto original** do material: vale em
todas as execuções seguintes e deixa de valer se a descrição mudar na
origem. Sugestão de prioridade para quem revisa: primeiro materiais com
`vantagem_sobre_proximo` pequena (dois candidatos empatados) ou com conflito
no primeiro colocado.

Consultas úteis:

```sql
-- candidatos da última execução para um material
SELECT posicao, codigo_item, round(similaridade::numeric, 3), situacao_especificacao, decisao
FROM semantica.v_fila_revisao WHERE identificador_material = 'ma0012' ORDER BY posicao;

-- materiais já resolvidos
SELECT texto_material, codigo_item, revisor, revisada_em
FROM semantica.revisao_correspondencia WHERE decisao = 'equivalente';
```

## 7. Busca híbrida (padrão desde a V4)

A busca só por cosseno **recupera bem e ordena mal**: o item correto costuma
estar entre os vizinhos, mas não em primeiro. Por isso a etapa `corresponder`
usa, por padrão, o método `hibrido` (`codigos/semantica/reordenacao.py`):

1. **cosseno**: os `k_vetor` (50) itens CATMAT de vetor mais próximo, como antes;
2. **trigramas**: os `k_trigrama` (20) itens de texto normalizado mais
   parecido pelo `pg_trgm` (operador `<->`, índice GiST criado na V4). Acha
   itens com as mesmas palavras e números que o modelo deixou passar;
3. **reordenação** da união com uma pontuação de 0 a 100:

   `pontuacao = 0,40·cosseno·100 + 0,20·token_set + 0,15·token_sort + 0,25·cobertura`

   `token_set` e `token_sort` são medidas do rapidfuzz sobre os textos em
   maiúsculas, sem acento e sem pontuação; `cobertura` é a % dos termos do
   material (sem palavras genéricas como MATERIAL, TIPO, COR) presentes no item;
4. candidatos com **conflito de especificação vão para o fim** da lista, mesmo
   com pontuação maior; os `top_k` primeiros são gravados.

`candidato_catmat` ganha `pontuacao`, `medidas` (as quatro medidas acima) e
`recuperado_por` (`{vetor}`, `{trigrama}` ou os dois); `execucao_correspondencia`
guarda o método, `k_vetor`, `k_trigrama`, os pesos e `versao_reordenacao`.
O método antigo continua disponível com `--metodo cosseno`.

Qualidade medida no conjunto de referência (`codigos/semantica/referencia/`,
150 materiais reais rotulados; reproduzir com
`docker compose run --rm semantica python -m semantica.medir_referencia`):

| Medida (103 materiais com item equivalente) | Só cosseno, top-10 (ADR 0005) | Híbrida (padrão) |
|---|---|---|
| Item correto entre os candidatos recuperados | 69,9% (10 vizinhos) | 88,3% (união de 50 por cosseno + 20 por trigramas) |
| Item correto entre os 10 gravados | 69,9% | **81,6%** |
| Item correto em 1º lugar | 40,8% | **59,2%** |

Só por trigramas, 65,0% dos itens corretos estão entre os 20 vizinhos; só por
cosseno, 86,4% estão entre os 50. As duas buscas se completam. Custo: a
etapa `corresponder` passa de ~6 para ~13 min nos 2.306 materiais.

Mesmo com a reordenação, o primeiro colocado erra em boa parte dos casos:
**nenhum candidato é aprovado automaticamente**. A decisão vem da revisão
(seção 8).

## 8. Decisões em lote: agentes de IA e planilhas

`python -m semantica importar --arquivo ARQUIVO.csv --revisor NOME --tipo-revisor pessoa|agente`
carrega decisões de um CSV (separador `;`), uma linha por material:

| Coluna | Conteúdo |
|---|---|
| `material` | texto do material exatamente como em `prata.material.descricao_normalizada` |
| `codigos_equivalentes` | códigos CATMAT equivalentes separados por `\|` (vazio se não houver) |
| `sem_correspondente` | `sim` quando não existe item CATMAT ativo equivalente; senão `nao` |
| `confianca` | `alta`, `media` ou `baixa` (baixa = prioridade de revisão) |
| `justificativa` | texto livre |
| `revisor` (opcional) | quem decidiu; sem a coluna vale `--revisor` |

- Os itens equivalentes vão para `revisao_correspondencia` (decisão
  `equivalente`) e a decisão sobre o material, inclusive "sem correspondente",
  para `revisao_material` (V5).
- `tipo_revisor` separa decisões de **pessoas** das sugeridas por **agentes
  de IA**. Agente nunca sobrescreve pessoa; pessoa sobrescreve agente.
- A visão `semantica.v_item_aprovado` lista os itens equivalentes (de pessoa
  ou de agente) dos materiais ativos: é a entrada da busca de compras.
- A `v_fila_revisao` só tira da fila o material resolvido **por pessoa**. Os
  resolvidos por agente continuam nela, com a sugestão visível nas colunas
  `decisao`, `revisor`, `sugestao_sem_correspondente` e `confianca_sugestao`.

O serviço `semantica` do Docker importa, depois da busca,
`codigos/semantica/decisoes/decisoes_agentes.csv`: as decisões dos 2.306
materiais da Prata sugeridas por agentes de IA, com a confiança e a
justificativa de cada uma. Como foram produzidas e qual a concordância medida:
[ADR 0006](adr/0006-busca-hibrida-e-decisoes-por-agentes.md) e
[Uso de IA](gestao/ai-usage.md). **Ainda não foram conferidas pela squad**;
comece pelas de confiança `baixa` e pelos materiais de maior valor em estoque.

## Como executar

Com Docker (sobe a cadeia inteira; ver o [README](https://github.com/MatheusHenrickSantos/SIGMA-UnB#readme)):

```bash
docker compose up --build                 # a cadeia inteira, até as compras
docker compose run --rm semantica         # só a busca semântica, incremental
```

Teste rápido: `CATMAT_MAX_PAGINAS=5` no `.env` baixa só 2.500 itens do CATMAT.

Parâmetros (opção da linha de comando ou variável no `.env`):

| Opção | Variável | Padrão | Efeito |
|---|---|---|---|
| `--modelo` | `SEMANTICA_MODELO` | `intfloat/multilingual-e5-small` | nome no Hugging Face ou pasta local |
| `--revisao` | `SEMANTICA_REVISAO` | mais recente | fixa o commit do modelo |
| `--top-k` | `SEMANTICA_TOP_K` | 10 | candidatos por material (1 a 100) |
| `--limiar-similaridade` | `SEMANTICA_LIMIAR` | sem filtro | descarta candidatos abaixo do valor, depois do top-K |
| `--metodo` | `SEMANTICA_METODO` | `hibrido` | `hibrido` (seção 7) ou `cosseno` |
| `--k-vetor` | `SEMANTICA_K_VETOR` | 50 | híbrido: vizinhos por cosseno antes de reordenar |
| `--k-trigrama` | `SEMANTICA_K_TRIGRAMA` | 20 | híbrido: vizinhos por trigramas (0 desliga) |
| `--busca-exata` | `SEMANTICA_BUSCA_EXATA=1` | não | proíbe índice HNSW (hoje não há: a busca já é exata) |
| `--ef-search` | `SEMANTICA_EF_SEARCH` | max(40, top-K) | só com índice HNSW: precisão × velocidade |
| `--incluir-catmat-inativo` | — | não | sincroniza também itens inativos |

O modelo é baixado do Hugging Face na primeira execução e fica no volume
`modelos`. Essa é a única dependência externa da etapa, além do banco.

### Calibrar o limiar

Não há limiar padrão porque não temos pares revisados. Depois de revisar uma
amostra (sugestão: 100 materiais sorteados), compare a similaridade dos pares
`equivalente` e `nao_equivalente`:

```sql
SELECT r.decisao, count(*),
       percentile_cont(ARRAY[0.1, 0.5, 0.9]) WITHIN GROUP (ORDER BY v.similaridade) AS p10_p50_p90
FROM semantica.revisao_correspondencia r
JOIN semantica.v_candidato_catmat v
  ON v.codigo_item = r.codigo_item AND v.id_execucao = r.id_execucao
JOIN semantica.descricao m
  ON m.chave_origem = v.identificador_material AND m.hash_original = r.hash_original_material
GROUP BY r.decisao;
```

## Testes

```bash
pip install -r codigos/requirements.txt pytest
SIGMA_TESTES_BANCO="host=localhost user=sigma password=sigma dbname=postgres" pytest
```

Sem `SIGMA_TESTES_BANCO` os testes que precisam de banco são pulados. Com o
Compose no ar, o valor acima funciona (porta 5432 exposta). Os testes não
baixam o modelo: usam um codificador falso determinístico
(`testes/codificador_teste.py`) e a amostra escrita à mão em
`testes/dados/amostra` (não são dados reais).

| Arquivo | Cobre |
|---|---|
| `teste_migracao_semantica.py` | V2/V3: objetos criados, cosseno, índice recriável, restrições |
| `teste_normalizacao.py` | regras, idempotência, preservação de números e códigos, recusas |
| `teste_embeddings.py` | prefixos, sincronização incremental, falhas, dimensão |
| `teste_especificacoes.py` | conflitos de especificação conhecidos |
| `teste_correspondencia.py` | ordem e valores, limiar, plano sem índice, exata × HNSW recriado, atomicidade, revisão, busca híbrida (reordenação, recuperação por trigramas, conflito por último) |
| `teste_reordenacao.py` | pontuação da busca híbrida, sem banco |
| `teste_decisoes.py` | importação em lote, pessoa × agente, fila e `v_item_aprovado` (V5) |
| `teste_pipeline_semantico.py` | Prata → linha de comando → candidatos → fila |

## Limitações conhecidas

- As medições de qualidade usam um conjunto de referência rotulado por IA,
  não por especialistas, e as decisões em `decisoes_agentes.csv` ainda não
  foram conferidas pela squad (ver seção 8).
- Similaridade não é equivalência; a checagem de especificações só reconhece
  as categorias implementadas e não vê unidade de fornecimento (o estoque não
  a informa).
- A busca exata relê todo o CATMAT a cada execução (~7,5 min medidos); ver o
  gatilho para criar um índice no ADR 0005. A busca por trigramas usa o
  índice GiST da V4.
- `prata.material` é a fonte da chave do material: se os identificadores da
  Prata mudarem entre execuções, as descrições são tratadas como novas (as
  revisões continuam valendo, porque usam o hash do texto).
- Itens CATMAT que somem da Prata têm o vetor apagado; se voltarem, o vetor é
  recalculado.

## Compras públicas

Os itens de `semantica.v_item_aprovado` são a entrada da busca de preços:

| Serviço | Faz |
|---|---|
| `compras` | `codigos/inserir/baixar_compras.py` consulta a API de pesquisa de preços do Compras.gov.br (`modulo-pesquisa-preco/1_consultarMaterial`) para cada código aprovado, na janela `COMPRAS_INICIO`–`COMPRAS_FIM` (padrão 01/07/2025 a 31/12/2025), grava um JSON por código em `dados/compras/` e carrega em `raw.compras` |
| `transformar_ouro` | `dbt build --select compras_bronze+ path:snapshots+ path:models/ouro+`: `bronze.compras` (um registro da API por linha, deduplicado por `id_item_compra`) e `prata.compra_publica` (janela e preço > 0) |

As páginas da API ficam em `dados/compras_cache/<janela>/<código>/`: outra
execução só pede à API o que falta. A API filtra por data no servidor, não
ordena por data e usa `idItemCompra` como chave real (detalhes no cabeçalho
de `baixar_compras.py`).

Resultado com os dados reais (janela 01/07/2025 a 31/12/2025, decisões dos
agentes): 3.528 códigos CATMAT aprovados para 1.620 materiais; 2.458 códigos
(70%) têm compra na janela, somando 41.514 registros em `prata.compra_publica`.
Isso dá preço público a 1.255 materiais, que somam **50,9% do valor do
estoque de 12/2025** (83,1% do valor está em materiais com item equivalente;
a diferença são itens sem compra no semestre).
