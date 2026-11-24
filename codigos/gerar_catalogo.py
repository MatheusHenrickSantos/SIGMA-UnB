#!/usr/bin/env python3
"""Gera o catálogo de dados e a linhagem entre modelos a partir do manifesto do dbt.

    dbt parse --profiles-dir . --project-dir .     # cria target/manifest.json
    python codigos/gerar_catalogo.py                # escreve docs/governanca/catalogo-gerado.md

O manifesto é a fonte: se um modelo, uma coluna documentada ou uma dependência
mudar, rodar de novo atualiza a página. A linhagem de colunas do painel até a
fonte pública, que o dbt não registra, está escrita à mão em
docs/governanca/catalogo-e-linhagem.md.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CAMADAS = ["raw", "bronze", "prata", "semantica", "ouro", "reverso"]


def camada(no: dict) -> str:
    return no.get("schema") or "?"


def principais(manifesto: dict) -> dict[str, dict]:
    nos = {}
    for chave, no in manifesto["nodes"].items():
        if no["resource_type"] in ("model", "seed", "snapshot"):
            nos[chave] = no
    return nos


def gerar(manifesto: dict) -> str:
    nos = principais(manifesto)
    fontes = manifesto.get("sources", {})
    nome_de = {k: v["name"] for k, v in nos.items()} | {k: f"{v['source_name']}.{v['name']}" for k, v in fontes.items()}
    consumidores: dict[str, list[str]] = defaultdict(list)
    for chave, no in nos.items():
        for dep in no["depends_on"].get("nodes", []):
            if dep in nome_de:
                consumidores[dep].append(no["name"])

    linhas = [
        "# Catálogo de dados (gerado)",
        "",
        "> Gerado por `codigos/gerar_catalogo.py` a partir do manifesto do dbt. **Não edite à mão**: "
        "mude a descrição no `.yml` do modelo e gere de novo.",
        "",
        f"Modelos, sementes e snapshots: **{len(nos)}**. Fontes (tabelas escritas fora do dbt): **{len(fontes)}**.",
        "",
    ]
    por_camada: dict[str, list[dict]] = defaultdict(list)
    for no in nos.values():
        por_camada[camada(no)].append(no)
    for c in CAMADAS + sorted(set(por_camada) - set(CAMADAS)):
        if c not in por_camada:
            continue
        linhas += [f"## Camada `{c}`", ""]
        linhas += ["| Objeto | Tipo | Descrição | Colunas documentadas | Lê de | Lido por |", "|---|---|---|:-:|---|---|"]
        for no in sorted(por_camada[c], key=lambda n: n["name"]):
            deps = [nome_de[d] for d in no["depends_on"].get("nodes", []) if d in nome_de]
            usado = sorted(set(consumidores.get(no["unique_id"], [])))
            descricao = " ".join((no.get("description") or "—").split())
            linhas.append(
                f"| `{no['name']}` | {no['resource_type']} | {descricao[:220]}{'…' if len(descricao) > 220 else ''} "
                f"| {len([col for col in no['columns'].values() if col.get('description')])} "
                f"| {', '.join(f'`{d}`' for d in deps) or '—'} | {', '.join(f'`{u}`' for u in usado) or '—'} |"
            )
        linhas.append("")
    linhas += ["## Fontes escritas fora do dbt", "", "| Fonte | Descrição |", "|---|---|"]
    for no in sorted(fontes.values(), key=lambda n: (n["source_name"], n["name"])):
        linhas.append(f"| `{no['source_name']}.{no['name']}` | {' '.join((no.get('description') or '—').split())[:200]} |")
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    manifesto = RAIZ / "target" / "manifest.json"
    if not manifesto.exists():
        sys.exit("target/manifest.json não existe: rode `dbt parse` antes.")
    saida = RAIZ / "docs" / "governanca" / "catalogo-gerado.md"
    saida.write_text(gerar(json.loads(manifesto.read_text(encoding="utf-8"))), encoding="utf-8")
    print(f"escrito {saida}")
