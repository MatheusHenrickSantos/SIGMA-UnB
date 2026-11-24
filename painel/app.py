"""Painel SIGMA-UnB: preço do estoque × preço de compras públicas.

Lê só a camada ouro (fato_comparacao_preco, dimensões, monitor_atualizacao,
qualidade_dados e resumo_correspondencia). Responde à pergunta de gestão:

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

# Paleta institucional da UnB (azul, verde e vermelho do logotipo), com neutros
# e um âmbar só para o estado "atenção". Confirme os tons no manual de
# identidade visual da UnB antes de uso oficial.
AZUL = "#003366"
AZUL_CLARO = "#6B8FB5"
VERDE = "#00843D"
VERMELHO = "#C8102E"
AMBAR = "#B7791F"  # mais escuro que um amarelo puro, para ter contraste sobre branco
TEXTO = "#1F2933"
CINZA = "#5B6770"
LINHA = "#E3E7EB"
SUPERFICIE = "#F3F5F7"
SITUACAO = {"ok": VERDE, "atencao": AMBAR, "critico": VERMELHO, "sem_dado": CINZA}
ROTULO_SITUACAO = {"ok": "OK", "atencao": "Atenção", "critico": "Crítico", "sem_dado": "Sem dado"}
REVISOR = alt.Scale(domain=["pessoa", "agente", "sem_decisao"], range=[VERDE, AZUL, "#B8C0C8"])

@alt.theme.register("unb", enable=True)
def _tema_unb() -> alt.theme.ThemeConfig:
    return {"config": {
        "background": "transparent",
        "view": {"stroke": "transparent"},
        "font": "sans-serif",
        "axis": {"gridColor": LINHA, "domainColor": LINHA, "tickColor": LINHA, "labelColor": CINZA,
                 "titleColor": CINZA, "labelFontSize": 12, "titleFontSize": 12, "titleFontWeight": "normal"},
        "legend": {"labelColor": TEXTO, "titleColor": CINZA, "titleFontWeight": "normal"},
        "range": {"category": [AZUL, VERDE, AZUL_CLARO, VERMELHO]},
    }}

st.set_page_config(page_title="SIGMA-UnB · Preços", page_icon="📊", layout="wide")

st.markdown(
    f"""
    <style>
      .block-container {{ padding-top: 2rem; max-width: 1200px; }}
      h1, h2, h3 {{ color: {AZUL}; font-weight: 600; letter-spacing: -.01em; }}
      h3 {{ font-size: 1.05rem; }}
      div[data-testid="stMetric"] {{ background: white; border: 1px solid {LINHA};
                border-radius: 8px; padding: .8rem 1rem; }}
      div[data-testid="stMetricLabel"] p {{ color: {CINZA}; font-size: .8rem; }}
      div[data-testid="stMetricValue"] {{ color: {AZUL}; }}
      .selo {{ display:inline-block; padding:.05rem .55rem; border-radius:999px; font-size:.72rem;
               font-weight:600; border:1px solid currentColor; background: white; }}
      .linha-q {{ padding: .6rem 0; border-bottom: 1px solid {LINHA}; }}
      .linha-q small {{ color: {CINZA}; }}
      .sub {{ color: {CINZA}; margin-top: -.6rem; }}
      button[data-baseweb="tab"] {{ color: {CINZA}; }}
      button[data-baseweb="tab"][aria-selected="true"] {{ color: {AZUL}; }}
      div[data-baseweb="tab-highlight"] {{ background-color: {VERDE}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


def grafico(chart: alt.Chart) -> None:
    st.altair_chart(chart, theme=None, use_container_width=True)


def selo(situacao: str, texto: str | None = None) -> str:
    return f'<span class="selo" style="color:{SITUACAO[situacao]}">{texto or ROTULO_SITUACAO[situacao]}</span>'


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


def existe(tabela: str) -> bool:
    return bool(consultar("SELECT to_regclass(%s) IS NOT NULL AS e", (tabela,)).iloc[0, 0])


def inteiro(n: float) -> str:
    return f"{int(n):,}".replace(",", ".")


def reais(n: float) -> str:
    return "R$ " + f"{n:,.0f}".replace(",", ".")


def numerico(df: pd.DataFrame, colunas: list[str]) -> pd.DataFrame:
    for coluna in colunas:
        df[coluna] = pd.to_numeric(df[coluna])
    return df


st.title("SIGMA-UnB")
st.markdown(
    '<p class="sub">Preço do estoque × compras públicas: quais materiais têm item CATMAT e compras '
    "comparáveis, e onde estão as maiores diferenças.</p>",
    unsafe_allow_html=True,
)

if not existe("ouro.fato_comparacao_preco"):
    st.error("A camada ouro ainda não foi gerada. Rode o pipeline (docker compose up).")
    st.stop()

tem_qualidade = existe("ouro.qualidade_dados")
tem_resumo = existe("ouro.resumo_correspondencia")

# --- Filtros ---------------------------------------------------------------
meses = consultar(
    "SELECT mes_referencia, ano_mes FROM ouro.dim_tempo WHERE publicado ORDER BY mes_referencia DESC"
)
almoxarifados = consultar("SELECT identificador_almoxarifado, nome FROM ouro.dim_almoxarifado ORDER BY nome")

with st.sidebar:
    st.header("Filtros")
    ano_mes = st.selectbox("Mês de referência", meses["ano_mes"].tolist(), index=0)
    st.markdown("**Almoxarifado**")
    escolhidos = [
        nome for nome in almoxarifados["nome"].tolist()
        if st.checkbox(nome, value=True, key=f"almox_{nome}")
    ]
    if not escolhidos:
        st.caption("Marque ao menos um almoxarifado.")
    minimo_compras = st.slider("Mínimo de compras públicas na referência", 1, 50, 5)
    so_pessoa = st.checkbox("Só correspondências conferidas por pessoa", value=False)
    st.caption(
        "A correspondência material × CATMAT foi sugerida por agentes de IA e ainda está em "
        "revisão pela Squad; marque a opção acima para ver só as conferidas."
    )

mes = meses.loc[meses["ano_mes"] == ano_mes, "mes_referencia"].iloc[0]

# --- Freshness / SLA -------------------------------------------------------
monitor = consultar(
    "SELECT tabela, ultimo_dado, atraso_dias, sla_dias, situacao_sla FROM ouro.monitor_atualizacao ORDER BY tabela"
)
fora = monitor[(monitor["situacao_sla"] == "fora do SLA") & (monitor["tabela"] == "ouro.fato_comparacao_preco")]
if not fora.empty:
    linha = fora.iloc[0]
    st.warning(
        f"Dado desatualizado: o estoque mais recente é de {linha['ultimo_dado']:%m/%Y} "
        f"({linha['atraso_dias']} dias de atraso; SLA de {linha['sla_dias']} dias). "
        "O portal dados.unb.br não publicou meses mais novos."
    )

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
base = numerico(base[base["almoxarifado"].isin(escolhidos)].copy(), [
    "quantidade", "preco_estoque", "valor_estoque", "preco_publico_mediano",
    "diferenca_absoluta", "diferenca_pct",
])

com_item = base[base["codigos_equivalentes"].fillna("") != ""]
com_preco = base[base["tem_preco_publico"]]
valor_total = base["valor_estoque"].sum()
ranking = com_preco[com_preco["compras_publicas"] >= minimo_compras]
if so_pessoa:
    ranking = ranking[ranking["tipo_revisor_correspondencia"] == "pessoa"]
ranking = ranking.sort_values("diferenca_pct", ascending=False)

aba_geral, aba_precos, aba_busca, aba_almox, aba_serie, aba_qualidade, aba_revisao = st.tabs(
    ["Visão geral", "Maiores diferenças", "Buscar produto", "Almoxarifados", "Série mensal",
     "Qualidade dos dados", "Revisão CATMAT"]
)

# --- Visão geral -----------------------------------------------------------
with aba_geral:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Materiais em estoque", inteiro(len(base)))
    c2.metric("Com item CATMAT", inteiro(len(com_item)),
              f"{len(com_item) / max(len(base), 1):.0%} dos materiais", delta_color="off")
    c3.metric("Com preço público", inteiro(len(com_preco)),
              f"{len(com_preco) / max(len(base), 1):.0%} dos materiais", delta_color="off")
    c4.metric("Valor comparável",
              f"{com_preco['valor_estoque'].sum() / valor_total:.1%}" if valor_total else "-",
              f"de {reais(valor_total)} em estoque", delta_color="off")

    if tem_qualidade:
        q = consultar("SELECT situacao, count(*) AS n FROM ouro.qualidade_dados GROUP BY 1")
        contagem = dict(zip(q["situacao"], q["n"]))
        st.markdown("**Confiabilidade:** " + " ".join(
            selo(s, f"{ROTULO_SITUACAO[s]}: {contagem.get(s, 0)}")
            for s in ("ok", "atencao", "critico", "sem_dado")
        ) + " — detalhes na aba **Qualidade dos dados**.", unsafe_allow_html=True)

    esq, dir_ = st.columns(2)
    with esq:
        st.subheader("Cobertura da comparação")
        funil = pd.DataFrame({
            "etapa": ["Em estoque", "Com item CATMAT", "Com preço público", "Com 5+ compras"],
            "materiais": [len(base), len(com_item), len(com_preco),
                          int((com_preco["compras_publicas"] >= 5).sum())],
        })
        grafico(
            alt.Chart(funil).mark_bar(color=AZUL).encode(
                y=alt.Y("etapa:N", sort=None, title=None), x=alt.X("materiais:Q", title="Materiais"),
                tooltip=["etapa", "materiais"],
            ).properties(height=220)
        )
    with dir_:
        st.subheader("Quem decidiu a correspondência")
        quem = base.groupby("tipo_revisor_correspondencia").agg(
            materiais=("identificador_material", "size")).reset_index()
        grafico(
            alt.Chart(quem).mark_arc(innerRadius=55).encode(
                theta="materiais:Q",
                color=alt.Color("tipo_revisor_correspondencia:N", title="Revisor", scale=REVISOR),
                tooltip=["tipo_revisor_correspondencia", "materiais"],
            ).properties(height=220)
        )

# --- Maiores diferenças ----------------------------------------------------
with aba_precos:
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
        grafico(
            alt.Chart(top).mark_bar(color=AZUL).encode(
                x=alt.X("diferenca_pct:Q", title="Diferença (%)"),
                y=alt.Y("rotulo:N", sort="-x", title=None),
                color=alt.Color("tipo_revisor_correspondencia:N", title="Correspondência por",
                                scale=REVISOR),
                tooltip=["descricao", "almoxarifado", "preco_estoque", "preco_publico_mediano",
                         "diferenca_pct", "compras_publicas", "unidade_fornecimento_predominante"],
            ).properties(height=420)
        )
        st.dataframe(
            ranking[[
                "material", "descricao", "almoxarifado", "preco_estoque", "preco_publico_mediano",
                "diferenca_pct", "diferenca_absoluta", "compras_publicas",
                "unidade_fornecimento_predominante", "tipo_revisor_correspondencia", "codigos_equivalentes",
            ]].rename(columns={
                "material": "Material", "descricao": "Descrição", "almoxarifado": "Almoxarifado",
                "preco_estoque": "Preço estoque (R$)", "preco_publico_mediano": "Mediana pública (R$)",
                "diferenca_pct": "Diferença (%)", "diferenca_absoluta": "Diferença (R$)",
                "compras_publicas": "Compras", "unidade_fornecimento_predominante": "Unidade (compras)",
                "tipo_revisor_correspondencia": "Correspondência por", "codigos_equivalentes": "Itens CATMAT",
            }),
            hide_index=True, width="stretch",
        )

# --- Buscar produto --------------------------------------------------------
with aba_busca:
    todos = consultar(
        "SELECT identificador_material, descricao, codigos_equivalentes, tipo_revisor, confianca "
        "FROM ouro.dim_material WHERE atual ORDER BY descricao"
    )
    st.caption(f"{inteiro(len(todos))} materiais cadastrados. Busque por palavras da descrição "
               "(todas precisam aparecer) ou pelo código do material, como ma0123.")
    termo = st.text_input("Produto", placeholder="ex.: papel a4, luva procedimento, ma0123",
                          label_visibility="collapsed")
    achados = todos
    for palavra in termo.split():
        achados = achados[achados["descricao"].str.contains(palavra, case=False, regex=False)
                          | achados["identificador_material"].str.contains(palavra, case=False, regex=False)]
    if not termo.strip():
        st.info("Digite parte do nome do produto para começar.")
    elif achados.empty:
        st.warning("Nenhum material encontrado. Tente menos palavras ou outra grafia (com acento, em maiúsculas).")
    else:
        st.write(f"{inteiro(len(achados))} material(is) encontrado(s)"
                 + (" — mostrando os 200 primeiros." if len(achados) > 200 else "."))
        opcoes = achados.head(200)
        escolha = st.selectbox(
            "Resultado", opcoes["identificador_material"].tolist(), label_visibility="collapsed",
            format_func=lambda i: f"{i} · {opcoes.loc[opcoes['identificador_material'] == i, 'descricao'].iloc[0]}",
        )
        item = opcoes[opcoes["identificador_material"] == escolha].iloc[0]
        revisor = {"pessoa": "conferida por pessoa", "agente": "sugerida por agente de IA",
                   "sem_decisao": "sem decisão"}[item["tipo_revisor"]]
        st.subheader(item["descricao"])
        st.markdown(
            f"Itens CATMAT: **{item['codigos_equivalentes'] or 'nenhum'}** · correspondência {revisor}"
            + (f" · confiança {item['confianca']}" if item["confianca"] else "")
        )
        hist = numerico(consultar(
            """
            SELECT f.mes_referencia, a.nome AS almoxarifado, f.quantidade, f.preco_estoque,
                   f.valor_estoque, f.preco_publico_mediano, f.compras_publicas, f.diferenca_pct
            FROM ouro.fato_comparacao_preco f
            JOIN ouro.dim_almoxarifado a USING (identificador_almoxarifado)
            WHERE f.identificador_material = %s ORDER BY f.mes_referencia
            """,
            (escolha,),
        ), ["quantidade", "preco_estoque", "valor_estoque", "preco_publico_mediano", "diferenca_pct"])
        if hist.empty:
            st.info("Este material está no cadastro, mas não tem registro de estoque com preço positivo.")
        else:
            ultimo = hist[hist["mes_referencia"] == hist["mes_referencia"].max()]
            c1, c2, c3 = st.columns(3)
            c1.metric("Preço no estoque (último mês)", f"R$ {ultimo['preco_estoque'].mean():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            pub = ultimo["preco_publico_mediano"].dropna()
            c2.metric("Mediana pública", "sem compras" if pub.empty else
                      f"R$ {pub.iloc[0]:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            dif = ultimo["diferenca_pct"].dropna()
            c3.metric("Diferença", "-" if dif.empty else f"{dif.iloc[0]:+.1f}%")
            linhas = alt.Chart(hist).mark_line(point=True).encode(
                x=alt.X("mes_referencia:T", title=None), y=alt.Y("preco_estoque:Q", title="Preço unitário (R$)"),
                color=alt.Color("almoxarifado:N", title="Almoxarifado"),
                tooltip=["mes_referencia", "almoxarifado", "preco_estoque", "quantidade", "preco_publico_mediano"],
            )
            publico = alt.Chart(hist.dropna(subset=["preco_publico_mediano"])).mark_rule(
                color=VERMELHO, strokeDash=[4, 4]).encode(y="mean(preco_publico_mediano):Q")
            grafico((linhas + publico).properties(height=280))
            st.caption("Linha tracejada vermelha: mediana do preço das compras públicas (quando há).")
            st.dataframe(
                hist.sort_values("mes_referencia", ascending=False).rename(columns={
                    "mes_referencia": "Mês", "almoxarifado": "Almoxarifado", "quantidade": "Saldo",
                    "preco_estoque": "Preço estoque (R$)", "valor_estoque": "Valor (R$)",
                    "preco_publico_mediano": "Mediana pública (R$)", "compras_publicas": "Compras",
                    "diferenca_pct": "Diferença (%)"}),
                hide_index=True, width="stretch",
            )

# --- Almoxarifados ---------------------------------------------------------
with aba_almox:
    por_almox = base.groupby("almoxarifado").agg(
        materiais=("identificador_material", "size"),
        valor_estoque=("valor_estoque", "sum"),
        com_preco=("tem_preco_publico", "sum"),
    ).reset_index()
    mediana = com_preco.groupby("almoxarifado")["diferenca_pct"].median().rename("mediana_diferenca_pct")
    por_almox = por_almox.merge(mediana, on="almoxarifado", how="left")
    por_almox["cobertura_pct"] = 100 * por_almox["com_preco"] / por_almox["materiais"].clip(lower=1)
    esq, dir_ = st.columns(2)
    with esq:
        st.subheader("Valor em estoque")
        grafico(
            alt.Chart(por_almox).mark_bar(color=AZUL).encode(
                x=alt.X("almoxarifado:N", title=None), y=alt.Y("valor_estoque:Q", title="R$"),
                tooltip=["almoxarifado", "valor_estoque", "materiais"],
            ).properties(height=280)
        )
    with dir_:
        st.subheader("Cobertura de preço público (%)")
        grafico(
            alt.Chart(por_almox).mark_bar(color=VERDE).encode(
                x=alt.X("almoxarifado:N", title=None),
                y=alt.Y("cobertura_pct:Q", title="% dos materiais", scale=alt.Scale(domain=[0, 100])),
                tooltip=["almoxarifado", "cobertura_pct", "com_preco"],
            ).properties(height=280)
        )
    st.dataframe(
        por_almox.rename(columns={
            "almoxarifado": "Almoxarifado", "materiais": "Materiais", "valor_estoque": "Valor (R$)",
            "com_preco": "Com preço público", "mediana_diferenca_pct": "Mediana da diferença (%)",
            "cobertura_pct": "Cobertura (%)",
        }),
        hide_index=True, width="stretch",
    )

# --- Série mensal ----------------------------------------------------------
with aba_serie:
    serie = consultar(
        """
        SELECT f.mes_referencia, a.nome AS almoxarifado,
               SUM(f.valor_estoque) AS valor_estoque,
               COUNT(*) AS materiais,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.diferenca_pct)
                   FILTER (WHERE f.tem_preco_publico) AS mediana_diferenca_pct
        FROM ouro.fato_comparacao_preco f
        JOIN ouro.dim_almoxarifado a USING (identificador_almoxarifado)
        GROUP BY 1, 2 ORDER BY 1
        """
    )
    serie = numerico(serie[serie["almoxarifado"].isin(escolhidos)].copy(),
                     ["valor_estoque", "mediana_diferenca_pct"])
    st.caption("Só os meses que o portal publicou; os meses sem arquivo aparecem como lacuna, sem interpolação.")
    cores = alt.Scale(range=[AZUL, VERDE, AZUL_CLARO, VERMELHO])
    st.subheader("Valor em estoque por mês")
    grafico(
        alt.Chart(serie).mark_line(point=True).encode(
            x=alt.X("mes_referencia:T", title=None), y=alt.Y("valor_estoque:Q", title="R$"),
            color=alt.Color("almoxarifado:N", title="Almoxarifado", scale=cores),
            tooltip=["mes_referencia", "almoxarifado", "valor_estoque", "materiais"],
        ).properties(height=300)
        )
    st.subheader("Mediana da diferença de preço (%)")
    st.caption("Só meses dentro da janela das compras públicas; fora dela não há preço de referência.")
    grafico(
        alt.Chart(serie.dropna(subset=["mediana_diferenca_pct"])).mark_line(point=True).encode(
            x=alt.X("mes_referencia:T", title=None), y=alt.Y("mediana_diferenca_pct:Q", title="%"),
            color=alt.Color("almoxarifado:N", title="Almoxarifado", scale=cores),
            tooltip=["mes_referencia", "almoxarifado", "mediana_diferenca_pct"],
        ).properties(height=260)
        )

# --- Qualidade -------------------------------------------------------------
with aba_qualidade:
    if not tem_qualidade:
        st.info("ouro.qualidade_dados ainda não existe: rode o transformar_ouro.")
    else:
        q = consultar(
            "SELECT verificacao, categoria, descricao, valor, limite_atencao, limite_critico, sentido, "
            "unidade, situacao FROM ouro.qualidade_dados ORDER BY categoria, verificacao"
        )
        q = numerico(q, ["valor", "limite_atencao", "limite_critico"])
        st.caption(
            "Cada verificação compara um valor medido com limites de projeto (atenção e crítico). "
            "Os testes do dbt derrubam o build; estas medidas dizem o quanto confiar na comparação."
        )
        colunas = st.columns(4)
        for coluna, situacao in zip(colunas, ("ok", "atencao", "critico", "sem_dado")):
            coluna.metric(ROTULO_SITUACAO[situacao], int((q["situacao"] == situacao).sum()))
        for categoria, grupo in q.groupby("categoria"):
            st.subheader(categoria)
            for _, v in grupo.iterrows():
                valor = "sem dado" if pd.isna(v["valor"]) else f"{v['valor']:g} {v['unidade']}"
                regra = "≤" if v["sentido"] == "max" else "≥"
                st.markdown(
                    f'<div class="linha-q">{selo(v["situacao"])} '
                    f'<b>{v["verificacao"].replace("_", " ")}</b> · {valor} '
                    f'<small>(ok {regra} {v["limite_atencao"]:g}; crítico além de {v["limite_critico"]:g})</small>'
                    f'<br><small>{v["descricao"]}</small></div>',
                    unsafe_allow_html=True,
                )

# --- Revisão da correspondência -------------------------------------------
with aba_revisao:
    if not tem_resumo:
        st.info("ouro.resumo_correspondencia ainda não existe: rode o transformar_ouro.")
    else:
        rev = numerico(consultar(
            "SELECT identificador_material, material, tipo_revisor, confianca, sem_correspondente, "
            "quantidade_itens_catmat, codigos_equivalentes, justificativa, pontuacao_melhor_candidato, "
            "situacao_melhor_candidato, valor_estoque, pendente_conferencia, prioridade_revisao "
            "FROM ouro.resumo_correspondencia"
        ), ["valor_estoque", "prioridade_revisao", "pontuacao_melhor_candidato"])
        total = len(rev)
        por_pessoa = int((rev["tipo_revisor"] == "pessoa").sum())
        c1, c2, c3 = st.columns(3)
        c1.metric("Conferidos por pessoa", f"{por_pessoa / max(total, 1):.1%}", f"{por_pessoa} de {inteiro(total)}",
                  delta_color="off")
        c2.metric("Confiança baixa (agente)", inteiro(((rev["confianca"] == "baixa")
                                                       & (rev["tipo_revisor"] == "agente")).sum()))
        c3.metric("Sem correspondente", inteiro(rev["sem_correspondente"].fillna(False).sum()))
        cruz = rev.groupby(["tipo_revisor", rev["confianca"].fillna("sem decisão")]).size().reset_index(name="materiais")
        cruz.columns = ["tipo_revisor", "confianca", "materiais"]
        grafico(
            alt.Chart(cruz).mark_bar().encode(
                x=alt.X("confianca:N", title="Confiança", sort=["alta", "media", "baixa", "sem decisão"]),
                y=alt.Y("materiais:Q", title="Materiais"),
                color=alt.Color("tipo_revisor:N", title="Revisor", scale=REVISOR),
                tooltip=["tipo_revisor", "confianca", "materiais"],
            ).properties(height=240)
        )
        st.subheader("Fila de conferência (maior valor × menor confiança primeiro)")
        fila = rev[rev["pendente_conferencia"]].sort_values("prioridade_revisao", ascending=False).head(100)
        st.dataframe(
            fila[["identificador_material", "material", "confianca", "valor_estoque", "codigos_equivalentes",
                  "situacao_melhor_candidato", "justificativa"]].rename(columns={
                "identificador_material": "ID", "material": "Material", "confianca": "Confiança",
                "valor_estoque": "Valor em estoque (R$)", "codigos_equivalentes": "Itens CATMAT",
                "situacao_melhor_candidato": "Checagem do 1º candidato", "justificativa": "Justificativa do agente",
            }),
            hide_index=True, width="stretch",
        )

st.caption(
    "Fonte: camada ouro do SIGMA-UnB (estoque dos almoxarifados da UnB, CATMAT e pesquisa de preços do "
    "Compras.gov.br, janela 07–12/2025). Grão do fato: uma linha por material, por almoxarifado, por mês."
)
