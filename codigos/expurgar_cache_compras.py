"""Expurgo do cache de compras: uso `python codigos/expurgar_cache_compras.py dados/compras_cache`.
Remove niFornecedor e nomeFornecedor das páginas do cache de compras (mesma minimização da V12)."""
import json, os, re, sys
from pathlib import Path

raiz = Path(sys.argv[1])
CAMPOS = ("niFornecedor", "nomeFornecedor")
arquivos = alterados = itens = cpf = 0
for f in sorted(raiz.rglob("*.json")):
    arquivos += 1
    dados = json.loads(f.read_text(encoding="utf-8"))
    mudou = False
    for item in dados.get("resultado", []):
        itens += 1
        ni = re.sub(r"\D", "", str(item.get("niFornecedor") or ""))
        cpf += len(ni) == 11
        for c in CAMPOS:
            if c in item:
                del item[c]; mudou = True
    if mudou:
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, f)
        alterados += 1
print(f"arquivos={arquivos} alterados={alterados} itens={itens} com_cpf_encontrados={cpf}")
