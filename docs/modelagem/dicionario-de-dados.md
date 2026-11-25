# Dicionário de dados

## Convenções

- **Tipo ID**: O tipo de dados "ID" será uma composição única entre o nome abreviado da tabela, com duas letras, e um serial, com quatro dígitos.  
  - *Exemplo: "es0001" representa o primeiro item cadastrado na tabela `estoque`.*



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
          <td>Descrição detalhada do item CATMAT, sem limite físico fixo.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
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
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
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
          <td>TEXT</td>
          <td>-</td>
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

### Busca vetorial e correspondência material–CATMAT

  A migração V6 separa o espaço técnico de busca dos dados de correspondência. As **Tabelas 16 a 19** ficam no schema `busca`: registro de modelos, descrições sincronizadas, vetores e execuções. O serviço Python `semantica` escreve nesses artefatos; eles não constituem a camada semântica analítica que poderá ser criada depois da Ouro.

  As **Tabelas 20 a 22** e as **visões 23 a 25** ficam na Prata: candidatos gerados, decisões por par e por material e visões para revisão e consumo. O candidato é uma sugestão; as tabelas de revisão registram decisões de pessoas ou sugestões de agentes. O snapshot `snap_correspondencia_material` lê a descrição de `busca` e as revisões da Prata; o serviço `compras` consome `prata.v_item_aprovado`. O processo está descrito em [Busca semântica](dados-e-pipeline/semantica.md), e as decisões arquiteturais nos [ADR 0005](adr/0005-busca-semantica-com-pgvector.md) e [ADR 0006](adr/0006-busca-hibrida-e-decisoes-por-agentes.md).

#### Busca vetorial — schema `busca`

<details>
  <summary>Tabela 16 – Dicionário de dados da tabela modelo_embedding
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 16 – Dicionário de dados da tabela modelo_embedding</strong></p>
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
          <td><code>id_modelo</code></td>
          <td>Identificador do modelo de embedding, gerado automaticamente.</td>
          <td>SMALLSERIAL</td>
          <td>-</td>
          <td>-</td>
          <td>PK</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>nome</code></td>
          <td>Nome do modelo no Hugging Face ou caminho de uma pasta local. Padrão: <code>intfloat/multilingual-e5-small</code>.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>Texto não vazio</td>
          <td>-</td>
          <td>Not NULL / CHECK / Unique composto</td>
        </tr>
        <tr>
          <td><code>revisao</code></td>
          <td>Commit do repositório do modelo no Hugging Face; <code>desconhecida</code> quando não é possível identificá-lo.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>Texto não vazio</td>
          <td>-</td>
          <td>Not NULL / CHECK / Unique composto</td>
        </tr>
        <tr>
          <td><code>dimensao</code></td>
          <td>Quantidade de dimensões dos vetores gerados pelo modelo. Precisa ser igual à da coluna <code>embedding.vetor</code>.</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>Maior que 0</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>prefixo_consulta</code></td>
          <td>Prefixo somado ao texto do material do estoque antes de gerar o vetor (<code>query: </code> na família e5).</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default '' / Unique composto</td>
        </tr>
        <tr>
          <td><code>prefixo_documento</code></td>
          <td>Prefixo somado ao texto do item CATMAT antes de gerar o vetor (<code>passage: </code> na família e5).</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default '' / Unique composto</td>
        </tr>
        <tr>
          <td><code>metadados</code></td>
          <td>Ambiente que gerou os vetores: biblioteca e versões (sentence-transformers, transformers, torch), dispositivo, limite de tokens e normalização L2. Gravado na primeira execução e não alterado depois.</td>
          <td>JSONB</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default '{}'</td>
        </tr>
        <tr>
          <td><code>registrado_em</code></td>
          <td>Data e hora em que o modelo foi registrado.</td>
          <td>TIMESTAMPTZ</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default now()</td>
        </tr>
      </tbody>
    </table>
    <p>Chave única composta: (<code>nome</code>, <code>revisao</code>, <code>prefixo_consulta</code>, <code>prefixo_documento</code>). Vetores de modelos diferentes nunca são comparados.</p>
    <p>Autora: <a href="https://github.com/samarawwleticia">Samara Letícia</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 17 – Dicionário de dados da tabela descricao
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 17 – Dicionário de dados da tabela descricao</strong></p>
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
          <td><code>id_descricao</code></td>
          <td>Identificador da descrição, gerado automaticamente.</td>
          <td>BIGSERIAL</td>
          <td>-</td>
          <td>-</td>
          <td>PK</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>origem</code></td>
          <td>De onde vem a descrição: material do estoque ou item do CATMAT.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>estoque, catmat</td>
          <td>-</td>
          <td>Not NULL / CHECK / Unique composto</td>
        </tr>
        <tr>
          <td><code>chave_origem</code></td>
          <td>Chave do registro na Prata: <code>identificador_material</code> de <code>prata.material</code> (ex.: <code>ma0012</code>) ou <code>codigo_item</code> de <code>prata.catmat_item</code>.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>Texto não vazio</td>
          <td>-</td>
          <td>Not NULL / CHECK / Unique composto</td>
        </tr>
        <tr>
          <td><code>texto_original</code></td>
          <td>Descrição exatamente como está na Prata (<code>prata.material.descricao_normalizada</code> ou <code>prata.catmat_item.descricao_item</code>), sem nenhuma alteração.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>CHECK (nulo somente junto com <code>hash_original</code>)</td>
        </tr>
        <tr>
          <td><code>hash_original</code></td>
          <td>Hash SHA-256 do texto original. É a chave das decisões de revisão.</td>
          <td>CHAR</td>
          <td>64</td>
          <td>Hexadecimal (0-9, a-f)</td>
          <td>-</td>
          <td>CHECK (nulo somente junto com <code>texto_original</code>)</td>
        </tr>
        <tr>
          <td><code>texto_normalizado</code></td>
          <td>Texto depois das regras compartilhadas de <code>codigos/normalizar/limpeza.py</code> (minúsculas, sem acento, abreviações expandidas, número separado da unidade). É o texto enviado ao modelo.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>CHECK (preenchido somente quando <code>situacao</code> = <code>valida</code>)</td>
        </tr>
        <tr>
          <td><code>hash_normalizado</code></td>
          <td>Hash SHA-256 da versão da normalização somada ao texto normalizado. Muda quando o texto ou a regra mudam, o que torna o vetor desatualizado.</td>
          <td>CHAR</td>
          <td>64</td>
          <td>Hexadecimal (0-9, a-f)</td>
          <td>-</td>
          <td>CHECK (preenchido somente quando <code>situacao</code> = <code>valida</code>)</td>
        </tr>
        <tr>
          <td><code>versao_normalizacao</code></td>
          <td>Versão das regras de normalização aplicadas ao texto (atualmente <code>2</code>).</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>situacao</code></td>
          <td>Indica se a descrição serve para gerar vetor. Descrição nula ou em branco é <code>vazia</code>; só números ou símbolos, ou menos de 3 caracteres, é <code>invalida</code>.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>valida, vazia, invalida</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>motivo</code></td>
          <td>Motivo da recusa quando a descrição não é válida (ex.: <em>sem letras (só números ou símbolos)</em>).</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>CHECK (nulo somente quando <code>situacao</code> = <code>valida</code>)</td>
        </tr>
        <tr>
          <td><code>ativa</code></td>
          <td>Indica se a chave ainda existe na Prata. Vira <code>FALSE</code> quando o registro some da origem; a linha é mantida porque candidatos antigos apontam para ela.</td>
          <td>BOOLEAN</td>
          <td>-</td>
          <td>TRUE / FALSE</td>
          <td>-</td>
          <td>Not NULL / Default TRUE</td>
        </tr>
        <tr>
          <td><code>sincronizada_em</code></td>
          <td>Data e hora da última sincronização da linha com a Prata.</td>
          <td>TIMESTAMPTZ</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default now()</td>
        </tr>
        <tr>
          <td><code>atualizada_em</code></td>
          <td>Data e hora da última mudança no texto original, no texto normalizado ou na situação.</td>
          <td>TIMESTAMPTZ</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default now()</td>
        </tr>
      </tbody>
    </table>
    <p>Chaves únicas compostas: (<code>origem</code>, <code>chave_origem</code>) e (<code>id_descricao</code>, <code>origem</code>), esta última alvo da chave estrangeira de <code>embedding</code>. Índices: <code>ix_descricao_hash</code> (<code>origem</code>, <code>hash_normalizado</code>) e <code>ix_descricao_catmat_trgm</code> (GiST com trigramas sobre <code>texto_normalizado</code>, só itens CATMAT válidos e ativos, criado na V4).</p>
    <p>Autora: <a href="https://github.com/samarawwleticia">Samara Letícia</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 18 – Dicionário de dados da tabela embedding
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 18 – Dicionário de dados da tabela embedding</strong></p>
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
          <td><code>id_descricao</code></td>
          <td>Descrição que originou o vetor.</td>
          <td>BIGINT</td>
          <td>-</td>
          <td>-</td>
          <td>PK, FK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>origem</code></td>
          <td>Cópia de <code>descricao.origem</code>, garantida pela chave estrangeira composta. Permite filtrar só os vetores do CATMAT na busca.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>estoque, catmat</td>
          <td>FK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>id_modelo</code></td>
          <td>Modelo que gerou o vetor.</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>-</td>
          <td>PK, FK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>hash_normalizado</code></td>
          <td>Hash do texto normalizado que gerou o vetor. Se for diferente de <code>descricao.hash_normalizado</code>, o vetor está desatualizado e é apagado na próxima sincronização.</td>
          <td>CHAR</td>
          <td>64</td>
          <td>Hexadecimal (0-9, a-f)</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>vetor</code></td>
          <td>Vetor de embedding do texto normalizado, com norma 1 (extensão pgvector). A dimensão é a do modelo padrão; outro modelo com outra dimensão exige uma nova migração.</td>
          <td>VECTOR</td>
          <td>384</td>
          <td>Números reais finitos</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>gerado_em</code></td>
          <td>Data e hora em que o vetor foi gerado.</td>
          <td>TIMESTAMPTZ</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default now()</td>
        </tr>
      </tbody>
    </table>
    <p>Chave estrangeira composta (<code>id_descricao</code>, <code>origem</code>) → <code>descricao</code>, com <code>ON DELETE CASCADE</code>; <code>id_modelo</code> → <code>modelo_embedding</code>. Só fica gravado o vetor atual de cada descrição. O índice HNSW criado na V2 foi removido na V3: a busca por cosseno é exata (ver ADR 0005).</p>
    <p>Autora: <a href="https://github.com/samarawwleticia">Samara Letícia</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 19 – Dicionário de dados da tabela execucao_correspondencia
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 19 – Dicionário de dados da tabela execucao_correspondencia</strong></p>
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
          <td><code>id_execucao</code></td>
          <td>Identificador da execução da busca de correspondência, gerado automaticamente.</td>
          <td>BIGSERIAL</td>
          <td>-</td>
          <td>-</td>
          <td>PK</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>id_modelo</code></td>
          <td>Modelo cujos vetores foram comparados.</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>-</td>
          <td>FK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>top_k</code></td>
          <td>Quantidade máxima de candidatos gravados por material (padrão 10).</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>1 a 100</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>limiar_similaridade</code></td>
          <td>Similaridade mínima para gravar um candidato. Nulo significa sem filtro (ainda não há limiar calibrado).</td>
          <td>REAL</td>
          <td>-</td>
          <td>-1 a 1</td>
          <td>-</td>
          <td>CHECK</td>
        </tr>
        <tr>
          <td><code>busca_exata</code></td>
          <td>Indica se o uso de índice foi proibido na execução, forçando a varredura completa.</td>
          <td>BOOLEAN</td>
          <td>-</td>
          <td>TRUE / FALSE</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>ef_search</code></td>
          <td>Valor de <code>hnsw.ef_search</code> usado na sessão. Só tem efeito se existir índice HNSW; nulo quando a busca exata foi forçada.</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>Maior que 0</td>
          <td>-</td>
          <td>CHECK</td>
        </tr>
        <tr>
          <td><code>versao_normalizacao</code></td>
          <td>Versão das regras de normalização vigente na execução.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>versao_regras</code></td>
          <td>Versão das regras de checagem de especificações (<code>codigos/semantica/especificacoes.py</code>).</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>iniciada_em</code></td>
          <td>Data e hora de início da execução.</td>
          <td>TIMESTAMPTZ</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default now()</td>
        </tr>
        <tr>
          <td><code>finalizada_em</code></td>
          <td>Data e hora de fim da execução. Nulo enquanto não termina; só execuções finalizadas entram na fila de revisão.</td>
          <td>TIMESTAMPTZ</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>materiais</code></td>
          <td>Materiais do estoque, válidos e ativos, considerados na execução.</td>
          <td>INTEGER</td>
          <td>-</td>
          <td>≥ 0</td>
          <td>-</td>
          <td>CHECK</td>
        </tr>
        <tr>
          <td><code>materiais_sem_candidato</code></td>
          <td>Materiais para os quais nenhum candidato foi gravado.</td>
          <td>INTEGER</td>
          <td>-</td>
          <td>≥ 0</td>
          <td>-</td>
          <td>CHECK</td>
        </tr>
        <tr>
          <td><code>candidatos</code></td>
          <td>Total de candidatos gravados na execução.</td>
          <td>INTEGER</td>
          <td>-</td>
          <td>≥ 0</td>
          <td>-</td>
          <td>CHECK</td>
        </tr>
        <tr>
          <td><code>metodo</code></td>
          <td>Método de busca: <code>cosseno</code> ordena pela similaridade; <code>hibrido</code> une os vizinhos por cosseno e por trigramas e reordena pela pontuação. O pipeline usa <code>hibrido</code> por padrão.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>cosseno, hibrido</td>
          <td>-</td>
          <td>Not NULL / CHECK / Default 'cosseno'</td>
        </tr>
        <tr>
          <td><code>k_vetor</code></td>
          <td>Busca híbrida: vizinhos recuperados por cosseno antes da reordenação (padrão 50).</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>1 a 500</td>
          <td>-</td>
          <td>CHECK</td>
        </tr>
        <tr>
          <td><code>k_trigrama</code></td>
          <td>Busca híbrida: vizinhos recuperados por trigramas (padrão 20; 0 desliga essa busca).</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>0 a 500</td>
          <td>-</td>
          <td>CHECK</td>
        </tr>
        <tr>
          <td><code>versao_reordenacao</code></td>
          <td>Busca híbrida: versão das regras de reordenação (<code>codigos/semantica/reordenacao.py</code>).</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>CHECK</td>
        </tr>
        <tr>
          <td><code>pesos</code></td>
          <td>Busca híbrida: pesos de cada medida na pontuação (<code>cosseno</code> 0,40; <code>token_set</code> 0,20; <code>token_sort</code> 0,15; <code>cobertura</code> 0,25).</td>
          <td>JSONB</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>CHECK</td>
        </tr>
      </tbody>
    </table>
    <p>Restrição <code>ck_execucao_hibrida</code>: quando <code>metodo</code> = <code>hibrido</code>, <code>k_vetor</code>, <code>k_trigrama</code>, <code>versao_reordenacao</code> e <code>pesos</code> são obrigatórios. As colunas de <code>metodo</code> a <code>pesos</code> foram acrescentadas na V4.</p>
    <p>Autora: <a href="https://github.com/samarawwleticia">Samara Letícia</a>.</p>
  </div>
</details>

#### Correspondências e decisões — camada Prata

<details>
  <summary>Tabela 20 – Dicionário de dados da tabela candidato_catmat
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 20 – Dicionário de dados da tabela candidato_catmat</strong></p>
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
          <td><code>id_execucao</code></td>
          <td>Execução que gerou o candidato.</td>
          <td>BIGINT</td>
          <td>-</td>
          <td>-</td>
          <td>PK, FK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>id_descricao_material</code></td>
          <td>Descrição do material do estoque para o qual o candidato foi sugerido.</td>
          <td>BIGINT</td>
          <td>-</td>
          <td>-</td>
          <td>PK, FK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>posicao</code></td>
          <td>Posição do candidato na lista do material (1 = primeiro colocado). Na busca híbrida, candidatos com conflito de especificação ficam no fim.</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>≥ 1</td>
          <td>PK</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>id_descricao_catmat</code></td>
          <td>Descrição do item CATMAT sugerido.</td>
          <td>BIGINT</td>
          <td>-</td>
          <td>-</td>
          <td>FK</td>
          <td>Not NULL / Unique composto</td>
        </tr>
        <tr>
          <td><code>similaridade</code></td>
          <td>Similaridade de cosseno entre o vetor do material e o do item (1 − distância de cosseno; 1 = mesma direção).</td>
          <td>DOUBLE PRECISION</td>
          <td>-</td>
          <td>-1 a 1</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>situacao_especificacao</code></td>
          <td>Resultado da checagem de especificações (medidas, unidades, cor, apresentação, códigos) entre o texto do estoque e o do CATMAT. Não altera a similaridade.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>conflito_tecnico, sem_conflito_mas_incompleto, sem_conflito_detectado, sem_especificacoes_verificaveis</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>especificacoes</code></td>
          <td>Detalhes da checagem: especificações encontradas no estoque e no CATMAT e as categorias compatíveis, ausentes no CATMAT e em conflito, com a descrição de cada conflito.</td>
          <td>JSONB</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default '{}'</td>
        </tr>
        <tr>
          <td><code>pontuacao</code></td>
          <td>Pontuação da busca híbrida, combinando cosseno, <code>token_set</code>, <code>token_sort</code> e cobertura de termos. Nulo nas execuções só por cosseno.</td>
          <td>DOUBLE PRECISION</td>
          <td>-</td>
          <td>0 a 100</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>medidas</code></td>
          <td>Medidas que formaram a pontuação: <code>cosseno</code>, <code>token_set</code>, <code>token_sort</code> e <code>cobertura</code>.</td>
          <td>JSONB</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default '{}'</td>
        </tr>
        <tr>
          <td><code>recuperado_por</code></td>
          <td>Busca que trouxe o candidato: por vetor, por trigramas ou pelas duas.</td>
          <td>TEXT[]</td>
          <td>-</td>
          <td>{vetor}, {trigrama}, {vetor,trigrama}</td>
          <td>-</td>
          <td>Not NULL / Default '{vetor}'</td>
        </tr>
      </tbody>
    </table>
    <p>Chave primária composta: (<code>id_execucao</code>, <code>id_descricao_material</code>, <code>posicao</code>). Chave única composta: (<code>id_execucao</code>, <code>id_descricao_material</code>, <code>id_descricao_catmat</code>), para que o mesmo item não apareça duas vezes na lista de um material. <code>id_execucao</code> → <code>execucao_correspondencia</code> (<code>ON DELETE CASCADE</code>); <code>id_descricao_material</code> e <code>id_descricao_catmat</code> → <code>descricao</code>. Um candidato é uma sugestão para revisão, nunca uma equivalência aprovada. As colunas <code>pontuacao</code>, <code>medidas</code> e <code>recuperado_por</code> foram acrescentadas na V4.</p>
    <p>Autora: <a href="https://github.com/samarawwleticia">Samara Letícia</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 21 – Dicionário de dados da tabela revisao_correspondencia
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 21 – Dicionário de dados da tabela revisao_correspondencia</strong></p>
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
          <td><code>hash_original_material</code></td>
          <td>Hash SHA-256 do texto original do material (<code>descricao.hash_original</code>). A decisão vale para aquele texto exato e continua valendo depois de reprocessamentos.</td>
          <td>CHAR</td>
          <td>64</td>
          <td>Hexadecimal (0-9, a-f)</td>
          <td>PK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>codigo_item</code></td>
          <td>Código do item CATMAT avaliado.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>0-9</td>
          <td>PK</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>decisao</code></td>
          <td>Decisão sobre o par material × item CATMAT.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>equivalente, nao_equivalente, incerto</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>revisor</code></td>
          <td>Quem tomou a decisão.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>Texto não vazio</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>observacao</code></td>
          <td>Observação livre de quem revisou.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>texto_material</code></td>
          <td>Cópia do texto do material revisado, para leitura humana.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>id_execucao</code></td>
          <td>Última execução em que o par apareceu como candidato, gravada na revisão par a par (comando <code>revisar</code>). Nulo nas decisões importadas em lote (comando <code>importar</code>), quando o par nunca foi candidato ou quando a execução é apagada.</td>
          <td>BIGINT</td>
          <td>-</td>
          <td>-</td>
          <td>FK</td>
          <td>ON DELETE SET NULL</td>
        </tr>
        <tr>
          <td><code>revisada_em</code></td>
          <td>Data e hora da decisão.</td>
          <td>TIMESTAMPTZ</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default now()</td>
        </tr>
        <tr>
          <td><code>tipo_revisor</code></td>
          <td>Origem da decisão: <code>pessoa</code> (conferida pela squad) ou <code>agente</code> (sugerida por agente de IA, ainda sem conferência). Decisão de pessoa substitui a de agente; a de agente nunca substitui a de pessoa.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>pessoa, agente</td>
          <td>-</td>
          <td>Not NULL / CHECK / Default 'pessoa'</td>
        </tr>
      </tbody>
    </table>
    <p>Chave primária composta: (<code>hash_original_material</code>, <code>codigo_item</code>). Junto com <code>revisao_material</code>, é a única tabela da camada que não pode ser recalculada a partir da Prata. <code>tipo_revisor</code> foi acrescentada na V5.</p>
    <p>Autora: <a href="https://github.com/samarawwleticia">Samara Letícia</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 22 – Dicionário de dados da tabela revisao_material
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 22 – Dicionário de dados da tabela revisao_material</strong></p>
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
          <td><code>hash_original_material</code></td>
          <td>Hash SHA-256 do texto original do material (<code>descricao.hash_original</code>).</td>
          <td>CHAR</td>
          <td>64</td>
          <td>Hexadecimal (0-9, a-f)</td>
          <td>PK</td>
          <td>Unique / Not NULL</td>
        </tr>
        <tr>
          <td><code>sem_correspondente</code></td>
          <td>Indica que não existe item CATMAT ativo equivalente ao material.</td>
          <td>BOOLEAN</td>
          <td>-</td>
          <td>TRUE / FALSE</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>confianca</code></td>
          <td>Confiança na decisão: <code>alta</code> = inequívoca; <code>media</code> = com inferência; <code>baixa</code> = palpite, prioridade de revisão.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>alta, media, baixa</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>justificativa</code></td>
          <td>Justificativa da decisão.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>revisor</code></td>
          <td>Quem tomou a decisão.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>Texto não vazio</td>
          <td>-</td>
          <td>Not NULL / CHECK</td>
        </tr>
        <tr>
          <td><code>tipo_revisor</code></td>
          <td>Origem da decisão: <code>pessoa</code> ou <code>agente</code> de IA.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>pessoa, agente</td>
          <td>-</td>
          <td>Not NULL / CHECK / Default 'pessoa'</td>
        </tr>
        <tr>
          <td><code>texto_material</code></td>
          <td>Cópia do texto do material revisado, para leitura humana.</td>
          <td>TEXT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL</td>
        </tr>
        <tr>
          <td><code>revisada_em</code></td>
          <td>Data e hora da decisão.</td>
          <td>TIMESTAMPTZ</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>Not NULL / Default now()</td>
        </tr>
      </tbody>
    </table>
    <p>Decisão sobre o material como um todo, criada na V5; os itens equivalentes ficam em <code>revisao_correspondencia</code>. Registra principalmente o caso "sem correspondente", que não tem código CATMAT para apontar.</p>
    <p>Autora: <a href="https://github.com/samarawwleticia">Samara Letícia</a>.</p>
  </div>
</details>

#### Visões de consumo — camada Prata

<details>
  <summary>Tabela 23 – Dicionário de dados da visão v_candidato_catmat
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 23 – Dicionário de dados da visão v_candidato_catmat</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Origem</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>id_execucao</code></td>
          <td>Execução que gerou o candidato.</td>
          <td>BIGINT</td>
          <td><code>candidato_catmat.id_execucao</code></td>
        </tr>
        <tr>
          <td><code>id_modelo</code></td>
          <td>Modelo usado na execução.</td>
          <td>SMALLINT</td>
          <td><code>execucao_correspondencia.id_modelo</code></td>
        </tr>
        <tr>
          <td><code>metodo</code></td>
          <td>Método da execução.</td>
          <td>TEXT</td>
          <td><code>execucao_correspondencia.metodo</code></td>
        </tr>
        <tr>
          <td><code>identificador_material</code></td>
          <td>Identificador do material na Prata.</td>
          <td>TEXT</td>
          <td><code>descricao.chave_origem</code> (estoque)</td>
        </tr>
        <tr>
          <td><code>material</code></td>
          <td>Descrição original do material.</td>
          <td>TEXT</td>
          <td><code>descricao.texto_original</code> (estoque)</td>
        </tr>
        <tr>
          <td><code>posicao</code></td>
          <td>Posição do candidato na lista do material.</td>
          <td>SMALLINT</td>
          <td><code>candidato_catmat.posicao</code></td>
        </tr>
        <tr>
          <td><code>codigo_item</code></td>
          <td>Código do item CATMAT sugerido.</td>
          <td>TEXT</td>
          <td><code>descricao.chave_origem</code> (catmat)</td>
        </tr>
        <tr>
          <td><code>descricao_catmat</code></td>
          <td>Descrição original do item CATMAT.</td>
          <td>TEXT</td>
          <td><code>descricao.texto_original</code> (catmat)</td>
        </tr>
        <tr>
          <td><code>similaridade</code></td>
          <td>Similaridade de cosseno.</td>
          <td>DOUBLE PRECISION</td>
          <td><code>candidato_catmat.similaridade</code></td>
        </tr>
        <tr>
          <td><code>pontuacao</code></td>
          <td>Pontuação da busca híbrida (0 a 100).</td>
          <td>DOUBLE PRECISION</td>
          <td><code>candidato_catmat.pontuacao</code></td>
        </tr>
        <tr>
          <td><code>vantagem_sobre_proximo</code></td>
          <td>Diferença entre a medida que define a ordem (pontuação na busca híbrida, similaridade na de cosseno) e a do candidato seguinte. Valor pequeno indica empate; nulo no último candidato.</td>
          <td>DOUBLE PRECISION</td>
          <td>Calculado com <code>lead()</code> sobre <code>posicao</code></td>
        </tr>
        <tr>
          <td><code>situacao_especificacao</code></td>
          <td>Resultado da checagem de especificações.</td>
          <td>TEXT</td>
          <td><code>candidato_catmat.situacao_especificacao</code></td>
        </tr>
        <tr>
          <td><code>especificacoes</code></td>
          <td>Detalhes da checagem de especificações.</td>
          <td>JSONB</td>
          <td><code>candidato_catmat.especificacoes</code></td>
        </tr>
        <tr>
          <td><code>medidas</code></td>
          <td>Medidas que formaram a pontuação.</td>
          <td>JSONB</td>
          <td><code>candidato_catmat.medidas</code></td>
        </tr>
        <tr>
          <td><code>recuperado_por</code></td>
          <td>Busca que trouxe o candidato.</td>
          <td>TEXT[]</td>
          <td><code>candidato_catmat.recuperado_por</code></td>
        </tr>
        <tr>
          <td><code>decisao</code></td>
          <td>Decisão registrada para o par, se houver.</td>
          <td>TEXT</td>
          <td><code>revisao_correspondencia.decisao</code></td>
        </tr>
        <tr>
          <td><code>revisor</code></td>
          <td>Quem decidiu.</td>
          <td>TEXT</td>
          <td><code>revisao_correspondencia.revisor</code></td>
        </tr>
        <tr>
          <td><code>revisada_em</code></td>
          <td>Data e hora da decisão.</td>
          <td>TIMESTAMPTZ</td>
          <td><code>revisao_correspondencia.revisada_em</code></td>
        </tr>
      </tbody>
    </table>
    <p>Candidatos de todas as execuções, com os textos dos dois lados e a revisão do par. Faz o papel da entidade <code>candidatoCatmat</code> (Tabela 10) do diagrama de arquitetura.</p>
    <p>Autora: <a href="https://github.com/samarawwleticia">Samara Letícia</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 24 – Dicionário de dados da visão v_fila_revisao
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 24 – Dicionário de dados da visão v_fila_revisao</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Origem</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><em>Todas as colunas de</em> <code>v_candidato_catmat</code></td>
          <td>Mesmas colunas e descrições da Tabela 23.</td>
          <td>-</td>
          <td><code>v_candidato_catmat</code></td>
        </tr>
        <tr>
          <td><code>sugestao_sem_correspondente</code></td>
          <td>Decisão registrada de que o material não tem item CATMAT equivalente.</td>
          <td>BOOLEAN</td>
          <td><code>revisao_material.sem_correspondente</code></td>
        </tr>
        <tr>
          <td><code>confianca_sugestao</code></td>
          <td>Confiança dessa decisão.</td>
          <td>TEXT</td>
          <td><code>revisao_material.confianca</code></td>
        </tr>
      </tbody>
    </table>
    <p>Candidatos da última execução finalizada de cada modelo, só dos materiais que ainda não foram resolvidos por uma pessoa (nem item <code>equivalente</code> nem <code>sem_correspondente</code> decididos com <code>tipo_revisor</code> = <code>pessoa</code>). Materiais resolvidos só por agente continuam na fila, com a sugestão visível. É exportada para <code>dados/semantica/fila_revisao.csv</code> pelo comando <code>python -m semantica fila</code>.</p>
    <p>Autora: <a href="https://github.com/samarawwleticia">Samara Letícia</a>.</p>
  </div>
</details>

<details>
  <summary>Tabela 25 – Dicionário de dados da visão v_item_aprovado
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 25 – Dicionário de dados da visão v_item_aprovado</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do atributo</th>
          <th>Descrição</th>
          <th>Tipo de dados</th>
          <th>Origem</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><code>identificador_material</code></td>
          <td>Identificador do material na Prata.</td>
          <td>TEXT</td>
          <td><code>descricao.chave_origem</code> (estoque)</td>
        </tr>
        <tr>
          <td><code>material</code></td>
          <td>Descrição original do material.</td>
          <td>TEXT</td>
          <td><code>descricao.texto_original</code> (estoque)</td>
        </tr>
        <tr>
          <td><code>codigo_item</code></td>
          <td>Código do item CATMAT equivalente.</td>
          <td>TEXT</td>
          <td><code>revisao_correspondencia.codigo_item</code></td>
        </tr>
        <tr>
          <td><code>tipo_revisor</code></td>
          <td>Origem da decisão (pessoa ou agente).</td>
          <td>TEXT</td>
          <td><code>revisao_correspondencia.tipo_revisor</code></td>
        </tr>
        <tr>
          <td><code>revisor</code></td>
          <td>Quem decidiu.</td>
          <td>TEXT</td>
          <td><code>revisao_correspondencia.revisor</code></td>
        </tr>
        <tr>
          <td><code>revisada_em</code></td>
          <td>Data e hora da decisão.</td>
          <td>TIMESTAMPTZ</td>
          <td><code>revisao_correspondencia.revisada_em</code></td>
        </tr>
      </tbody>
    </table>
    <p>Itens CATMAT marcados como <code>equivalente</code>, por pessoa ou por agente, dos materiais ativos. É a entrada do serviço <code>compras</code>, que busca as compras públicas de cada código aprovado.</p>
    <p>Autora: <a href="https://github.com/samarawwleticia">Samara Letícia</a>.</p>
  </div>
</details>

---

### Camada ouro

> **Tabelas acrescentadas na E4** (camada semântica de métricas, qualidade, fila de revisão e ETL reverso): `ouro.metrica_mensal`, `ouro.catalogo_metrica`, `ouro.qualidade_dados`, `ouro.resumo_correspondencia`, `reverso.alerta_preco_compras` e `reverso.acesso_almoxarifado`. Ainda não estão descritas neste dicionário no formato das tabelas abaixo; o [catálogo gerado do manifesto do dbt](../governanca/catalogo-gerado.md) lista colunas, testes e linhagem de cada uma.

  A camada ouro organiza os dados em um **modelo estrela** que responde à pergunta de gestão: para quais materiais do estoque existe preço de compras públicas comparável e quais têm as maiores diferenças, por almoxarifado e período. A decisão e as alternativas estão na [ADR 7](adr/0007-modelo-estrela-para-comparacao-de-precos.md), e o funcionamento do modelo em [Camada ouro: modelo analítico](dados-e-pipeline/camada-ouro.md). Todas as tabelas são geradas pelo dbt (`models/ouro/` e `snapshots/`) no esquema `ouro`.

  A **Tabela 26** descreve o fato `fato_comparacao_preco`, cujo grão é **uma linha por material, por almoxarifado, por mês de referência publicado**. As **Tabelas 27 a 30** descrevem as dimensões: `dim_material`, que guarda a correspondência material × CATMAT como dimensão de variação lenta do tipo 2 (uma linha por versão), `dim_almoxarifado`, `dim_tempo` e `dim_item_catmat`. A **Tabela 31** descreve `monitor_atualizacao`, que mede o atraso (freshness) das tabelas de consumo diante do SLA declarado.

  Nesta camada, os tipos são os que o PostgreSQL atribui às colunas geradas pelo dbt. Os identificadores de material e almoxarifado seguem o tipo ID das camadas anteriores; na `dim_material` o identificador vem do registro de descrições do schema `busca` e por isso é armazenado como _TEXT_, com o mesmo formato. Atributos numéricos sem tamanho são _NUMERIC_ sem precisão fixa; os que passam por arredondamento indicam o número de casas decimais.

<details>
  <summary>Tabela 26 – Dicionário de dados da tabela fato_comparacao_preco
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 26 – Dicionário de dados da tabela fato_comparacao_preco</strong></p>
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
  <summary>Tabela 27 – Dicionário de dados da tabela dim_material
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 27 – Dicionário de dados da tabela dim_material</strong></p>
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
  <summary>Tabela 28 – Dicionário de dados da tabela dim_almoxarifado
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 28 – Dicionário de dados da tabela dim_almoxarifado</strong></p>
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
  <summary>Tabela 29 – Dicionário de dados da tabela dim_tempo
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 29 – Dicionário de dados da tabela dim_tempo</strong></p>
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
  <summary>Tabela 30 – Dicionário de dados da tabela dim_item_catmat
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 30 – Dicionário de dados da tabela dim_item_catmat</strong></p>
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
          <td>Nome do Padrão Descritivo de Materiais (PDM).</td>
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
  <summary>Tabela 31 – Dicionário de dados da tabela monitor_atualizacao
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 31 – Dicionário de dados da tabela monitor_atualizacao</strong></p>
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
| `1.4` | Adiciona ao dicionário as tabelas e as visões da camada semântica (schema _semantica_, migrações V2 a V5). | [Samara Letícia](https://github.com/samarawwleticia) | 16/11/2026 | - | - |
| `1.5` | Adiciona ao dicionário as tabelas da camada ouro (fato, dimensões e monitor de atualização). | [magnluiz](https://github.com/magnluiz) | 15/11/2026 | - | - |
| `1.6` | Atualiza a localização dos artefatos de busca e das correspondências após a migração V6. | Matheus Henrick | 23/11/2026 | - | - |
