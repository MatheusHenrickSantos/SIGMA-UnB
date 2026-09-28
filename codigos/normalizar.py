import html
import json
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_ENTRADA = RAIZ_PROJETO / "dados" / "bruto" / "estoque"
PASTA_SAIDA = RAIZ_PROJETO / "dados" / "processados"
ARQUIVO_SAIDA = PASTA_SAIDA / "almoxarifado_normalizado.json"


def remover_acentos(texto):
    texto_normalizado = unicodedata.normalize("NFKD", texto)

    return "".join(
        caractere
        for caractere in texto_normalizado
        if not unicodedata.combining(caractere)
    )


def limpar_texto(valor):
    """
    Desfaz entidades HTML (&amp; -> &), junta espaços repetidos e tira os
    espaços das pontas. Mantém maiúsculas e acentos como vieram.
    """
    texto = html.unescape(str(valor))
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def gerar_termo_busca(material):
    """
    Converte a descrição original em um texto mais apropriado
    para buscas em lojas online.
    """
    texto = material.strip().lower()
    texto = remover_acentos(texto)

    # Separa números das unidades.
    texto = re.sub(
        r"(\d+(?:[.,]\d+)?)\s*(kg|g|gr|mg|l|ml|cm|mm|m)\b",
        r"\1 \2",
        texto,
    )

    # Remove pontuações que não ajudam na busca.
    texto = re.sub(r"[,;:/\\|]+", " ", texto)

    # Mantém letras, números, pontos, sinais e espaços.
    texto = re.sub(r"[^a-z0-9.\-+ ]", " ", texto)

    # Remove espaços repetidos.
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def converter_decimal(valor):
    """
    Converte valores como:
    'R$            12,00' -> Decimal('12.00')
    '1.234,56'            -> Decimal('1234.56')
    '1573.00'             -> Decimal('1573.00')
    """
    if valor is None:
        return None

    texto = str(valor).strip()

    if not texto:
        return None

    # Remove prefixo R$ e caracteres de espaço.
    texto = re.sub(r"[R$\s]", "", texto)

    # Formato brasileiro com ponto de milhar e vírgula decimal.
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")

    try:
        return Decimal(texto)
    except InvalidOperation:
        return None


def decimal_para_texto(valor):
    if valor is None:
        return None

    return format(valor, "f")


def extrair_data(nome_arquivo):
    """
    Procura mês e ano no nome do arquivo.
    Retorna uma tupla (mes, ano) como strings, ou (None, None).

    Exemplos aceitos:
    12-2025
    12_2025
    12 2025
    """
    resultado = re.search(
        r"(0[1-9]|1[0-2])[\-_ ](20\d{2})",
        nome_arquivo,
    )

    if not resultado:
        return None, None

    mes, ano = resultado.groups()
    return mes, ano


def obter_registros(conteudo):
    """
    Aceita arquivos cuja raiz seja uma lista ou um objeto.
    """
    if isinstance(conteudo, list):
        return conteudo

    if isinstance(conteudo, dict):
        for chave in ("resultados", "results", "dados", "data", "registros"):
            registros = conteudo.get(chave)

            if isinstance(registros, list):
                return registros

        if "material" in conteudo:
            return [conteudo]

    return []


def normalizar_registro(registro, arquivo_origem, mes, ano):
    material = limpar_texto(registro.get("material", ""))
    almoxarifado = limpar_texto(registro.get("almoxarifado", ""))

    quantidade = converter_decimal(registro.get("saldo"))
    preco_unitario = converter_decimal(registro.get("preco"))
    valor_total = converter_decimal(registro.get("valor_total"))

    return {
        "material": material,
        "termo_busca": gerar_termo_busca(material),
        "almoxarifado": almoxarifado,
        "quantidade": decimal_para_texto(quantidade),
        "preco_unitario": decimal_para_texto(preco_unitario),
        "valor_total_original": decimal_para_texto(valor_total),
        "mes": mes,
        "ano": ano,
        "arquivo_origem": arquivo_origem,
    }


def main():
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    arquivos = sorted(PASTA_ENTRADA.glob("*.json"))

    if not arquivos:
        print(f"Nenhum JSON encontrado em: {PASTA_ENTRADA.resolve()}")
        return

    # Mapeia arquivos com data válida
    arquivos_com_data = []
    for caminho in arquivos:
        mes, ano = extrair_data(caminho.name)
        if mes and ano:
            # Usa (int(ano), int(mes)) como chave para comparação correta
            arquivos_com_data.append(
                ((int(ano), int(mes)), mes, ano, caminho)
            )

    if not arquivos_com_data:
        print("Nenhum arquivo com data (mês/ano) foi identificado.")
        return

    # Descobre a maior data (mais recente)
    maior_data = max(item[0] for item in arquivos_com_data)
    arquivos_mais_recentes = [
        item for item in arquivos_com_data if item[0] == maior_data
    ]

    ano_rec, mes_rec = maior_data
    print(f"Última data identificada: {mes_rec:02d}/{ano_rec}")
    print(f"Arquivo(s) selecionado(s): {[item[3].name for item in arquivos_mais_recentes]}\n")

    registros_normalizados = []
    arquivos_processados = 0

    for _, mes, ano, caminho in arquivos_mais_recentes:
        print(f"Processando: {caminho.name}")

        try:
            with caminho.open("r", encoding="utf-8-sig") as arquivo:
                conteudo = json.load(arquivo)
        except (OSError, json.JSONDecodeError) as erro:
            print(f"Não foi possível processar {caminho.name}: {erro}")
            continue

        registros = obter_registros(conteudo)

        for registro in registros:
            if not isinstance(registro, dict):
                continue

            registro_normalizado = normalizar_registro(
                registro,
                caminho.name,
                mes,
                ano,
            )

            if registro_normalizado["material"]:
                registros_normalizados.append(registro_normalizado)

        arquivos_processados += 1

    with ARQUIVO_SAIDA.open("w", encoding="utf-8") as arquivo:
        json.dump(
            registros_normalizados,
            arquivo,
            ensure_ascii=False,
            indent=4,
        )

    print()
    print(f"Arquivos processados: {arquivos_processados}")
    print(f"Registros gerados: {len(registros_normalizados)}")
    print(f"Arquivo de saída: {ARQUIVO_SAIDA.resolve()}")


if __name__ == "__main__":
    main()