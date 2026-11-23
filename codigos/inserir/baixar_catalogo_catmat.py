#!/usr/bin/env python3
"""Baixa o catálogo CATMAT e grava o JSON diretamente em raw.catmat."""
from __future__ import annotations

import argparse
import sys
import time
from typing import Any

import requests

from codigos.banco_de_dados.gravar_fontes_raw import salvar_catmat, serializar_json

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


def baixar_catalogo(
    tamanho_pagina: int,
    pausa: float,
    max_paginas: int | None,
) -> list[dict[str, Any]]:
    sessao = requests.Session()
    sessao.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "pipeline-academico-catmat/1.0",
        }
    )
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
    for pagina in range(1, paginas_a_baixar + 1):
        if pagina == 1:
            corpo = primeira
        else:
            corpo = solicitar_pagina(sessao, pagina, tamanho_pagina, pausa)

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

    return linhas


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
    argumentos = parser.parse_args()

    if not 10 <= argumentos.tamanho_pagina <= 500:
        parser.error("--tamanho-pagina deve estar entre 10 e 500.")
    if argumentos.max_paginas is not None and argumentos.max_paginas < 1:
        parser.error("--max-paginas deve ser maior que zero.")

    try:
        catalogo = baixar_catalogo(
            argumentos.tamanho_pagina,
            argumentos.pausa,
            argumentos.max_paginas,
        )
    except KeyboardInterrupt:
        print(
            "\nInterrupção solicitada. O catálogo não foi gravado; execute novamente para baixá-lo.",
            file=sys.stderr,
        )
        return 130

    conteudo = serializar_json(catalogo, indent=2)
    inserido = salvar_catmat(catalogo, conteudo)
    situacao = "gravado" if inserido else "já estava no banco"
    print(f"Catálogo CATMAT com {len(catalogo)} códigos {situacao} em raw.catmat.")
    return 0


if __name__ == "__main__":
    raise SystemExit(executar())
