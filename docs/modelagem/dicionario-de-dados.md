# Dicionário de Dados

## Convenções

- **Tipo ID**: O tipo de dados "ID" será uma composição única entre o nome abreviado da tabela, com três letras, e um serial, com três dígitos.  
  - *Exemplo: "est001" representa o primeiro item cadastrado na tabela `estoque`.*



## Definição das Tabelas

### Camada Bronze

  A **Tabela 1** abaixo apresenta a descrição da tabela `estoque`, que é oriunda dos **Dados Abertos da UnB**. Os campos `preco`, `valor_total`,`material`, `almoxarifado` e `saldo` são armazenados na camada bronze como *TEXT* e sem nenhum tipo de restrição para preservar os valores conforme disponibilizados pela fonte e evitar falhas de carga causadas por variações de formato, como símbolos monetários, separadores decimais ou espaços. A conversão para tipos mais adequados e a validação dos valores são realizadas nas etapas posteriores de tratamento dos dados. O mesmo vale para a **Tabela 2**, que apresenta a descrição da tabela CATMAT e para a **Tabela 3**, que apresenta a descrição da tabela de compras.

<details>
  <summary>Tabela 1 – Dicionário de Dados da Tabela Estoque
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 1 – Dicionário de Dados da Tabela Estoque</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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
        <tr>
          <td><code>ArquivoDeOrigem</code></td>
          <td>Nome do arquivo de origem dos dados.</td>
          <td>CHAR</td>
          <td>50</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>LinhaDoArquivo</code></td>
          <td>Número da linha onde o material está salvo no arquivo de origem.</td>
          <td>SMALLINT</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
          <td>-</td>
        </tr>
        <tr>
          <td><code>DataDaInsercao</code></td>
          <td>Data em que o arquivo foi salvo.</td>
          <td>TIMESTAMP</td>
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
  <summary>Tabela 2 – Dicionário de Dados da Tabela CATMAT
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 2 – Dicionário de Dados da Tabela CATMAT</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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
  <summary>Tabela 3 – Dicionário de Dados da Tabela Compras
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 3 – Dicionário de Dados da Tabela Compras</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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

### Camada Prata

  As **Tabelas 4 a 12** apresentam o dicionário de dados das tabelas geradas após a etapa de transformação da Camada Bronze, contendo seus respectivos atributos e descrições.

<details>
  <summary>Tabela 4 – Dicionário de Dados da Tabela Estoque
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 4 – Dicionário de Dados da Tabela Estoque</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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
  <summary>Tabela 5 – Dicionário de Dados da Tabela Material
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 5 – Dicionário de Dados da Tabela Material</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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
  <summary>Tabela 6 – Dicionário de Dados da Tabela Almoxarifado
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela64 – Dicionário de Dados da Tabela Almoxarifado</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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
  <summary>Tabela 7 – Dicionário de Dados da Tabela candidatoCatmat
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 7 – Dicionário de Dados da Tabela candidatoCatmat</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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
  <summary>Tabela 8 – Dicionário de Dados da Tabela catmatGrupo
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 8 – Dicionário de Dados da Tabela catmatGrupo</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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
  <summary>Tabela 9 – Dicionário de Dados da Tabela catmatClasse
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 9 – Dicionário de Dados da Tabela catmatClasse</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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
  <summary>Tabela 10 – Dicionário de Dados da Tabela catmatPdm
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 10 – Dicionário de Dados da Tabela catmatPdm</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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
  <summary>Tabela 11 – Dicionário de Dados da Tabela catmatItem
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 11 – Dicionário de Dados da Tabela catmatItem</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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
  <summary>Tabela 12 – Dicionário de Dados da Tabela compraPublica
    <svg class="arrow-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24"><path d="M8.59,16.58L13.17,12L8.59,7.41L10,6L16,12L10,18L8.59,16.58Z" /></svg>
  </summary>
  <div align="center">
    <p><strong>Tabela 12 – Dicionário de Dados da Tabela compraPublica</strong></p>
    <table>
      <thead>
        <tr>
          <th>Nome do Atributo</th>
          <th>Descrição</th>
          <th>Tipo de Dados</th>
          <th>Tamanho</th>
          <th>Valores Permitidos</th>
          <th>É chave?</th>
          <th>Outras Restrições</th>
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
> Dicionário de Dados. Repositório do Grupo Marventura da disciplina de Sistemas de Banco de Dados 1 da Universidade de Brasília, 2025. Disponível em: [https://sbd1.github.io/2025.1-Marventura/#/modelagem/dicionario-de-dados]https://sbd1.github.io/2025.1-Marventura/#/modelagem/dicionario-de-dados). Acesso em: 12 out. 2026.



## 📑 Histórico de Versões

| Versão | Descrição | Autor(es) | Data de Produção | Revisor(es) | Data de Revisão | 
| :----: | --------- | --------- | :--------------: | ----------- | :-------------: |
| `1.0` | Criação do documento | [Matheus Henrick](https://github.com/MatheusHenrickSantos) | 12/10/2026 | - | - |
| `1.1` | Atualiza a tabela _estoque_ da camada bronze e adiciona as tabelas _estoque_, _material_ e _almoxarifado_ na camada prata. | [Matheus Henrick](https://github.com/MatheusHenrickSantos) | 18/10/2026 | - | - |
| `1.2` | Adiciona ao dicionário as entidades e os atributos Bronze e Prata do diagrama de arquitetura versão 2.0. | [Matheus Henrick](https://github.com/MatheusHenrickSantos) | 04/11/2026 |  |  |