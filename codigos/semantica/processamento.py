"""Etapas do pipeline semântico: junta normalização, modelo e banco.

Cada função recebe o que precisa (conexão, codificador, registros) e
devolve um resumo; quem decide de onde vêm os registros e o que imprimir
é o ponto de entrada (python -m semantica).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable

import psycopg

from . import repositorio
from .embeddings import Codificador, ErroEmbedding, validar_vetores
from .normalizacao import DescricaoNormalizada, normalizar_descricao


@dataclass(frozen=True)
class ResumoEmbeddings:
    origem: str
    id_modelo: int
    reaproveitados: int
    pendentes: int
    gravados: int
    textos_enviados_ao_modelo: int
    textos_truncados: int
    lotes: int


def normalizar_registros(
    registros: Iterable[tuple[object, object]],
) -> tuple[list[tuple[str, DescricaoNormalizada]], int, int]:
    """Normaliza (chave, texto) da origem.

    Devolve as descrições, quantas linhas vieram sem chave (descartadas) e
    quantas chaves se repetiram (vale a última, na ordem da origem).
    """
    por_chave: dict[str, DescricaoNormalizada] = {}
    sem_chave = repetidas = 0
    for chave, texto in registros:
        chave_texto = "" if chave is None else str(chave).strip()
        if not chave_texto:
            sem_chave += 1
            continue
        if chave_texto in por_chave:
            repetidas += 1
        por_chave[chave_texto] = normalizar_descricao(texto)
    return list(por_chave.items()), sem_chave, repetidas


def sincronizar_origem(
    conn: psycopg.Connection, origem: str, registros: Iterable[tuple[object, object]]
) -> tuple[repositorio.ResumoSincronizacao, int, int]:
    """Normaliza e grava a fotografia atual de uma origem."""
    descricoes, sem_chave, repetidas = normalizar_registros(registros)
    resumo = repositorio.gravar_descricoes(conn, origem, descricoes)
    return resumo, sem_chave, repetidas


def preparar_modelo(conn: psycopg.Connection, codificador: Codificador) -> int:
    """Confere a dimensão contra a coluna do banco e registra o modelo."""
    dimensao_banco = repositorio.dimensao_da_coluna(conn)
    if codificador.dimensao != dimensao_banco:
        raise ErroEmbedding(
            f"o modelo {codificador.nome} gera vetores de {codificador.dimensao} dimensões, "
            f"mas semantica.embedding.vetor é vector({dimensao_banco}). "
            "Use um modelo dessa dimensão ou crie uma migração para o novo modelo."
        )
    return repositorio.registrar_modelo(
        conn,
        codificador.nome,
        codificador.revisao,
        codificador.dimensao,
        codificador.prefixos,
        codificador.metadados,
    )


def atualizar_embeddings(
    conn: psycopg.Connection,
    codificador: Codificador,
    id_modelo: int,
    origem: str,
    papel: str,
    tamanho_lote: int = 256,
) -> ResumoEmbeddings:
    """Gera vetores só para as descrições válidas que ainda não têm vetor atual.

    Cada lote é gravado na sua própria transação: se o modelo falhar no meio,
    os lotes anteriores ficam gravados e a próxima execução continua de onde
    parou. A falha é propagada (não é engolida).
    """
    if tamanho_lote < 1:
        raise ValueError("tamanho_lote deve ser >= 1")

    reaproveitados = repositorio.reaproveitar_vetores(conn, id_modelo, origem)
    pendentes = repositorio.descricoes_pendentes(conn, id_modelo, origem)

    # textos repetidos em lotes diferentes: guarda o vetor para não recalcular
    repeticoes = Counter(hash_ for _, _, hash_ in pendentes)
    guardados: dict[str, list[float]] = {}
    contar_truncados = getattr(codificador, "contar_truncados", None)

    enviados = truncados = lotes = 0
    for inicio in range(0, len(pendentes), tamanho_lote):
        lote = pendentes[inicio:inicio + tamanho_lote]
        lotes += 1

        textos_por_hash: dict[str, str] = {}
        for _, texto, hash_ in lote:
            if hash_ not in guardados:
                textos_por_hash.setdefault(hash_, texto)
        hashes = list(textos_por_hash)
        textos = [textos_por_hash[h] for h in hashes]

        if textos:
            try:
                vetores = codificador.codificar(textos, papel)
                validar_vetores(vetores, len(textos), codificador.dimensao)
            except Exception as erro:
                raise ErroEmbedding(
                    f"falha no lote {lotes} de {origem} ({len(textos)} textos); "
                    f"{inicio} descrições já gravadas nesta execução"
                ) from erro
            enviados += len(textos)
            if contar_truncados is not None:
                truncados += contar_truncados(textos, papel)
            calculados = dict(zip(hashes, vetores))
        else:
            calculados = {}

        linhas = []
        for id_descricao, _, hash_ in lote:
            vetor = guardados[hash_] if hash_ in guardados else calculados[hash_]
            linhas.append((id_descricao, hash_, vetor))
            if repeticoes[hash_] > 1:
                guardados[hash_] = vetor
        repositorio.gravar_vetores(conn, id_modelo, origem, linhas)

    return ResumoEmbeddings(
        origem=origem,
        id_modelo=id_modelo,
        reaproveitados=reaproveitados,
        pendentes=len(pendentes),
        gravados=len(pendentes),
        textos_enviados_ao_modelo=enviados,
        textos_truncados=truncados,
        lotes=lotes,
    )
