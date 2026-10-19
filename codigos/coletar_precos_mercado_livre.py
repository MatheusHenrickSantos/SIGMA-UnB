import json
import os
import statistics
import time
import unicodedata
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

import psycopg
import requests

RAIZ_PROJETO = Path(__file__).resolve().parent.parent

PASTA_SAIDA = (
    RAIZ_PROJETO
    / "dados"
    / "coletas"
    / "mercado_livre"
)

SITE_ID = "MLB"
URL_BUSCA = f"https://api.mercadolibre.com/sites/{SITE_ID}/search"

LIMITE_RESULTADOS = 5
INTERVALO_SEGUNDOS = 1
TIMEOUT_SEGUNDOS = 30
MAX_RETENTATIVAS = 3

# Filtrar apenas produtos novos nas buscas?
APENAS_PRODUTOS_NOVOS = True

# Quantos materiais coletar por rodada (os de maior valor em estoque primeiro).
LIMITE_MATERIAIS = int(os.getenv("COLETA_LIMITE_MATERIAIS", "50"))


def carregar_materiais(conn):
    """
    Materiais com saldo no último mês de estoque, dos maiores valores para os
    menores, no formato que o coletor já usava. Só quem tem termo_busca entra.
    """
    linhas = conn.execute(
        """
        WITH ultimo AS (SELECT max(data_referencia) AS mes FROM estoque_saldo)
        SELECT m.id_material, m.descricao, m.termo_busca, a.nome,
               e.saldo, e.preco_unitario, e.valor_total, e.data_referencia
        FROM estoque_saldo e
        JOIN ultimo u ON e.data_referencia = u.mes
        JOIN material m USING (id_material)
        JOIN almoxarifado a USING (id_almoxarifado)
        WHERE e.saldo > 0 AND m.termo_busca IS NOT NULL AND btrim(m.termo_busca) <> ''
        ORDER BY e.valor_total DESC NULLS LAST, m.id_material
        LIMIT %s
        """,
        (LIMITE_MATERIAIS,),
    ).fetchall()
    return [
        {
            "id_material": r[0], "material": r[1], "termo_busca": r[2],
            "almoxarifado": r[3], "quantidade": str(r[4]),
            "preco_unitario": str(r[5]) if r[5] is not None else None,
            "valor_total_original": str(r[6]) if r[6] is not None else None,
            "mes": r[7].month, "ano": r[7].year,
        }
        for r in linhas
    ]


def titulo_relevante(titulo, termo_busca):
    """
    Descarta anúncio de outro produto: o título precisa conter ao menos 60% das
    palavras do termo de busca (ignora números soltos de 1 caractere).
    """
    palavras = [p for p in normalizar_texto(termo_busca).split() if len(p) > 1]
    if not palavras:
        return True
    titulo_norm = normalizar_texto(titulo or "")
    achadas = sum(1 for p in palavras if p in titulo_norm)
    return achadas / len(palavras) >= 0.6


def normalizar_texto(texto):
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join("".join(c if c.isalnum() else " " for c in sem_acento.lower()).split())


def gravar_cotacoes(conn, material, coleta):
    """Grava os anúncios no banco. Idempotente por (material, loja, url, semana)."""
    agora = datetime.now(timezone.utc)
    semana = (agora - timedelta(days=agora.weekday())).date()
    gravadas = 0
    for anuncio in coleta["anuncios"]:
        preco = converter_decimal(anuncio.get("preco"))
        if preco is None or preco <= 0 or not anuncio.get("url"):
            continue
        cur = conn.execute(
            "INSERT INTO cotacao_online (id_material, loja, titulo, preco, url, "
            "data_coleta, semana_coleta) VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (id_material, loja, url, semana_coleta) DO NOTHING",
            (material["id_material"], coleta["fonte"], anuncio.get("titulo"), preco,
             anuncio["url"], agora, semana),
        )
        gravadas += cur.rowcount
    return gravadas


def criar_sessao():
    sessao = requests.Session()
    sessao.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "SIGMA-UnB/1.0",
        }
    )

    token = os.getenv("MERCADO_LIVRE_ACCESS_TOKEN")
    if token:
        sessao.headers.update({"Authorization": f"Bearer {token}"})

    return sessao


def converter_decimal(valor):
    if valor is None:
        return None
    try:
        return Decimal(str(valor))
    except InvalidOperation:
        return None


def solicitar_busca_com_retry(sessao, termo_busca):
    parametros = {
        "q": termo_busca,
        "limit": LIMITE_RESULTADOS,
    }

    if APENAS_PRODUTOS_NOVOS:
        parametros["ITEM_CONDITION"] = "223028"  # Código ML para "Novo"

    tempo_espera = 2

    for tentativa in range(1, MAX_RETENTATIVAS + 1):
        try:
            resposta = sessao.get(
                URL_BUSCA,
                params=parametros,
                timeout=TIMEOUT_SEGUNDOS,
            )

            if resposta.status_code == 401:
                raise RuntimeError("Token de acesso inválido ou expirado (401).")

            if resposta.status_code == 403:
                raise RuntimeError("Acesso negado à API do Mercado Livre (403).")

            if resposta.status_code == 429:
                print(f"   [Rate Limit 429] Aguardando {tempo_espera}s antes de tentar novamente...")
                time.sleep(tempo_espera)
                tempo_espera *= 2
                continue

            resposta.raise_for_status()
            return resposta.json()

        except (requests.Timeout, requests.ConnectionError) as erro:
            if tentativa == MAX_RETENTATIVAS:
                raise erro
            print(f"   [Erro temporário] Tentativa {tentativa}/{MAX_RETENTATIVAS}. Aguardando {tempo_espera}s...")
            time.sleep(tempo_espera)
            tempo_espera *= 2

    raise RuntimeError("Excedido número máximo de retentativas para a requisição.")


def normalizar_resultado(anuncio, posicao):
    preco = converter_decimal(anuncio.get("price"))
    vendedor = anuncio.get("seller") or {}

    return {
        "posicao": posicao,
        "id_externo": anuncio.get("id"),
        "titulo": anuncio.get("title"),
        "preco": format(preco, ".2f") if preco is not None else None,
        "moeda": anuncio.get("currency_id"),
        "condicao": anuncio.get("condition"),
        "quantidade_disponivel": anuncio.get("available_quantity"),
        "id_vendedor": vendedor.get("id"),
        "url": anuncio.get("permalink"),
    }


def calcular_resumo(anuncios, preco_unitario_estoque=None):
    precos = [
        converter_decimal(a.get("preco"))
        for a in anuncios
        if converter_decimal(a.get("preco")) is not None and converter_decimal(a.get("preco")) > 0
    ]

    if not precos:
        return {
            "quantidade_resultados_validos": 0,
            "preco_minimo": None,
            "preco_medio": None,
            "preco_mediano": None,
            "preco_maximo": None,
            "variacao_mediana_vs_estoque_pct": None,
        }

    precos_float = [float(p) for p in precos]
    preco_mediano = Decimal(str(statistics.median(precos_float)))
    preco_medio = Decimal(str(statistics.mean(precos_float)))

    variacao_pct = None
    if preco_unitario_estoque is not None and preco_unitario_estoque > 0:
        variacao = ((preco_mediano - preco_unitario_estoque) / preco_unitario_estoque) * 100
        variacao_pct = format(variacao, ".2f")

    return {
        "quantidade_resultados_validos": len(precos),
        "preco_minimo": format(min(precos), ".2f"),
        "preco_medio": format(preco_medio, ".2f"),
        "preco_mediano": format(preco_mediano, ".2f"),
        "preco_maximo": format(max(precos), ".2f"),
        "variacao_mediana_vs_estoque_pct": variacao_pct,
    }


def coletar_material(sessao, material, numero, total, cache_buscas):
    descricao = str(material.get("material", "")).strip()
    termo_busca = str(material.get("termo_busca", "")).strip()
    preco_unitario_estoque = converter_decimal(material.get("preco_unitario"))

    print(f"[{numero}/{total}] Buscando: {termo_busca or descricao}")

    coleta = {
        "material": descricao,
        "termo_busca": termo_busca,
        "almoxarifado": material.get("almoxarifado"),
        "quantidade_estoque": material.get("quantidade"),
        "preco_unitario_estoque": material.get("preco_unitario"),
        "valor_total_estoque": material.get("valor_total_original"),
        "mes_estoque": material.get("mes"),
        "ano_estoque": material.get("ano"),
        "fonte": "Mercado Livre",
        "site_id": SITE_ID,
        "data_coleta": datetime.now(timezone.utc).isoformat(),
        "status": "pendente",
        "erro": None,
        "resumo": None,
        "anuncios": [],
    }

    if not termo_busca:
        coleta["status"] = "ignorado"
        coleta["erro"] = "Material sem termo de busca."
        return coleta

    # Aproveita busca idêntica se já tiver sido executada nesta mesma rodada
    if termo_busca in cache_buscas:
        print("   [Cache] Reutilizando resultado de busca anterior.")
        resultado_cached = cache_buscas[termo_busca]
        coleta["anuncios"] = resultado_cached["anuncios"]
        coleta["resumo"] = calcular_resumo(resultado_cached["anuncios"], preco_unitario_estoque)
        coleta["status"] = resultado_cached["status"]
        coleta["erro"] = resultado_cached["erro"]
        return coleta

    try:
        resposta = solicitar_busca_com_retry(sessao, termo_busca)
        resultados = resposta.get("results", [])

        anuncios = [
            normalizar_resultado(anuncio, posicao)
            for posicao, anuncio in enumerate(resultados, start=1)
        ]
        # descarta anúncios de outro produto (termo_busca confiável, RF-12)
        anuncios = [a for a in anuncios if titulo_relevante(a["titulo"], termo_busca)]

        coleta["anuncios"] = anuncios
        coleta["resumo"] = calcular_resumo(anuncios, preco_unitario_estoque)
        coleta["status"] = "sucesso" if anuncios else "sem_resultados"

        # Salva no cache da memória
        cache_buscas[termo_busca] = {
            "anuncios": anuncios,
            "status": coleta["status"],
            "erro": None,
        }

    except requests.Timeout:
        coleta["status"] = "erro"
        coleta["erro"] = "Tempo limite da requisição excedido."
    except requests.RequestException as erro:
        coleta["status"] = "erro"
        coleta["erro"] = f"Erro HTTP: {erro}"
    except (RuntimeError, ValueError) as erro:
        coleta["status"] = "erro"
        coleta["erro"] = str(erro)

    return coleta


def gerar_caminho_saida():
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    instante = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return PASTA_SAIDA / f"precos_mercado_livre_{instante}.json"


def salvar_resultados(resultados, caminho_saida):
    documento = {
        "fonte": "Mercado Livre",
        "site_id": SITE_ID,
        "data_inicio_coleta": resultados["data_inicio_coleta"],
        "data_fim_coleta": datetime.now(timezone.utc).isoformat(),
        "total_materiais": len(resultados["coletas"]),
        "coletas": resultados["coletas"],
    }

    with caminho_saida.open("w", encoding="utf-8") as arquivo:
        json.dump(documento, arquivo, ensure_ascii=False, indent=2)


def main():
    with psycopg.connect(autocommit=True) as conn:
        materiais = carregar_materiais(conn)
        total = len(materiais)

        if total == 0:
            print("Nenhum material encontrado.")
            return

        sessao = criar_sessao()
        caminho_saida = gerar_caminho_saida()
        cache_buscas = {}

        resultados = {
            "data_inicio_coleta": datetime.now(timezone.utc).isoformat(),
            "coletas": [],
        }
        gravadas = erros = 0

        for numero, material in enumerate(materiais, start=1):
            coleta = coletar_material(sessao, material, numero, total, cache_buscas)
            gravadas += gravar_cotacoes(conn, material, coleta)
            erros += coleta["status"] == "erro"

            resultados["coletas"].append(coleta)
            salvar_resultados(resultados, caminho_saida)

            if numero < total:
                time.sleep(INTERVALO_SEGUNDOS)

    print()
    print(f"Coleta concluída: {total} material(is), {gravadas} cotação(ões) nova(s) "
          f"no banco, {erros} com erro.")
    print(f"Arquivo gerado: {caminho_saida}")
    if erros == total:
        raise SystemExit("Todas as buscas falharam (token do Mercado Livre?).")


if __name__ == "__main__":
    main()
