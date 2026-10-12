"""
Copia a camada bruta local (dados/bruto/) para a bronze do data lake, sem
nenhuma transformação: é o "L" do ELT.

Cada arquivo vai para bronze/portal/<dataset>/<sha256[:16]>/<arquivo>.
O caminho inclui o hash do conteúdo, então:
  * o mesmo conteúdo nunca é enviado duas vezes (rodar de novo é barato);
  * se o portal republicar um arquivo com o mesmo nome e conteúdo diferente,
    a versão antiga continua na bronze e a nova entra ao lado dela.

O manifesto da coleta (url, data no portal, sha256 de cada arquivo) vai
para bronze/portal/_manifestos/<coletado_em>.json.

Uso:
    python enviar_bruto.py
"""

import json
import sys
import time

from lake import BUCKET, PASTA_BRUTO, existe, garantir_bucket, sistema_arquivos, tamanho_mb

TAMANHO_BLOCO = 8 * 1_048_576


def enviar(s3, origem, destino):
    with origem.open("rb") as entrada, s3.open_output_stream(destino) as saida:
        for bloco in iter(lambda: entrada.read(TAMANHO_BLOCO), b""):
            saida.write(bloco)


def main():
    manifesto_local = PASTA_BRUTO / "manifesto.json"
    if not manifesto_local.exists():
        print(f"ERRO: {manifesto_local} não existe. Rode baixar_dados.py antes.")
        sys.exit(1)

    manifesto = json.loads(manifesto_local.read_text(encoding="utf-8"))
    s3 = sistema_arquivos()
    garantir_bucket(s3)

    inicio = time.perf_counter()
    enviados = pulados = 0
    bytes_enviados = 0

    for dataset, info in manifesto.get("datasets", {}).items():
        for arquivo in info.get("arquivos", []):
            origem = PASTA_BRUTO / arquivo["arquivo"]
            nome = origem.name
            destino = f"{BUCKET}/bronze/portal/{dataset}/{arquivo['sha256'][:16]}/{nome}"

            if existe(s3, destino):
                pulados += 1
                continue
            if not origem.exists():
                print(f"  AVISO: {origem} está no manifesto mas não existe no disco")
                continue

            enviar(s3, origem, destino)
            enviados += 1
            bytes_enviados += origem.stat().st_size
            print(f"  enviado: {dataset}/{nome} ({tamanho_mb(origem.stat().st_size)})")

    carimbo = manifesto.get("coletado_em", "sem-data").replace(":", "-")
    destino_manifesto = f"{BUCKET}/bronze/portal/_manifestos/{carimbo}.json"
    with s3.open_output_stream(destino_manifesto) as saida:
        saida.write(manifesto_local.read_bytes())

    print(
        f"\nbronze/portal: {enviados} arquivo(s) enviado(s) ({tamanho_mb(bytes_enviados)}), "
        f"{pulados} já existiam, em {time.perf_counter() - inicio:.1f} s"
    )


if __name__ == "__main__":
    main()
