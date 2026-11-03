import os
import requests

# 1. URL da API do CKAN para o dataset do almoxarifado da UnB
dataset_id = "estoque-do-almoxarifado"
api_url = f"https://dados.unb.br/api/3/action/package_show?id={dataset_id}"

# Pasta onde os arquivos JSON serão salvos
pasta_destino = "../dados/almoxarifado"
os.makedirs(pasta_destino, exist_ok=True)

print(f"Buscando recursos no portal de dados abertos da UnB...")

try:
    # 2. Requisição para a API
    response = requests.get(api_url, timeout=30)
    response.raise_for_status()
    data = response.json()

    # 3. Filtrar e baixar os recursos em CSV
    recursos = data.get("result", {}).get("resources", [])

    downloads_realizados = 0
    for recurso in recursos:
        formato = (recurso.get("format") or "").upper()
        url_download = recurso.get("url")
        nome_arquivo = (recurso.get("name") or "recurso").strip()

        # Verifica se o recurso é CSV ou se a URL termina com .csv
        url_base = url_download.lower().split("?")[0] if url_download else ""
        if formato == "CSV" or url_base.endswith(".csv"):
            nome_limpo = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in nome_arquivo)
            caminho_arquivo = os.path.join(pasta_destino, f"{nome_limpo}.csv")

            print(f"Baixando: {nome_arquivo}...")

            res_file = requests.get(url_download, timeout=30)
            res_file.raise_for_status()

            with open(caminho_arquivo, "w", encoding="utf-8", newline="") as f:
                f.write(res_file.text)

            downloads_realizados += 1
            print(f"Salvo em: {caminho_arquivo}")

    print(f"\nConcluído! Total de {downloads_realizados} arquivos CSV baixados na pasta '{pasta_destino}'.")

except Exception as e:
    print(f"Ocorreu um erro ao buscar os dados: {e}")