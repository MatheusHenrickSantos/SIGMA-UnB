#!/usr/bin/env python3
"""Baixa o catálogo CATMAT e grava o JSON diretamente em raw.catmat."""
from __future__ import annotations

import argparse
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests

from codigos.banco_de_dados.gravar_fontes_raw import (
    catmat_cache_vencido,
    catmat_em_cache,
    salvar_catmat,
    serializar_json,
)

URL_API = "https://dadosabertos.compras.gov.br/modulo-material/4_consultarItemMaterial"
TAMANHO_PADRAO_PAGINA = 500
# Depois de ~100 páginas na mesma conexão (keep-alive), a API passa a
# devolver 400 para qualquer página, enquanto uma conexão nova recebe 200.
# Por isso cada falha fecha as conexões da sessão antes de tentar de novo.
TENTATIVAS = 8


def solicitar_pagina(
    sessao: requests.Session,
    pagina: int,
    tamanho_pagina: int,
    pausa: float,
) -> dict[str, Any]:
    ultimo_erro: Exception | None = None
    for tentativa in range(TENTATIVAS):
        try:
            if pausa and tentativa == 0:
                time.sleep(pausa)
            resposta = sessao.get(
                URL_API,
                params={"pagina": pagina, "tamanhoPagina": tamanho_pagina},
                timeout=(10, 90),
            )
            resposta.raise_for_status()
            corpo = resposta.json()
            if not isinstance(corpo, dict) or not isinstance(corpo.get("resultado"), list):
                raise ValueError(
                    f"Resposta inesperada na página {pagina}: "
                    "faltou lista 'resultado'."
                )
            return corpo
        except Exception as exc:
            ultimo_erro = exc
            print(
                f"Página {pagina}: tentativa {tentativa + 1}/{TENTATIVAS} falhou: {exc}",
                file=sys.stderr,
            )
            sessao.close()  # a próxima tentativa abre uma conexão nova
            if tentativa < TENTATIVAS - 1:
                time.sleep(min(5 * 2**tentativa, 120))
    raise RuntimeError(
        f"Não foi possível obter a página {pagina}: {ultimo_erro}"
    )


def criar_sessao() -> requests.Session:
    sessao = requests.Session()
    sessao.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "pipeline-academico-catmat/1.0",
        }
    )
    return sessao


def baixar_paginas_em_paralelo(
    paginas: list[int], tamanho_pagina: int, pausa: float, trabalhadores: int
) -> dict[int, dict[str, Any]]:
    """Baixa as páginas com `trabalhadores` conexões independentes (uma sessão por página
    lida em sequência dentro de cada trabalhador, como no modo serial)."""
    if not paginas:
        return {}
    trabalhadores = max(1, min(trabalhadores, len(paginas)))
    # fatias intercaladas: cada trabalhador usa a sua própria sessão do início ao fim
    fatias = [paginas[i::trabalhadores] for i in range(trabalhadores)]
    feitas = 0

    def trabalhar(fatia: list[int]) -> dict[int, dict[str, Any]]:
        nonlocal feitas
        sessao = criar_sessao()
        saida: dict[int, dict[str, Any]] = {}
        for pagina in fatia:
            saida[pagina] = solicitar_pagina(sessao, pagina, tamanho_pagina, pausa)
            feitas += 1
            if feitas % 50 == 0:
                print(f"Páginas baixadas: {feitas}/{len(paginas)}")
        return saida

    resultado: dict[int, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=trabalhadores) as pool:
        for parcial in pool.map(trabalhar, fatias):
            resultado.update(parcial)
    return resultado


def baixar_catalogo(
    tamanho_pagina: int,
    pausa: float,
    max_paginas: int | None,
    trabalhadores: int = 1,
) -> tuple[list[dict[str, Any]], int, int]:
    sessao = criar_sessao()
    primeira = solicitar_pagina(sessao, 1, tamanho_pagina, pausa)

    try:
        total_paginas = int(primeira.get("totalPaginas") or 1)
    except (TypeError, ValueError):
        total_paginas = 1
    paginas_a_baixar = (
        min(total_paginas, max_paginas) if max_paginas else total_paginas
    )
    print(f"API informa totalPaginas={total_paginas}.")
    if max_paginas and max_paginas < total_paginas:
        print(
            "Modo parcial: baixando somente "
            f"{paginas_a_baixar} de {total_paginas} páginas."
        )

    linhas: list[dict[str, Any]] = []
    restantes = baixar_paginas_em_paralelo(
        list(range(2, paginas_a_baixar + 1)), tamanho_pagina, pausa, trabalhadores
    )
    for pagina in range(1, paginas_a_baixar + 1):
        corpo = primeira if pagina == 1 else restantes[pagina]

        linhas_pagina = corpo.get("resultado", [])
        linhas.extend(
            linha for linha in linhas_pagina if isinstance(linha, dict)
        )
        if (
            pagina == 1
            or pagina % 25 == 0
            or pagina == paginas_a_baixar
        ):
            print(
                f"Página {pagina}/{paginas_a_baixar}: "
                f"{len(linhas_pagina)} registros nesta página; "
                f"{len(linhas)} acumulados."
            )

    if not linhas:
        raise RuntimeError("A API não retornou registros. Confira endpoint, acesso à rede e paginação.")

    if any("codigoItem" in linha for linha in linhas):
        codigos_vistos = set()
        catalogo_reverso = []
        for linha in reversed(linhas):
            codigo = linha.get("codigoItem")
            if codigo not in codigos_vistos:
                codigos_vistos.add(codigo)
                catalogo_reverso.append(linha)
        linhas = list(reversed(catalogo_reverso))

    return linhas, total_paginas, paginas_a_baixar


def executar() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pausa",
        type=float,
        default=0.25,
        help="Pausa mínima entre requisições (segundos; padrão: 0.25)",
    )
    parser.add_argument(
        "--tamanho-pagina",
        type=int,
        default=TAMANHO_PADRAO_PAGINA,
        help="Máximo documentado: 500",
    )
    parser.add_argument(
        "--max-paginas",
        type=int,
        default=None,
        help="Opcional: limitar para teste; sem isso baixa todas as páginas",
    )
    parser.add_argument(
        "--atualizar",
        action="store_true",
        help="Ignorar o snapshot completo em raw e baixar o CATMAT novamente",
    )
    parser.add_argument(
        "--paralelismo",
        type=int,
        default=4,
        help="Conexões simultâneas para baixar as páginas (padrão: 4; 1 = em sequência)",
    )
    parser.add_argument(
        "--validade-dias",
        type=int,
        default=30,
        help="Idade máxima do snapshot em raw.catmat antes de baixar de novo (padrão: 30; 0 = nunca vence)",
    )
    argumentos = parser.parse_args()

    if argumentos.paralelismo < 1:
        parser.error("--paralelismo deve ser maior que zero.")
    if not 10 <= argumentos.tamanho_pagina <= 500:
        parser.error("--tamanho-pagina deve estar entre 10 e 500.")
    if argumentos.max_paginas is not None and argumentos.max_paginas < 1:
        parser.error("--max-paginas deve ser maior que zero.")

    if (
        catmat_em_cache()
        and not argumentos.atualizar
        and argumentos.max_paginas is None
        and not catmat_cache_vencido(argumentos.validade_dias)
    ):
        print(
            "CATMAT completo já está no cache do banco (raw.catmat) e dentro da validade "
            f"({argumentos.validade_dias} dias); download ignorado. Use --atualizar para forçar."
        )
        return 0

    try:
        catalogo, total_paginas, paginas_baixadas = baixar_catalogo(
            argumentos.tamanho_pagina,
            argumentos.pausa,
            argumentos.max_paginas,
            argumentos.paralelismo,
        )
    except KeyboardInterrupt:
        print(
            "\nInterrupção solicitada. O catálogo não foi gravado; execute novamente para baixá-lo.",
            file=sys.stderr,
        )
        return 130

    conteudo = serializar_json(catalogo, indent=2)
    completa = paginas_baixadas == total_paginas
    salvar_catmat(
        catalogo,
        conteudo,
        completa=completa,
        total_paginas=total_paginas,
    )
    situacao = "completo" if completa else "parcial"
    print(f"Catálogo CATMAT com {len(catalogo)} códigos gravado em raw.catmat ({situacao}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(executar())
