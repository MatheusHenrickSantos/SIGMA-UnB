"""
Demonstração do CDC: altera linhas do OLTP e mostra os eventos capturados.

Pré-requisito: banco no ar com as migrações aplicadas (docker compose up).
Uso:  docker compose run --rm --no-deps ingest python cdc_demo.py

A demonstração cria um material de teste, altera e apaga, e no fim remove os
arquivos de evento que ela mesma gerou para não poluir dados/cdc/.
"""

import json

import psycopg

import cdc_consumidor as cdc

DESCRICAO = "MATERIAL DEMO CDC"


def mostrar(titulo, arquivos):
    print(f"\n== {titulo}")
    for arquivo in arquivos:
        for linha in arquivo.read_text(encoding="utf-8").splitlines():
            e = json.loads(linha)
            print(f"  {e['operacao'].upper():<6} {e['tabela']:<16} id_evento={e['id_evento']}")
            if e["antes"]:
                print(f"         antes : {e['antes']}")
            if e["depois"]:
                print(f"         depois: {e['depois']}")


def passo(conn, titulo, sql, params=()):
    antes = set(cdc.PASTA_CDC.glob("eventos-*.jsonl")) if cdc.PASTA_CDC.exists() else set()
    conn.execute(sql, params)
    cdc.drenar(conn)
    novos = sorted(set(cdc.PASTA_CDC.glob("eventos-*.jsonl")) - antes)
    mostrar(titulo, novos)
    return novos


def main():
    with psycopg.connect(autocommit=True) as conn:
        cdc.garantir_slot(conn)
        cdc.drenar(conn)  # descarta o que sobrou de execuções anteriores
        conn.execute("DELETE FROM material WHERE descricao = %s", (DESCRICAO,))
        cdc.drenar(conn)

        gerados = []
        gerados += passo(conn, "1. INSERT", "INSERT INTO material (descricao) VALUES (%s)", (DESCRICAO,))
        gerados += passo(conn, "2. UPDATE (note antes e depois)",
                         "UPDATE material SET termo_busca = 'demo cdc', atualizado_em = now() "
                         "WHERE descricao = %s", (DESCRICAO,))
        gerados += passo(conn, "3. DELETE", "DELETE FROM material WHERE descricao = %s", (DESCRICAO,))

        print("\n== 4. Reprocessamento: nada novo, nada duplicado")
        print(f"  eventos lidos de novo: {cdc.drenar(conn)}")

        for arquivo in gerados:
            arquivo.unlink()


if __name__ == "__main__":
    main()
