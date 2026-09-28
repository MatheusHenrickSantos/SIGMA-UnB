"""
Medições do ADR 0001 (modelagem da origem), feitas no banco já carregado.

1. Caracterização da carga: linhas por tabela, tamanho em disco, linhas por
   mês de referência e crescimento.
2. Comparação das três formas de guardar o saldo do estoque:
     A. CRUD (opção nula: só o saldo mais recente, sobrescrito a cada mês)
     B. insert-only (uma foto por mês, que é o esquema adotado)
     C. CRUD + tabela de histórico alimentada por trigger
   para as duas consultas do Bloco 3 que dependem disso:
     Q4 - saldo atual de um material (a mais frequente, ~200/dia)
     Q7 - evolução do valor total em estoque mês a mês

As tabelas de A e C são montadas em um schema temporário (medicao) a partir
dos dados de B e apagadas no final.

Uso (com a plataforma no ar):
    docker compose run --rm ingest python medir_adr0001.py
"""

import random
import statistics
import time

import psycopg

REPETICOES = 300
SEMENTE = 2026


def cronometrar(cur, sql, parametros_lista):
    tempos = []
    for parametros in parametros_lista:
        inicio = time.perf_counter()
        cur.execute(sql, parametros)
        cur.fetchall()
        tempos.append((time.perf_counter() - inicio) * 1000)
    tempos.sort()
    return statistics.median(tempos), tempos[int(len(tempos) * 0.95) - 1]


def tamanho(cur, *tabelas):
    total = 0
    for tabela in tabelas:
        cur.execute("SELECT pg_total_relation_size(%s)", (tabela,))
        total += cur.fetchone()[0]
    return total / 1024 / 1024


def contar(cur, tabela):
    cur.execute(f"SELECT count(*) FROM {tabela}")
    return cur.fetchone()[0]


def caracterizar(cur):
    print("## 1. Caracterização da carga\n")
    print("| Tabela | Linhas | Tamanho (MB, com índices) |")
    print("|---|---:|---:|")
    for tabela in ("unidade", "material", "almoxarifado", "natureza_despesa", "credor",
                   "estoque_saldo", "gasto", "empenho", "requisicao_servico"):
        print(f"| {tabela} | {contar(cur, tabela):,} | {tamanho(cur, tabela):.1f} |")

    print("\n### Linhas por mês de referência\n")
    consultas = {
        "estoque_saldo": "SELECT data_referencia, count(*) FROM estoque_saldo GROUP BY 1 ORDER BY 1",
        "gasto": "SELECT data_referencia, count(*) FROM gasto GROUP BY 1 ORDER BY 1",
        "empenho": "SELECT date_trunc('month', data_emissao)::date, count(*) FROM empenho "
                   "WHERE data_emissao IS NOT NULL GROUP BY 1 ORDER BY 1",
        "requisicao_servico": "SELECT date_trunc('month', data_envio)::date, count(*) "
                              "FROM requisicao_servico WHERE data_envio IS NOT NULL GROUP BY 1 ORDER BY 1",
    }
    print("| Tabela | Meses | Primeiro | Último | Mediana linhas/mês | Máx. linhas/mês |")
    print("|---|---:|---|---|---:|---:|")
    for tabela, sql in consultas.items():
        cur.execute(sql)
        linhas = cur.fetchall()
        if not linhas:
            print(f"| {tabela} | 0 | - | - | - | - |")
            continue
        por_mes = [n for _, n in linhas]
        print(f"| {tabela} | {len(linhas)} | {linhas[0][0]:%m/%Y} | {linhas[-1][0]:%m/%Y} | "
              f"{statistics.median(por_mes):,.0f} | {max(por_mes):,} |")

    # Gastos: o valor de cada mês é do mês ou acumulado no ano? Se for
    # acumulado, quase nunca diminui de um mês para o seguinte no mesmo ano.
    cur.execute("""
        SELECT count(*) FILTER (WHERE valor >= anterior), count(*)
          FROM (SELECT valor,
                       lag(valor) OVER (PARTITION BY id_unidade, id_natureza,
                                        extract(year FROM data_referencia)
                                        ORDER BY data_referencia) AS anterior
                  FROM gasto) t
         WHERE anterior IS NOT NULL
    """)
    nao_diminuiu, pares = cur.fetchone()
    if pares:
        print(f"\nGastos: em {nao_diminuiu:,} de {pares:,} pares de meses seguidos do mesmo ano "
              f"({nao_diminuiu / pares:.0%}) o valor não diminuiu "
              "(perto de 100% indica valor acumulado no ano, não valor do mês).")

    cur.execute(
        "SELECT dataset, count(*), sum(linhas_lidas), sum(linhas_gravadas), sum(linhas_rejeitadas) "
        "FROM carga_execucao GROUP BY 1 ORDER BY 1"
    )
    print("\n### Resultado da carga\n")
    print("| Dataset | Arquivos | Lidas | Gravadas | Rejeitadas |")
    print("|---|---:|---:|---:|---:|")
    for dataset, arquivos, lidas, gravadas, rejeitadas in cur.fetchall():
        print(f"| {dataset} | {arquivos} | {lidas:,} | {gravadas:,} | {rejeitadas:,} |")

    cur.execute("SELECT motivo, count(*) FROM carga_rejeitado GROUP BY 1 ORDER BY 2 DESC LIMIT 8")
    motivos = cur.fetchall()
    if motivos:
        print("\nPrincipais motivos de rejeição:\n")
        for motivo, n in motivos:
            print(f"- {motivo}: {n:,}")


def comparar_estoque(cur):
    print("\n## 2. Estoque: CRUD × insert-only × CRUD com histórico\n")

    cur.execute("DROP SCHEMA IF EXISTS medicao CASCADE")
    cur.execute("CREATE SCHEMA medicao")

    # A: só o estado mais recente de cada material/almoxarifado
    cur.execute("""
        CREATE TABLE medicao.estoque_crud AS
        SELECT DISTINCT ON (id_material, id_almoxarifado)
               id_material, id_almoxarifado, saldo, preco_unitario, valor_total,
               data_referencia AS atualizado_em
          FROM estoque_saldo
         ORDER BY id_material, id_almoxarifado, data_referencia DESC
    """)
    cur.execute("ALTER TABLE medicao.estoque_crud ADD PRIMARY KEY (id_material, id_almoxarifado)")

    # C: A + histórico com todas as versões anteriores (o que o trigger gravaria)
    cur.execute("""
        CREATE TABLE medicao.estoque_historico AS
        SELECT e.id_material, e.id_almoxarifado, e.saldo, e.preco_unitario,
               e.valor_total, e.data_referencia AS valido_ate
          FROM estoque_saldo e
          JOIN medicao.estoque_crud c USING (id_material, id_almoxarifado)
         WHERE e.data_referencia < c.atualizado_em
    """)
    cur.execute("CREATE INDEX ON medicao.estoque_historico (id_material, valido_ate)")
    cur.execute("ANALYZE medicao.estoque_crud")
    cur.execute("ANALYZE medicao.estoque_historico")
    cur.execute("ANALYZE estoque_saldo")

    cur.execute("SELECT DISTINCT id_material FROM estoque_saldo")
    materiais = [linha[0] for linha in cur.fetchall()]
    random.seed(SEMENTE)
    amostra = [(random.choice(materiais),) for _ in range(REPETICOES)]

    q4 = {
        "A": "SELECT saldo, preco_unitario FROM medicao.estoque_crud WHERE id_material = %s",
        "B": "SELECT saldo, preco_unitario FROM estoque_saldo "
             "WHERE id_material = %s AND data_referencia = "
             "(SELECT max(data_referencia) FROM estoque_saldo)",
        "C": "SELECT saldo, preco_unitario FROM medicao.estoque_crud WHERE id_material = %s",
    }
    q7 = {
        "A": None,
        "B": "SELECT data_referencia, sum(valor_total) FROM estoque_saldo GROUP BY 1 ORDER BY 1",
        "C": "SELECT mes, sum(valor_total) FROM ("
             "  SELECT valido_ate AS mes, valor_total FROM medicao.estoque_historico"
             "  UNION ALL SELECT atualizado_em, valor_total FROM medicao.estoque_crud"
             ") t GROUP BY 1 ORDER BY 1",
    }

    resultado = {}
    for alternativa in "ABC":
        mediana4, p95_4 = cronometrar(cur, q4[alternativa], amostra)
        if q7[alternativa]:
            mediana7, p95_7 = cronometrar(cur, q7[alternativa], [()] * 30)
            texto_q7 = f"{mediana7:.1f} / {p95_7:.1f}"
        else:
            texto_q7 = "não responde (histórico perdido)"
        resultado[alternativa] = (mediana4, p95_4, texto_q7)

    linhas = {
        "A": contar(cur, "medicao.estoque_crud"),
        "B": contar(cur, "estoque_saldo"),
        "C": contar(cur, "medicao.estoque_crud") + contar(cur, "medicao.estoque_historico"),
    }
    tamanhos = {
        "A": tamanho(cur, "medicao.estoque_crud"),
        "B": tamanho(cur, "estoque_saldo"),
        "C": tamanho(cur, "medicao.estoque_crud", "medicao.estoque_historico"),
    }
    nomes = {"A": "A — CRUD (opção nula)", "B": "B — insert-only", "C": "C — CRUD + histórico"}

    print(f"Consultas repetidas: Q4 {REPETICOES}x com materiais sorteados (semente {SEMENTE}), "
          "Q7 30x. Tempo medido no cliente, em ms.\n")
    print("| Alternativa | Linhas | Tamanho (MB) | Q4 mediana / p95 (ms) | Q7 mediana / p95 (ms) |")
    print("|---|---:|---:|---:|---:|")
    for a in "ABC":
        mediana4, p95_4, texto_q7 = resultado[a]
        print(f"| {nomes[a]} | {linhas[a]:,} | {tamanhos[a]:.1f} | {mediana4:.2f} / {p95_4:.2f} | {texto_q7} |")

    # Quanto do histórico a opção A jogaria fora: materiais cujo preço mudou
    cur.execute("""
        SELECT count(*) FILTER (WHERE precos > 1), count(*)
          FROM (SELECT id_material, id_almoxarifado, count(DISTINCT preco_unitario) AS precos
                  FROM estoque_saldo GROUP BY 1, 2) t
    """)
    mudaram, total = cur.fetchone()
    print(f"\nPares material/almoxarifado com mais de um preço unitário ao longo do tempo: "
          f"{mudaram:,} de {total:,} ({mudaram / max(total, 1):.0%}). "
          "Na alternativa A, todos esses preços antigos seriam sobrescritos.")

    # Custo do insert-only: linhas iguais às do mês anterior (nada mudou)
    cur.execute("""
        SELECT count(*) FILTER (WHERE saldo = saldo_ant AND preco_unitario IS NOT DISTINCT FROM preco_ant),
               count(*)
          FROM (SELECT saldo, preco_unitario,
                       lag(saldo) OVER w AS saldo_ant, lag(preco_unitario) OVER w AS preco_ant
                  FROM estoque_saldo
                WINDOW w AS (PARTITION BY id_material, id_almoxarifado ORDER BY data_referencia)) t
         WHERE saldo_ant IS NOT NULL
    """)
    iguais, comparaveis = cur.fetchone()
    print(f"Linhas de estoque idênticas às do mês anterior (saldo e preço): {iguais:,} de "
          f"{comparaveis:,} ({iguais / max(comparaveis, 1):.0%}).")

    cur.execute("DROP SCHEMA medicao CASCADE")


def mudancas_de_estado(cur):
    print("\n## 3. Entidades que mudam de estado (atualizadas depois da primeira carga)\n")
    print("| Tabela | Atualizadas | Total | % |")
    print("|---|---:|---:|---:|")
    for tabela in ("unidade", "empenho", "requisicao_servico"):
        cur.execute(
            f"SELECT count(*) FILTER (WHERE atualizado_em > carregado_em), "
            f"count(*) FROM {tabela}"
        )
        atualizadas, total = cur.fetchone()
        print(f"| {tabela} | {atualizadas:,} | {total:,} | {atualizadas / max(total, 1):.0%} |")

    # A chave do empenho precisa da unidade gestora? Conta os (ano, número)
    # que aparecem em mais de uma UG.
    cur.execute("""
        SELECT count(*) FROM (SELECT ano, cod_empenho FROM empenho
                              GROUP BY 1, 2 HAVING count(DISTINCT id_unidade_gestora) > 1) t
    """)
    repetidos = cur.fetchone()[0]
    cur.execute("SELECT count(DISTINCT id_unidade_gestora) FROM empenho")
    print(f"\nEmpenhos: {repetidos:,} pares (ano, número) aparecem em mais de uma unidade "
          f"gestora ({cur.fetchone()[0]} UGs distintas).")

    cur.execute("SELECT fonte, count(*) FROM unidade GROUP BY 1 ORDER BY 1")
    print("\nUnidades por origem: " + ", ".join(f"{f} = {n}" for f, n in cur.fetchall()))


def main():
    with psycopg.connect(autocommit=True) as conn:
        with conn.cursor() as cur:
            caracterizar(cur)
            comparar_estoque(cur)
            mudancas_de_estado(cur)


if __name__ == "__main__":
    main()
