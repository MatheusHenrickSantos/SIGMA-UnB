# Dicionário de dados

## Convenções

- **Tipo ID**: O tipo de dados "ID" será uma composição única entre o nome abreviado da tabela, com três letras, e um serial, com três dígitos.  
  - *Exemplo: "est001" representa o primeiro item cadastrado na tabela `estoque`.*



## Definição das tabelas

### Camada raw

A __Tabela 1__ abaixo apresenta a descrição da tabela `estoque`, que armazena os dados brutos mensais de estoque oriundos dos dados abertos da UnB. O campo `DadoBruto` é armazenado como _JSONB_ para preservar o arquivo exatamente como disponibilizado pela fonte, enquanto `MesDeReferencia` e `AnoDeReferencia` utilizam o tipo _SMALLINT_ e a `HashDoArquivo` utiliza _CHAR(64)_ (gerada via SHA-256) para garantir a integridade e unicidade da carga. As __Tabelas 2 e 3__ apresentam, respectivamente, a descrição da tabela `compras` e da tabela `CATMAT`, compostas pelos atributos `DadoBruto`, `HashDoArquivo` e `DataDaInsercao` (_TIMESTAMP_). Essa estruturação garante a rastreabilidade e a imutabilidade do dado de entrada sem nenhum tipo de tratamento prévio.

<details>
  <summary>Tabela 1 – Dicionário de dados da tabela estoque
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 1 – Dicionário de dados da tabela estoque</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>DadoBruto</code></td>
          <td>Linha bruta ou conteúdo integral do arquivo JSON mensal de estoque.</td>
          <td>JSONB</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>HashDoArquivo</code></td>
          <td>Hash de controle gerado via SHA-256 para garantir a integridade e unicidade da carga.</td>
          <td>CHAR</td>
          <td>64</td>
          <td>-</td>
          <td>-</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>MesDeReferencia</code></td>
          <td>Mês de referência extraído do arquivo de origem.</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>1 a 12</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>AnoDeReferencia</code></td>
          <td>Ano de referência extraído do arquivo de origem.</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/IsraelThalles">Israel Thalles</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 2 – Dicionário de dados da tabela compras
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 2 – Dicionário de dados da tabela compras</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>DadoBruto</code></td>
          <td>Conteúdo integral ou registro bruto dos dados de compras do gov.br.</td>
          <td>JSONB</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>HashDoArquivo</code></td>
          <td>Hash de controle gerado via SHA-256 para verificação de duplicidade e integridade da carga.</td>
          <td>CHAR</td>
          <td>64</td>
          <td>-</td>
          <td>-</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>DataDaInsercao</code></td>
          <td>Carimbo de data e hora indicando o momento em que o dado foi inserido.</td>
          <td>TIMESTAMP</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/IsraelThalles">Israel Thalles</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 3 – Dicionário de dados da tabela catmat
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 3 – Dicionário de dados da tabela catmat</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>DadoBruto</code></td>
          <td>Conteúdo integral ou registro bruto do arquivo CATMAT.</td>
          <td>JSONB</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>HashDoArquivo</code></td>
          <td>Hash de controle gerado via SHA-256 para verificação de duplicidade e integridade do arquivo.</td>
          <td>CHAR</td>
          <td>64</td>
          <td>-</td>
          <td>-</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>DataDaInsercao</code></td>
          <td>Carimbo de data e hora indicando o momento em que o dado foi inserido.</td>
          <td>TIMESTAMP</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/IsraelThalles">Israel Thalles</a>.</p>
  </div>
</details>

---

### Camada bronze

  A **Tabela 4** abaixo apresenta a descrição da tabela `estoque`, que é oriunda dos **Dados Abertos da UnB**. Os campos `preco`, `valor_total`,`material`, `almoxarifado` e `saldo` são armazenados na camada bronze como *TEXT* e sem nenhum tipo de restrição para preservar os valores conforme disponibilizados pela fonte e evitar falhas de carga causadas por variações de formato, como símbolos monetários, separadores decimais ou espaços. A conversão para tipos mais adequados e a validação dos valores são realizadas nas etapas posteriores de tratamento dos dados. O mesmo vale para a **Tabela 5**, que apresenta a descrição da tabela `CATMAT` e para a **Tabela 6**, que apresenta a descrição da tabela de `compras`.

<details>
  <summary>Tabela 4 – Dicionário de dados da tabela estoque
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 4 – Dicionário de dados da tabela estoque</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>material</code></td>
          <td>Descrição resumida do material.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>almoxarifado</code></td>
          <td>Nome do almoxarifado.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>saldo</code></td>
          <td>Quantidade de itens em estoque.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>preco</code></td>
          <td>Preço praticado do material.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>valor_total</code></td>
          <td>Indica o valor total do material no estoque.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 5 – Dicionário de dados da tabela CATMAT
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 5 – Dicionário de dados da tabela CATMAT</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>codigoItem</code></td>
          <td>Código do item do catálogo CATMAT.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>descricaoItem</code></td>
          <td>Descrição do item do catálogo CATMAT.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>codigoGrupo</code></td>
          <td>Código do grupo ao qual o item pertence.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>nomeGrupo</code></td>
          <td>Nome do grupo do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>codigoClasse</code></td>
          <td>Código da classe do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>nomeClasse</code></td>
          <td>Nome da classe do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>codigoPdm</code></td>
          <td>Código do Padrão Descritivo de Materiais (PDM).</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>nomePdm</code></td>
          <td>Nome do Padrão Descritivo de Materiais (PDM).</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>statusItem</code></td>
          <td>Situação do item no catálogo.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>dataHoraAtualizacao</code></td>
          <td>Data e hora da última atualização do item no catálogo.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 6 – Dicionário de dados da tabela compras
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 6 – Dicionário de dados da tabela compras</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>idCompra</code></td>
          <td>Identificador da compra na fonte de dados.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>dataCompra</code></td>
          <td>Data em que a compra foi realizada.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>forma</code></td>
          <td>Forma ou modalidade da compra, conforme informada pela fonte.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>dataHoraAtualizacaoCompra</code></td>
          <td>Data e hora da última atualização da compra na fonte.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>codigoItemCatalogo</code></td>
          <td>Código do item de catálogo associado à compra.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>quantidade</code></td>
          <td>Quantidade do item comprada.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>precoUnitario</code></td>
          <td>Preço unitário informado para o item comprado.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>descricaoItem</code></td>
          <td>Descrição do item comprado.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>siglaUnidadeFornecimento</code></td>
          <td>Sigla da unidade de fornecimento do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>nomeUnidadeFornecimento</code></td>
          <td>Nome da unidade de fornecimento do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>capacidadeUnidadeFornecimento</code></td>
          <td>Capacidade da unidade de fornecimento do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>siglaUnidadeMedida</code></td>
          <td>Sigla da unidade de medida do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>nomeUnidadeMedida</code></td>
          <td>Nome da unidade de medida do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>codigoClasse</code></td>
          <td>Código da classe CATMAT do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>nomeClasse</code></td>
          <td>Nome da classe CATMAT do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>codigoPdm</code></td>
          <td>Código do PDM CATMAT do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>nomePdm</code></td>
          <td>Nome do PDM CATMAT do item.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

---

### Camada prata

  As **Tabelas 7 a 15** apresentam o dicionário de dados das tabelas geradas após a etapa de transformação da camada bronze, contendo seus respectivos atributos e descrições.

<details>
  <summary>Tabela 7 – Dicionário de dados da tabela estoque
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 7 – Dicionário de dados da tabela estoque</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>IdentificadorMaterial</code></td>
          <td>Identificador único do material.</td>
          <td>ID</td>
          <td>6</td>
          <td>Padrão do tipo ID</td>
          <td>PK, FK</td>
          <td>Unique / Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>IdentificadorAlmoxarifado</code></td>
          <td>Identificador único do almoxarifado.</td>
          <td>ID</td>
          <td>6</td>
          <td>Padrão do tipo ID</td>
          <td>PK, FK</td>
          <td>Unique / Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>quantidade</code></td>
          <td>Quantidade de itens em estoque.</td>
          <td>NUMERIC</td>
          <td>(10,2)</td>
          <td>Maior que 0</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 8 – Dicionário de dados da tabela material
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 8 – Dicionário de dados da tabela material</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>IdentificadorMaterial</code></td>
          <td>Identificador único do material.</td>
          <td>ID</td>
          <td>6</td>
          <td>Padrão do tipo ID</td>
          <td>PK</td>
          <td>Unique / Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>nome</code></td>
          <td>Nome do material.</td>
          <td>CHAR</td>
          <td>50</td>
          <td>A-Z, 0-9</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>descricao</code></td>
          <td>Descrição do material.</td>
          <td>CHAR</td>
          <td>100</td>
          <td>A-Z, 0-9</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>preco</code></td>
          <td>Preço praticado do material.</td>
          <td>NUMERIC</td>
          <td>(10,2)</td>
          <td>Maior que 0</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 9 – Dicionário de dados da tabela almoxarifado
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 9 – Dicionário de dados da tabela almoxarifado</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>IdentificadorAlmoxarifado</code></td>
          <td>Identificador único do almoxarifado.</td>
          <td>ID</td>
          <td>6</td>
          <td>Padrão do tipo ID</td>
          <td>PK</td>
          <td>Unique / Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>nome</code></td>
          <td>Nome do almoxarifado.</td>
          <td>CHAR</td>
          <td>20</td>
          <td>CENTRAL, PRC</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 10 – Dicionário de dados da tabela candidatoCatmat
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 10 – Dicionário de dados da tabela candidatoCatmat</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>IdentificadorCandidato</code></td>
          <td>Identificador único da associação candidata entre um material e um item CATMAT.</td>
          <td>ID</td>
          <td>6</td>
          <td>Padrão do tipo ID</td>
          <td>PK</td>
          <td>Unique / Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>IdentificadorMaterial</code></td>
          <td>Identificador do material associado.</td>
          <td>ID</td>
          <td>6</td>
          <td>Padrão do tipo ID</td>
          <td>FK</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>codigoItem</code></td>
          <td>Código do item CATMAT candidato.</td>
          <td>ID_ITEM</td>
          <td>6</td>
          <td>0-9</td>
          <td>FK</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>pontuacao</code></td>
          <td>Pontuação atribuída à correspondência entre o material e o item CATMAT.</td>
          <td>NUMERIC</td>
          <td>(5,2)</td>
          <td>≥ 0<br>≤ 100</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 11 – Dicionário de dados da tabela catmatGrupo
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 11 – Dicionário de dados da tabela catmatGrupo</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>codigoGrupo</code></td>
          <td>Código único do grupo CATMAT.</td>
          <td>ID_GRUPO</td>
          <td>2</td>
          <td>0-9</td>
          <td>PK</td>
          <td>Unique / Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>nomeGrupo</code></td>
          <td>Nome do grupo CATMAT.</td>
          <td>CHAR</td>
          <td>150</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 12 – Dicionário de dados da tabela catmatClasse
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 12 – Dicionário de dados da tabela catmatClasse</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>codigoClasse</code></td>
          <td>Código único da classe CATMAT.</td>
          <td>ID_CLASSE</td>
          <td>4</td>
          <td>0-9</td>
          <td>PK</td>
          <td>Unique / Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>codigoGrupo</code></td>
          <td>Código do grupo CATMAT ao qual a classe pertence.</td>
          <td>ID_GRUPO</td>
          <td>2</td>
          <td>0-9</td>
          <td>FK</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>nomeClasse</code></td>
          <td>Nome da classe CATMAT.</td>
          <td>CHAR</td>
          <td>100</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 13 – Dicionário de dados da tabela catmatPdm
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 13 – Dicionário de dados da tabela catmatPdm</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>codigoPdm</code></td>
          <td>Código único do Padrão Descritivo de Materiais (PDM).</td>
          <td>ID_PDM</td>
          <td>4</td>
          <td>0-9</td>
          <td>PK</td>
          <td>Unique / Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>codigoClasse</code></td>
          <td>Código da classe CATMAT à qual o PDM pertence.</td>
          <td>ID_CLASSE</td>
          <td>4</td>
          <td>0-9</td>
          <td>FK</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>nomePdm</code></td>
          <td>Nome do Padrão Descritivo de Materiais (PDM).</td>
          <td>CHAR</td>
          <td>100</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 14 – Dicionário de dados da tabela catmatItem
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 14 – Dicionário de dados da tabela catmatItem</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>codigoItem</code></td>
          <td>Código único do item CATMAT.</td>
          <td>ID_ITEM</td>
          <td>6</td>
          <td>0-9</td>
          <td>PK</td>
          <td>Unique / Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>codigoPdm</code></td>
          <td>Código do PDM CATMAT ao qual o item pertence.</td>
          <td>ID_PDM</td>
          <td>4</td>
          <td>0-9</td>
          <td>FK</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>descricaoItem</code></td>
          <td>Descrição do item CATMAT.</td>
          <td>CHAR</td>
          <td>200</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>statusItem</code></td>
          <td>Situação do item no catálogo CATMAT.</td>
          <td>Boleano</td>
          <td>-</td>
          <td>TRUE / FALSE</td>
          <td>-</td>
          <td>CHECK</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 15 – Dicionário de dados da tabela compraPublica
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 15 – Dicionário de dados da tabela compraPublica</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>IdentificadorCompra</code></td>
          <td>Identificador único da compra pública.</td>
          <td>ID</td>
          <td>6</td>
          <td>Padrão do tipo ID</td>
          <td>PK</td>
          <td>Unique / Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>codigoItem</code></td>
          <td>Código do item CATMAT comprado.</td>
          <td>ID_ITEM</td>
          <td>6</td>
          <td>0-9</td>
          <td>FK</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>quantidade</code></td>
          <td>Quantidade do item comprada.</td>
          <td>NUMERIC</td>
          <td>(10,2)</td>
          <td>Maior que 0</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>precoUnitario</code></td>
          <td>Preço unitário do item na compra.</td>
          <td>NUMERIC</td>
          <td>(10,2)</td>
          <td>Maior que 0,00</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>unidadeFornecimento</code></td>
          <td>Unidade de fornecimento do item comprado.</td>
          <td>CHAR</td>
          <td>10</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>dataCompra</code></td>
          <td>Data em que a compra foi realizada.</td>
          <td>DATE</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/MatheusHenrickSantos">Matheus Henrick</a>.</p>
  </div>
</details>

---

### Camada ouro

  A camada ouro organiza os dados em um **modelo estrela** que responde à pergunta de gestão: para quais materiais do estoque existe preço de compras públicas comparável e quais têm as maiores diferenças, por almoxarifado e período. A decisão e as alternativas estão na [ADR 7](adr/0007-modelo-estrela-para-comparacao-de-precos.md), e o funcionamento do modelo em [Camada ouro: modelo analítico](dados-e-pipeline/camada-ouro.md). Todas as tabelas são geradas pelo dbt (`models/ouro/` e `snapshots/`) no esquema `ouro`.

  A **Tabela 16** descreve o fato `fato_comparacao_preco`, cujo grão é **uma linha por material, por almoxarifado, por mês de referência publicado**. As **Tabelas 17 a 20** descrevem as dimensões: `dim_material`, que guarda a correspondência material × CATMAT como dimensão de variação lenta do tipo 2 (uma linha por versão), `dim_almoxarifado`, `dim_tempo` e `dim_item_catmat`. A **Tabela 21** descreve `monitor_atualizacao`, que mede o atraso (freshness) das tabelas de consumo diante do SLA declarado.

  Nesta camada, os tipos são os que o PostgreSQL atribui às colunas geradas pelo dbt. Os identificadores de material e almoxarifado seguem o tipo ID das camadas anteriores; na `dim_material` o identificador vem do esquema `semantica` e por isso é armazenado como _TEXT_, com o mesmo formato. Atributos numéricos sem tamanho são _NUMERIC_ sem precisão fixa; os que passam por arredondamento indicam o número de casas decimais.

<details>
  <summary>Tabela 16 – Dicionário de dados da tabela fato_comparacao_preco
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 16 – Dicionário de dados da tabela fato_comparacao_preco</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>mes_referencia</code></td>
          <td>Primeiro dia do mês de referência do estoque publicado no portal da UnB.</td>
          <td>DATE</td>
          <td>-</td>
          <td>Dia 1 de um mês presente em <code>dim_tempo</code></td>
          <td>PK, FK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>identificador_material</code></td>
          <td>Identificador do material no estoque (<code>prata.material</code>).</td>
          <td>ID</td>
          <td>6</td>
          <td>Padrão do tipo ID (prefixo <code>ma</code>)</td>
          <td>PK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>identificador_almoxarifado</code></td>
          <td>Identificador do almoxarifado que guarda o material.</td>
          <td>ID</td>
          <td>6</td>
          <td>Padrão do tipo ID (prefixo <code>al</code>)</td>
          <td>PK, FK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>sk_material</code></td>
          <td>Chave da versão da correspondência em <code>dim_material</code> vigente quando a linha foi carregada.</td>
          <td>TEXT</td>
          <td>32</td>
          <td>Hash MD5 em hexadecimal</td>
          <td>FK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>tipo_revisor_correspondencia</code></td>
          <td>Quem decidiu a correspondência material × CATMAT usada no cálculo.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>pessoa, agente, sem_decisao</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>quantidade</code></td>
          <td>Saldo do material no almoxarifado no mês (soma das linhas de origem). É saldo: soma entre almoxarifados no mesmo mês, nunca entre meses.</td>
          <td>NUMERIC</td>
          <td>-</td>
          <td>≥ 0</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>preco_estoque</code></td>
          <td>Preço unitário registrado no estoque: média ponderada pela quantidade das linhas do mês (média simples quando a quantidade é zero).</td>
          <td>NUMERIC</td>
          <td>4 casas decimais</td>
          <td>Maior que 0</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>valor_estoque</code></td>
          <td>Valor do saldo em estoque (soma de quantidade × preço).</td>
          <td>NUMERIC</td>
          <td>-</td>
          <td>≥ 0</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>linhas_origem</code></td>
          <td>Quantidade de linhas de <code>prata.estoque</code> agregadas na linha do fato.</td>
          <td>BIGINT</td>
          <td>-</td>
          <td>≥ 1</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>preco_publico_mediano</code></td>
          <td>Mediana do preço unitário das compras públicas dos itens CATMAT equivalentes ao material, na janela <code>compras_inicio</code>..<code>compras_fim</code>.</td>
          <td>NUMERIC</td>
          <td>4 casas decimais</td>
          <td>Maior que 0</td>
          <td>-</td>
          <td>NULL quando não há compra comparável</td>
        </tr>
        <tr>
          <td><code>compras_publicas</code></td>
          <td>Número de compras públicas usadas no cálculo da mediana.</td>
          <td>BIGINT</td>
          <td>-</td>
          <td>≥ 0</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>itens_catmat_com_compra</code></td>
          <td>Número de itens CATMAT equivalentes que tiveram ao menos uma compra na janela.</td>
          <td>BIGINT</td>
          <td>-</td>
          <td>≥ 0</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>unidade_fornecimento_predominante</code></td>
          <td>Unidade de fornecimento mais frequente nas compras usadas (moda). Serve para conferir se a unidade é a mesma do estoque.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>NULL quando não há compra comparável</td>
        </tr>
        <tr>
          <td><code>tem_preco_publico</code></td>
          <td>Indica se existe preço público comparável para o material.</td>
          <td>BOOLEAN</td>
          <td>-</td>
          <td>TRUE / FALSE</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>diferenca_absoluta</code></td>
          <td><code>preco_estoque - preco_publico_mediano</code>.</td>
          <td>NUMERIC</td>
          <td>4 casas decimais</td>
          <td>-</td>
          <td>-</td>
          <td>NULL quando não há preço público</td>
        </tr>
        <tr>
          <td><code>diferenca_pct</code></td>
          <td><code>(preco_estoque / preco_publico_mediano - 1) × 100</code>. Sinal para investigar, não prova de sobrepreço.</td>
          <td>NUMERIC</td>
          <td>2 casas decimais</td>
          <td>-</td>
          <td>-</td>
          <td>NULL quando não há preço público</td>
        </tr>
        <tr>
          <td><code>carregado_em</code></td>
          <td>Data e hora em que a linha foi carregada no fato.</td>
          <td>TIMESTAMPTZ</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/magnluiz">magnluiz</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 17 – Dicionário de dados da tabela dim_material
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 17 – Dicionário de dados da tabela dim_material</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>sk_material</code></td>
          <td>Chave substituta da versão: MD5 de <code>identificador_material</code> + <code>valido_de</code>.</td>
          <td>TEXT</td>
          <td>32</td>
          <td>Hash MD5 em hexadecimal</td>
          <td>PK</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>identificador_material</code></td>
          <td>Identificador do material (<code>prata.material</code>). Repete entre versões.</td>
          <td>TEXT</td>
          <td>6</td>
          <td>Padrão do tipo ID (prefixo <code>ma</code>)</td>
          <td>-</td>
          <td>Not NULL / Unique com <code>valido_de</code></td>
        </tr>
        <tr>
          <td><code>nome</code></td>
          <td>Nome do material (primeiro trecho da descrição normalizada).</td>
          <td>TEXT</td>
          <td>≤ 50</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>descricao</code></td>
          <td>Descrição original do material, como veio do estoque.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>codigos_equivalentes</code></td>
          <td>Códigos dos itens CATMAT decididos como equivalentes, separados por <code>|</code> e ordenados.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>Códigos CATMAT separados por <code>|</code>, ou vazio</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>quantidade_itens_catmat</code></td>
          <td>Quantidade de itens em <code>codigos_equivalentes</code>.</td>
          <td>INTEGER</td>
          <td>-</td>
          <td>≥ 0</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>sem_correspondente</code></td>
          <td>Indica que a revisão concluiu que o material não tem item CATMAT correspondente.</td>
          <td>BOOLEAN</td>
          <td>-</td>
          <td>TRUE / FALSE</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>tipo_revisor</code></td>
          <td>Quem decidiu a correspondência nesta versão.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>pessoa, agente, sem_decisao</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>confianca</code></td>
          <td>Confiança declarada na decisão sobre o material.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>alta, media, baixa</td>
          <td>-</td>
          <td>NULL quando não há decisão por material</td>
        </tr>
        <tr>
          <td><code>valido_de</code></td>
          <td>Início da vigência da versão.</td>
          <td>TIMESTAMP</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>valido_ate</code></td>
          <td>Fim da vigência da versão; <code>9999-12-31</code> para a versão vigente.</td>
          <td>TIMESTAMP</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>atual</code></td>
          <td>Indica se esta é a versão vigente da correspondência.</td>
          <td>BOOLEAN</td>
          <td>-</td>
          <td>TRUE / FALSE</td>
          <td>-</td>
          <td>Not NULL / uma versão atual por material</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/magnluiz">magnluiz</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 18 – Dicionário de dados da tabela dim_almoxarifado
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 18 – Dicionário de dados da tabela dim_almoxarifado</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>identificador_almoxarifado</code></td>
          <td>Identificador único do almoxarifado.</td>
          <td>ID</td>
          <td>6</td>
          <td>Padrão do tipo ID (prefixo <code>al</code>)</td>
          <td>PK</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>nome</code></td>
          <td>Nome do almoxarifado, sem espaços nas pontas.</td>
          <td>TEXT</td>
          <td>≤ 20</td>
          <td>CENTRAL, PRC</td>
          <td>-</td>
          <td>-</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/magnluiz">magnluiz</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 19 – Dicionário de dados da tabela dim_tempo
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 19 – Dicionário de dados da tabela dim_tempo</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>mes_referencia</code></td>
          <td>Primeiro dia do mês. Vai do primeiro ao último mês com estoque, sem lacunas.</td>
          <td>DATE</td>
          <td>-</td>
          <td>Dia 1 do mês</td>
          <td>PK</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>ano</code></td>
          <td>Ano do mês de referência.</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>mes</code></td>
          <td>Número do mês.</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>1 a 12</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>ano_mes</code></td>
          <td>Mês no formato <code>AAAA-MM</code>, para rótulos.</td>
          <td>TEXT</td>
          <td>7</td>
          <td>AAAA-MM</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>publicado</code></td>
          <td>Indica se o portal publicou o arquivo de estoque daquele mês (há meses sem arquivo).</td>
          <td>BOOLEAN</td>
          <td>-</td>
          <td>TRUE / FALSE</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>na_janela_compras</code></td>
          <td>Indica se o mês está dentro da janela de compras públicas consultada (<code>compras_inicio</code>..<code>compras_fim</code>).</td>
          <td>BOOLEAN</td>
          <td>-</td>
          <td>TRUE / FALSE</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/magnluiz">magnluiz</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 20 – Dicionário de dados da tabela dim_item_catmat
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 20 – Dicionário de dados da tabela dim_item_catmat</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>codigo_item</code></td>
          <td>Código único do item CATMAT.</td>
          <td>INTEGER</td>
          <td>-</td>
          <td>0-9</td>
          <td>PK</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>descricao_item</code></td>
          <td>Descrição do item CATMAT.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>status_item</code></td>
          <td>Situação do item no catálogo (ativo ou inativo).</td>
          <td>BOOLEAN</td>
          <td>-</td>
          <td>TRUE / FALSE</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>codigo_pdm</code></td>
          <td>Código do Padrão Descritivo de Materiais (PDM) do item.</td>
          <td>INTEGER</td>
          <td>-</td>
          <td>0-9</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>nome_pdm</code></td>
          <td>Nome do PDM.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>codigo_classe</code></td>
          <td>Código da classe CATMAT do PDM.</td>
          <td>INTEGER</td>
          <td>-</td>
          <td>0-9</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>nome_classe</code></td>
          <td>Nome da classe CATMAT.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>codigo_grupo</code></td>
          <td>Código do grupo CATMAT da classe.</td>
          <td>INTEGER</td>
          <td>-</td>
          <td>0-9</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>nome_grupo</code></td>
          <td>Nome do grupo CATMAT.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/magnluiz">magnluiz</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 21 – Dicionário de dados da tabela monitor_atualizacao
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 21 – Dicionário de dados da tabela monitor_atualizacao</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Tamanho</th>
          <th>Valores permitidos</th>
          <th>É chave?</th>
          <th>Outras restrições</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>tabela</code></td>
          <td>Tabela de consumo monitorada.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>ouro.fato_comparacao_preco, prata.compra_publica</td>
          <td>PK</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>ultimo_dado</code></td>
          <td>Fim do período do dado mais recente (último dia do último mês no fato; data da última compra nas compras).</td>
          <td>DATE</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>ultima_carga</code></td>
          <td>Data e hora da última carga do fato.</td>
          <td>TIMESTAMPTZ</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>NULL para <code>prata.compra_publica</code></td>
        </tr>
        <tr>
          <td><code>atraso_dias</code></td>
          <td>Dias entre <code>ultimo_dado</code> e a data da medição.</td>
          <td>INTEGER</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>sla_dias</code></td>
          <td>Atraso máximo aceito pelo SLA declarado.</td>
          <td>INTEGER</td>
          <td>-</td>
          <td>45 (fato), 60 (compras)</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>situacao_sla</code></td>
          <td>Situação da tabela diante do SLA.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>dentro do SLA, fora do SLA</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>medido_em</code></td>
          <td>Data e hora da medição.</td>
          <td>TIMESTAMPTZ</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
      </tbody>
    </table>
    <p>Autor: <a href="https://github.com/magnluiz">magnluiz</a>.</p>
  </div>
</details>

---

## 📚 Bibliografia

> DATE, C. J. **Introdução a Sistemas de Bancos de Dados**. 8. ed. Rio de Janeiro: Campus, 2004.
>
> SILBERSCHATZ, Abraham; KORTH, Henry F.; SUDARSHAN, S. **Fundamentos de bases de datos**. 5. ed. Madrid: McGraw-Hill España, 2006.
>
> Dicionário de Dados. Repositório do Grupo Marventura da disciplina de Sistemas de Banco de Dados 1 da Universidade de Brasília, 2025. Disponível em: [https://sbd1.github.io/2025.1-Marventura/#/modelagem/dicionario-de-dados](https://sbd1.github.io/2025.1-Marventura/#/modelagem/dicionario-de-dados). Acesso em: 12 out. 2026.



## 📑 Histórico de versões

| Versão | Descrição | Autor(es) | Data de produção | Revisor(es) | Data de revisão | 
| :----: | --------- | --------- | :--------------: | ----------- | :-------------: |
| `1.0` | Criação do documento | [Matheus Henrick](https://github.com/MatheusHenrickSantos) | 12/10/2026 | - | - |
| `1.1` | Atualiza a tabela _estoque_ da camada bronze e adiciona as tabelas _estoque_, _material_ e _almoxarifado_ na camada prata. | [Matheus Henrick](https://github.com/MatheusHenrickSantos) | 18/10/2026 | - | - |
| `1.2` | Adiciona ao dicionário as entidades e os atributos bronze e prata do diagrama de arquitetura versão 2.0. | [Matheus Henrick](https://github.com/MatheusHenrickSantos) | 04/11/2026 | [Israel Thalles](https://github.com/IsraelThalles) | 05/11/2026 |
| `1.3` | Adiciona ao dicionário as entidades da camada _raw_. | [Israel Thalles](https://github.com/IsraelThalles) | 05/11/2026 | [Matheus Henrick](https://github.com/MatheusHenrickSantos) | 05/11/2026 |
| `1.4` | Adiciona ao dicionário as tabelas da camada ouro (fato, dimensões e monitor de atualização). | [magnluiz](https://github.com/magnluiz) | 15/11/2026 | - | - |
