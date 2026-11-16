"""Mede a qualidade da busca no conjunto de referência (rótulos conhecidos).

    python -m semantica.medir_referencia [--arquivo semantica/referencia/rotulos_referencia.csv]

Para cada material rotulado com pelo menos um item CATMAT equivalente, roda
as duas recuperações da busca híbrida (cosseno e trigramas) e a reordenação,
e informa:

- recall@k: o item correto está entre os k recuperados (cosseno, trigramas
  e a união das duas buscas);
- top-1: o primeiro colocado é um item correto (só cosseno x híbrido).

Precisa do banco com a etapa embeddings já executada (os vetores são lidos,
não calculados). Os rótulos usam o mesmo formato de semantica/decisoes.py;
'sem_correspondente = sim' fica fora das contas (não há item a acertar).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg

from . import decisoes
from .correspondencia import (
    _HIBRIDA_TRIGRAMA,
    _HIBRIDA_VETOR,
    ParametrosBusca,
    _candidatos_hibridos,
)

PADRAO = Path(__file__).resolve().parent / "referencia" / "rotulos_referencia.csv"


def _percentual(acertos: int, total: int) -> str:
    return f"{acertos}/{total} ({100 * acertos / total:.1f}%)" if total else "-"


def medir(conn: psycopg.Connection, rotulos: list[decisoes.Decisao], parametros: ParametrosBusca,
          id_modelo: int) -> dict[str, tuple[int, int]]:
    corretos_por_texto = {d.material: set(d.codigos) for d in rotulos if not d.sem_correspondente}
    chave_por_texto = dict(conn.execute(
        "SELECT texto_original, chave_origem FROM semantica.descricao "
        "WHERE origem = 'estoque' AND ativa AND situacao = 'valida' AND texto_original = ANY(%s)",
        (list(corretos_por_texto),),
    ).fetchall())
    corretos = {chave_por_texto[t]: c for t, c in corretos_por_texto.items() if t in chave_por_texto}
    if not corretos:
        raise SystemExit("nenhum material rotulado encontrado em semantica.descricao (rode sincronizar)")

    id_para_chave = dict(conn.execute(
        "SELECT id_descricao, chave_origem FROM semantica.descricao "
        "WHERE origem = 'estoque' AND chave_origem = ANY(%s)", (list(corretos),)
    ).fetchall())
    filtro = {"modelo": id_modelo, "chaves": list(corretos)}

    with conn.transaction(), conn.cursor() as cur:
        cur.execute("SET LOCAL hnsw.ef_search = 400")
        recuperados: dict[str, dict[str, list[str]]] = {c: {"vetor": [], "trigrama": []} for c in corretos}
        for nome, sql, k in (("vetor", _HIBRIDA_VETOR, parametros.k_vetor),
                             ("trigrama", _HIBRIDA_TRIGRAMA, parametros.k_trigrama)):
            linhas = cur.execute(sql + " ORDER BY 1, 8 DESC", {**filtro, "k": k}).fetchall()
            for id_m, _, _, _, chave_k, _, _, _ in linhas:
                recuperados[id_para_chave[id_m]][nome].append(chave_k)
        hibrido = _candidatos_hibridos(cur, filtro, parametros)
        chave_catmat = dict(cur.execute(
            "SELECT id_descricao, chave_origem FROM semantica.descricao WHERE origem = 'catmat' "
            "AND id_descricao = ANY(%s)",
            (list({c[0] for lista in hibrido.values() for c in lista}),),
        ).fetchall())

    total = len(corretos)
    resultado = {
        f"recall@{parametros.k_vetor} cosseno": 0,
        f"recall@{parametros.k_trigrama} trigramas": 0,
        "recall da união": 0,
        "top-1 só cosseno": 0,
        "top-1 híbrido": 0,
        f"top-{parametros.top_k} híbrido": 0,
    }
    for chave, certos in corretos.items():
        vetor, trigrama = recuperados[chave]["vetor"], recuperados[chave]["trigrama"]
        resultado[f"recall@{parametros.k_vetor} cosseno"] += bool(certos & set(vetor))
        resultado[f"recall@{parametros.k_trigrama} trigramas"] += bool(certos & set(trigrama))
        resultado["recall da união"] += bool(certos & (set(vetor) | set(trigrama)))
        resultado["top-1 só cosseno"] += bool(vetor) and vetor[0] in certos
        id_m = next(i for i, c in id_para_chave.items() if c == chave)
        ordem = [chave_catmat[c[0]] for c in hibrido.get(id_m, [])]
        resultado["top-1 híbrido"] += bool(ordem) and ordem[0] in certos
        resultado[f"top-{parametros.top_k} híbrido"] += bool(certos & set(ordem))
    return {nome: (acertos, total) for nome, acertos in resultado.items()}


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analisador.add_argument("--arquivo", default=str(PADRAO))
    analisador.add_argument("--k-vetor", type=int, default=50)
    analisador.add_argument("--k-trigrama", type=int, default=20)
    analisador.add_argument("--top-k", type=int, default=10)
    args = analisador.parse_args(argv)

    rotulos = []
    for registro in decisoes.ler_arquivo(args.arquivo):
        decisao, erro = decisoes.interpretar(registro)
        if erro:
            raise SystemExit(f"rótulo inválido: {erro}")
        rotulos.append(decisao)
    parametros = ParametrosBusca(top_k=args.top_k, k_vetor=args.k_vetor, k_trigrama=args.k_trigrama)
    parametros.validar()

    with psycopg.connect(
        host=os.environ["HOST_DO_BANCO"], port=int(os.environ["PORTA_DO_BANCO"]),
        dbname=os.environ["NOME_DO_BANCO"], user=os.environ["USUARIO_DO_BANCO"],
        password=os.environ["SENHA_DO_BANCO"], autocommit=True,
    ) as conn:
        linha = conn.execute(
            "SELECT id_modelo, nome FROM semantica.modelo_embedding ORDER BY id_modelo DESC LIMIT 1"
        ).fetchone()
        if linha is None:
            raise SystemExit("nenhum modelo registrado: rode a etapa embeddings")
        medidas = medir(conn, rotulos, parametros, linha[0])

    com_item = sum(not d.sem_correspondente for d in rotulos)
    print(f"[referencia] {len(rotulos)} rótulos, {com_item} com item equivalente; modelo {linha[1]}")
    for nome, (acertos, total) in medidas.items():
        print(f"  {nome:<24} {_percentual(acertos, total)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
