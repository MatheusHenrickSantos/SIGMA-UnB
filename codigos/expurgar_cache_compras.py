"""Expurgo de arquivos antigos de compras: `python codigos/expurgar_cache_compras.py PASTA [PASTA...]`.

Remove niFornecedor e nomeFornecedor (mesma minimização da migração V12) dos JSON que
o pipeline anterior gravava em disco: `dados/compras_cache/**/pagina_*.json` (objeto com
a lista em "resultado") e `dados/compras/compras-*.json` (lista de registros). O
pipeline atual grava direto em raw.compras e não cria esses arquivos (ADR 0009); o
script serve para cópias que ainda existam em disco. Idempotente.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

CAMPOS = ("niFornecedor", "nomeFornecedor")


def registros(dados) -> list[dict]:
    """Os registros de compra de um JSON, nos dois formatos conhecidos."""
    if isinstance(dados, list):
        return [r for r in dados if isinstance(r, dict)]
    if isinstance(dados, dict) and isinstance(dados.get("resultado"), list):
        return [r for r in dados["resultado"] if isinstance(r, dict)]
    return []


def expurgar(raiz: Path) -> dict[str, int]:
    total = dict(arquivos=0, alterados=0, itens=0, com_cpf=0, ignorados=0)
    for arquivo in sorted(raiz.rglob("*.json")):
        total["arquivos"] += 1
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        itens = registros(dados)
        if not itens and dados not in ([], {}) and not isinstance(dados, (list, dict)):
            total["ignorados"] += 1
        mudou = False
        for item in itens:
            total["itens"] += 1
            numero = re.sub(r"\D", "", str(item.get("niFornecedor") or ""))
            total["com_cpf"] += len(numero) == 11
            for campo in CAMPOS:
                if campo in item:
                    del item[campo]
                    mudou = True
        if mudou:
            tmp = arquivo.with_suffix(".tmp")
            tmp.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, arquivo)
            total["alterados"] += 1
    return total


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    for pasta in sys.argv[1:]:
        print(pasta, expurgar(Path(pasta)))
