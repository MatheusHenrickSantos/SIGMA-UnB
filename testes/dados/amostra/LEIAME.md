# Amostra para testes e demonstração

**Estes arquivos não são dados reais.** Foram escritos à mão, no mesmo
formato das fontes, para testar o pipeline sem acesso às APIs:

| Arquivo | Imita | Conteúdo |
|---|---|---|
| `estoque/estoque-do-almoxarifado-11-2025.json` e `-12-2025.json` | dataset *Estoque do almoxarifado* (dados.unb.br) | 21 e 20 registros (`material`, `almoxarifado`, `saldo`, `preco`, `valor_total`) |
| `catmat/catalogo_catmat.json` | API `4_consultarItemMaterial` (Compras.gov.br) | 26 itens com códigos **fictícios** (990001 a 990026), um inativo |

Casos incluídos de propósito:

- descrições com entidades HTML (`ESFEROGR&Aacute;FICA`), mojibake
  (`SABÃƒO EM PÃ“`), caixa e espaços diferentes para o mesmo material e
  uma descrição só com dígitos (`1234`);
- pares quase iguais que diferem no que importa: pilha AA x AAA,
  resistor 10 kΩ x 1 kΩ, papel 75 x 90 g/m², álcool líquido x gel.

Os nomes de almoxarifado são `CENTRAL` e `PRC`, os valores aceitos pelo
teste `accepted_values` de `models/prata/almoxarifado.yml`.

Para rodar o fluxo raw → dbt → semântica com esta amostra, veja
`docs/semantica.md`.
