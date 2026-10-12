"""
Medições dos ADRs da E2, com os dados do próprio projeto.

  ADR 2 (ELT)            — o que a bronze/portal guarda e quanto tempo leva
                           para ler tudo de volta (reprocessar sem o portal).
  ADR 3 (armazenamento)  — tamanho do dado bruto do portal x Parquet do lote,
                           e tempo da consulta "gasto por unidade no último
                           mês" no Postgres x DuckDB lendo o Parquet.
  ADR 4 (CDC)            — tempo e linhas de uma extração completa x uma
                           captura incremental a partir da marca atual.

Rode depois de o compose ter subido tudo (o lote e o CDC já precisam existir):
    docker compose run --rm --no-deps extract python medir_e2.py

A saída é Markdown, pronta para colar na seção Medição de cada ADR.
Cada tempo é a mediana de REPETICOES execuções.
"""

import statistics
import time
from datetime import datetime

import duckdb
import pyarrow.dataset as ds
from pyarrow import fs

from lake import (BUCKET, CAMINHO_MARCAS, PASTA_BRUTO, TABELAS, conectar_postgres,
                  esquema_tabela, exportar_parquet, ler_json, sistema_arquivos, tamanho_mb)

REPETICOES = 5

# dataset do portal -> tabela do Postgres que ele alimenta
DATASET_TABELA = {
    "unidades": "unidade",
    "estoque": "estoque_saldo",
    "gastos": "gasto",
    "empenhos": "empenho",
    "requisicoes": "requisicao_servico",
}

GASTO_POR_UNIDADE = """
    SELECT u.nome, sum(g.valor) AS total
      FROM {gasto} g JOIN {unidade} u ON u.id_unidade = g.id_unidade
     WHERE g.data_referencia = (SELECT max(data_referencia) FROM {gasto})
     GROUP BY u.nome
     ORDER BY total DESC
"""


def mediana_segundos(funcao):
    tempos = []
    for _ in range(REPETICOES):
        inicio = time.perf_counter()
        funcao()
        tempos.append(time.perf_counter() - inicio)
    return statistics.median(tempos)


def arquivos_em(s3, pasta):
    if s3.get_file_info(pasta).type == fs.FileType.NotFound:
        return []
    return [i for i in s3.get_file_info(fs.FileSelector(pasta, recursive=True))
            if i.type == fs.FileType.File]


def ultima_foto(s3, tabela):
    pastas = sorted(i.path for i in s3.get_file_info(
        fs.FileSelector(f"{BUCKET}/bronze/lote/{tabela}")) if "data_extracao=" in i.path)
    return f"{pastas[-1]}/{tabela}.parquet"


def medir_adr2(s3):
    print("## ADR 2: bronze/portal\n")
    arquivos = [a for a in arquivos_em(s3, f"{BUCKET}/bronze/portal")
                if "/_manifestos/" not in a.path]
    total = sum(a.size for a in arquivos)

    def ler_tudo():
        for a in arquivos:
            with s3.open_input_stream(a.path) as f:
                while f.read(8 * 1_048_576):
                    pass

    segundos = mediana_segundos(ler_tudo) if arquivos else 0
    print("| Arquivos na bronze/portal | Volume | Tempo para ler tudo de volta |")
    print("|---|---|---|")
    print(f"| {len(arquivos)} | {tamanho_mb(total)} | {segundos:.1f} s |\n")


def medir_adr3(s3, conn):
    print("## ADR 3: armazenamento\n")
    print("| Dataset | Bruto do portal (JSON/CSV) | Parquet zstd (lote) | Redução |")
    print("|---|---|---|---|")
    for dataset, tabela in DATASET_TABELA.items():
        pasta = PASTA_BRUTO / dataset
        bruto = sum(p.stat().st_size for p in pasta.glob("*") if p.is_file()) if pasta.exists() else 0
        parquet = s3.get_file_info(ultima_foto(s3, tabela)).size
        reducao = f"{1 - parquet / bruto:.0%}" if bruto else "-"
        print(f"| {dataset} → {tabela} | {tamanho_mb(bruto)} | {tamanho_mb(parquet)} | {reducao} |")

    consulta_pg = GASTO_POR_UNIDADE.format(gasto="gasto", unidade="unidade")
    with conn.cursor() as cur:
        t_pg = mediana_segundos(lambda: cur.execute(consulta_pg).fetchall())

    duck = duckdb.connect()
    gasto = ds.dataset(ultima_foto(s3, "gasto"), filesystem=s3, format="parquet")
    unidade = ds.dataset(ultima_foto(s3, "unidade"), filesystem=s3, format="parquet")
    duck.register("gasto_parquet", gasto)
    duck.register("unidade_parquet", unidade)
    consulta_duck = GASTO_POR_UNIDADE.format(gasto="gasto_parquet", unidade="unidade_parquet")
    t_duck = mediana_segundos(lambda: duck.sql(consulta_duck).fetchall())

    print("\n| Consulta \"gasto por unidade no último mês\" | Mediana |")
    print("|---|---|")
    print(f"| PostgreSQL (OLTP) | {t_pg * 1000:.1f} ms |")
    print(f"| DuckDB sobre Parquet no MinIO | {t_duck * 1000:.1f} ms |\n")


def medir_adr4(s3, conn):
    print("## ADR 4: lote completo x CDC incremental\n")
    marcas = ler_json(s3, CAMINHO_MARCAS, {})
    destino_teste = f"{BUCKET}/bronze/_medicao"
    print("| Tabela | Linhas (completo) | Completo | Linhas desde a marca | Incremental |")
    print("|---|---|---|---|---|")
    soma_completo = soma_incremental = 0.0
    for tabela, (coluna, _chave) in TABELAS.items():
        esquema = esquema_tabela(conn, tabela)
        linhas = {}

        def completo():
            linhas["c"] = exportar_parquet(conn, s3, f"SELECT * FROM {tabela}", None, esquema,
                                           f"{destino_teste}/{tabela}.parquet", gravar_vazio=True)

        marca = (marcas.get(tabela) or {}).get("marca")
        marca = datetime.fromisoformat(marca) if marca else None

        def incremental():
            filtro, parametros = (f"WHERE {coluna} > %s", [marca]) if marca else ("", None)
            linhas["i"] = exportar_parquet(conn, s3, f"SELECT * FROM {tabela} {filtro}", parametros,
                                           esquema, f"{destino_teste}/{tabela}_inc.parquet",
                                           gravar_vazio=False)

        t_c = mediana_segundos(completo)
        t_i = mediana_segundos(incremental)
        soma_completo += t_c
        soma_incremental += t_i
        print(f"| {tabela} | {linhas['c']} | {t_c:.2f} s | {linhas['i']} | {t_i:.3f} s |")
    print(f"| **total** | | **{soma_completo:.2f} s** | | **{soma_incremental:.3f} s** |\n")
    s3.delete_dir_contents(destino_teste, missing_dir_ok=True)


def main():
    s3 = sistema_arquivos()
    conn = conectar_postgres()
    print(f"_Medido em {datetime.now():%Y-%m-%d %H:%M}, mediana de {REPETICOES} execuções._\n")
    with conn:
        medir_adr2(s3)
        medir_adr3(s3, conn)
        medir_adr4(s3, conn)


if __name__ == "__main__":
    main()
