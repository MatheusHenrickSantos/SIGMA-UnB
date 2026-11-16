#!/usr/bin/env python3
"""Baixa as compras públicas dos itens CATMAT aprovados e salva um JSON por código.

Fonte: API de pesquisa de preços do Compras.gov.br
(modulo-pesquisa-preco/1_consultarMaterial?tipo=codigoItemCatalogo&codigo=...).

Códigos consultados: os itens CATMAT aprovados como equivalentes a algum
material do estoque (semantica.v_item_aprovado, decisões de pessoas ou de
agentes), ou a lista passada em --codigos.

Saída: dados/compras/compras-<codigo>-<inicio>_<fim>.json, com a lista de
registros da API (todas as páginas, sem alteração). A camada raw carrega
esses arquivos com InserirDadosNaCamadaRaw.inserir_compras. Código sem
compra na janela não gera arquivo.

O que se sabe da API (verificado na API real e no swagger /v3/api-docs):

- filtra por data no servidor (dataCompraInicio/dataCompraFim, AAAA-MM-DD,
  inclusivos), por isso só a janela é baixada;
- pagina com pagina (a partir de 1) e tamanhoPagina (10 a 500); a resposta
  traz totalRegistros e totalPaginas;
- os resultados NÃO vêm ordenados por data;
- a chave de um registro é idItemCompra: (idCompra, codigoItemCatalogo) se
  repete quando a compra tem vários itens do mesmo código ou fornecedores
  diferentes no mesmo item;
- item sem compras devolve {"resultado": [], "totalRegistros": 0, ...}.

Cada página é guardada em dados/compras_cache/<inicio>_<fim>/<codigo>/: uma
nova execução reaproveita o que já foi baixado e continua de onde parou.

Uso (a partir da raiz do repositório):
    python codigos/inserir/baixar_compras.py
    python codigos/inserir/baixar_compras.py --codigos 463583,463576 --inicio 2025-01-01
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

import requests

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))

URL_API = "https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial"
TAMANHO_PAGINA = 500
TENTATIVAS = 8

SQL_CODIGOS = """
    SELECT DISTINCT codigo_item::bigint
    FROM semantica.v_item_aprovado
    ORDER BY 1
"""


def criar_sessao() -> requests.Session:
    sessao = requests.Session()
    sessao.headers.update(
        {"Accept": "application/json", "User-Agent": "pipeline-academico-compras/1.0"}
    )
    return sessao


def solicitar_pagina(
    sessao: requests.Session, codigo: int, pagina: int, inicio: date, fim: date, pausa: float
) -> dict[str, Any]:
    """Uma página da API, com novas tentativas e espera crescente."""
    parametros = {
        "tipo": "codigoItemCatalogo",
        "codigo": codigo,
        "pagina": pagina,
        "tamanhoPagina": TAMANHO_PAGINA,
        "dataCompraInicio": inicio.isoformat(),
        "dataCompraFim": fim.isoformat(),
    }
    ultimo_erro: Exception | None = None
    for tentativa in range(TENTATIVAS):
        try:
            if pausa:
                time.sleep(pausa)
            resposta = sessao.get(URL_API, params=parametros, timeout=(15, 90))
            resposta.raise_for_status()
            corpo = resposta.json()
            if not isinstance(corpo, dict) or not isinstance(corpo.get("resultado"), list):
                raise ValueError("resposta sem a lista 'resultado'")
            return corpo
        except Exception as exc:  # noqa: BLE001 - qualquer falha de rede ou de formato é refeita
            ultimo_erro = exc
            print(f"  código {codigo}, página {pagina}: tentativa {tentativa + 1}/{TENTATIVAS} "
                  f"falhou: {exc}", file=sys.stderr)
            # A API passa a devolver 400 numa conexão keep-alive antiga, enquanto
            # uma conexão nova responde normalmente: descarta as conexões abertas.
            sessao.close()
            if tentativa < TENTATIVAS - 1:
                time.sleep(min(5 * 2**tentativa, 120))
    raise RuntimeError(f"código {codigo}, página {pagina}: {ultimo_erro}")


def pagina_do_cache_ou_api(
    sessao, codigo: int, pagina: int, pasta_cache: Path, inicio: date, fim: date, pausa: float
) -> tuple[dict[str, Any], bool]:
    """Devolve (corpo, veio_da_api)."""
    caminho = pasta_cache / str(codigo) / f"pagina_{pagina:05d}.json"
    if caminho.exists():
        try:
            corpo = json.loads(caminho.read_text(encoding="utf-8"))
            if isinstance(corpo, dict) and isinstance(corpo.get("resultado"), list):
                return corpo, False
        except ValueError:
            pass  # cache corrompido: baixa de novo
    corpo = solicitar_pagina(sessao, codigo, pagina, inicio, fim, pausa)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    temporario.write_text(json.dumps(corpo, ensure_ascii=False), encoding="utf-8")
    temporario.replace(caminho)
    return corpo, True


def baixar_codigo(
    sessao, codigo: int, pasta_cache: Path, inicio: date, fim: date, pausa: float, max_paginas: int
) -> tuple[list[dict[str, Any]], int, bool]:
    """Todos os registros de um código na janela. Devolve (registros, requisições, parcial)."""
    registros: list[dict[str, Any]] = []
    requisicoes = 0
    pagina, total_paginas = 1, 1
    while pagina <= total_paginas:
        if pagina > max_paginas:
            return registros, requisicoes, True
        corpo, da_api = pagina_do_cache_ou_api(sessao, codigo, pagina, pasta_cache, inicio, fim, pausa)
        requisicoes += da_api
        total_paginas = max(int(corpo.get("totalPaginas") or 1), 1)
        registros.extend(r for r in corpo["resultado"] if isinstance(r, dict))
        pagina += 1
    return registros, requisicoes, False


def codigos_aprovados() -> list[int]:
    from codigos.banco_de_dados.conectar_com_banco_de_dados import conectar

    with conectar() as conexao:
        existe = conexao.execute("SELECT to_regclass('semantica.v_item_aprovado')").fetchone()[0]
        if existe is None:
            raise RuntimeError("semantica.v_item_aprovado não existe: aplique as migrações (V5)")
        return [linha[0] for linha in conexao.execute(SQL_CODIGOS)]


def formatar_tempo(segundos: float) -> str:
    segundos = int(segundos)
    return f"{segundos // 3600}h{segundos % 3600 // 60:02d}m{segundos % 60:02d}s"


def executar() -> int:
    analisador = argparse.ArgumentParser(description=__doc__,
                                         formatter_class=argparse.RawDescriptionHelpFormatter)
    analisador.add_argument("--codigos", default="",
                            help="códigos CATMAT separados por vírgula (sem isso, lê do banco)")
    analisador.add_argument("--inicio", default="2025-07-01", help="início da janela (AAAA-MM-DD)")
    analisador.add_argument("--fim", default="2025-12-31", help="fim da janela (AAAA-MM-DD)")
    analisador.add_argument("--pausa", type=float, default=0.3,
                            help="pausa antes de cada requisição, em segundos (padrão 0,3)")
    analisador.add_argument("--max-paginas-por-codigo", type=int, default=40,
                            help="limite de páginas por código (padrão 40 = 20 mil registros)")
    analisador.add_argument("--saida", default=str(RAIZ / "dados" / "compras"),
                            help="pasta dos JSON (padrão dados/compras)")
    analisador.add_argument("--estrito", action="store_true",
                            help="sai com erro se algum código falhar (padrão: só avisa)")
    args = analisador.parse_args()

    inicio, fim = date.fromisoformat(args.inicio), date.fromisoformat(args.fim)
    if inicio > fim:
        analisador.error("--inicio depois de --fim")
    codigos = ([int(c) for c in args.codigos.split(",") if c.strip()] if args.codigos
               else codigos_aprovados())
    if not codigos:
        print("[compras] nenhum item CATMAT aprovado: nada a baixar "
              "(importe ou registre decisões em semantica antes).")
        return 0

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    pasta_cache = RAIZ / "dados" / "compras_cache" / f"{inicio}_{fim}"
    print(f"[compras] {len(codigos)} código(s), janela {inicio} a {fim}; cache em {pasta_cache}")

    sessao = criar_sessao()
    comeco = time.monotonic()
    com_compra = registros_total = requisicoes_total = 0
    erros: list[int] = []
    parciais: list[int] = []
    for i, codigo in enumerate(codigos, start=1):
        try:
            registros, requisicoes, parcial = baixar_codigo(
                sessao, codigo, pasta_cache, inicio, fim, args.pausa, args.max_paginas_por_codigo
            )
        except Exception as exc:  # noqa: BLE001 - um código com problema não para os outros
            erros.append(codigo)
            print(f"  [{i}/{len(codigos)}] {codigo}: ERRO {exc}", file=sys.stderr)
            continue
        requisicoes_total += requisicoes
        if parcial:
            parciais.append(codigo)
        if registros:
            com_compra += 1
            registros_total += len(registros)
            destino = saida / f"compras-{codigo}-{inicio}_{fim}.json"
            destino.write_text(json.dumps(registros, ensure_ascii=False), encoding="utf-8")
        if i % 100 == 0 or i == len(codigos):
            decorrido = time.monotonic() - comeco
            print(f"  [{i}/{len(codigos)}] {com_compra} com compra, {registros_total} registros, "
                  f"{requisicoes_total} requisições; {formatar_tempo(decorrido)} "
                  f"(faltam ~{formatar_tempo(decorrido / i * (len(codigos) - i))})")

    print(f"[compras] {com_compra} de {len(codigos)} código(s) com compra na janela; "
          f"{registros_total} registros; {requisicoes_total} requisições à API; "
          f"{formatar_tempo(time.monotonic() - comeco)}")
    if parciais:
        print(f"[compras] AVISO: parou no limite de {args.max_paginas_por_codigo} páginas: "
              f"{', '.join(map(str, parciais))}")
    if erros:
        print(f"[compras] AVISO: {len(erros)} código(s) com erro (rode de novo para tentar outra vez): "
              f"{', '.join(map(str, erros))}")
        if args.estrito:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(executar())
