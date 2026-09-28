"""
Baixa os datasets do portal de dados abertos da UnB (dados.unb.br) para a
camada bruta em dados/bruto/<dataset>/.

Os arquivos são gravados exatamente como vieram do portal, sem nenhuma
transformação. Isso permite reprocessar tudo depois se a carga mudar.

Ao final é gerado dados/bruto/manifesto.json com a origem de cada arquivo
(url, data de modificação no portal, tamanho e sha256).

Uso:
    python baixar_dados.py            # baixa só o que ainda não existe
    python baixar_dados.py --forcar   # baixa tudo de novo
"""

import hashlib
import json
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

import requests

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_BRUTO = RAIZ_PROJETO / "dados" / "bruto"
ARQUIVO_MANIFESTO = PASTA_BRUTO / "manifesto.json"

URL_API = "https://dados.unb.br/api/3/action"

TIMEOUT_SEGUNDOS = 60
MAX_TENTATIVAS = 5

# chave -> (id no portal, termos de busca, obrigatório?)
# Se o id deixar de existir, o dataset é procurado pelo package_search.
DATASETS = {
    "estoque": ("estoque-do-almoxarifado", ["estoque almoxarifado"], True),
    "unidades": ("unidades-academicas", ["unidades academicas"], True),
    "empenhos": ("empenhos", ["empenhos"], False),
    "gastos": ("gastos-por-unidade", ["gastos por unidade"], False),
    "requisicoes": ("requisicoes-de-servicos", ["requisicoes de servicos"], False),
}

FORMATOS_ACEITOS = ("JSON", "CSV")


def sem_acento(texto):
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


def get_com_tentativas(sessao, url, **kwargs):
    ultimo_erro = None

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        try:
            resposta = sessao.get(url, timeout=TIMEOUT_SEGUNDOS, **kwargs)
            resposta.raise_for_status()
            return resposta
        except requests.RequestException as erro:
            ultimo_erro = erro
            print(f"  tentativa {tentativa} falhou: {erro}")
            # o portal devolve 502 com frequência; espera cada vez mais
            time.sleep(5 * 2 ** (tentativa - 1))

    raise ultimo_erro


def chamar_api(sessao, acao, **params):
    resposta = get_com_tentativas(sessao, f"{URL_API}/{acao}", params=params)
    dados = resposta.json()

    if not dados.get("success"):
        raise RuntimeError(f"API respondeu sem sucesso em {acao}: {dados.get('error')}")

    return dados["result"]


def encontrar_dataset(sessao, id_conhecido, termos):
    if id_conhecido:
        try:
            return chamar_api(sessao, "package_show", id=id_conhecido)
        except (requests.HTTPError, RuntimeError) as erro:
            print(f"  package_show falhou ({erro}); procurando pelo nome")

    for termo in termos:
        resultado = chamar_api(sessao, "package_search", q=termo, rows=20)
        palavras = sem_acento(termo).split()

        for pacote in resultado.get("results", []):
            titulo = sem_acento(pacote.get("title", "") + " " + pacote.get("name", ""))
            if all(p in titulo for p in palavras):
                return pacote

    return None


def escolher_recursos(recursos):
    """
    Fica com os recursos JSON. Se o dataset não tiver nenhum JSON, usa os CSV.
    """
    def formato(recurso):
        fmt = (recurso.get("format") or "").upper().strip(".")
        url = (recurso.get("url") or "").lower()
        if not fmt:
            fmt = url.rsplit(".", 1)[-1].upper()
        return fmt

    por_formato = {fmt: [] for fmt in FORMATOS_ACEITOS}
    for recurso in recursos:
        fmt = formato(recurso)
        if fmt in por_formato and recurso.get("url"):
            por_formato[fmt].append((fmt, recurso))

    return por_formato["JSON"] or por_formato["CSV"]


def nome_arquivo(recurso, fmt, usados):
    """
    Usa o nome do arquivo na URL (ex.: empenhos-08-2021.json), que é mais
    confiável que o nome do recurso: o portal tem vários recursos com o mesmo
    nome. Se ainda assim repetir, acrescenta o começo do id do recurso.
    """
    base = unquote((recurso.get("url") or "").rstrip("/").rsplit("/", 1)[-1])
    base = base.rsplit(".", 1)[0] if "." in base else base
    if not base:
        base = recurso.get("name") or recurso.get("id") or "recurso"

    base = re.sub(r"[^a-z0-9_-]+", "_", sem_acento(base)).strip("_")
    nome = f"{base}.{fmt.lower()}"

    if nome in usados:
        nome = f"{base}_{(recurso.get('id') or '')[:8]}.{fmt.lower()}"
    usados.add(nome)
    return nome


def sha256(caminho):
    h = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def baixar_dataset(sessao, chave, pacote, forcar):
    pasta = PASTA_BRUTO / chave
    pasta.mkdir(parents=True, exist_ok=True)

    recursos = escolher_recursos(pacote.get("resources", []))
    arquivos = []
    falhas = []
    usados = set()

    for fmt, recurso in recursos:
        destino = pasta / nome_arquivo(recurso, fmt, usados)

        if destino.exists() and destino.stat().st_size > 0 and not forcar:
            print(f"  já existe: {destino.name}")
        else:
            print(f"  baixando: {destino.name}")
            try:
                resposta = get_com_tentativas(sessao, recurso["url"])

                if not resposta.content.strip():
                    raise RuntimeError("arquivo vazio")

                if fmt == "JSON":
                    # só confere se é JSON válido; o arquivo é gravado como veio
                    json.loads(resposta.content.decode("utf-8-sig"))
            except Exception as erro:
                # um arquivo com problema não impede os outros meses
                print(f"  FALHOU: {destino.name}: {erro}")
                falhas.append({"arquivo": destino.name, "url": recurso.get("url"),
                               "erro": str(erro)})
                continue

            temporario = destino.with_suffix(destino.suffix + ".tmp")
            temporario.write_bytes(resposta.content)
            temporario.replace(destino)

        arquivos.append(
            {
                "arquivo": str(destino.relative_to(PASTA_BRUTO)).replace("\\", "/"),
                "nome_no_portal": recurso.get("name"),
                "formato": fmt,
                "url": recurso.get("url"),
                "modificado_no_portal": recurso.get("last_modified") or recurso.get("created"),
                "bytes": destino.stat().st_size,
                "sha256": sha256(destino),
            }
        )

    return arquivos, falhas


def main():
    forcar = "--forcar" in sys.argv
    PASTA_BRUTO.mkdir(parents=True, exist_ok=True)

    sessao = requests.Session()
    sessao.headers.update({"User-Agent": "SIGMA-UnB/1.0 (projeto academico BD2)"})

    manifesto = {"coletado_em": datetime.now().astimezone().isoformat(), "datasets": {}}
    falhas_obrigatorias = []

    print("Buscando datasets no portal de dados abertos da UnB...")

    for chave, (id_conhecido, termos, obrigatorio) in DATASETS.items():
        print(f"\n[{chave}]")
        try:
            pacote = encontrar_dataset(sessao, id_conhecido, termos)
            if pacote is None:
                raise RuntimeError(f"nenhum dataset encontrado para {termos}")

            print(f"  dataset: {pacote['name']} ({pacote.get('title')})")
            arquivos, falhas = baixar_dataset(sessao, chave, pacote, forcar)

            manifesto["datasets"][chave] = {
                "id": pacote["name"],
                "titulo": pacote.get("title"),
                "arquivos": arquivos,
                "falhas": falhas,
            }
            print(f"  {len(arquivos)} arquivo(s), {len(falhas)} falha(s)")

            if not arquivos:
                raise RuntimeError("nenhum arquivo do dataset foi baixado")

        except Exception as erro:
            print(f"  ERRO: {erro}")
            if obrigatorio:
                falhas_obrigatorias.append(chave)

    ARQUIVO_MANIFESTO.write_text(
        json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nManifesto gravado em {ARQUIVO_MANIFESTO}")

    if falhas_obrigatorias:
        print(f"Falha nos datasets obrigatórios: {falhas_obrigatorias}")
        sys.exit(1)


if __name__ == "__main__":
    main()
