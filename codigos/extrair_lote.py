"""
Caminho 1 da E2: extração em lote.

Tira uma foto completa de cada tabela de negócio do Postgres e grava em
bronze/lote/<tabela>/data_extracao=AAAA-MM-DD/<tabela>.parquet.

Todas as tabelas são lidas na mesma transação (REPEATABLE READ, só leitura),
então a foto é consistente entre si: um empenho nunca aponta para um credor
que ainda não estava na foto.

Rodar de novo no mesmo dia substitui a foto do dia; dias diferentes ficam
lado a lado, e a pasta data_extracao=... funciona como partição para o
DuckDB e o dbt na E3.

Uso:
    python extrair_lote.py
"""

import time

from psycopg import IsolationLevel

from lake import (BUCKET, TABELAS, agora, conectar_postgres, esquema_tabela,
                  exportar_parquet, garantir_bucket, sistema_arquivos, tamanho_mb)


def main():
    s3 = sistema_arquivos()
    garantir_bucket(s3)
    dia = agora().date().isoformat()

    conn = conectar_postgres()
    conn.isolation_level = IsolationLevel.REPEATABLE_READ

    print(f"Extração em lote para bronze/lote/ (data_extracao={dia})\n")
    print(f"{'tabela':<20} {'linhas':>9} {'tamanho':>10} {'tempo':>8}")
    inicio_total = time.perf_counter()
    total_linhas = total_bytes = 0

    with conn:
        for tabela in TABELAS:
            inicio = time.perf_counter()
            destino = f"{BUCKET}/bronze/lote/{tabela}/data_extracao={dia}/{tabela}.parquet"
            linhas = exportar_parquet(
                conn, s3,
                f"SELECT * FROM {tabela}", None,
                esquema_tabela(conn, tabela),
                destino,
                gravar_vazio=True,
            )
            tamanho = s3.get_file_info(destino).size
            total_linhas += linhas
            total_bytes += tamanho
            print(f"{tabela:<20} {linhas:>9} {tamanho_mb(tamanho):>10} "
                  f"{time.perf_counter() - inicio:>7.2f}s")

    print(f"{'TOTAL':<20} {total_linhas:>9} {tamanho_mb(total_bytes):>10} "
          f"{time.perf_counter() - inicio_total:>7.2f}s")


if __name__ == "__main__":
    main()
