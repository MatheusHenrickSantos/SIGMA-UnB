"""Integração: Prata (amostra) -> python -m semantica -> candidatos e revisão.

As tabelas prata.material e prata.catmat_item são montadas a partir da
amostra em testes/dados/amostra com as mesmas colunas que o dbt gera
(models/prata/material_prata.sql e catmat_item_prata.sql). O modelo de
linguagem é trocado pelo codificador de teste.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import psycopg
import psycopg.conninfo
import pytest

from codificador_teste import CodificadorDeTeste
from semantica import __main__ as cli
from semantica import fontes

AMOSTRA = Path(__file__).resolve().parent / "dados" / "amostra"


def montar_prata(conn: psycopg.Connection) -> None:
    materiais = sorted({
        registro["material"].strip()
        for arquivo in sorted((AMOSTRA / "estoque").glob("*.json"))
        for registro in json.loads(arquivo.read_text(encoding="utf-8"))
        if registro["material"].strip()
    })
    itens = json.loads((AMOSTRA / "catmat" / "catalogo_catmat.json").read_text(encoding="utf-8"))
    conn.execute("CREATE SCHEMA prata")
    conn.execute(
        "CREATE TABLE prata.material (identificador_material CHAR(6), nome CHAR(50), "
        "descricao CHAR(100), material_original TEXT)"
    )
    conn.execute(
        "CREATE TABLE prata.catmat_item (codigo_item INTEGER, codigo_pdm INTEGER, "
        "descricao_item TEXT, status_item BOOLEAN)"
    )
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO prata.material VALUES (%s, split_part(%s, ',', 1), %s, %s)",
            [(f"ma{n:04d}", texto, texto, texto) for n, texto in enumerate(materiais, 1)],
        )
        cur.executemany(
            "INSERT INTO prata.catmat_item VALUES (%s, %s, %s, %s)",
            [(i["codigoItem"], i["codigoPdm"], i["descricaoItem"], i["statusItem"]) for i in itens],
        )


@pytest.fixture
def banco_com_prata(banco, monkeypatch):
    with psycopg.connect(banco, autocommit=True) as conn:
        montar_prata(conn)
    partes = psycopg.conninfo.conninfo_to_dict(banco)
    for chave, variavel in (("host", "PGHOST"), ("port", "PGPORT"), ("dbname", "PGDATABASE"),
                            ("user", "PGUSER"), ("password", "PGPASSWORD")):
        if chave in partes:
            monkeypatch.setenv(variavel, str(partes[chave]))
    for variavel in ("SEMANTICA_MODELO", "SEMANTICA_LIMIAR", "SEMANTICA_TOP_K", "SEMANTICA_REVISAO"):
        monkeypatch.delenv(variavel, raising=False)
    return banco


@pytest.fixture
def codificador(monkeypatch):
    falso = CodificadorDeTeste()
    falso.nome = cli.MODELO_PADRAO  # finge ser o modelo padrão para 'corresponder' achá-lo
    monkeypatch.setattr(cli, "_codificador", lambda args: falso)
    return falso


def teste_fontes_leem_a_prata(banco_com_prata):
    with psycopg.connect(banco_com_prata, autocommit=True) as conn:
        estoque = fontes.ler(conn, "estoque")
        ativos = fontes.ler(conn, "catmat")
        todos = fontes.ler(conn, "catmat", incluir_catmat_inativo=True)
    assert len(estoque) == 22 and estoque[0][0] == "ma0001"
    assert len(ativos) == 25 and "990026" not in {codigo for codigo, _ in ativos}
    assert len(todos) == 26


def teste_fonte_inexistente_tem_mensagem_clara(banco):
    with psycopg.connect(banco, autocommit=True) as conn:
        with pytest.raises(fontes.ErroFonte, match="dbt"):
            fontes.ler(conn, "estoque")


def teste_fluxo_completo_pela_linha_de_comando(banco_com_prata, codificador, tmp_path, capsys):
    assert cli.main(["tudo", "--top-k", "3"]) == 0
    enviados_na_primeira = len(codificador.textos_enviados)

    assert cli.main(["tudo", "--top-k", "3"]) == 0
    saida = capsys.readouterr().out

    with psycopg.connect(banco_com_prata, autocommit=True) as conn:
        situacoes = dict(conn.execute(
            "SELECT situacao, count(*) FROM semantica.descricao WHERE origem = 'estoque' GROUP BY 1"
        ).fetchall())
        vetores = dict(conn.execute(
            "SELECT origem, count(*) FROM semantica.embedding GROUP BY 1"
        ).fetchall())
        execucoes = conn.execute(
            "SELECT count(*), min(materiais), min(candidatos) FROM semantica.execucao_correspondencia"
        ).fetchone()
        pilha = conn.execute(
            """
            SELECT codigo_item, situacao_especificacao FROM semantica.v_candidato_catmat
            WHERE id_execucao = 2 AND material = 'PILHA ALCALINA AAA 1,5V' ORDER BY posicao
            """
        ).fetchall()

    # 22 materiais na Prata; '1234' é recusado
    assert situacoes == {"valida": 21, "invalida": 1}
    # 21 válidos, 21 vetores (um por material, mesmo com texto repetido)
    assert vetores == {"estoque": 21, "catmat": 25}
    # a segunda execução não manda nada ao modelo
    assert len(codificador.textos_enviados) == enviados_na_primeira
    # as duas canetas azuis (caixa/espaço diferentes) viram um texto só: 20 + 25
    assert enviados_na_primeira == 20 + 25
    assert execucoes == (2, 21, 63)
    assert dict(pilha)["990010"] == "conflito_tecnico"
    assert "sugestões" in saida


def teste_revisao_e_fila_pela_linha_de_comando(banco_com_prata, codificador, tmp_path):
    assert cli.main(["tudo", "--top-k", "2"]) == 0
    with psycopg.connect(banco_com_prata, autocommit=True) as conn:
        papel = conn.execute(
            "SELECT chave_origem FROM semantica.descricao WHERE origem = 'estoque' "
            "AND texto_original LIKE 'PAPEL A4%'"
        ).fetchone()[0]

    assert cli.main(["revisar", "--material", papel, "--codigo", "990001",
                     "--decisao", "equivalente", "--revisor", "Equipe de teste"]) == 0
    arquivo = tmp_path / "fila.csv"
    assert cli.main(["fila", "--saida", str(arquivo)]) == 0

    with arquivo.open(encoding="utf-8-sig") as entrada:
        linhas = list(csv.DictReader(entrada))
    materiais_na_fila = {linha["identificador_material"] for linha in linhas}
    assert papel not in materiais_na_fila
    assert len(materiais_na_fila) == 20
    assert {"similaridade", "conflitos", "situacao_especificacao"} <= set(linhas[0])


def teste_erros_viram_mensagem_e_codigo_1(banco_com_prata, capsys):
    assert cli.main(["corresponder"]) == 1
    assert "rode a etapa embeddings" in capsys.readouterr().err


def teste_revisar_exige_os_campos(banco_com_prata):
    with pytest.raises(SystemExit):
        cli.main(["revisar", "--material", "ma0001"])
