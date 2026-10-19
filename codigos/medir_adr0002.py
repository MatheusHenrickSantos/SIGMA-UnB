"""
Medições do ADR 0002: serialização, compressão e particionamento do
estoque_saldo na camada analítica.

Uso:  docker compose run --rm --no-deps ingest python medir_adr0002.py
Usa os dados reais do OLTP (todas as linhas de estoque_saldo).
"""

import csv
import json
import os
import shutil
import tempfile
import time
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.dataset as ds
import pyarrow.parquet as pq

import lake


def tamanho(caminho):
    caminho = Path(caminho)
    if caminho.is_file():
        return caminho.stat().st_size
    return sum(f.stat().st_size for f in caminho.rglob("*") if f.is_file())


def tempo(funcao, repeticoes=5):
    melhor = None
    for _ in range(repeticoes):
        inicio = time.perf_counter()
        funcao()
        decorrido = time.perf_counter() - inicio
        melhor = decorrido if melhor is None else min(melhor, decorrido)
    return melhor * 1000


def main():
    from deltalake import DeltaTable
    tabela = DeltaTable(lake.caminho("estoque_saldo")).to_pyarrow_table()
    tabela = tabela.drop(["removido", "ultimo_evento"])
    print(f"estoque_saldo: {tabela.num_rows} linhas, {tabela.num_columns} colunas\n")

    base = Path(tempfile.mkdtemp())
    try:
        # serialização e compressão
        pacsv.write_csv(tabela, base / "t.csv")
        with open(base / "t.jsonl", "w") as f:
            for linha in tabela.to_pylist():
                f.write(json.dumps(linha, default=str) + "\n")
        for comp in ("NONE", "SNAPPY", "ZSTD", "GZIP"):
            pq.write_table(tabela, base / f"t_{comp}.parquet", compression=comp)
        # particionado por ano
        pq.write_to_dataset(tabela, base / "particionado", partition_cols=["ano_referencia"],
                            compression="ZSTD")
        pq.write_table(tabela, base / "plano.parquet", compression="ZSTD")

        print("Tamanho em disco")
        for nome in ("t.jsonl", "t.csv", "t_NONE.parquet", "t_SNAPPY.parquet",
                     "t_ZSTD.parquet", "t_GZIP.parquet"):
            print(f"  {nome:<18} {tamanho(base / nome) / 1024:>9.0f} KiB")

        # consulta típica: saldo e valor de um ano (filtro por período, 3 colunas)
        def plano():
            t = pq.read_table(base / "plano.parquet", columns=["id_material", "valor_total"],
                              filters=[("ano_referencia", "=", 2024)])
            return pc.sum(t["valor_total"])

        def particionado():
            d = ds.dataset(base / "particionado", partitioning="hive")
            t = d.to_table(columns=["id_material", "valor_total"],
                           filter=ds.field("ano_referencia") == 2024)
            return pc.sum(t["valor_total"])

        def csv_inteiro():
            t = pacsv.read_csv(base / "t.csv")
            t = t.filter(pc.equal(t["ano_referencia"], 2024))
            return pc.sum(t["valor_total"])

        print("\nConsulta: soma do valor em estoque de 2024 (melhor de 5, ms)")
        print(f"  CSV, lê tudo                 {tempo(csv_inteiro):>8.1f}")
        print(f"  Parquet ZSTD, arquivo único  {tempo(plano):>8.1f}")
        print(f"  Parquet ZSTD, part. por ano  {tempo(particionado):>8.1f}")
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
    import sys
    sys.stdout.flush()
    os._exit(0)
