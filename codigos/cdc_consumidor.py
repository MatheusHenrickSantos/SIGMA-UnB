"""
Consumidor de captura de mudanças (CDC) do OLTP.

Lê o slot de replicação lógica `sigma_cdc` (plugin pgoutput, publicação
`sigma_cdc`) e grava cada INSERT/UPDATE/DELETE como uma linha JSON em
dados/cdc/eventos-<lote>.jsonl. É a entrada da camada analítica.

Semântica de entrega: **pelo menos uma vez**, com idempotência por chave.
  1. os eventos são lidos com *peek* (não consome o slot);
  2. o arquivo do lote é gravado e renomeado atomicamente;
  3. só então o slot avança até o fim da última transação gravada.
Se o processo morrer entre 2 e 3, o lote é lido de novo e gera o mesmo
arquivo (nome derivado do LSN final), então reprocessar não muda o resultado.
Cada evento tem `id_evento` = LSN da mensagem, único e estável, para o
destino deduplicar.

Uso:
    python cdc_consumidor.py              # drena o que houver e sai
    python cdc_consumidor.py --continuo   # repete a cada 2 s
"""

import json
import struct
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_CDC = RAIZ_PROJETO / "dados" / "cdc"

SLOT = "sigma_cdc"
PUBLICACAO = "sigma_cdc"
EPOCA_PG = datetime(2000, 1, 1, tzinfo=timezone.utc)


def garantir_slot(conn):
    existe = conn.execute(
        "SELECT 1 FROM pg_replication_slots WHERE slot_name = %s", (SLOT,)
    ).fetchone()
    if not existe:
        conn.execute("SELECT pg_create_logical_replication_slot(%s, 'pgoutput')", (SLOT,))
        print(f"Slot {SLOT} criado: só mudanças a partir de agora serão capturadas.")


class Leitor:
    """Percorre os bytes de uma mensagem pgoutput."""

    def __init__(self, dados):
        self.dados, self.pos = bytes(dados), 0

    def ler(self, formato):
        valor = struct.unpack_from("!" + formato, self.dados, self.pos)
        self.pos += struct.calcsize("!" + formato)
        return valor[0] if len(valor) == 1 else valor

    def texto(self):
        fim = self.dados.index(b"\0", self.pos)
        valor = self.dados[self.pos:fim].decode()
        self.pos = fim + 1
        return valor

    def bytes(self, n):
        valor = self.dados[self.pos:self.pos + n]
        self.pos += n
        return valor

    def tupla(self, colunas):
        qtd = self.ler("h")
        linha = {}
        for i in range(qtd):
            tipo = self.bytes(1)
            if tipo == b"t":
                linha[colunas[i]] = self.bytes(self.ler("i")).decode()
            elif tipo == b"n":
                linha[colunas[i]] = None
            # 'u' = valor TOAST inalterado: omitido
        return linha


def ts_pg(micros):
    return (EPOCA_PG + timedelta(microseconds=micros)).isoformat()


def decodificar(mensagens):
    """
    mensagens: [(lsn, bytes)] em ordem. Devolve (transacoes, lsn_fim), onde
    cada transação é a lista de eventos de um BEGIN..COMMIT completo. Mensagens
    de transação ainda incompleta são ignoradas.
    """
    relacoes = {}
    transacoes, atual, lsn_fim = [], None, None
    for lsn, dados in mensagens:
        leitor = Leitor(dados)
        tipo = leitor.bytes(1)
        if tipo == b"R":
            oid = leitor.ler("I")
            esquema, nome = leitor.texto(), leitor.texto()
            leitor.ler("B")
            colunas = []
            for _ in range(leitor.ler("h")):
                leitor.ler("B")
                colunas.append(leitor.texto())
                leitor.ler("II")
            relacoes[oid] = (f"{esquema}.{nome}", colunas)
        elif tipo == b"B":
            _, ts, xid = leitor.ler("QqI")
            atual = {"xid": xid, "commit_ts": ts_pg(ts), "eventos": []}
        elif tipo in (b"I", b"U", b"D") and atual is not None:
            tabela, colunas = relacoes[leitor.ler("I")]
            antes = depois = None
            marca = leitor.bytes(1)
            if marca in (b"K", b"O"):
                antes = leitor.tupla(colunas)
                marca = leitor.bytes(1) if tipo == b"U" else None
            if marca == b"N":
                depois = leitor.tupla(colunas)
            atual["eventos"].append({
                "id_evento": str(lsn),
                "operacao": {b"I": "insert", b"U": "update", b"D": "delete"}[tipo],
                "tabela": tabela,
                "antes": antes,
                "depois": depois,
            })
        elif tipo == b"C" and atual is not None:
            _, _, fim, _ = leitor.ler("BQQq")
            atual["lsn_fim"] = fim
            transacoes.append(atual)
            lsn_fim = fim
            atual = None
    return transacoes, lsn_fim


def lsn_texto(valor):
    return f"{valor >> 32:X}/{valor & 0xFFFFFFFF:X}"


def drenar(conn):
    """Lê, grava o lote e só então avança o slot. Devolve o nº de eventos."""
    linhas = conn.execute(
        "SELECT lsn::text, data FROM pg_logical_slot_peek_binary_changes("
        "%s, NULL, NULL, 'proto_version', '1', 'publication_names', %s)",
        (SLOT, PUBLICACAO),
    ).fetchall()
    # o LSN textual (X/Y) vira inteiro para ordenar e nomear o lote
    mensagens = [(int(a, 16) << 32 | int(b, 16), d)
                 for (l, d) in linhas for a, b in [l.split("/")]]
    transacoes, lsn_fim = decodificar(mensagens)
    if not transacoes:
        return 0

    PASTA_CDC.mkdir(parents=True, exist_ok=True)
    destino = PASTA_CDC / f"eventos-{lsn_fim:016X}.jsonl"
    temporario = destino.with_suffix(".tmp")
    total = 0
    with temporario.open("w", encoding="utf-8") as saida:
        for transacao in transacoes:
            for evento in transacao["eventos"]:
                evento = {**evento, "commit_ts": transacao["commit_ts"], "xid": transacao["xid"]}
                saida.write(json.dumps(evento, ensure_ascii=False) + "\n")
                total += 1
    temporario.replace(destino)  # atômico: ou o lote inteiro existe, ou nada

    conn.execute("SELECT pg_replication_slot_advance(%s, %s::pg_lsn)", (SLOT, lsn_texto(lsn_fim)))
    print(f"{total} evento(s) em {destino.name}")
    return total


def main():
    continuo = "--continuo" in sys.argv
    with psycopg.connect(autocommit=True) as conn:
        garantir_slot(conn)
        while True:
            drenar(conn)
            if not continuo:
                break
            time.sleep(2)


if __name__ == "__main__":
    main()
