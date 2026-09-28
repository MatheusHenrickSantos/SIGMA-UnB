# SIGMA-UnB

Sistema Integrado de Gestão de Materiais e Almoxarifado da UnB.

O sistema apresenta os materiais do almoxarifado da UnB e
acompanha os preços desses itens em lojas online ao longo do tempo.

## Pré-requisitos

Antes de executar o projeto, instale:

- Python 3.11 ou superior
- PostgreSQL
- Git

## Instalação

Clone o repositório:

```bash
git clone https://github.com/MatheusHenrickSantos/SIGMA-UnB.git
cd projeto-sigma
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```
Ative o ambiente no Windows:

```bash
.venv\Scripts\activate
```

Ative o ambiente no Linux ou macOS:

```bash
source .venv/bin/activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Obtenção dos dados

A partir da pasta scripts, execute:

```bash
python buscar-dados-de-almoxarifado.py
```

Esse comando consulta o portal de dados abertos da UnB e salva os arquivos originais em:

```bash
dados/almoxarifado/
```

Os arquivos dessa pasta não devem ser alterados manualmente.

## Normalização dos dados

Depois do download, execute:

```bash
python normalizar-dados.py
```

O script realiza as seguintes operações:

remove espaços excedentes;
converte preços do formato brasileiro;
padroniza as quantidades;
gera um termo adequado para pesquisa em lojas online;
identifica o mês e o ano do arquivo;
consolida os registros em um único arquivo.

O resultado será salvo em:

```bash
dados/processados/almoxarifado_normalizado.json
```

## Coleta de preços no Mercado Livre

Após normalizar os dados, execute:

```bash
python scripts/coletar_precos_mercado_livre.py
```

O script lê os termos de busca presentes em:

```bash
dados/processados/almoxarifado_normalizado.json
```

Para cada material, o sistema consulta anúncios correspondentes e registra o título, o preço, a URL, a condição e a data da consulta.

As coletas são armazenadas separadamente em:

```bash
dados/coletas/mercado_livre/
```

Cada execução gera um novo arquivo. Dessa forma, os preços coletados anteriormente não são sobrescritos e podem compor um histórico.
