"""Medições do ADR 0005: busca exata x índice HNSW no pgvector.

Dois modos:

  python medir_adr0005.py sintetico [--catmat 345000] [--materiais 2400]
      Vetores aleatórios de 384 dimensões num schema temporário
      (medicao_adr0005, apagado no fim). Mede carga, construção do índice,
      latência da busca exata e da HNSW e o recall@K da HNSW. Vetores
      aleatórios não têm agrupamentos: é o pior caso para o recall.

  python medir_adr0005.py real
      Usa os vetores já gravados em semantica.embedding pelo pipeline
      (python -m semantica): latência da busca exata e recall@K da HNSW com
      vetores de verdade. Se não houver índice HNSW (situação desde a
      migração V3), cria um temporário, mede e o apaga no fim. A construção
      leva alguns minutos e bloqueia escritas na tabela enquanto isso.

Conexão pelas variáveis PG*. Exemplo no Docker:
  docker compose run --rm semantica python medir_adr0005.py real
"""

from __future__ import annotations

import argparse
import random
import statistics
import sys
import time
from pathlib import Path

import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent))

from semantica.correspondencia import _BUSCA, SQL_INDICE_HNSW  # noqa: E402

INDICE_TEMPORARIO = "ix_medicao_adr0005_tmp"

DIMENSAO = 384


def _ms(segundos: float) -> str:
    return f"{segundos * 1000:.1f} ms"


def _resumo(tempos: list[float]) -> str:
    ordenados = sorted(tempos)
    p95 = ordenados[max(0, round(0.95 * len(ordenados)) - 1)]
    return f"mediana {_ms(statistics.median(ordenados))}, p95 {_ms(p95)}"


def _vizinhos(cur, sql_busca: str, consulta: str, k: int) -> tuple[list, float]:
    inicio = time.perf_counter()
    ids = [linha[0] for linha in cur.execute(sql_busca, (consulta, k)).fetchall()]
    return ids, time.perf_counter() - inicio


def comparar(conn, sql_busca: str, consultas: list[str], k: int, valores_ef: list[int]) -> float:
    """Busca exata (sem índice) x HNSW (índice forçado), mesmas consultas.

    Devolve a mediana da busca exata, em segundos.
    """
    with conn.transaction(), conn.cursor() as cur:
        cur.execute("SET LOCAL enable_indexscan = off")
        exatos, tempos_exatos = zip(*(_vizinhos(cur, sql_busca, q, k) for q in consultas))
    print(f"  exata            : {_resumo(tempos_exatos)}; {len(consultas)} consultas, top-{k}")

    for ef in valores_ef:
        with conn.transaction(), conn.cursor() as cur:
            cur.execute(f"SET LOCAL hnsw.ef_search = {int(ef)}")
            cur.execute("SET LOCAL enable_seqscan = off")
            aproximados, tempos = zip(*(_vizinhos(cur, sql_busca, q, k) for q in consultas))
        recall = statistics.mean(len(set(a) & set(e)) / k for a, e in zip(aproximados, exatos))
        print(f"  hnsw ef_search={ef:<4}: {_resumo(tempos)}; recall@{k} = {recall:.3f}")
    return statistics.median(tempos_exatos)


def plano_padrao(conn, id_modelo: int, k: int) -> None:
    """Qual caminho o planejador escolhe sozinho na consulta do pipeline."""
    plano = "\n".join(
        linha[0] for linha in conn.execute(
            "EXPLAIN " + _BUSCA, {"modelo": id_modelo, "top_k": k, "limiar": None, "chaves": None}
        )
    )
    indices = [nome for (nome,) in conn.execute(
        "SELECT indexname FROM pg_indexes WHERE schemaname = 'semantica' "
        "AND tablename = 'embedding' AND indexdef ILIKE '%%hnsw%%'"
    )]
    usa = any(nome in plano for nome in indices)
    print(f"  consulta do pipeline (correspondencia._BUSCA) com configuração padrão: "
          f"{'usa o índice HNSW' if usa else 'NÃO usa o índice (varredura)'}")


def sintetico(conn, n_catmat: int, n_materiais: int, amostra: int, k: int) -> None:
    print(f"Sintético: {n_catmat} vetores 'CATMAT' e {n_materiais} 'materiais', {DIMENSAO} dimensões")
    conn.execute("DROP SCHEMA IF EXISTS medicao_adr0005 CASCADE")
    conn.execute("CREATE SCHEMA medicao_adr0005")
    try:
        conn.execute(f"CREATE TABLE medicao_adr0005.catmat (id int PRIMARY KEY, vetor vector({DIMENSAO}))")
        gerar = (
            "INSERT INTO medicao_adr0005.catmat "
            "SELECT i, l2_normalize((SELECT array_agg(random() - 0.5) "
            f"  FROM generate_series(1, {DIMENSAO}) WHERE i IS NOT NULL)::vector) "
            "FROM generate_series(%s::int, %s::int) AS i"
        )
        inicio = time.perf_counter()
        conn.execute(gerar, (1, n_catmat))
        print(f"  carga sem índice : {time.perf_counter() - inicio:.1f} s")

        conn.execute("SET maintenance_work_mem = '1GB'")
        inicio = time.perf_counter()
        conn.execute("CREATE INDEX ON medicao_adr0005.catmat USING hnsw (vetor vector_cosine_ops)")
        print(f"  CREATE INDEX hnsw (maintenance_work_mem 1GB): {time.perf_counter() - inicio:.1f} s")
        conn.execute("RESET maintenance_work_mem")

        extra = min(5000, n_catmat)
        inicio = time.perf_counter()
        conn.execute(gerar, (n_catmat + 1, n_catmat + extra))
        duracao = time.perf_counter() - inicio
        print(f"  inserção com índice já criado: {extra} vetores em {duracao:.1f} s "
              f"({extra / duracao:.0f}/s; {n_catmat / (extra / duracao) / 60:.0f} min para {n_catmat}, extrapolado)")

        tamanhos = conn.execute(
            "SELECT pg_size_pretty(pg_table_size('medicao_adr0005.catmat')), "
            "pg_size_pretty(pg_indexes_size('medicao_adr0005.catmat'))"
        ).fetchone()
        print(f"  tamanho: tabela {tamanhos[0]}, índice {tamanhos[1]}")
        conn.execute("ANALYZE medicao_adr0005.catmat")

        sorteio = random.Random(2026)
        consultas = []
        for _ in range(amostra):
            vetor = [sorteio.gauss(0, 1) for _ in range(DIMENSAO)]
            consultas.append("[" + ",".join(f"{v:.6f}" for v in vetor) + "]")
        mediana_exata = comparar(
            conn,
            "SELECT id FROM medicao_adr0005.catmat ORDER BY vetor <=> %s::vector LIMIT %s",
            consultas, k, [40, 100, 200],
        )
        print(f"  {n_materiais} materiais x busca exata ≈ {n_materiais * mediana_exata / 60:.1f} min "
              "(extrapolado da mediana)")

        # mesma forma da consulta do pipeline: um LATERAL por material
        conn.execute(f"CREATE TABLE medicao_adr0005.material (id int PRIMARY KEY, vetor vector({DIMENSAO}))")
        conn.execute(gerar.replace("medicao_adr0005.catmat", "medicao_adr0005.material"), (1, n_materiais))
        conn.execute("ANALYZE medicao_adr0005.material")
        lateral = (
            "SELECT m.id, v.id FROM medicao_adr0005.material m CROSS JOIN LATERAL ("
            "  SELECT c.id FROM medicao_adr0005.catmat c ORDER BY c.vetor <=> m.vetor LIMIT %s) v"
        )
        plano = "\n".join(r[0] for r in conn.execute("EXPLAIN " + lateral, (k,)))
        print(f"  LATERAL ({n_materiais} materiais) com configuração padrão: "
              f"{'usa o índice HNSW' if 'catmat_vetor_idx' in plano else 'NÃO usa o índice'}")
        inicio = time.perf_counter()
        linhas = conn.execute(lateral, (k,)).fetchall()
        print(f"  LATERAL completo pelo índice: {len(linhas)} pares em {time.perf_counter() - inicio:.1f} s")
    finally:
        conn.execute("DROP SCHEMA IF EXISTS medicao_adr0005 CASCADE")


def real(conn, amostra: int, k: int) -> None:
    linha = conn.execute(
        "SELECT id_modelo, count(*) FROM semantica.embedding WHERE origem = 'catmat' "
        "GROUP BY id_modelo ORDER BY count(*) DESC LIMIT 1"
    ).fetchone()
    if linha is None:
        sys.exit("não há vetores CATMAT em semantica.embedding: rode python -m semantica antes")
    id_modelo, n_catmat = linha
    # amostra fixa, mas espalhada (ordem do md5 do id, não do id)
    consultas = [
        texto for (texto,) in conn.execute(
            "SELECT vetor::text FROM semantica.embedding WHERE origem = 'estoque' AND id_modelo = %s "
            "ORDER BY md5(id_descricao::text) LIMIT %s", (id_modelo, amostra),
        )
    ]
    print(f"Real: modelo {id_modelo}, {n_catmat} vetores CATMAT, {len(consultas)} materiais consultados")
    plano_padrao(conn, id_modelo, k)

    tem_indice = conn.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname = 'semantica' "
        "AND tablename = 'embedding' AND indexdef ILIKE '%%hnsw%%')"
    ).fetchone()[0]
    try:
        if not tem_indice:
            print(f"  sem índice HNSW: criando {INDICE_TEMPORARIO} só para a medição...")
            conn.execute("SET maintenance_work_mem = '1GB'")
            inicio = time.perf_counter()
            conn.execute(SQL_INDICE_HNSW.format(nome=INDICE_TEMPORARIO))
            print(f"  CREATE INDEX: {time.perf_counter() - inicio:.1f} s")
            conn.execute("ANALYZE semantica.embedding")
        comparar(
            conn,
            "SELECT id_descricao FROM semantica.embedding WHERE origem = 'catmat' "
            f"AND id_modelo = {int(id_modelo)} ORDER BY vetor <=> %s::vector LIMIT %s",
            consultas, k, [40, 100, 200],
        )
    finally:
        if not tem_indice:
            conn.execute(f"DROP INDEX IF EXISTS semantica.{INDICE_TEMPORARIO}")


def main() -> int:
    analisador = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    analisador.add_argument("modo", choices=["sintetico", "real"])
    analisador.add_argument("--catmat", type=int, default=345_000)
    analisador.add_argument("--materiais", type=int, default=2_400)
    analisador.add_argument("--amostra", type=int, default=100, help="consultas medidas")
    analisador.add_argument("--top-k", type=int, default=10)
    args = analisador.parse_args()

    with psycopg.connect(autocommit=True) as conn:
        if args.modo == "sintetico":
            sintetico(conn, args.catmat, args.materiais, args.amostra, args.top_k)
        else:
            real(conn, args.amostra, args.top_k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
