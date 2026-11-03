#!/usr/bin/env python3
"""Baixa o catálogo CATMAT pela API oficial.

Uso:
  python baixar_catmat_e_testar_amostra.py --saida dados/teste

Este script só coleta o catálogo e salva o CSV em disco. A etapa de
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

import pandas as pd
import requests

API_URL = "https://dadosabertos.compras.gov.br/modulo-material/4_consultarItemMaterial"
DEFAULT_PAGE_SIZE = 500


def request_page(session: requests.Session, page: int, page_size: int, pause: float) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            if pause and attempt == 0:
                time.sleep(pause)
            response = session.get(
                API_URL,
                params={"pagina": page, "tamanhoPagina": page_size},
                timeout=(10, 90),
            )
            response.raise_for_status()
            body = response.json()
            if not isinstance(body, dict) or not isinstance(body.get("resultado"), list):
                raise ValueError(f"Resposta inesperada na página {page}: faltou lista 'resultado'.")
            return body
        except Exception as exc:
            last_error = exc
            print(f"Página {page}: tentativa {attempt + 1}/5 falhou: {exc}", file=sys.stderr)
            if attempt < 4:
                time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"Não foi possível obter a página {page}: {last_error}")


def download_catalog(cache_dir: Path, page_size: int, pause: float, max_pages: int | None) -> pd.DataFrame:
    cache_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"Accept": "application/json", "User-Agent": "pipeline-academico-catmat/1.0"})

    first_path = cache_dir / "pagina_000001.json"
    if first_path.exists():
        first = json.loads(first_path.read_text(encoding="utf-8"))
    else:
        first = request_page(session, 1, page_size, pause)
        first_path.write_text(json.dumps(first, ensure_ascii=False), encoding="utf-8")

    try:
        total_pages = int(first.get("totalPaginas") or 1)
    except (TypeError, ValueError):
        total_pages = 1
    pages_to_get = min(total_pages, max_pages) if max_pages else total_pages
    print(f"API informa totalPaginas={total_pages}.")
    if max_pages and max_pages < total_pages:
        print(f"Modo parcial: baixando somente {pages_to_get} de {total_pages} páginas.")

    all_rows: list[dict[str, Any]] = []
    for page in range(1, pages_to_get + 1):
        page_path = cache_dir / f"pagina_{page:06d}.json"
        if page == 1:
            body = first
        elif page_path.exists():
            try:
                body = json.loads(page_path.read_text(encoding="utf-8"))
                if not isinstance(body, dict) or not isinstance(body.get("resultado"), list):
                    raise ValueError("cache inválido")
            except Exception:
                body = request_page(session, page, page_size, pause)
                page_path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        else:
            body = request_page(session, page, page_size, pause)
            page_path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")

        rows = body.get("resultado", [])
        all_rows.extend(row for row in rows if isinstance(row, dict))
        if page == 1 or page % 25 == 0 or page == pages_to_get:
            print(f"Página {page}/{pages_to_get}: {len(rows)} registros nesta página; {len(all_rows)} acumulados.")

    if not all_rows:
        raise RuntimeError("A API não retornou registros. Confira endpoint, acesso à rede e paginação.")

    catalog = pd.DataFrame(all_rows)
    if "codigoItem" in catalog.columns:
        catalog = catalog.drop_duplicates(subset=["codigoItem"], keep="last")
    return catalog


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    default_output = repo_root / "dados" / "teste"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", default=str(default_output), help="Diretório de saída (padrão: dados/teste)")
    parser.add_argument("--pausa", type=float, default=0.25, help="Pausa mínima entre requisições (segundos; padrão: 0.25)")
    parser.add_argument("--tamanho-pagina", type=int, default=DEFAULT_PAGE_SIZE, help="Máximo documentado: 500")
    parser.add_argument("--max-paginas", type=int, default=None, help="Opcional: limitar para teste; sem isso baixa todas as páginas")
    args = parser.parse_args()

    if not 10 <= args.tamanho_pagina <= 500:
        parser.error("--tamanho-pagina deve estar entre 10 e 500.")

    output_dir = Path(args.saida)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = output_dir / "cache_catmat_json"

    try:
        catalog = download_catalog(cache_dir, args.tamanho_pagina, args.pausa, args.max_paginas)
    except KeyboardInterrupt:
        print(
            "\nInterrupção solicitada pelo usuário. O cache parcial foi preservado e pode ser reutilizado "
            "na próxima execução deste mesmo comando.",
            file=sys.stderr,
        )
        return 130

    catalog_path = output_dir / "catalogo_catmat.csv"
    legacy_path = output_dir / "catalogo_catmat_baixado.csv"
    catalog.to_csv(catalog_path, index=False, encoding="utf-8-sig")
    catalog.to_csv(legacy_path, index=False, encoding="utf-8-sig")

    print(f"Catálogo salvo com {len(catalog)} códigos distintos: {catalog_path}")
    print(f"Também salvo em: {legacy_path}")
    print("A correspondência com materiais do estoque fica em outro script deste pipeline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
