# Teste de Viabilidade: validação automática CATMAT e cobertura de preços públicos

## Objetivo

Executar dois testes reproduzíveis sobre a amostra de materiais do almoxarifado:

1. identificar candidatos CATMAT com conflitos explícitos em atributos técnicos;
2. medir quantos códigos candidatos possuem registros de compra com preço unitário positivo na janela temporal escolhida.

**Importante:** a validação automática é conservadora e baseada apenas nas categorias de atributos implementadas. Um candidato sem conflito detectado não é uma associação confirmada. A cobertura de preços mede a disponibilidade de registros para candidatos; só poderá ser interpretada como cobertura dos materiais depois que a correspondência CATMAT estiver suficientemente validada.

## Dependências

No ambiente do projeto, use o ambiente virtual do repositório:

```bash
cd SIGMA-UnB
python -m venv .venv
. .venv/bin/activate
python -m pip install pandas requests rapidfuzz
```

## Fluxo completo do teste

A execução correta do teste é feita em quatro etapas antes da validação e da cobertura de preços:

1. buscar os dados do almoxarifado;
2. baixar o catálogo CATMAT;
3. gerar a amostra do último mês por almoxarifado;
4. gerar candidatos CATMAT para essa amostra;
5. validar e avaliar cobertura de preços.

## Passo 1: Obter os Dados do Almoxarifado

Se a base local ainda não estiver disponível em `dados/almoxarifado`, execute:

```bash
python codigos/buscar-dados-de-almoxarifado.py
```

Esse script salva os CSVs do estoque no diretório `dados/almoxarifado`.

## Passo 2: Baixar o Catálogo CATMAT

```bash
python codigos/baixar_catalogo_catmat.py --saida dados/teste
```

Esse comando salva o catálogo em `dados/teste/catalogo_catmat.csv` e mantém o cache em `dados/teste/cache_catmat_json/` para permitir retomada sem baixar tudo de novo.

## Passo 3: Gerar Amostra de Materiais

Execute o script de amostragem para selecionar materiais do último mês disponível de cada almoxarifado, garantindo diversidade entre as famílias de produtos:

```bash
python codigos/gerar_amostra_almoxarifado.py \
  --entrada dados/almoxarifado \
  --saida dados/teste \
  --min-por-almoxarifado 10
```

Arquivo gerado:

- `dados/teste/amostra_10_por_almoxarifado_ultimo_mes.csv`

## Passo 4: Gerar Candidatos CATMAT

Use a amostra gerada e o catálogo baixado:

```bash
python codigos/gerar_candidatos_catmat.py \
  dados/teste/amostra_10_por_almoxarifado_ultimo_mes.csv \
  dados/teste/catalogo_catmat.csv \
  --saida dados/teste \
  --top 20 \
  --candidatos-por-metodo 100
```

O script gera os candidatos em:

- `dados/teste/candidatos_catmat.csv`
- `dados/teste/resumo_catmat.csv`

Esses arquivos são a entrada da etapa seguinte.

## Arquivo de entrada da etapa 2

A etapa de validação e cobertura utiliza o arquivo `candidatos_catmat.csv` gerado acima. Ele deve incluir, no mínimo:

- `linha_amostra`;
- `material_estoque`;
- `codigoItem`;
- `descricaoItem_CATMAT`;
- `score_combinado` (ou score equivalente).

O script também aceita variações conhecidas de nomes de colunas e campos opcionais como `almoxarifado` e `statusItem`.

## Passo A: executar somente a validação

```bash
python codigos/validacao_e_cobertura_precos.py \
  dados/teste/candidatos_catmat.csv \
  --somente-validacao \
  --saida dados/teste/validacao
```

Esse modo não acessa a internet. Use-o primeiro para conferir as regras e os conflitos sinalizados.

### Categorias de resultado

- `conflito_tecnico`: foi encontrado ao menos um conflito explícito numa especificação extraída, como resistência elétrica, capacitância, potência, dimensão, cor ou apresentação.
- `sem_conflito_mas_incompleto`: não foi detectado conflito, mas a descrição CATMAT não apresenta uma ou mais especificações extraídas do material do estoque.
- `sem_conflito_detectado`: as categorias reconhecidas pelo algoritmo não apresentaram conflito e foram comparadas. Isso não garante que todos os atributos relevantes estejam presentes.
- `sem_especificacoes_verificaveis`: não foi possível extrair atributos estruturados relevantes do material a partir das regras implementadas.

As regras podem ser ampliadas ao observar novas descrições. Os resultados não são uma verdade de referência e não devem ser usados para afirmar uma taxa de precisão sem uma amostra de associações verdadeiras verificadas.

## Passo B: testar a cobertura de preços

```bash
python codigos/validacao_e_cobertura_precos.py \
  dados/teste/candidatos_catmat.csv \
  --inicio 2025-07-01 \
  --fim 2025-12-31 \
  --top-n-precos 1 \
  --saida dados/teste/cobertura \
  --cache dados/teste/cache_precos_catmat
```

O padrão consulta o melhor candidato sem conflito explícito para cada material. Se quiser ampliar a exploração para até três candidatos por material:

```bash
python codigos/validacao_e_cobertura_precos.py \
  dados/teste/candidatos_catmat.csv \
  --inicio 2025-07-01 \
  --fim 2025-12-31 \
  --top-n-precos 3 \
  --saida dados/teste/cobertura_top3 \
  --cache dados/teste/cache_precos_catmat
```

O modo completo percorre todas as páginas retornadas para cada código selecionado. A API permite até 500 registros por página. Como o endpoint de preços não documenta filtro por intervalo de datas, o programa extrai os registros do código e aplica o intervalo de datas na coluna `dataCompra` localmente.

Para fazer apenas um teste rápido da resposta e da paginação, pode-se limitar as páginas:

```bash
python codigos/validacao_e_cobertura_precos.py \
  dados/teste/candidatos_catmat.csv \
  --max-pages-per-code 5 \
  --saida dados/teste/cobertura_piloto
```

Esse último modo é deliberadamente parcial. Se o resultado indicar zero preços, isso **não** comprova ausência de preços no período, pois registros mais antigos ou mais recentes podem estar em páginas não lidas. Não use uma execução limitada como medida definitiva de cobertura.

As respostas JSON ficam em cache por código e página. Uma execução posterior reutiliza o cache. Para atualizar a cópia, acrescente `--refresh-cache`.

## Arquivos de saída

- `validacao_especificacoes_catmat.csv`: todos os candidatos, scores, atributos extraídos, categorias compatíveis, atributos ausentes e conflitos.
- `resumo_validacao_por_material.csv`: melhor candidato pelo score e melhor candidato sem conflito explícito para cada material.
- `candidatos_selecionados_para_teste_precos.csv`: candidatos que serão consultados, após excluir conflitos técnicos explícitos.
- `cobertura_precos_por_codigo.csv`: resultado da consulta por código CATMAT, paginação, registros no período e estatísticas de preços positivos.
- `precos_publicos_periodo.csv`: registros de compras retornados na janela selecionada.
- `cobertura_precos_por_material.csv`: resumo da disponibilidade de preços entre os candidatos consultados para cada material.
- `metadados_execucao.json`: parâmetros, datas e quantidade de códigos consultados.
- `cache_precos_catmat/<codigo>/pagina_<n>.json`: respostas brutas da API para cada código e página.

## Como interpretar a cobertura

A cobertura deve ser apresentada em pelo menos dois níveis:

1. **Cobertura por código candidato:** proporção dos códigos consultados que tiveram ao menos um preço unitário positivo dentro da janela e com consulta completa.
2. **Cobertura por material da amostra:** proporção dos materiais que tiveram pelo menos um dos seus candidatos consultados com preços no período.

Os indicadores são exploratórios até a associação CATMAT ser validada. Um código errado pode ter muitos preços; a existência de registros não prova que ele representa o material correto.

Antes de comparar valores, confira as unidades de medida e de fornecimento, capacidade da embalagem e descrição detalhada. A mediana é apenas uma estatística inicial e não elimina a necessidade de verificar se as aquisições são comparáveis.

## Fontes oficiais

- Documentação interativa da API de Dados Abertos: https://dadosabertos.compras.gov.br/swagger-ui/index.html
- Manual da API do Compras.gov.br, versão 2.0: https://www.gov.br/compras/pt-br/acesso-a-informacao/manuais/manual-dados-abertos/manual-api-compras.pdf
- Pesquisa de Preços em Dados Abertos: https://www.gov.br/compras/pt-br/sistemas/conheca-o-compras/pesquisa-de-precos/pesquisa-de-precos/
