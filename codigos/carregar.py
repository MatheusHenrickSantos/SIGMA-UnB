"""
Carrega a camada bruta (dados/bruto/) no PostgreSQL.

Ordem: unidades -> estoque -> gastos -> empenhos -> requisições.
Cada arquivo é carregado em uma transação própria e registrado em
carga_execucao. Um arquivo que já foi carregado com o mesmo sha256 é pulado,
então rodar a carga duas vezes não duplica nada.

Registros que não passam na validação vão para carga_rejeitado com o motivo,
em vez de derrubar a carga inteira.

Conexão pelas variáveis padrão do Postgres: PGHOST, PGPORT, PGDATABASE,
PGUSER, PGPASSWORD.
"""

import csv
import hashlib
import io
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

from normalizar import converter_decimal, gerar_termo_busca, limpar_texto

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
PASTA_BRUTO = RAIZ_PROJETO / "dados" / "bruto"

# Se o número de linhas de um mês cair mais que isso em relação ao mês
# anterior, a carga do arquivo é desfeita (provável arquivo incompleto).
QUEDA_MAXIMA = 0.30


class RegistroInvalido(Exception):
    pass


# ---------------------------------------------------------------------------
# Leitura dos arquivos brutos
# ---------------------------------------------------------------------------

def ler_json(caminho):
    conteudo = json.loads(caminho.read_bytes().decode("utf-8-sig"))

    if isinstance(conteudo, list):
        return conteudo

    if isinstance(conteudo, dict):
        for chave in ("resultados", "results", "dados", "data", "registros", "records"):
            if isinstance(conteudo.get(chave), list):
                return conteudo[chave]

    raise ValueError(f"estrutura de JSON não reconhecida em {caminho.name}")


def ler_csv(caminho):
    bruto = caminho.read_bytes()
    try:
        texto = bruto.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = bruto.decode("latin-1")

    amostra = texto[:5000]
    delimitador = ";" if amostra.count(";") > amostra.count(",") else ","
    return list(csv.DictReader(io.StringIO(texto), delimiter=delimitador))


def ler_registros(caminho):
    registros = ler_json(caminho) if caminho.suffix == ".json" else ler_csv(caminho)
    # padroniza os nomes das colunas: minúsculas, sem espaços nas pontas
    return [
        {str(k).strip().lower(): v for k, v in r.items()}
        for r in registros
        if isinstance(r, dict)
    ]


def sha256(caminho):
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Conversões
# ---------------------------------------------------------------------------

def campo(registro, *nomes):
    """Primeiro campo não vazio entre os nomes aceitos."""
    for nome in nomes:
        valor = registro.get(nome)
        if valor is not None and str(valor).strip() != "":
            return valor
    return None


def texto(valor):
    if valor is None:
        return None
    valor = limpar_texto(valor)
    return valor or None


def inteiro(valor):
    if valor is None or str(valor).strip() == "":
        return None
    try:
        return int(float(str(valor).strip()))
    except ValueError:
        raise RegistroInvalido(f"número inteiro inválido: {valor!r}")


def decimal(valor):
    if valor is None or str(valor).strip() == "":
        return None
    numero = converter_decimal(valor)
    if numero is None:
        raise RegistroInvalido(f"valor numérico inválido: {valor!r}")
    return numero


FORMATOS_DATA = ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S",
                 "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M")


def data_hora(valor):
    if valor is None or str(valor).strip() == "":
        return None
    valor = str(valor).strip()[:19]
    for formato in FORMATOS_DATA:
        try:
            return datetime.strptime(valor, formato)
        except ValueError:
            continue
    raise RegistroInvalido(f"data inválida: {valor!r}")


def mes_do_arquivo(caminho):
    """
    Extrai o mês de referência do nome do arquivo: 12-2025, 12_2025,
    2025-12, 2025_12, dezembro_2025...
    """
    nome = caminho.stem.lower()
    meses = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
             "agosto", "setembro", "outubro", "novembro", "dezembro"]

    achado = re.search(r"(?<!\d)(0?[1-9]|1[0-2])[-_ ](20\d{2})(?!\d)", nome)
    if achado:
        return date(int(achado.group(2)), int(achado.group(1)), 1)

    achado = re.search(r"(20\d{2})[-_ ](0?[1-9]|1[0-2])(?!\d)", nome)
    if achado:
        return date(int(achado.group(1)), int(achado.group(2)), 1)

    for numero, mes in enumerate(meses, start=1):
        achado = re.search(mes + r"[-_ ]*(20\d{2})", nome)
        if achado:
            return date(int(achado.group(1)), numero, 1)

    return None


# ---------------------------------------------------------------------------
# Cadastros com chave substituta (material, almoxarifado, natureza, credor)
# ---------------------------------------------------------------------------

class Cadastro:
    """Guarda em memória descrição -> id para não consultar o banco a cada linha."""

    def __init__(self, tabela, coluna_id, coluna_texto, extras=None):
        self.tabela = tabela
        self.coluna_id = coluna_id
        self.coluna_texto = coluna_texto
        self.extras = extras or (lambda _: {})
        self.ids = {}
        self.novos = []

    def carregar_existentes(self, cur):
        cur.execute(f"SELECT {self.coluna_texto}, {self.coluna_id} FROM {self.tabela}")
        self.ids = dict(cur.fetchall())
        self.novos = []

    def confirmar(self):
        self.novos = []

    def desfazer(self):
        # a linha falhou e o savepoint desfez os INSERTs: tira do cache
        for descricao in self.novos:
            self.ids.pop(descricao, None)
        self.novos = []

    def obter_id(self, cur, descricao):
        if descricao is None:
            return None
        if descricao in self.ids:
            return self.ids[descricao]

        extras = self.extras(descricao)
        colunas = [self.coluna_texto, *extras]
        marcadores = ", ".join(["%s"] * len(colunas))
        cur.execute(
            f"INSERT INTO {self.tabela} ({', '.join(colunas)}) VALUES ({marcadores}) "
            f"ON CONFLICT ({self.coluna_texto}) DO UPDATE SET {self.coluna_texto} = EXCLUDED.{self.coluna_texto} "
            f"RETURNING {self.coluna_id}",
            [descricao, *extras.values()],
        )
        self.ids[descricao] = cur.fetchone()[0]
        self.novos.append(descricao)
        return self.ids[descricao]


MATERIAIS = Cadastro("material", "id_material", "descricao",
                     extras=lambda d: {"termo_busca": gerar_termo_busca(d)})
ALMOXARIFADOS = Cadastro("almoxarifado", "id_almoxarifado", "nome")
NATUREZAS = Cadastro("natureza_despesa", "id_natureza", "descricao")
CREDORES = Cadastro("credor", "id_credor", "nome")
CADASTROS = (MATERIAIS, ALMOXARIFADOS, NATUREZAS, CREDORES)

UNIDADES_EXISTENTES = set()
UNIDADES_NOVAS = []  # criadas na linha em andamento (para desfazer no cache)


def recarregar_caches(conn):
    with conn.cursor() as cur:
        for cadastro in CADASTROS:
            cadastro.carregar_existentes(cur)
        cur.execute("SELECT id_unidade FROM unidade")
        UNIDADES_EXISTENTES.clear()
        UNIDADES_EXISTENTES.update(linha[0] for linha in cur.fetchall())


def garantir_unidade(cur, id_unidade, nome):
    """
    Devolve o id se a unidade existe. Se não existe mas o registro trouxe o
    nome dela, cria a unidade com fonte = 'referencia' (unidades
    administrativas, como a 605 - UNIVERSIDADE DE BRASÍLIA, não estão no
    dataset Unidades Acadêmicas). Sem id, devolve None.
    """
    if id_unidade is None:
        return None
    if id_unidade in UNIDADES_EXISTENTES:
        return id_unidade

    nome = texto(nome)
    if nome is None:
        raise RegistroInvalido(f"unidade {id_unidade} não existe e veio sem nome")

    cur.execute(
        "INSERT INTO unidade (id_unidade, nome, fonte) VALUES (%s, %s, 'referencia') "
        "ON CONFLICT (id_unidade) DO NOTHING",
        (id_unidade, nome),
    )
    UNIDADES_NOVAS.append(id_unidade)
    UNIDADES_EXISTENTES.add(id_unidade)
    return id_unidade


# ---------------------------------------------------------------------------
# Uma função por dataset: recebe um registro bruto e grava uma linha
# ---------------------------------------------------------------------------

def gravar_unidade(cur, r, contexto):
    id_unidade = inteiro(r.get("id_unidade"))
    nome = texto(r.get("nome"))
    if id_unidade is None or nome is None:
        raise RegistroInvalido("unidade sem id ou sem nome")

    # a unidade superior pode ainda não ter sido lida neste arquivo
    superiores = [
        garantir_unidade(cur, inteiro(r.get(coluna_id)), r.get(coluna_nome))
        if inteiro(r.get(coluna_id)) != id_unidade else id_unidade
        for coluna_id, coluna_nome in (
            ("id_unidade_responsavel", "unidade_responsavel"),
            ("id_unidade_gestora", "unidade_gestora"),
            ("id_gestora_academica", "unidade_gestora_academica"),
        )
    ]

    cur.execute(
        """
        INSERT INTO unidade (id_unidade, nome, sigla, sigla_academica,
                             tipo_organizacional, tipo_academica,
                             id_unidade_responsavel, id_unidade_gestora,
                             id_gestora_academica, fonte)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'cadastro')
        ON CONFLICT (id_unidade) DO UPDATE SET
            nome = EXCLUDED.nome,
            sigla = EXCLUDED.sigla,
            sigla_academica = EXCLUDED.sigla_academica,
            tipo_organizacional = EXCLUDED.tipo_organizacional,
            tipo_academica = EXCLUDED.tipo_academica,
            id_unidade_responsavel = EXCLUDED.id_unidade_responsavel,
            id_unidade_gestora = EXCLUDED.id_unidade_gestora,
            id_gestora_academica = EXCLUDED.id_gestora_academica,
            fonte = 'cadastro',
            atualizado_em = now()
        WHERE (unidade.nome, unidade.sigla, unidade.sigla_academica,
               unidade.tipo_organizacional, unidade.tipo_academica,
               unidade.id_unidade_responsavel, unidade.id_unidade_gestora,
               unidade.id_gestora_academica, unidade.fonte)
              IS DISTINCT FROM
              (EXCLUDED.nome, EXCLUDED.sigla, EXCLUDED.sigla_academica,
               EXCLUDED.tipo_organizacional, EXCLUDED.tipo_academica,
               EXCLUDED.id_unidade_responsavel, EXCLUDED.id_unidade_gestora,
               EXCLUDED.id_gestora_academica, 'cadastro')
        """,
        (
            id_unidade,
            nome,
            texto(r.get("sigla")),
            texto(r.get("sigla_academica")),
            texto(r.get("tipo_organizacional")),
            texto(r.get("tipo_academica")),
            *superiores,
        ),
    )
    if id_unidade not in UNIDADES_EXISTENTES:
        UNIDADES_NOVAS.append(id_unidade)
        UNIDADES_EXISTENTES.add(id_unidade)


def gravar_estoque(cur, r, contexto):
    material = texto(r.get("material"))
    almoxarifado = texto(r.get("almoxarifado"))
    if material is None or almoxarifado is None:
        raise RegistroInvalido("estoque sem material ou sem almoxarifado")

    saldo = decimal(r.get("saldo"))
    if saldo is None:
        raise RegistroInvalido("estoque sem saldo")

    preco = decimal(r.get("preco"))
    valor_total = decimal(r.get("valor_total"))
    if valor_total is None and preco is not None:
        valor_total = round(saldo * preco, 2)

    cur.execute(
        """
        INSERT INTO estoque_saldo (id_material, id_almoxarifado, data_referencia,
                                   saldo, preco_unitario, valor_total, id_carga)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (
            MATERIAIS.obter_id(cur, material),
            ALMOXARIFADOS.obter_id(cur, almoxarifado),
            contexto["data_referencia"],
            saldo,
            preco,
            valor_total,
            contexto["id_carga"],
        ),
    )
    if cur.rowcount == 0:
        raise RegistroInvalido("material repetido no mesmo almoxarifado e mês")


def gravar_gasto(cur, r, contexto):
    id_unidade = garantir_unidade(cur, inteiro(r.get("id_unidade")), r.get("unidade"))
    natureza = texto(r.get("natureza_despesa"))
    valor = decimal(r.get("valor"))
    if id_unidade is None or natureza is None or valor is None:
        raise RegistroInvalido("gasto sem unidade, natureza ou valor")

    cur.execute(
        """
        INSERT INTO gasto (id_unidade, id_natureza, data_referencia, valor, id_carga)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (id_unidade, NATUREZAS.obter_id(cur, natureza), contexto["data_referencia"],
         valor, contexto["id_carga"]),
    )
    if cur.rowcount == 0:
        raise RegistroInvalido("unidade e natureza repetidas no mesmo mês")


def gravar_empenho(cur, r, contexto):
    id_gestora = garantir_unidade(cur, inteiro(r.get("id_unidade_gestora")),
                                  r.get("nome_unidade_gestora"))
    ano = inteiro(r.get("ano"))
    cod = inteiro(r.get("cod_empenho"))
    if id_gestora is None or ano is None or cod is None:
        raise RegistroInvalido("empenho sem unidade gestora, ano ou número")

    data_emissao = data_hora(r.get("data"))

    cur.execute(
        """
        INSERT INTO empenho (id_unidade_gestora, ano, cod_empenho, data_emissao, modalidade,
                             id_natureza, id_credor, valor_empenho, valor_reforcado,
                             valor_anulado, valor_cancelado, saldo_empenho, fonte_recurso,
                             programa_trabalho_resumido, plano_interno, esfera, processo,
                             documento_associado, licitacao, convenio, observacoes, id_carga)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id_unidade_gestora, ano, cod_empenho) DO UPDATE SET
            data_emissao = EXCLUDED.data_emissao,
            modalidade = EXCLUDED.modalidade,
            id_natureza = EXCLUDED.id_natureza,
            id_credor = EXCLUDED.id_credor,
            valor_empenho = EXCLUDED.valor_empenho,
            valor_reforcado = EXCLUDED.valor_reforcado,
            valor_anulado = EXCLUDED.valor_anulado,
            valor_cancelado = EXCLUDED.valor_cancelado,
            saldo_empenho = EXCLUDED.saldo_empenho,
            fonte_recurso = EXCLUDED.fonte_recurso,
            programa_trabalho_resumido = EXCLUDED.programa_trabalho_resumido,
            plano_interno = EXCLUDED.plano_interno,
            esfera = EXCLUDED.esfera,
            processo = EXCLUDED.processo,
            documento_associado = EXCLUDED.documento_associado,
            licitacao = EXCLUDED.licitacao,
            convenio = EXCLUDED.convenio,
            observacoes = EXCLUDED.observacoes,
            id_carga = EXCLUDED.id_carga,
            atualizado_em = now()
        WHERE (empenho.valor_empenho, empenho.valor_reforcado, empenho.valor_anulado,
               empenho.valor_cancelado, empenho.saldo_empenho, empenho.id_credor,
               empenho.observacoes)
              IS DISTINCT FROM
              (EXCLUDED.valor_empenho, EXCLUDED.valor_reforcado, EXCLUDED.valor_anulado,
               EXCLUDED.valor_cancelado, EXCLUDED.saldo_empenho, EXCLUDED.id_credor,
               EXCLUDED.observacoes)
        """,
        (
            id_gestora,
            ano,
            cod,
            data_emissao.date() if data_emissao else None,
            texto(r.get("modalidade")),
            NATUREZAS.obter_id(cur, texto(r.get("natureza_despesa"))),
            CREDORES.obter_id(cur, texto(r.get("credor"))),
            decimal(r.get("valor_empenho")),
            decimal(r.get("valor_reforcado")),
            decimal(r.get("valor_anulado")),
            decimal(r.get("valor_cancelado")),
            decimal(r.get("saldo_empenho")),
            texto(r.get("fonte_recurso")),
            texto(r.get("programa_trabalho_resumido")),
            texto(r.get("plano_interno")),
            texto(r.get("esfera")),
            texto(r.get("processo")),
            texto(r.get("documento_associado")),
            texto(r.get("licitacao")),
            texto(r.get("convenio")),
            texto(r.get("observacoes")),
            contexto["id_carga"],
        ),
    )


def gravar_requisicao(cur, r, contexto):
    numero = inteiro(r.get("numero"))
    ano = inteiro(r.get("ano"))
    if numero is None or ano is None:
        raise RegistroInvalido("requisição sem número ou sem ano")

    data_envio = data_hora(r.get("data_envio"))
    data_autorizacao = data_hora(r.get("data_autorizacao_chefe"))
    if data_envio and data_autorizacao and data_autorizacao < data_envio:
        raise RegistroInvalido("autorização anterior ao envio")

    cur.execute(
        """
        INSERT INTO requisicao_servico (numero, ano, tipo, id_unidade_requisitante,
                                        id_unidade_custo, data_envio,
                                        data_autorizacao_chefe, status, observacoes, id_carga)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ano, numero) DO UPDATE SET
            tipo = EXCLUDED.tipo,
            id_unidade_requisitante = EXCLUDED.id_unidade_requisitante,
            id_unidade_custo = EXCLUDED.id_unidade_custo,
            data_envio = EXCLUDED.data_envio,
            data_autorizacao_chefe = EXCLUDED.data_autorizacao_chefe,
            status = EXCLUDED.status,
            observacoes = EXCLUDED.observacoes,
            id_carga = EXCLUDED.id_carga,
            atualizado_em = now()
        WHERE (requisicao_servico.status, requisicao_servico.data_autorizacao_chefe,
               requisicao_servico.id_unidade_custo, requisicao_servico.observacoes)
              IS DISTINCT FROM
              (EXCLUDED.status, EXCLUDED.data_autorizacao_chefe,
               EXCLUDED.id_unidade_custo, EXCLUDED.observacoes)
        """,
        (
            numero,
            ano,
            texto(r.get("tipo")),
            garantir_unidade(cur, inteiro(r.get("id_unidade_requisitante")),
                             r.get("nome_unidade_requisitante")),
            garantir_unidade(cur, inteiro(r.get("id_unidade_custo")),
                             r.get("nome_unidade_custo")),
            data_envio.date() if data_envio else None,
            data_autorizacao.date() if data_autorizacao else None,
            texto(r.get("status")),
            texto(r.get("observacoes")),
            contexto["id_carga"],
        ),
    )


# dataset -> (função, é uma foto mensal?)
# Nas fotos mensais (estoque, gastos) o mês de referência vem do nome do
# arquivo e cada mês entra uma vez. Nos outros, cada registro traz a própria
# data e os arquivos se sobrepõem; vale a versão mais recente (upsert).
DATASETS = {
    "unidades": (gravar_unidade, False),
    "estoque": (gravar_estoque, True),
    "gastos": (gravar_gasto, True),
    "empenhos": (gravar_empenho, False),
    "requisicoes": (gravar_requisicao, False),
}


# ---------------------------------------------------------------------------
# Controle
# ---------------------------------------------------------------------------

def ja_carregado(cur, dataset, hash_arquivo):
    cur.execute(
        "SELECT 1 FROM carga_execucao WHERE dataset = %s AND sha256 = %s "
        "AND finalizado_em IS NOT NULL",
        (dataset, hash_arquivo),
    )
    return cur.fetchone() is not None


def corrigir_hierarquia(cur):
    """
    Unidade que aponta para uma unidade superior que não existe no cadastro
    quebraria a chave estrangeira no commit. A referência fica nula.
    """
    total = 0
    for coluna in ("id_unidade_responsavel", "id_unidade_gestora", "id_gestora_academica"):
        cur.execute(
            f"UPDATE unidade u SET {coluna} = NULL WHERE {coluna} IS NOT NULL "
            f"AND NOT EXISTS (SELECT 1 FROM unidade p WHERE p.id_unidade = u.{coluna})"
        )
        total += cur.rowcount
    return total


def verificar_queda(cur, dataset, data_referencia, gravadas):
    """Compara com o mês anterior já carregado do mesmo dataset."""
    tabela = {"estoque": "estoque_saldo", "gastos": "gasto"}.get(dataset)
    if tabela is None or data_referencia is None:
        return

    cur.execute(
        f"SELECT count(*) FROM {tabela} WHERE data_referencia = "
        f"(SELECT max(data_referencia) FROM {tabela} WHERE data_referencia < %s)",
        (data_referencia,),
    )
    anterior = cur.fetchone()[0]
    if anterior and gravadas < anterior * (1 - QUEDA_MAXIMA):
        raise RuntimeError(
            f"{dataset} {data_referencia:%m/%Y}: {gravadas} linhas contra {anterior} "
            f"do mês anterior (queda maior que {QUEDA_MAXIMA:.0%})"
        )


def carregar_arquivo(conn, dataset, caminho, hash_arquivo, data_referencia, gravar):
    arquivo = str(caminho.relative_to(PASTA_BRUTO)).replace("\\", "/")

    with conn.cursor() as cur:
        if ja_carregado(cur, dataset, hash_arquivo):
            return "pulado", 0, 0

    registros = ler_registros(caminho)

    with conn.transaction():
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO carga_execucao (dataset, arquivo, sha256, linhas_lidas) "
                "VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (dataset, sha256) DO UPDATE SET arquivo = EXCLUDED.arquivo, "
                "iniciado_em = now() "
                "RETURNING id_carga",
                (dataset, arquivo, hash_arquivo, len(registros)),
            )
            id_carga = cur.fetchone()[0]
            contexto = {"id_carga": id_carga, "data_referencia": data_referencia}

            gravadas = rejeitadas = 0
            for registro in registros:
                try:
                    with conn.transaction():
                        gravar(cur, registro, contexto)
                    gravadas += 1
                    for cadastro in CADASTROS:
                        cadastro.confirmar()
                    UNIDADES_NOVAS.clear()
                except (RegistroInvalido, psycopg.errors.DataError,
                        psycopg.errors.IntegrityError) as erro:
                    rejeitadas += 1
                    for cadastro in CADASTROS:
                        cadastro.desfazer()
                    UNIDADES_EXISTENTES.difference_update(UNIDADES_NOVAS)
                    UNIDADES_NOVAS.clear()
                    cur.execute(
                        "INSERT INTO carga_rejeitado (id_carga, registro, motivo) "
                        "VALUES (%s, %s, %s)",
                        (id_carga, Jsonb(registro), str(erro).splitlines()[0][:500]),
                    )

            if dataset == "unidades":
                soltas = corrigir_hierarquia(cur)
                if soltas:
                    print(f"  AVISO: {soltas} referência(s) a unidade superior inexistente "
                          "foram deixadas em branco")

            verificar_queda(cur, dataset, data_referencia, gravadas)

            cur.execute(
                "UPDATE carga_execucao SET linhas_gravadas = %s, linhas_rejeitadas = %s, "
                "finalizado_em = now() WHERE id_carga = %s",
                (gravadas, rejeitadas, id_carga),
            )

    return "carregado", gravadas, rejeitadas


def ler_manifesto():
    """arquivo relativo -> data de modificação no portal (texto ISO)."""
    caminho = PASTA_BRUTO / "manifesto.json"
    if not caminho.exists():
        return {}
    manifesto = json.loads(caminho.read_text(encoding="utf-8"))
    return {
        a["arquivo"]: a.get("modificado_no_portal") or ""
        for d in manifesto.get("datasets", {}).values()
        for a in d.get("arquivos", [])
    }


def selecionar_arquivos(dataset, precisa_mes, modificados):
    """
    O portal publica o mesmo arquivo várias vezes (mesmo mês, às vezes com
    o mesmo conteúdo). Regras:
      * conteúdo idêntico (mesmo sha256) entra uma vez só;
      * nos datasets mensais (estoque, gastos) fica uma versão por mês: a
        modificada por último no portal;
      * arquivo sem mês no nome usa o mês em que foi publicado no portal.
    Retorna [(caminho, sha256, data_referencia)] em ordem cronológica.
    """
    pasta = PASTA_BRUTO / dataset
    if not pasta.exists():
        return []

    candidatos = {}
    for caminho in pasta.iterdir():
        if caminho.suffix not in (".json", ".csv"):
            continue

        relativo = str(caminho.relative_to(PASTA_BRUTO)).replace("\\", "/")
        modificado = modificados.get(relativo, "")
        mes = mes_do_arquivo(caminho)
        if mes is None and modificado[:7]:
            mes = date(int(modificado[:4]), int(modificado[5:7]), 1)

        if precisa_mes and mes is None:
            print(f"  AVISO: sem mês de referência para {caminho.name}; arquivo ignorado")
            continue

        hash_arquivo = sha256(caminho)
        chave = mes if precisa_mes else hash_arquivo
        atual = candidatos.get(chave)
        if atual is None or (modificado, caminho.name) > (atual[3], atual[0].name):
            candidatos[chave] = (caminho, hash_arquivo, mes, modificado)

    vistos = {}
    selecionados = []
    for caminho, hash_arquivo, mes, modificado in sorted(
        candidatos.values(), key=lambda c: (c[2] or date.min, c[3], c[0].name)
    ):
        if hash_arquivo in vistos:
            if precisa_mes:
                # o portal publicou para este mês o mesmo arquivo de outro mês;
                # carregar criaria um mês "parado" que não aconteceu
                print(f"  AVISO: {mes:%m/%Y} tem o mesmo conteúdo de "
                      f"{vistos[hash_arquivo]:%m/%Y}; mês ignorado")
            continue
        vistos[hash_arquivo] = mes
        selecionados.append((caminho, hash_arquivo, mes))
    return selecionados


def main():
    if not PASTA_BRUTO.exists():
        print(f"Pasta {PASTA_BRUTO} não existe. Rode antes: python baixar_dados.py")
        sys.exit(1)

    total_gravadas = 0
    erros = []

    with psycopg.connect(autocommit=True) as conn:
        conn.execute("SET TIME ZONE 'America/Sao_Paulo'")
        recarregar_caches(conn)

        modificados = ler_manifesto()

        for dataset, (gravar, precisa_mes) in DATASETS.items():
            print(f"\n[{dataset}]")
            arquivos = selecionar_arquivos(dataset, precisa_mes, modificados)
            print(f"  {len(arquivos)} arquivo(s) distintos para carregar")

            for caminho, hash_arquivo, data_referencia in arquivos:
                try:
                    situacao, gravadas, rejeitadas = carregar_arquivo(
                        conn, dataset, caminho, hash_arquivo, data_referencia, gravar
                    )
                except Exception as erro:
                    erros.append(f"{dataset}/{caminho.name}: {erro}")
                    print(f"  ERRO em {caminho.name}: {erro}")
                    # o rollback do arquivo pode ter desfeito ids que estavam no cache
                    recarregar_caches(conn)
                    continue

                total_gravadas += gravadas
                if situacao == "carregado":
                    print(f"  {caminho.name}: {gravadas} gravadas, {rejeitadas} rejeitadas")

        with conn.cursor() as cur:
            print("\nLinhas por tabela:")
            for tabela in ("unidade", "material", "almoxarifado", "estoque_saldo",
                           "natureza_despesa", "credor", "gasto", "empenho",
                           "requisicao_servico"):
                cur.execute(f"SELECT count(*) FROM {tabela}")
                print(f"  {tabela:<20} {cur.fetchone()[0]:>9}")

    if erros:
        print(f"\n{len(erros)} arquivo(s) com erro:")
        for erro in erros:
            print(f"  {erro}")
        sys.exit(1)


if __name__ == "__main__":
    main()
