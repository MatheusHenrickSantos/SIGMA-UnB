"""Ponto de entrada: python -m semantica <etapa> [opções]

Etapas (cada uma pode rodar sozinha e é segura para repetir):

  sincronizar   lê prata.material e prata.catmat_item e atualiza semantica.descricao
  embeddings    gera vetores só das descrições novas ou alteradas
  corresponder  busca os top-K itens CATMAT de cada material e grava uma execução
  tudo          as três acima, em ordem (padrão)
  revisar       registra a decisão humana sobre um par material x item CATMAT
  fila          exporta a fila de revisão (semantica.v_fila_revisao) para CSV

Banco: variáveis HOST_DO_BANCO, PORTA_DO_BANCO, NOME_DO_BANCO,
USUARIO_DO_BANCO e SENHA_DO_BANCO. Opções de busca também podem vir de
variáveis SEMANTICA_* (ver --help de cada etapa).
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

import psycopg

from . import correspondencia, fontes, processamento
from .correspondencia import ParametrosBusca
from .embeddings import MODELO_PADRAO, ErroEmbedding
from .repositorio import ErroOrigem

ORIGENS = ("estoque", "catmat")


def _ambiente(nome: str, padrao: str | None = None) -> str | None:
    valor = os.environ.get(nome, "").strip()
    return valor or padrao


def _numero_opcional(texto: str | None, tipo):
    return None if texto in (None, "") else tipo(texto)


def _sincronizar(conn, args) -> None:
    for origem in ORIGENS:
        registros = fontes.ler(conn, origem, args.incluir_catmat_inativo)
        resumo, sem_chave, repetidas = processamento.sincronizar_origem(conn, origem, registros)
        print(
            f"[sincronizar] {origem}: {resumo.lidas} lidas, {resumo.novas} novas, "
            f"{resumo.alteradas} alteradas, {resumo.desativadas} desativadas, "
            f"{resumo.validas} válidas, {resumo.recusadas} recusadas, "
            f"{resumo.vetores_descartados} vetores descartados"
        )
        if sem_chave or repetidas:
            print(f"  AVISO: {sem_chave} sem chave (ignoradas), {repetidas} chaves repetidas (vale a última)")


def _codificador(args):
    from .embeddings import CodificadorSentenceTransformers

    print(f"[modelo] carregando {args.modelo} (revisão: {args.revisao or 'mais recente'})")
    return CodificadorSentenceTransformers(
        args.modelo, revisao=args.revisao, dispositivo=args.dispositivo, tamanho_lote=args.lote_modelo
    )


def _embeddings(conn, args, codificador) -> int:
    id_modelo = processamento.preparar_modelo(conn, codificador)
    print(f"[modelo] id {id_modelo}: {codificador.nome}@{codificador.revisao}, {codificador.dimensao} dimensões")
    for origem in ORIGENS:
        resumo = processamento.atualizar_embeddings(
            conn, codificador, id_modelo, origem, fontes.PAPEL_POR_ORIGEM[origem], args.tamanho_lote
        )
        print(
            f"[embeddings] {origem}: {resumo.pendentes} pendentes, {resumo.reaproveitados} reaproveitados, "
            f"{resumo.textos_enviados_ao_modelo} textos enviados ao modelo em {resumo.lotes} lote(s)"
        )
        if resumo.textos_truncados:
            print(
                f"  AVISO: {resumo.textos_truncados} texto(s) passam do limite de tokens do modelo; "
                "o final deles foi ignorado no vetor"
            )
    return id_modelo


def _id_modelo_registrado(conn, args) -> int:
    linha = conn.execute(
        "SELECT id_modelo FROM semantica.modelo_embedding "
        "WHERE nome = %s AND (%s::text IS NULL OR revisao = %s) "
        "ORDER BY id_modelo DESC LIMIT 1",
        (args.modelo, args.revisao, args.revisao),
    ).fetchone()
    if linha is None:
        raise ErroEmbedding(f"modelo {args.modelo} ainda não registrado: rode a etapa embeddings")
    return linha[0]


def _corresponder(conn, args, id_modelo: int) -> None:
    parametros = ParametrosBusca(
        top_k=args.top_k,
        limiar_similaridade=args.limiar_similaridade,
        busca_exata=args.busca_exata,
        ef_search=args.ef_search,
    )
    resumo = correspondencia.executar_correspondencia(conn, id_modelo, parametros)
    print(
        f"[corresponder] execução {resumo.id_execucao}: {resumo.materiais} materiais, "
        f"{resumo.candidatos} candidatos ({resumo.candidatos_com_conflito} com conflito de especificação), "
        f"{resumo.materiais_sem_candidato} sem candidato"
    )
    if resumo.materiais_sem_vetor:
        print(f"  AVISO: {resumo.materiais_sem_vetor} material(is) sem vetor ficaram de fora")
    print("  Candidatos são sugestões: confira em semantica.v_fila_revisao antes de usar.")


def _fila(conn, args) -> None:
    linhas = conn.execute(
        """
        SELECT identificador_material, material, posicao, codigo_item, descricao_catmat,
               round(similaridade::numeric, 4), round(vantagem_sobre_proximo::numeric, 4),
               situacao_especificacao,
               array_to_string(ARRAY(SELECT jsonb_array_elements_text(especificacoes -> 'conflitos')), ' | '),
               decisao
        FROM semantica.v_fila_revisao
        ORDER BY identificador_material, posicao
        """
    ).fetchall()
    destino = Path(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="", encoding="utf-8-sig") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow([
            "identificador_material", "material", "posicao", "codigo_item", "descricao_catmat",
            "similaridade", "vantagem_sobre_proximo", "situacao_especificacao", "conflitos", "decisao",
        ])
        escritor.writerows(linhas)
    print(f"[fila] {len(linhas)} candidato(s) exportado(s) para {destino}")


def _revisar(conn, args) -> None:
    correspondencia.registrar_revisao(
        conn, args.material, args.codigo, args.decisao, args.revisor, args.observacao
    )
    print(f"[revisar] {args.material} x {args.codigo}: {args.decisao} ({args.revisor})")


def _argumentos(argv: list[str] | None) -> argparse.Namespace:
    analisador = argparse.ArgumentParser(prog="python -m semantica", description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analisador.add_argument("etapa", nargs="?", default="tudo",
                            choices=["sincronizar", "embeddings", "corresponder", "tudo", "revisar", "fila"])

    modelo = analisador.add_argument_group("modelo")
    modelo.add_argument("--modelo", default=_ambiente("SEMANTICA_MODELO", MODELO_PADRAO),
                        help="nome no Hugging Face ou pasta local (SEMANTICA_MODELO)")
    modelo.add_argument("--revisao", default=_ambiente("SEMANTICA_REVISAO"),
                        help="commit do modelo no Hugging Face; vazio = mais recente (SEMANTICA_REVISAO)")
    modelo.add_argument("--dispositivo", default=_ambiente("SEMANTICA_DISPOSITIVO", "cpu"))
    modelo.add_argument("--lote-modelo", type=int, default=32, help="textos por passada do modelo")
    modelo.add_argument("--tamanho-lote", type=int,
                        default=int(_ambiente("SEMANTICA_TAMANHO_LOTE", "256")),
                        help="descrições gravadas por transação (SEMANTICA_TAMANHO_LOTE)")

    busca = analisador.add_argument_group("busca")
    busca.add_argument("--top-k", type=int, default=int(_ambiente("SEMANTICA_TOP_K", "10")),
                       help="candidatos por material (SEMANTICA_TOP_K, padrão 10)")
    busca.add_argument("--limiar-similaridade", type=float,
                       default=_numero_opcional(_ambiente("SEMANTICA_LIMIAR"), float),
                       help="descarta candidatos abaixo deste valor; sem padrão calibrado (SEMANTICA_LIMIAR)")
    busca.add_argument("--busca-exata", action="store_true",
                       default=_ambiente("SEMANTICA_BUSCA_EXATA", "") in ("1", "true", "sim"),
                       help="proíbe o uso de índice HNSW, se houver; sem índice a busca já é exata "
                            "(SEMANTICA_BUSCA_EXATA=1)")
    busca.add_argument("--ef-search", type=int, default=_numero_opcional(_ambiente("SEMANTICA_EF_SEARCH"), int),
                       help="hnsw.ef_search, só com índice HNSW; padrão max(40, top_k) (SEMANTICA_EF_SEARCH)")
    busca.add_argument("--incluir-catmat-inativo", action="store_true",
                       help="sincroniza também itens CATMAT inativos")

    revisao = analisador.add_argument_group("revisar")
    revisao.add_argument("--material", help="identificador_material (prata.material)")
    revisao.add_argument("--codigo", help="codigo_item do CATMAT")
    revisao.add_argument("--decisao", choices=correspondencia.DECISOES)
    revisao.add_argument("--revisor", help="nome de quem revisou")
    revisao.add_argument("--observacao")

    analisador.add_argument("--saida", default="dados/semantica/fila_revisao.csv",
                            help="arquivo CSV da etapa fila")
    args = analisador.parse_args(argv)
    if args.etapa == "revisar" and not all((args.material, args.codigo, args.decisao, args.revisor)):
        analisador.error("revisar exige --material, --codigo, --decisao e --revisor")
    return args


def main(argv: list[str] | None = None) -> int:
    args = _argumentos(argv)
    try:
        with psycopg.connect(
            host=os.environ["HOST_DO_BANCO"],
            port=int(os.environ["PORTA_DO_BANCO"]),
            dbname=os.environ["NOME_DO_BANCO"],
            user=os.environ["USUARIO_DO_BANCO"],
            password=os.environ["SENHA_DO_BANCO"],
            autocommit=True,
        ) as conn:
            if args.etapa in ("sincronizar", "tudo"):
                _sincronizar(conn, args)
            id_modelo = None
            if args.etapa in ("embeddings", "tudo"):
                id_modelo = _embeddings(conn, args, _codificador(args))
            if args.etapa in ("corresponder", "tudo"):
                _corresponder(conn, args, id_modelo or _id_modelo_registrado(conn, args))
            if args.etapa == "revisar":
                _revisar(conn, args)
            if args.etapa == "fila":
                _fila(conn, args)
    except (ErroOrigem, ErroEmbedding, fontes.ErroFonte,
            correspondencia.ErroCorrespondencia, ValueError) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        if erro.__cause__ is not None:
            print(f"  causa: {erro.__cause__!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
