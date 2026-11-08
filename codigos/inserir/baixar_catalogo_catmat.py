#!/usr/bin/env python3
"""Baixa o catálogo CATMAT pela API oficial.

Uso:
  python baixar_catalogo_catmat.py --saida dados/catmat

Este script só coleta o catálogo e salva o JSON em disco. A etapa de
correspondência entre material do estoque e CATMAT fica em outro script,
para manter uma separação clara entre download e classificação.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import requests

URL_API = "https://dadosabertos.compras.gov.br/modulo-material/4_consultarItemMaterial"
TAMANHO_PADRAO_PAGINA = 500


def solicitar_pagina(
    sessao: requests.Session,
    pagina: int,
    tamanho_pagina: int,
    pausa: float,
) -> dict[str, Any]:
    ultimo_erro: Exception | None = None
    for tentativa in range(5):
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
                f"Página {pagina}: tentativa {tentativa + 1}/5 falhou: {exc}",
                file=sys.stderr,
            )
            if tentativa < 4:
                time.sleep(min(2**tentativa, 20))
    raise RuntimeError(
        f"Não foi possível obter a página {pagina}: {ultimo_erro}"
    )


def baixar_catalogo(
    diretorio_cache: Path,
    tamanho_pagina: int,
    pausa: float,
    max_paginas: int | None,
) -> list[dict[str, Any]]:
    diretorio_cache.mkdir(parents=True, exist_ok=True)
    sessao = requests.Session()
    sessao.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "pipeline-academico-catmat/1.0",
        }
    )

    caminho_primeira = diretorio_cache / "pagina_000001.json"
    if caminho_primeira.exists():
        try:
            primeira = json.loads(caminho_primeira.read_text(encoding="utf-8"))
            if not isinstance(primeira, dict) or not isinstance(
                primeira.get("resultado"), list
            ):
                raise ValueError("cache principal inválido")
        except Exception:
            primeira = solicitar_pagina(sessao, 1, tamanho_pagina, pausa)
            caminho_primeira.write_text(
                json.dumps(primeira, ensure_ascii=False),
                encoding="utf-8",
            )
    else:
        primeira = solicitar_pagina(sessao, 1, tamanho_pagina, pausa)
        caminho_primeira.write_text(
            json.dumps(primeira, ensure_ascii=False),
            encoding="utf-8",
        )

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
        caminho_pagina = diretorio_cache / f"pagina_{pagina:06d}.json"
        if pagina == 1:
            corpo = primeira
        elif caminho_pagina.exists():
            try:
                corpo = json.loads(caminho_pagina.read_text(encoding="utf-8"))
                if not isinstance(corpo, dict) or not isinstance(
                    corpo.get("resultado"), list
                ):
                    raise ValueError("cache inválido")
            except Exception:
                corpo = solicitar_pagina(
                    sessao, pagina, tamanho_pagina, pausa
                )
                caminho_pagina.write_text(
                    json.dumps(corpo, ensure_ascii=False),
                    encoding="utf-8",
                )
        else:
            corpo = solicitar_pagina(sessao, pagina, tamanho_pagina, pausa)
            caminho_pagina.write_text(
                json.dumps(corpo, ensure_ascii=False),
                encoding="utf-8",
            )

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
    raiz_projeto = Path(__file__).resolve().parents[1]
    saida_padrao = raiz_projeto / "dados" / "catmat"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--saida",
        default=str(saida_padrao),
        help="Diretório de saída (padrão: dados/catmat)",
    )
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

    diretorio_saida = Path(argumentos.saida)
    diretorio_saida.mkdir(parents=True, exist_ok=True)
    diretorio_cache = diretorio_saida / "cache_catmat_json"

    try:
        catalogo = baixar_catalogo(
            diretorio_cache,
            argumentos.tamanho_pagina,
            argumentos.pausa,
            argumentos.max_paginas,
        )
    except KeyboardInterrupt:
        print(
            "\nInterrupção solicitada pelo usuário. O cache parcial foi preservado e pode ser reutilizado "
            "na próxima execução deste mesmo comando.",
            file=sys.stderr,
        )
        return 130

    caminho_catalogo = diretorio_saida / "catalogo_catmat.json"
    caminho_catalogo.write_text(
        json.dumps(catalogo, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"Catálogo salvo com {len(catalogo)} códigos distintos: "
        f"{caminho_catalogo}"
    )
    print("A correspondência com materiais do estoque fica em outro script deste pipeline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(executar())
