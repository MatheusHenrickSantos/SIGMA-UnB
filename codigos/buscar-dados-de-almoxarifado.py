import os
import requests
import json

# 1. URL da API do CKAN para o dataset do almoxarifado da UnB
dataset_id = "estoque-do-almoxarifado"
api_url = f"https://dados.unb.br/api/3/action/package_show?id={dataset_id}"

# Pasta onde os arquivos JSON serão salvos
pasta_destino = "../dados/almoxarifado"
os.makedirs(pasta_destino, exist_ok=True)

print(f"Buscando recursos no portal de dados abertos da UnB...")

try:
    # 2. Requisição para a API
    response = requests.get(api_url)
    response.raise_for_status()
    data = response.json()

    # 3. Filtrar e baixar os recursos que são JSON
    recursos = data.get("result", {}).get("resources", [])
    
    downloads_realizados = 0
    for recurso in recursos:
        formato = recurso.get("format", "").upper()
        url_download = recurso.get("url")
        nome_arquivo = recurso.get("name", "recurso").strip()

        # Verifica se o recurso é do formato JSON ou se a URL termina com .json
        if formato == "JSON" or (url_download and url_download.lower().endswith(".json")):
            # Define o nome do arquivo local
            nome_limpo = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in nome_arquivo)
            caminho_arquivo = os.path.join(pasta_destino, f"{nome_limpo}.json")

            print(f"Baixando: {nome_arquivo}...")
            
            # Baixa o arquivo
            res_file = requests.get(url_download)
            json_data = res_file.json()

            with open(caminho_arquivo, "w", encoding="utf-8") as f:
                json.dump(json_data, f, ensure_ascii=False, indent=4)
            
            downloads_realizados += 1
            print(f"Salvo em: {caminho_arquivo}")

    print(f"\nConcluído! Total de {downloads_realizados} arquivos JSON baixados na pasta '{pasta_destino}'.")

except Exception as e:
    print(f"Ocorreu um erro ao buscar os dados: {e}")