# Dicionário de Dados

## Convenções

- **Tipo ID**: O tipo de dados "ID" será uma composição única entre o nome abreviado da tabela, com três letras, e um serial, com três dígitos.  
  - *Exemplo: "est001" representa o primeiro item cadastrado na tabela `estoque`.*



## Definição das Tabelas

A **Tabela 1** abaixo apresenta a descrição da tabela `estoque`, que é oriunda dos **Dados Abertos da UnB**. Os
 campos `preco`, `valor_total`,`material`, `almoxarifado` e `saldo` são armazenados na camada bronze como *TEXT*
 e sem nenhum tipo de restrição para preservar os valores conforme disponibilizados pela fonte e evitar falhas de
 carga causadas por variações de formato, como símbolos monetários, separadores decimais ou espaços. A conversão
 para tipos mais adequados e a validação dos valores são realizadas nas etapas posteriores de tratamento dos dados.

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
| `1.0` | Criação do documento | [Matheus Henrick](https://github.com/MatheusHenrickSantos) | 12/10/2026 |  |  |