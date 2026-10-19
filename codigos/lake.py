"""
Camada analítica em formato aberto: tabelas Delta Lake (Parquet + log de
transações) em dados/lake/.

Comandos:
    python lake.py carga [--janela AAAA-MM]  # OLTP -> lake (carga em lote)
    python lake.py cdc                       # dados/cdc/*.jsonl -> lake
    python lake.py compactar                 # junta arquivos pequenos
    python lake.py status                    # versões, linhas e arquivos

Decisões (ver docs/adr/adr-2.md):
  * Parquet com compressão ZSTD: leitura analítica por coluna e por período;
  * estoque_saldo particionada por ano (o filtro típico é por período);
  * escrita sempre por MERGE com chave: reexecutar não duplica nem muda o
    resultado (idempotência);
  * toda linha carrega `ultimo_evento` (LSN do último evento aplicado) e
    `removido` (exclusão lógica). Um evento só vale se for mais novo que o
    estado atual, então evento atrasado ou repetido não desfaz estado mais
    recente nem ressuscita linha apagada.
"""

import json
import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

import psycopg
import pyarrow as pa
from deltalake import DeltaTable, WriterProperties, write_deltalake

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_LAKE = RAIZ_PROJETO / "dados" / "lake"
PASTA_CDC = RAIZ_PROJETO / "dados" / "cdc"

PROPRIEDADES = WriterProperties(compression="ZSTD", compression_level=3)

TS = pa.timestamp("us", tz="UTC")
CONTROLE = [("removido", pa.bool_()), ("ultimo_evento", pa.int64())]

# nome -> colunas, chave, partição, condição para a carga em lote atualizar
# uma linha já existente (None = a carga só insere; mudanças vêm pelo CDC)
TABELAS = {
    "material": dict(
        colunas=[("id_material", pa.int32()), ("descricao", pa.string()),
                 ("termo_busca", pa.string()), ("carregado_em", TS),
                 ("atualizado_em", TS)],
        chave=["id_material"], particao=[],
        atualiza_se="s.atualizado_em > t.atualizado_em",
    ),
    "almoxarifado": dict(
        colunas=[("id_almoxarifado", pa.int32()), ("nome", pa.string()),
                 ("id_unidade", pa.int32()), ("carregado_em", TS),
                 ("atualizado_em", TS)],
        chave=["id_almoxarifado"], particao=[],
        atualiza_se="s.atualizado_em > t.atualizado_em",
    ),
    "estoque_saldo": dict(
        colunas=[("id_material", pa.int32()), ("id_almoxarifado", pa.int32()),
                 ("data_referencia", pa.date32()), ("saldo", pa.decimal128(14, 3)),
                 ("preco_unitario", pa.decimal128(14, 4)),
                 ("valor_total", pa.decimal128(16, 2)), ("id_carga", pa.int64()),
                 ("carregado_em", TS), ("ano_referencia", pa.int32())],
        chave=["id_material", "id_almoxarifado", "data_referencia"],
        particao=["ano_referencia"],
        # dado reenviado por uma carga mais nova (correção) substitui o anterior
        atualiza_se="s.id_carga > t.id_carga",
    ),
    "cotacao_online": dict(
        colunas=[("id_cotacao", pa.int64()), ("id_material", pa.int32()),
                 ("loja", pa.string()), ("titulo", pa.string()),
                 ("preco", pa.decimal128(14, 2)), ("url", pa.string()),
                 ("data_coleta", TS), ("carregado_em", TS)],
        chave=["id_cotacao"], particao=[],
        atualiza_se=None,
    ),
}

# Log append-only de todo evento recebido (uma linha por id_evento).
ESQUEMA_EVENTOS = pa.schema([
    ("id_evento", pa.int64()), ("tabela", pa.string()), ("operacao", pa.string()),
    ("commit_ts", TS), ("data_commit", pa.date32()), ("recebido_em", TS),
    ("atrasado", pa.bool_()), ("antes", pa.string()), ("depois", pa.string()),
])


def esquema(nome):
    return pa.schema(TABELAS[nome]["colunas"] + CONTROLE)


def caminho(nome):
    return str(PASTA_LAKE / nome)


def existe(nome):
    return DeltaTable.is_deltatable(caminho(nome))


# ---------------------------------------------------------------------------
# Escrita idempotente
# ---------------------------------------------------------------------------

def mesclar(nome, dados, esq, chave, particao, atualiza_se):
    """MERGE por chave. Cria a tabela na primeira escrita."""
    if dados.num_rows == 0:
        return 0
    if not existe(nome):
        write_deltalake(caminho(nome), dados, partition_by=particao or None,
                        writer_properties=PROPRIEDADES)
        return dados.num_rows

    junta = " AND ".join(f"t.{c} = s.{c}" for c in chave)
    mescla = DeltaTable(caminho(nome)).merge(
        source=dados, predicate=junta, source_alias="s", target_alias="t",
        writer_properties=PROPRIEDADES,
    )
    if atualiza_se:
        mescla = mescla.when_matched_update_all(predicate=atualiza_se)
    mescla.when_not_matched_insert_all().execute()
    return dados.num_rows


def tabela_arrow(linhas, esq):
    return pa.Table.from_pylist(linhas, schema=esq)


# ---------------------------------------------------------------------------
# Carga em lote: OLTP -> lake
# ---------------------------------------------------------------------------

def carga(janela=None):
    with psycopg.connect(autocommit=True) as conn:
        for nome, t in TABELAS.items():
            colunas = [c for c, _ in t["colunas"] if c != "ano_referencia"]
            sql = f"SELECT {', '.join(colunas)} FROM {nome}"
            params = ()
            if janela:
                if nome != "estoque_saldo":
                    continue  # a janela só se aplica ao fato mensal
                sql += " WHERE data_referencia = %s"
                params = (date.fromisoformat(janela + "-01"),)
            linhas = []
            for registro in conn.execute(sql, params):
                linha = dict(zip(colunas, registro))
                if nome == "estoque_saldo":
                    linha["ano_referencia"] = linha["data_referencia"].year
                linha.update(removido=False, ultimo_evento=0)
                linhas.append(linha)
            n = mesclar(nome, tabela_arrow(linhas, esquema(nome)), esquema(nome),
                        t["chave"], t["particao"], t["atualiza_se"])
            print(f"  {nome:<16} {n:>7} linha(s) lidas do OLTP")


# ---------------------------------------------------------------------------
# CDC: eventos -> lake
# ---------------------------------------------------------------------------

def converter(texto, tipo):
    if texto is None:
        return None
    if pa.types.is_integer(tipo):
        return int(texto)
    if pa.types.is_decimal(tipo):
        return Decimal(texto)
    if pa.types.is_date(tipo):
        return date.fromisoformat(texto)
    if pa.types.is_timestamp(tipo):
        return datetime.fromisoformat(texto).astimezone(timezone.utc)
    if pa.types.is_boolean(tipo):
        return texto == "t"
    return texto


def ler_eventos():
    eventos = []
    for arquivo in sorted(PASTA_CDC.glob("eventos-*.jsonl")):
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            e = json.loads(linha)
            e["id_evento"] = int(e["id_evento"])
            e["commit_ts"] = datetime.fromisoformat(e["commit_ts"])
            e["tabela"] = e["tabela"].split(".")[-1]
            eventos.append(e)
    return eventos


def linha_do_evento(evento):
    """Estado resultante: depois (insert/update) ou antes marcado como removido."""
    esq = esquema(evento["tabela"])
    removido = evento["operacao"] == "delete"
    bruto = evento["antes"] if removido else evento["depois"]
    linha = {c.name: converter(bruto.get(c.name), c.type)
             for c in esq if c.name not in ("removido", "ultimo_evento", "ano_referencia")}
    if "ano_referencia" in esq.names:
        linha["ano_referencia"] = linha["data_referencia"].year
    linha.update(removido=removido, ultimo_evento=evento["id_evento"])
    return linha


def aplicar_cdc():
    eventos = [e for e in ler_eventos() if e["tabela"] in TABELAS]
    if not eventos:
        print("  nenhum evento em dados/cdc/")
        return

    conhecidos, maior_commit = set(), None
    if existe("cdc_eventos"):
        log = DeltaTable(caminho("cdc_eventos")).to_pyarrow_table(
            columns=["id_evento", "commit_ts"])
        conhecidos = set(log.column("id_evento").to_pylist())
        if log.num_rows:
            maior_commit = max(log.column("commit_ts").to_pylist())
    novos = [e for e in eventos if e["id_evento"] not in conhecidos]
    print(f"  {len(eventos)} evento(s) nos arquivos, {len(novos)} ainda não aplicado(s)")
    if not novos:
        return

    # 1) estado: por tabela, só o último evento de cada chave; MERGE só aplica
    #    se for mais novo que o estado atual (ultimo_evento)
    for nome, t in TABELAS.items():
        ultimo = {}
        for e in sorted((e for e in novos if e["tabela"] == nome),
                        key=lambda e: e["id_evento"]):
            linha = linha_do_evento(e)
            ultimo[tuple(linha[c] for c in t["chave"])] = linha
        if not ultimo:
            continue
        mesclar(nome, tabela_arrow(list(ultimo.values()), esquema(nome)),
                esquema(nome), t["chave"], t["particao"],
                "s.ultimo_evento > t.ultimo_evento")
        print(f"  {nome:<16} {len(ultimo):>7} chave(s) atualizada(s)")

    # 2) log: só depois do estado. Se o processo cair entre 1 e 2, o reprocesso
    #    reaplica o passo 1, que é idempotente.
    agora = datetime.now(timezone.utc)
    linhas = []
    for e in novos:
        # atrasado = chegou depois de um evento de commit mais recente
        atrasado = maior_commit is not None and e["commit_ts"] < maior_commit
        linhas.append(dict(
            id_evento=e["id_evento"], tabela=e["tabela"], operacao=e["operacao"],
            commit_ts=e["commit_ts"], data_commit=e["commit_ts"].date(),
            recebido_em=agora, atrasado=atrasado,
            antes=json.dumps(e["antes"]) if e["antes"] else None,
            depois=json.dumps(e["depois"]) if e["depois"] else None))
    mesclar("cdc_eventos", tabela_arrow(linhas, ESQUEMA_EVENTOS), ESQUEMA_EVENTOS,
            ["id_evento"], ["data_commit"], None)
    print(f"  cdc_eventos      {len(linhas):>7} evento(s) registrado(s); "
          f"{sum(l['atrasado'] for l in linhas)} atrasado(s)")


# ---------------------------------------------------------------------------
# Manutenção e inspeção
# ---------------------------------------------------------------------------

def compactar():
    for nome in [*TABELAS, "cdc_eventos"]:
        if existe(nome):
            r = DeltaTable(caminho(nome)).optimize.compact(writer_properties=PROPRIEDADES)
            print(f"  {nome:<16} {r['numFilesRemoved']} arquivo(s) -> {r['numFilesAdded']}")


def status():
    for nome in [*TABELAS, "cdc_eventos"]:
        if not existe(nome):
            continue
        dt = DeltaTable(caminho(nome))
        linhas = dt.to_pyarrow_table(columns=[dt.schema().fields[0].name]).num_rows
        print(f"  {nome:<16} versão {dt.version():>3}  {linhas:>7} linhas  "
              f"{len(dt.file_uris()):>3} arquivo(s)  partição={dt.metadata().partition_columns}")


def main():
    comando = sys.argv[1] if len(sys.argv) > 1 else "status"
    if comando == "carga":
        janela = sys.argv[sys.argv.index("--janela") + 1] if "--janela" in sys.argv else None
        carga(janela)
    elif comando == "cdc":
        aplicar_cdc()
    elif comando == "compactar":
        compactar()
    elif comando == "status":
        status()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
    # O runtime nativo do deltalake às vezes aborta ("terminate called") ao
    # encerrar o interpretador, depois de todo o trabalho feito. Saída direta
    # evita que isso vire código de erro no compose.
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(0)
