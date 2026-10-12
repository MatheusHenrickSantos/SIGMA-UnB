"""
Verifica se os dois caminhos da E2 chegaram inteiros à bronze.

Para cada tabela:
  lote  — a foto mais recente em bronze/lote/ tem o mesmo número de linhas
          que o Postgres agora (rode logo depois da extração: se o banco
          mudou desde a foto, a diferença é esperada);
  cdc   — juntando todos os arquivos de bronze/cdc/ e ficando com a versão
          mais recente de cada chave, o resultado tem exatamente as mesmas
          chaves que o Postgres, com o mesmo valor da coluna de mudança.
          Ou seja: a partir só do CDC dá para reconstruir o estado atual.

Também confere se todo arquivo do manifesto local está em bronze/portal/.

Sai com código 1 se algo divergir.

Uso:
    python verificar_e2.py
"""

import json
import sys

import pyarrow.compute as pc
import pyarrow.dataset as ds
import pyarrow.parquet as pq
from pyarrow import fs

from lake import BUCKET, PASTA_BRUTO, TABELAS, conectar_postgres, existe, sistema_arquivos


def foto_mais_recente(s3, tabela):
    pasta = f"{BUCKET}/bronze/lote/{tabela}"
    if not existe(s3, pasta):
        return None
    particoes = sorted(
        info.path for info in s3.get_file_info(fs.FileSelector(pasta))
        if info.type == fs.FileType.Directory and "data_extracao=" in info.path
    )
    return f"{particoes[-1]}/{tabela}.parquet" if particoes else None


def estado_pelo_cdc(s3, tabela, coluna, chave):
    """Conjunto {(chave..., valor da coluna)} da versão mais recente de cada chave."""
    pasta = f"{BUCKET}/bronze/cdc/{tabela}"
    if not existe(s3, pasta):
        return set()
    dados = ds.dataset(pasta, filesystem=s3, format="parquet", partitioning="hive")
    tabela_cdc = dados.to_table(columns=[*chave, coluna])
    ultima = tabela_cdc.group_by(chave).aggregate([(coluna, "max")])
    colunas = [ultima.column(c).to_pylist() for c in [*chave, f"{coluna}_max"]]
    return set(zip(*colunas))


def main():
    s3 = sistema_arquivos()
    conn = conectar_postgres()
    problemas = 0

    print(f"{'tabela':<20} {'postgres':>9} {'lote':>9} {'cdc':>9}  situação")
    with conn, conn.cursor() as cur:
        for tabela, (coluna, chave) in TABELAS.items():
            cur.execute(f"SELECT count(*) FROM {tabela}")
            n_pg = cur.fetchone()[0]

            arquivo = foto_mais_recente(s3, tabela)
            n_lote = pq.read_metadata(arquivo, filesystem=s3).num_rows if arquivo else None

            cur.execute(f"SELECT {', '.join(chave)}, {coluna} FROM {tabela}")
            estado_pg = set(cur.fetchall())
            estado_cdc = estado_pelo_cdc(s3, tabela, coluna, chave)

            erros = []
            if n_lote is None:
                erros.append("sem foto no lote")
            elif n_lote != n_pg:
                erros.append(f"foto do lote com {n_lote - n_pg:+d} linha(s) "
                             "(o Postgres mudou depois dela? rode extrair_lote.py)")
            if estado_cdc != estado_pg:
                faltam = len(estado_pg - estado_cdc)
                sobram = len(estado_cdc - estado_pg)
                erros.append(f"cdc: {faltam} versão(ões) faltando, {sobram} a mais")

            problemas += bool(erros)
            print(f"{tabela:<20} {n_pg:>9} {n_lote if n_lote is not None else '-':>9} "
                  f"{len(estado_cdc):>9}  {'OK' if not erros else 'DIVERGE: ' + '; '.join(erros)}")

    manifesto = PASTA_BRUTO / "manifesto.json"
    if manifesto.exists():
        dados = json.loads(manifesto.read_text(encoding="utf-8"))
        faltando = [
            a["arquivo"]
            for d, info in dados.get("datasets", {}).items()
            for a in info.get("arquivos", [])
            if not existe(s3, f"{BUCKET}/bronze/portal/{d}/{a['sha256'][:16]}/"
                              f"{a['arquivo'].rsplit('/', 1)[-1]}")
        ]
        print(f"\nbronze/portal: {'OK' if not faltando else f'{len(faltando)} arquivo(s) faltando'}")
        problemas += bool(faltando)

    if problemas:
        print(f"\n{problemas} problema(s). A bronze não está completa.")
        sys.exit(1)
    print("\nTudo certo: lote e CDC batem com o Postgres.")


if __name__ == "__main__":
    main()
