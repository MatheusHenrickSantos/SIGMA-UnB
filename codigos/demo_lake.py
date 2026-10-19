"""
Demonstração de entrega, idempotência e dado atrasado na camada analítica.

Pré-requisitos: banco no ar, `python lake.py carga` já executado.
Uso:  docker compose run --rm --no-deps ingest python demo_lake.py

Cenários (RD-08 e RD-09):
  1. evento novo do OLTP chega ao lake via CDC;
  2. reprocessar o mesmo arquivo de eventos não muda nada (idempotência);
  3. evento ATRASADO (mais antigo que o estado) não desfaz o estado novo;
  4. evento de INSERT repetido depois de um DELETE não ressuscita a linha;
  5. reprocessar uma janela do estoque (carga em lote) é idempotente.
Ao final, remove o material de teste do OLTP e os arquivos de evento gerados.
"""

import json

import psycopg
from deltalake import DeltaTable

import cdc_consumidor as cdc
import lake

DESCRICAO = "MATERIAL DEMO LAKE"


def estado():
    tabela = DeltaTable(lake.caminho("material")).to_pyarrow_table().to_pylist()
    return [r for r in tabela if r["descricao"] == DESCRICAO]


def resumo(titulo):
    versao = DeltaTable(lake.caminho("material")).version()
    print(f"  -> {titulo}: material v{versao}, linhas de teste = "
          f"{[(r['termo_busca'], r['removido'], r['ultimo_evento']) for r in estado()]}")


def evento_novo(conn, sql, params=()):
    antes = set(lake.PASTA_CDC.glob("eventos-*.jsonl")) if lake.PASTA_CDC.exists() else set()
    conn.execute(sql, params)
    cdc.drenar(conn)
    return sorted(set(lake.PASTA_CDC.glob("eventos-*.jsonl")) - antes)


def main():
    gerados = []
    with psycopg.connect(autocommit=True) as conn:
        cdc.garantir_slot(conn)
        cdc.drenar(conn)
        conn.execute("DELETE FROM material WHERE descricao = %s", (DESCRICAO,))
        cdc.drenar(conn)

        print("\n== 1. INSERT e UPDATE no OLTP chegam ao lake")
        gerados += evento_novo(conn, "INSERT INTO material (descricao) VALUES (%s)", (DESCRICAO,))
        arq_insert = gerados[-1]
        gerados += evento_novo(conn, "UPDATE material SET termo_busca = 'versao 2', "
                               "atualizado_em = now() WHERE descricao = %s", (DESCRICAO,))
        lake.aplicar_cdc()
        resumo("depois do CDC")

        print("\n== 2. Reprocessar os mesmos arquivos: nada muda")
        lake.aplicar_cdc()
        resumo("depois do reprocessamento")

        print("\n== 3. Evento atrasado (INSERT antigo reentregue) não desfaz o UPDATE")
        # o log já conhece o evento; para forçar a reaplicação ao estado,
        # simula o consumidor reentregando o lote antigo como se fosse novo
        evento = json.loads(arq_insert.read_text().splitlines()[0])
        evento["id_evento"], evento["tabela"] = int(evento["id_evento"]), "material"
        evento["commit_ts"] = lake.datetime.fromisoformat(evento["commit_ts"])
        lake.mesclar("material",
                     lake.tabela_arrow([lake.linha_do_evento(evento)], lake.esquema("material")),
                     lake.esquema("material"), ["id_material"], [],
                     "s.ultimo_evento > t.ultimo_evento")
        resumo("depois do evento atrasado (termo_busca deve continuar 'versao 2')")

        print("\n== 4. DELETE, e depois o INSERT antigo reentregue: linha continua removida")
        gerados += evento_novo(conn, "DELETE FROM material WHERE descricao = %s", (DESCRICAO,))
        lake.aplicar_cdc()
        lake.mesclar("material",
                     lake.tabela_arrow([lake.linha_do_evento(evento)], lake.esquema("material")),
                     lake.esquema("material"), ["id_material"], [],
                     "s.ultimo_evento > t.ultimo_evento")
        resumo("depois do INSERT antigo (removido deve continuar True)")

    print("\n== 5. Reprocessar a janela 2023-03 do estoque duas vezes")
    for tentativa in (1, 2):
        lake.carga("2023-03")
        dt = DeltaTable(lake.caminho("estoque_saldo"))
        print(f"  -> tentativa {tentativa}: estoque_saldo v{dt.version()}, "
              f"{dt.to_pyarrow_table(columns=['id_material']).num_rows} linhas")

    for arquivo in gerados:
        arquivo.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
    import os, sys
    sys.stdout.flush()
    os._exit(0)
