"""
Acesso ao data lake (MinIO, compatível com S3) e ao Postgres, usado pelos
scripts da E2.

Layout do bucket (LAKE_BUCKET, padrão sigma-lake):

    bronze/portal/<dataset>/<sha256[:16]>/<arquivo>     arquivos originais do portal
    bronze/portal/_manifestos/<coletado_em>.json        manifesto de cada coleta
    bronze/lote/<tabela>/data_extracao=AAAA-MM-DD/<tabela>.parquet
    bronze/cdc/<tabela>/data_captura=AAAA-MM-DD/<HHMMSS>.parquet
    bronze/_controle/marcas_cdc.json                    marca d'água do CDC

Configuração por variáveis de ambiente (todas com padrão):
    LAKE_ENDPOINT   minio:9000      LAKE_USER      sigma
    LAKE_BUCKET     sigma-lake      LAKE_PASSWORD  sigma12345
    LAKE_SCHEME     http
Postgres pelas variáveis padrão: PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import psycopg
import pyarrow as pa
import pyarrow.parquet as pq
from pyarrow import fs

FUSO = ZoneInfo("America/Sao_Paulo")
BUCKET = os.environ.get("LAKE_BUCKET", "sigma-lake")
RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_BRUTO = RAIZ_PROJETO / "dados" / "bruto"

# tabela -> (coluna que marca a mudança, chave primária)
# atualizado_em: o carregar.py só altera quando algum campo muda de verdade.
# carregado_em: tabelas insert-only ou cadastros que nunca são alterados.
TABELAS = {
    "unidade": ("atualizado_em", ["id_unidade"]),
    "almoxarifado": ("atualizado_em", ["id_almoxarifado"]),
    "material": ("atualizado_em", ["id_material"]),
    "natureza_despesa": ("carregado_em", ["id_natureza"]),
    "credor": ("carregado_em", ["id_credor"]),
    "estoque_saldo": ("carregado_em", ["id_material", "id_almoxarifado", "data_referencia"]),
    "gasto": ("atualizado_em", ["id_gasto"]),
    "empenho": ("atualizado_em", ["id_unidade_gestora", "ano", "cod_empenho"]),
    "requisicao_servico": ("atualizado_em", ["ano", "numero"]),
    "cotacao_online": ("carregado_em", ["id_cotacao"]),
}

CAMINHO_MARCAS = f"{BUCKET}/bronze/_controle/marcas_cdc.json"


def agora():
    return datetime.now(FUSO)


def sistema_arquivos():
    """Sistema de arquivos S3 do pyarrow apontando para o MinIO."""
    return fs.S3FileSystem(
        endpoint_override=os.environ.get("LAKE_ENDPOINT", "minio:9000"),
        scheme=os.environ.get("LAKE_SCHEME", "http"),
        access_key=os.environ.get("LAKE_USER", "sigma"),
        secret_key=os.environ.get("LAKE_PASSWORD", "sigma12345"),
        region="us-east-1",
        allow_bucket_creation=True,
    )


def garantir_bucket(s3):
    if s3.get_file_info(BUCKET).type == fs.FileType.NotFound:
        s3.create_dir(BUCKET)
        print(f"bucket {BUCKET} criado")


def existe(s3, caminho):
    return s3.get_file_info(caminho).type != fs.FileType.NotFound


def ler_json(s3, caminho, padrao):
    if not existe(s3, caminho):
        return padrao
    with s3.open_input_stream(caminho) as arquivo:
        return json.loads(arquivo.read().decode("utf-8"))


def gravar_json(s3, caminho, dados):
    with s3.open_output_stream(caminho) as arquivo:
        arquivo.write(json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8"))


def conectar_postgres():
    # Leitura apenas: as extrações nunca alteram a origem.
    conn = psycopg.connect(autocommit=False)
    conn.read_only = True
    return conn


def tamanho_mb(n_bytes):
    return f"{n_bytes / 1_048_576:.2f} MB"


# ---------------------------------------------------------------------------
# Postgres -> Parquet
# ---------------------------------------------------------------------------

TIPOS_SIMPLES = {
    "smallint": pa.int16(),
    "integer": pa.int32(),
    "bigint": pa.int64(),
    "real": pa.float32(),
    "double precision": pa.float64(),
    "boolean": pa.bool_(),
    "text": pa.string(),
    "character": pa.string(),
    "character varying": pa.string(),
    "jsonb": pa.string(),
    "date": pa.date32(),
    "timestamp with time zone": pa.timestamp("us", tz="America/Sao_Paulo"),
    "timestamp without time zone": pa.timestamp("us"),
}

TAMANHO_LOTE = 50_000


def esquema_tabela(conn, tabela):
    """
    Esquema Arrow a partir do catálogo do Postgres, e não inferido dos dados:
    assim uma coluna toda nula ou uma execução sem linhas não muda o tipo
    gravado no Parquet de uma execução para outra.
    """
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name, data_type, numeric_precision, numeric_scale "
            "FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position",
            (tabela,),
        )
        campos = []
        for nome, tipo, precisao, escala in cur.fetchall():
            if tipo == "numeric":
                tipo_arrow = pa.decimal128(precisao or 38, escala or 0)
            elif tipo in TIPOS_SIMPLES:
                tipo_arrow = TIPOS_SIMPLES[tipo]
            else:
                raise ValueError(f"{tabela}.{nome}: tipo {tipo} sem mapeamento para Parquet")
            campos.append(pa.field(nome, tipo_arrow))
    if not campos:
        raise ValueError(f"tabela {tabela} não existe no Postgres")
    return pa.schema(campos)


def exportar_parquet(conn, s3, consulta, parametros, esquema, destino, gravar_vazio):
    """
    Executa a consulta com cursor no servidor (lotes de TAMANHO_LOTE linhas,
    sem carregar a tabela inteira na memória) e grava em destino como Parquet
    com compressão zstd. Retorna o número de linhas gravadas.

    Com gravar_vazio=False, nenhum arquivo é criado se a consulta não trouxer
    linhas. Se algo falhar no meio, o arquivo parcial é apagado.
    """
    total = 0
    escritor = None
    saida = None
    ok = False
    try:
        with conn.cursor(name="exportacao") as cur:
            cur.execute(consulta, parametros)
            while True:
                linhas = cur.fetchmany(TAMANHO_LOTE)
                if not linhas:
                    break
                colunas = list(zip(*linhas))
                lote = pa.RecordBatch.from_arrays(
                    [pa.array(col, type=campo.type) for col, campo in zip(colunas, esquema)],
                    schema=esquema,
                )
                if escritor is None:
                    saida = s3.open_output_stream(destino)
                    escritor = pq.ParquetWriter(saida, esquema, compression="zstd")
                escritor.write_batch(lote)
                total += len(linhas)

        if escritor is None and gravar_vazio:
            saida = s3.open_output_stream(destino)
            escritor = pq.ParquetWriter(saida, esquema, compression="zstd")
        ok = True
    finally:
        if escritor is not None:
            escritor.close()
        if saida is not None:
            saida.close()
            if not ok and existe(s3, destino):
                # falhou no meio: não deixa um Parquet incompleto na bronze
                s3.delete_file(destino)
    return total
