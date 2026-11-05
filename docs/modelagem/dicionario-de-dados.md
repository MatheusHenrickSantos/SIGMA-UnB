# Dicionário de dados

## Convenções

- **Tipo ID**: O tipo de dados "ID" será uma composição única entre o nome abreviado da tabela, com três letras, e um serial, com três dígitos.  
  - *Exemplo: "est001" representa o primeiro item cadastrado na tabela `estoque`.*



## Definição das tabelas

### Camada raw

A __Tabela 1__ abaixo apresenta a descrição da tabela `estoque`, que armazena os dados brutos mensais de estoque oriundos dos dados abertos da UnB. O campo `DadoBruto` é armazenado como _TEXT_ para preservar o arquivo exatamente como disponibilizado pela fonte, enquanto `MesDeReferencia` e `AnoDeReferencia` utilizam o tipo _SMALLINT_ e a `HashDoArquivo` utiliza _CHAR(64)_ (gerada via SHA-256) para garantir a integridade e unicidade da carga. As __Tabelas 2 e 3__ apresentam, respectivamente, a descrição da tabela `compras` e da tabela `CATMAT`, compostas pelos atributos `DadoBruto`, `HashDoArquivo` e `DataDaInsercao` (_TIMESTAMP_). Essa estruturação garante a rastreabilidade e a imutabilidade do dado de entrada sem nenhum tipo de tratamento prévio.

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
          <td>Linha bruta ou conteúdo integral do arquivo CSV mensal de estoque.</td>
          <td>TEXT</td>
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
          <td>TEXT</td>
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
          <td>TEXT</td>
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