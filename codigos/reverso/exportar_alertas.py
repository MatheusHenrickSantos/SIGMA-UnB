#!/usr/bin/env python3
"""ETL reverso, caminho em arquivo: exporta reverso.alerta_preco_compras para CSV.

Consumidor: o setor de compras abre (ou um processo seu lê) o arquivo antes da
próxima compra. O destino PUXA: este script só grava arquivos numa pasta; se o
destino estiver fora do ar nada se perde, porque a fonte da verdade continua
na tabela e a próxima execução regrava o mesmo arquivo.

Saída (dados/saida/):
  alertas_preco_AAAA-MM.csv     o mês de referência (nome estável: reexecutar sobrescreve)
  alertas_preco_atual.csv       cópia do mais recente, para quem lê sempre o mesmo caminho
  alertas_preco_AAAA-MM.json    manifesto: linhas, sha256, gerado_em, versão das métricas

A escrita é atômica (arquivo temporário + rename): o consumidor nunca lê um
arquivo pela metade. Conecta com o usuário do ambiente; em produção use um
usuário do grupo sigma_compras, que não enxerga a justificativa do agente.

Uso: python codigos/reverso/exportar_alertas.py [--saida dados/saida]
Sai com 1 se a tabela não existir (a etapa anterior não rodou).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg

RAIZ = Path(__file__).resolve().parents[2]

# colunas concedidas ao grupo sigma_compras (V11 + hook do modelo); a justificativa do agente fica de fora
COLUNAS = [
    "mes_referencia", "identificador_material", "material", "almoxarifado", "quantidade",
    "preco_estoque", "preco_publico_mediano", "diferenca_pct", "diferenca_absoluta",
    "economia_potencial", "compras_publicas", "unidade_fornecimento_predominante",
    "codigos_equivalentes", "tipo_revisor_correspondencia", "confianca_correspondencia",
    "acao_sugerida", "versao_definicao_metricas", "gerado_em",
]


def conectar() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ["HOST_DO_BANCO"], port=int(os.environ["PORTA_DO_BANCO"]),
        dbname=os.environ["NOME_DO_BANCO"], user=os.environ["USUARIO_DO_BANCO"],
        password=os.environ["SENHA_DO_BANCO"],
    )


def gravar_atomico(destino: Path, conteudo: bytes) -> None:
    temporario = destino.with_suffix(destino.suffix + ".tmp")
    temporario.write_bytes(conteudo)
    temporario.replace(destino)


def exportar(saida: Path) -> int:
    with conectar() as conn:
        if not conn.execute("SELECT to_regclass('reverso.alerta_preco_compras') IS NOT NULL").fetchone()[0]:
            print("ERRO: reverso.alerta_preco_compras não existe; rode o transformar_ouro.", file=sys.stderr)
            return 1
        linhas = conn.execute(
            f"SELECT {', '.join(COLUNAS)} FROM reverso.alerta_preco_compras "
            "ORDER BY economia_potencial DESC, identificador_material, almoxarifado"
        ).fetchall()

    meses = {str(linha[0])[:7] for linha in linhas}
    if len(meses) > 1:
        print(f"ERRO: a tabela mistura meses {sorted(meses)}", file=sys.stderr)
        return 1
    mes = meses.pop() if meses else datetime.now(timezone.utc).strftime("%Y-%m")

    import io
    buffer = io.StringIO(newline="")
    escritor = csv.writer(buffer, delimiter=";", lineterminator="\n")
    escritor.writerow(COLUNAS)
    escritor.writerows(linhas)
    conteudo = ("﻿" + buffer.getvalue()).encode("utf-8")  # BOM: abre certo no Excel

    saida.mkdir(parents=True, exist_ok=True)
    arquivo = saida / f"alertas_preco_{mes}.csv"
    gravar_atomico(arquivo, conteudo)
    gravar_atomico(saida / "alertas_preco_atual.csv", conteudo)
    versao = linhas[0][COLUNAS.index("versao_definicao_metricas")] if linhas else None
    manifesto = {
        "arquivo": arquivo.name, "mes_referencia": mes, "linhas": len(linhas),
        "sha256": hashlib.sha256(conteudo).hexdigest(), "versao_definicao_metricas": versao,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    gravar_atomico(saida / f"alertas_preco_{mes}.json",
                   json.dumps(manifesto, ensure_ascii=False, indent=2).encode("utf-8"))
    print(f"[exportar] {len(linhas)} alerta(s) de {mes} em {arquivo}")
    return 0


if __name__ == "__main__":
    analisador = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    analisador.add_argument("--saida", default=str(RAIZ / "dados" / "saida"))
    sys.exit(exportar(Path(analisador.parse_args().saida)))
