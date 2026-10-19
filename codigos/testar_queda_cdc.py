"""
Teste de falha do CDC: o consumidor "cai" depois de gravar o lote e antes de
avançar o slot. Ao reiniciar, o lote deve ser relido, gerar o MESMO arquivo e
chegar ao lake sem duplicar nada.

Uso:  docker compose run --rm --no-deps ingest python testar_queda_cdc.py
"""

import os
import sys

import psycopg
from deltalake import DeltaTable

import cdc_consumidor as cdc
import lake

DESCRICAO = "MATERIAL TESTE QUEDA CDC"


def arquivos():
    return {a.name: a.read_text() for a in cdc.PASTA_CDC.glob("eventos-*.jsonl")}


def main():
    with psycopg.connect(autocommit=True) as conn:
        cdc.garantir_slot(conn)
        cdc.drenar(conn)
        base = arquivos()

        conn.execute("INSERT INTO material (descricao) VALUES (%s)", (DESCRICAO,))

        # 1) queda: o arquivo é gravado, mas o slot não avança
        original = cdc.lsn_texto
        def cai(_):
            raise RuntimeError("processo morreu antes de avançar o slot")
        cdc.lsn_texto = cai
        try:
            cdc.drenar(conn)
        except RuntimeError as erro:
            print(f"1. queda simulada: {erro}")
        cdc.lsn_texto = original
        apos_queda = arquivos()
        novos = set(apos_queda) - set(base)
        print(f"   arquivo gravado antes da queda: {sorted(novos)}")

        # 2) reinício: relê o mesmo lote
        cdc.drenar(conn)
        apos_reinicio = arquivos()
        print(f"2. após reinício: {len(set(apos_reinicio) - set(base))} arquivo(s) novo(s), "
              f"conteúdo igual ao de antes da queda: "
              f"{all(apos_reinicio[n] == apos_queda[n] for n in novos)}")
        assert set(apos_reinicio) == set(apos_queda), "reinício criou arquivo diferente"
        assert all(apos_reinicio[n] == apos_queda[n] for n in novos)

        # 3) o slot avançou: uma nova leitura não traz o lote de novo
        print(f"3. nova leitura traz {cdc.drenar(conn)} evento(s) (esperado 0)")

        # 4) o lake recebe o evento uma vez, mesmo aplicando duas vezes
        lake.aplicar_cdc()
        lake.aplicar_cdc()
        linhas = [r for r in DeltaTable(lake.caminho("material")).to_pyarrow_table().to_pylist()
                  if r["descricao"] == DESCRICAO]
        print(f"4. linhas desse material no lake: {len(linhas)} (esperado 1)")
        assert len(linhas) == 1

        # limpeza: remove o material e os arquivos gerados pelo teste
        conn.execute("DELETE FROM material WHERE descricao = %s", (DESCRICAO,))
        cdc.drenar(conn)
        lake.aplicar_cdc()
        for nome in set(arquivos()) - set(base):
            (cdc.PASTA_CDC / nome).unlink()
        print("OK: nenhuma perda e nenhuma duplicação.")


if __name__ == "__main__":
    main()
    sys.stdout.flush()
    os._exit(0)
