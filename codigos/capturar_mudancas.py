"""
Caminho 2 da E2: captura de mudanças (CDC por consulta, com marca d'água).

Para cada tabela, busca só as linhas que mudaram desde a última execução:

    WHERE <coluna> > <marca anterior>

onde <coluna> é atualizado_em (tabelas com upsert) ou carregado_em
(insert-only), conforme lake.TABELAS. O carregar.py só altera atualizado_em
quando algum campo muda de verdade (WHERE ... IS DISTINCT FROM EXCLUDED),
então recarregar o mesmo arquivo não gera mudança falsa.

Cada execução grava um arquivo novo em
    bronze/cdc/<tabela>/data_captura=AAAA-MM-DD/<HHMMSS>.parquet
e nunca sobrescreve: a bronze/cdc vira o histórico de versões de cada linha,
com três colunas a mais:
    _operacao       'insert' (carregado_em = atualizado_em) ou 'update'
    _capturado_em   quando esta execução leu a linha
    _marca_anterior a marca d'água usada no filtro

A marca de cada tabela fica em bronze/_controle/marcas_cdc.json e só avança
depois que o Parquet da tabela foi gravado. Se o script cair no meio, a
próxima execução recaptura a tabela; as duplicatas saem na E3.

Transação em andamento: now() no Postgres é a hora do INÍCIO da transação.
Se uma carga ainda não confirmada começou às 10:00 e outra, já confirmada,
gravou linhas às 10:01, avançar a marca para 10:01 perderia as linhas das
10:00 quando a primeira confirmasse. Por isso o limite superior da captura é
o início da transação mais antiga ainda aberta no banco.

Limitações (ver ADR 4): DELETE não é capturado, e duas alterações na mesma
linha entre duas execuções aparecem como uma só (a última).

Uso:
    python capturar_mudancas.py
"""

import time
from datetime import datetime

import pyarrow as pa
from psycopg import IsolationLevel

from lake import (BUCKET, CAMINHO_MARCAS, TABELAS, agora, conectar_postgres,
                  esquema_tabela, exportar_parquet, garantir_bucket, gravar_json,
                  ler_json, sistema_arquivos)

COLUNAS_CDC = [
    pa.field("_operacao", pa.string()),
    pa.field("_capturado_em", pa.timestamp("us", tz="America/Sao_Paulo")),
    pa.field("_marca_anterior", pa.timestamp("us", tz="America/Sao_Paulo")),
]


def inicio_transacao_mais_antiga(cur):
    """Início da transação aberta mais antiga de outra sessão, ou None."""
    cur.execute(
        "SELECT min(xact_start) FROM pg_stat_activity "
        "WHERE datname = current_database() AND pid <> pg_backend_pid() "
        "AND xact_start IS NOT NULL AND backend_type = 'client backend'"
    )
    return cur.fetchone()[0]


def capturar_tabela(conn, s3, tabela, coluna, marca, limite, momento):
    esquema = esquema_tabela(conn, tabela)
    tem_atualizacao = "atualizado_em" in esquema.names
    operacao = ("CASE WHEN carregado_em = atualizado_em THEN 'insert' ELSE 'update' END"
                if tem_atualizacao else "'insert'")

    filtros, parametros = [], []
    if marca is not None:
        filtros.append(f"{coluna} > %s")
        parametros.append(marca)
    if limite is not None:
        filtros.append(f"{coluna} < %s")
        parametros.append(limite)
    onde = f"WHERE {' AND '.join(filtros)}" if filtros else ""

    # nova marca = maior valor da coluna dentro da janela, lida no mesmo
    # snapshot da extração (a transação é REPEATABLE READ)
    with conn.cursor() as cur:
        cur.execute(f"SELECT max({coluna}) FROM {tabela} {onde}", parametros)
        nova_marca = cur.fetchone()[0]

    if nova_marca is None:
        return 0, marca, None

    destino = (f"{BUCKET}/bronze/cdc/{tabela}/data_captura={momento:%Y-%m-%d}/"
               f"{momento:%H%M%S}.parquet")
    consulta = (f"SELECT *, {operacao} AS _operacao, %s::timestamptz AS _capturado_em, "
                f"%s::timestamptz AS _marca_anterior FROM {tabela} {onde} ORDER BY {coluna}")
    linhas = exportar_parquet(
        conn, s3, consulta, [momento, marca, *parametros],
        pa.schema(list(esquema) + COLUNAS_CDC), destino, gravar_vazio=False,
    )
    return linhas, nova_marca, destino


def contar_operacoes(s3, destino):
    import pyarrow.parquet as pq
    tabela = pq.read_table(destino, columns=["_operacao"], filesystem=s3)
    contagem = tabela.column("_operacao").value_counts().to_pylist()
    return {c["values"]: c["counts"] for c in contagem}


def main():
    s3 = sistema_arquivos()
    garantir_bucket(s3)
    marcas = ler_json(s3, CAMINHO_MARCAS, {})
    momento = agora()

    conn = conectar_postgres()
    conn.isolation_level = IsolationLevel.REPEATABLE_READ

    print(f"Captura de mudanças para bronze/cdc/ ({momento:%Y-%m-%d %H:%M:%S})\n")
    print(f"{'tabela':<20} {'coluna':<14} {'linhas':>8} {'insert':>7} {'update':>7} {'tempo':>7}")
    total = 0
    inicio_total = time.perf_counter()

    with conn:
        with conn.cursor() as cur:
            limite = inicio_transacao_mais_antiga(cur)
        if limite is not None:
            print(f"(há transação aberta desde {limite:%H:%M:%S}: captura até esse instante)\n")

        for tabela, (coluna, _chave) in TABELAS.items():
            inicio = time.perf_counter()
            registro = marcas.get(tabela) or {}
            marca = registro.get("marca")
            marca = datetime.fromisoformat(marca) if marca else None

            linhas, nova_marca, destino = capturar_tabela(
                conn, s3, tabela, coluna, marca, limite, momento)

            ops = contar_operacoes(s3, destino) if destino else {}
            print(f"{tabela:<20} {coluna:<14} {linhas:>8} {ops.get('insert', 0):>7} "
                  f"{ops.get('update', 0):>7} {time.perf_counter() - inicio:>6.2f}s")
            total += linhas

            if destino:
                marcas[tabela] = {
                    "coluna": coluna,
                    "marca": nova_marca.isoformat(),
                    "ultimo_arquivo": destino.removeprefix(f"{BUCKET}/"),
                    "atualizado_em": momento.isoformat(),
                }
                gravar_json(s3, CAMINHO_MARCAS, marcas)

    print(f"{'TOTAL':<20} {'':<14} {total:>8} {'':>7} {'':>7} "
          f"{time.perf_counter() - inicio_total:>6.2f}s")
    if total == 0:
        print("\nNenhuma mudança desde a última captura.")


if __name__ == "__main__":
    main()
