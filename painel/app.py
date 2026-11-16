"""Painel SIGMA-UnB: preço do estoque × preço de compras públicas.

Lê só a camada ouro (ouro.fato_comparacao_preco e dimensões,
ouro.monitor_atualizacao). Responde à pergunta de gestão da E1:

    Para quais materiais do estoque da UnB é possível encontrar um item
    correspondente no CATMAT e em compras públicas comparáveis, e quais
    apresentam as maiores diferenças entre o preço registrado no estoque e
    os preços dessas compras, por almoxarifado e período?

Rodar: docker compose up painel  (http://localhost:8501)
"""

from __future__ import annotations

import os

import altair as alt
import pandas as pd
import psycopg
import streamlit as st

st.set_page_config(page_title="SIGMA-UnB · Preços", layout="wide")

AZUL = "#1E3A78"
VERDE = "#00843D"


@st.cache_resource
def conexao() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ.get("HOST_DO_BANCO", "localhost"),
        port=int(os.environ.get("PORTA_DO_BANCO", "5432")),
        dbname=os.environ.get("NOME_DO_BANCO", "sigma"),
        user=os.environ.get("USUARIO_DO_BANCO", "sigma"),
        password=os.environ.get("SENHA_DO_BANCO", "sigma"),
        autocommit=True,
    )


@st.cache_data(ttl=600)
def consultar(sql: str, parametros: tuple = ()) -> pd.DataFrame:
    with conexao().cursor() as cur:
        cur.execute(sql, parametros)
        colunas = [c.name for c in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=colunas)


def tabela_existe() -> bool:
    return bool(consultar("SELECT to_regclass('ouro.fato_comparacao_preco') IS NOT NULL AS existe")
                .iloc[0, 0])


st.title("Preço do estoque × preço de compras públicas")
st.caption(
    "Para quais materiais do estoque da UnB há item CATMAT e compras públicas comparáveis, "
    "e quais têm as maiores diferenças de preço, por almoxarifado e período?"
)

if not tabela_existe():
    st.error("A camada ouro ainda não foi gerada. Rode o pipeline (docker compose up).")
    st.stop()

# --- Freshness / SLA -------------------------------------------------------
monitor = consultar(
    "SELECT tabela, ultimo_dado, atraso_dias, sla_dias, situacao_sla FROM ouro.monitor_atualizacao "
    "ORDER BY tabela"
)
fora = monitor[monitor["situacao_sla"] == "fora do SLA"]
if not fora.empty:
    linha = monitor[monitor["tabela"] == "ouro.fato_comparacao_preco"].iloc[0]
    st.warning(
        f"Dado desatualizado: o estoque mais recente é de {linha['ultimo_dado']:%m/%Y} "
        f"({linha['atraso_dias']} dias de atraso; SLA de {linha['sla_dias']} dias). "
        "O portal dados.unb.br não publicou meses mais novos."
    )

# --- Filtros ---------------------------------------------------------------
meses = consultar(
    "SELECT mes_referencia, ano_mes FROM ouro.dim_tempo WHERE publicado ORDER BY mes_referencia DESC"
)
almoxarifados = consultar("SELECT identificador_almoxarifado, nome FROM ouro.dim_almoxarifado ORDER BY nome")

with st.sidebar:
    st.header("Filtros")
    ano_mes = st.selectbox("Mês de referência", meses["ano_mes"].tolist(), index=0)
    escolhidos = st.multiselect("Almoxarifado", almoxarifados["nome"].tolist(),
                                default=almoxarifados["nome"].tolist())
    minimo_compras = st.slider("Mínimo de compras públicas na referência", 1, 50, 5)
    so_pessoa = st.checkbox("Só correspondências conferidas por pessoa", value=False)
    st.caption(
        "A correspondência material × CATMAT foi sugerida por agentes de IA e ainda está "
        "em revisão pela Squad; marque a opção acima para ver só as conferidas."
    )

mes = meses.loc[meses["ano_mes"] == ano_mes, "mes_referencia"].iloc[0]

base = consultar(
    """
    SELECT f.identificador_material, d.nome AS material, d.descricao, a.nome AS almoxarifado,
           f.quantidade, f.preco_estoque, f.valor_estoque, f.preco_publico_mediano,
           f.compras_publicas, f.unidade_fornecimento_predominante, f.diferenca_absoluta,
           f.diferenca_pct, f.tem_preco_publico, f.tipo_revisor_correspondencia,
           d.codigos_equivalentes, d.sem_correspondente
    FROM ouro.fato_comparacao_preco f
    JOIN ouro.dim_material d USING (sk_material)
    JOIN ouro.dim_almoxarifado a USING (identificador_almoxarifado)
    WHERE f.mes_referencia = %s
    """,
    (mes,),
)
base = base[base["almoxarifado"].isin(escolhidos)]
for coluna in ("quantidade", "preco_estoque", "valor_estoque", "preco_publico_mediano",
               "diferenca_absoluta", "diferenca_pct"):
    base[coluna] = pd.to_numeric(base[coluna])

# --- Cobertura: quantos materiais dá para comparar -------------------------
com_item = base[base["codigos_equivalentes"] != ""]
com_preco = base[base["tem_preco_publico"]]
valor_total = base["valor_estoque"].sum()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Materiais em estoque", f"{len(base):,}".replace(",", "."))
c2.metric("Com item CATMAT equivalente", f"{len(com_item):,}".replace(",", "."),
          f"{len(com_item) / max(len(base), 1):.0%}", delta_color="off")
c3.metric("Com preço público para comparar", f"{len(com_preco):,}".replace(",", "."),
          f"{len(com_preco) / max(len(base), 1):.0%}", delta_color="off")
c4.metric("Valor do estoque comparável",
          f"{com_preco['valor_estoque'].sum() / valor_total:.1%}" if valor_total else "-",
          f"de R$ {valor_total:,.0f}".replace(",", "."), delta_color="off")

# --- Ranking: maiores diferenças -------------------------------------------
ranking = com_preco[com_preco["compras_publicas"] >= minimo_compras]
if so_pessoa:
    ranking = ranking[ranking["tipo_revisor_correspondencia"] == "pessoa"]
ranking = ranking.sort_values("diferenca_pct", ascending=False)

st.subheader(f"Maiores diferenças de preço em {ano_mes}")
st.caption(
    "Diferença = preço registrado no estoque ÷ mediana do preço das compras públicas dos itens "
    "CATMAT equivalentes − 1. É um sinal para investigar, não prova de sobrepreço: confira a "
    "unidade de fornecimento (ex.: galão × frasco) antes de concluir."
)

if ranking.empty:
    st.info("Nenhum material atende aos filtros.")
else:
    top = ranking.head(15).copy()
    top["rotulo"] = top["material"].str.slice(0, 40) + " · " + top["almoxarifado"]
    grafico = (
        alt.Chart(top)
        .mark_bar(color=AZUL)
        .encode(
            x=alt.X("diferenca_pct:Q", title="Diferença (%)"),
            y=alt.Y("rotulo:N", sort="-x", title=None),
            tooltip=["descricao", "almoxarifado", "preco_estoque", "preco_publico_mediano",
                     "diferenca_pct", "compras_publicas", "unidade_fornecimento_predominante"],
        )
        .properties(height=420)
    )
    st.altair_chart(grafico, use_container_width=True)

    st.dataframe(
        ranking[[
            "material", "descricao", "almoxarifado", "preco_estoque", "preco_publico_mediano",
            "diferenca_pct", "diferenca_absoluta", "compras_publicas",
            "unidade_fornecimento_predominante", "tipo_revisor_correspondencia",
            "codigos_equivalentes",
        ]].rename(columns={
            "material": "Material", "descricao": "Descrição", "almoxarifado": "Almoxarifado",
            "preco_estoque": "Preço estoque (R$)", "preco_publico_mediano": "Mediana pública (R$)",
            "diferenca_pct": "Diferença (%)", "diferenca_absoluta": "Diferença (R$)",
            "compras_publicas": "Compras", "unidade_fornecimento_predominante": "Unidade (compras)",
            "tipo_revisor_correspondencia": "Correspondência por", "codigos_equivalentes": "Itens CATMAT",
        }),
        hide_index=True,
        width="stretch",
    )

st.caption(
    "Fonte: camada ouro do SIGMA-UnB (estoque dos almoxarifados da UnB, CATMAT e pesquisa de "
    "preços do Compras.gov.br, janela 07–12/2025). Grão do fato: uma linha por material, por "
    "almoxarifado, por mês."
)
