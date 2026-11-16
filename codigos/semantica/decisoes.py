"""Importação de decisões de correspondência em lote (arquivo CSV).

Uso típico: carregar as decisões sugeridas por agentes de IA, ou um lote
revisado pela squad numa planilha, sem chamar `revisar` par a par.

Formato (CSV com cabeçalho, separador ';', UTF-8 com ou sem BOM):

    material ; codigos_equivalentes ; sem_correspondente ; confianca ; justificativa [; revisor]

- material: o texto do material exatamente como está em prata.material
  (descricao_normalizada), que é o texto_original de semantica.descricao;
- codigos_equivalentes: códigos CATMAT separados por '|' (vazio quando
  sem_correspondente = 'sim');
- sem_correspondente: 'sim' ou 'nao';
- confianca: 'alta', 'media' ou 'baixa';
- revisor (opcional): quem decidiu; sem a coluna, vale --revisor.

Regras:

- cada material do arquivo substitui o conjunto de itens equivalentes e a
  decisão por material registrados antes, numa transação só, então importar
  o mesmo arquivo de novo não duplica nada; pares marcados como
  'nao_equivalente' ou 'incerto' (revisão par a par) são mantidos;
- decisão de agente nunca sobrescreve decisão de pessoa: material já
  decidido por pessoa é ignorado, e par já revisado por pessoa fica como
  está; decisão de pessoa sobrescreve a de agente;
- material que não está em semantica.descricao (rode `sincronizar` antes) ou
  código que não é item CATMAT ativo: a linha é recusada e listada no resumo.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

import psycopg

from . import repositorio

TIPOS_REVISOR = ("pessoa", "agente")
CONFIANCAS = ("alta", "media", "baixa")


@dataclass(frozen=True)
class Decisao:
    material: str
    codigos: tuple[str, ...]
    sem_correspondente: bool
    confianca: str
    justificativa: str | None
    revisor: str | None


@dataclass
class ResumoImportacao:
    materiais: int = 0
    sem_correspondente: int = 0
    pares_equivalentes: int = 0
    preservadas_de_pessoa: int = 0
    recusadas: list[str] = field(default_factory=list)


def ler_arquivo(caminho: str | Path) -> list[dict[str, str]]:
    texto = Path(caminho).read_text(encoding="utf-8-sig")
    return list(csv.DictReader(texto.splitlines(), delimiter=";"))


def interpretar(registro: Mapping[str, str | None]) -> tuple[Decisao | None, str | None]:
    """Valida uma linha do arquivo. Devolve (decisão, None) ou (None, motivo)."""
    material = (registro.get("material") or "").strip()
    sem = (registro.get("sem_correspondente") or "").strip().lower().replace("ã", "a")
    confianca = (registro.get("confianca") or "").strip().lower().replace("é", "e")
    codigos_texto = (registro.get("codigos_equivalentes") or "").strip()
    if not material:
        return None, "material vazio"
    if sem not in ("sim", "nao"):
        return None, f"{material}: sem_correspondente deve ser sim ou nao ({sem!r})"
    if confianca not in CONFIANCAS:
        return None, f"{material}: confianca deve ser uma de {CONFIANCAS} ({confianca!r})"
    codigos_lidos = {c.strip() for c in codigos_texto.split("|") if c.strip()}
    if any(not c.isdigit() for c in codigos_lidos):
        return None, f"{material}: código não numérico em {codigos_texto!r}"
    codigos = tuple(sorted(codigos_lidos, key=int))
    if sem == "sim" and codigos:
        return None, f"{material}: sem_correspondente = sim, mas com códigos"
    if sem == "nao" and not codigos:
        return None, f"{material}: sem_correspondente = nao, mas sem códigos"
    return Decisao(
        material=material,
        codigos=codigos,
        sem_correspondente=sem == "sim",
        confianca=confianca,
        justificativa=(registro.get("justificativa") or "").strip() or None,
        revisor=(registro.get("revisor") or "").strip() or None,
    ), None


def importar(
    conn: psycopg.Connection,
    registros: Iterable[Mapping[str, str | None]],
    revisor_padrao: str,
    tipo_revisor: str,
) -> ResumoImportacao:
    """Grava as decisões numa transação só e devolve o resumo."""
    repositorio.exigir_autocommit(conn)
    if tipo_revisor not in TIPOS_REVISOR:
        raise ValueError(f"tipo_revisor deve ser um de {TIPOS_REVISOR}")
    if not revisor_padrao or not revisor_padrao.strip():
        raise ValueError("informe o revisor")

    resumo = ResumoImportacao()
    decisoes: dict[str, Decisao] = {}
    for registro in registros:
        decisao, erro = interpretar(registro)
        if erro:
            resumo.recusadas.append(erro)
        else:
            decisoes[decisao.material] = decisao  # a última linha do material vale

    with conn.transaction(), conn.cursor() as cur:
        materiais = {
            texto: hash_
            for texto, hash_ in cur.execute(
                "SELECT texto_original, hash_original FROM semantica.descricao "
                "WHERE origem = 'estoque' AND ativa AND texto_original IS NOT NULL"
            )
        }
        ativos = {
            chave for (chave,) in cur.execute(
                "SELECT chave_origem FROM semantica.descricao "
                "WHERE origem = 'catmat' AND ativa AND situacao = 'valida'"
            )
        }
        de_pessoa = {
            hash_ for (hash_,) in cur.execute(
                "SELECT hash_original_material FROM semantica.revisao_material "
                "WHERE tipo_revisor = 'pessoa'"
            )
        }

        for decisao in decisoes.values():
            hash_ = materiais.get(decisao.material)
            if hash_ is None:
                resumo.recusadas.append(f"{decisao.material}: material não encontrado (rode sincronizar)")
                continue
            invalidos = [c for c in decisao.codigos if c not in ativos]
            if invalidos:
                resumo.recusadas.append(
                    f"{decisao.material}: códigos inexistentes ou inativos no CATMAT {invalidos}"
                )
                continue
            revisor = decisao.revisor or revisor_padrao.strip()
            observacao = f"confiança {decisao.confianca}" + (
                f"; {decisao.justificativa}" if decisao.justificativa else ""
            )

            if tipo_revisor == "agente" and hash_ in de_pessoa:
                # material já decidido por pessoa: a sugestão do agente não entra
                resumo.preservadas_de_pessoa += 1
                continue

            # Substitui o conjunto de itens equivalentes do material: some o que
            # não está mais na lista. Agente só mexe nas linhas de agente; pessoa
            # também descarta as sugestões de agente. Pares 'nao_equivalente' e
            # 'incerto' (revisão par a par) são mantidos.
            cur.execute(
                """
                DELETE FROM semantica.revisao_correspondencia
                WHERE hash_original_material = %s AND decisao = 'equivalente'
                  AND (tipo_revisor = 'agente' OR %s = 'pessoa')
                  AND NOT (codigo_item = ANY(%s::text[]))
                """,
                (hash_, tipo_revisor, list(decisao.codigos)),
            )
            for codigo in decisao.codigos:
                cur.execute(
                    f"""
                    INSERT INTO semantica.revisao_correspondencia AS r
                        (hash_original_material, codigo_item, decisao, revisor, observacao,
                         texto_material, tipo_revisor)
                    VALUES (%s, %s, 'equivalente', %s, %s, %s, %s)
                    ON CONFLICT (hash_original_material, codigo_item) DO UPDATE SET
                        decisao = EXCLUDED.decisao, revisor = EXCLUDED.revisor,
                        observacao = EXCLUDED.observacao, tipo_revisor = EXCLUDED.tipo_revisor,
                        revisada_em = now()
                    {"WHERE r.tipo_revisor = 'agente'" if tipo_revisor == "agente" else ""}
                    """,
                    (hash_, codigo, revisor, observacao, decisao.material, tipo_revisor),
                )
                resumo.pares_equivalentes += cur.rowcount

            cur.execute(
                """
                INSERT INTO semantica.revisao_material
                    (hash_original_material, sem_correspondente, confianca, justificativa,
                     revisor, tipo_revisor, texto_material)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (hash_original_material) DO UPDATE SET
                    sem_correspondente = EXCLUDED.sem_correspondente,
                    confianca = EXCLUDED.confianca,
                    justificativa = EXCLUDED.justificativa,
                    revisor = EXCLUDED.revisor,
                    tipo_revisor = EXCLUDED.tipo_revisor,
                    texto_material = EXCLUDED.texto_material,
                    revisada_em = now()
                """,
                (hash_, decisao.sem_correspondente, decisao.confianca, decisao.justificativa,
                 revisor, tipo_revisor, decisao.material),
            )
            resumo.materiais += 1
            resumo.sem_correspondente += decisao.sem_correspondente

    return resumo
