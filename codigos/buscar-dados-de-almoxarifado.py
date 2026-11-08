import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

import requests

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
PASTA_DESTINO = RAIZ_PROJETO / "dados" / "estoque"
URL_API = "https://dados.unb.br/api/3/action/package_show"
DATASET_ID = "estoque-do-almoxarifado"
TIMEOUT_SEGUNDOS = 60
PADRAO_ARQUIVO = re.compile(
    r"estoque-do-almoxarifado-\d{2}-\d{4}\.json"
)


def selecionar_recursos_json(recursos: list[dict]) -> dict[str, dict]:
    """Seleciona a versão mais recente de cada recurso JSON mensal."""
    selecionados = {}

    for recurso in recursos:
        url = recurso.get("url") or ""
        nome_arquivo = unquote(Path(urlsplit(url).path).name)
        formato = (recurso.get("format") or "").strip().upper()

        if formato != "JSON" or not PADRAO_ARQUIVO.fullmatch(nome_arquivo):
            continue

        atual = selecionados.get(nome_arquivo)
        data_recurso = (
            recurso.get("last_modified") or recurso.get("created") or ""
        )
        data_atual = (
            atual.get("last_modified") or atual.get("created") or ""
            if atual
            else ""
        )

        if atual is None or data_recurso > data_atual:
            selecionados[nome_arquivo] = recurso

    return selecionados


def baixar_dados(pasta_destino: Path = PASTA_DESTINO) -> int:
    pasta_destino.mkdir(parents=True, exist_ok=True)

    resposta = requests.get(
        URL_API,
        params={"id": DATASET_ID},
        timeout=TIMEOUT_SEGUNDOS,
    )
    resposta.raise_for_status()
    pacote = resposta.json()

    if not pacote.get("success"):
        raise RuntimeError(
            f"Falha ao consultar o portal: {pacote.get('error')}"
        )

    recursos = pacote.get("result", {}).get("resources", [])
    selecionados = selecionar_recursos_json(recursos)
    if not selecionados:
        raise RuntimeError("O portal não retornou recursos JSON mensais.")

    for nome_arquivo, recurso in sorted(selecionados.items()):
        print(f"Baixando: {nome_arquivo}")
        resposta_arquivo = requests.get(
            recurso["url"],
            timeout=TIMEOUT_SEGUNDOS,
        )
        resposta_arquivo.raise_for_status()
        conteudo = resposta_arquivo.content.decode("utf-8-sig")
        json.loads(conteudo)

        destino = pasta_destino / nome_arquivo
        temporario = destino.with_suffix(destino.suffix + ".tmp")
        temporario.write_text(conteudo, encoding="utf-8")
        temporario.replace(destino)
        print(f"Salvo em: {destino}")

    print(
        f"Concluído: {len(selecionados)} arquivo(s) JSON salvo(s) "
        f"em '{pasta_destino}'."
    )
    return len(selecionados)


if __name__ == "__main__":
    baixar_dados()
