import csv

from codigos.normalizar.main import exportar_materials_normalizados


def test_exportar_materials_normalizados_le_estoque_do_bronze(tmp_path, monkeypatch):
    class Cursor:
        def __init__(self):
            self.rows = [
                ("LÂMPADA",),
                ("FERVEDORA",),
                ("  ",),
                (None,),
            ]

        def execute(self, query):
            self.query = query

        def fetchall(self):
            return [row for row in self.rows if row[0] and str(row[0]).strip()]

    class Conn:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def cursor(self):
            return Cursor()

    monkeypatch.setattr(
        "codigos.normalizar.fonte_banco.conectar",
        lambda: Conn(),
    )

    saida = tmp_path / "seeds" / "materiais_normalizados.csv"
    exportar_materials_normalizados(saida)

    assert saida.exists()
    with saida.open("r", encoding="utf-8-sig", newline="") as arquivo:
        linhas = list(csv.DictReader(arquivo))

    assert linhas == [
        {
            "descricao_original": "LÂMPADA",
            "descricao_normalizada": "LAMPADA",
        },
        {
            "descricao_original": "FERVEDORA",
            "descricao_normalizada": "FERVEDORA",
        },
    ]


def test_normalizacao_remove_acentos_e_entidades_html():
    from codigos.normalizar.limpeza import normalizar_texto

    assert normalizar_texto("ALCOOL, ETILICO, L&amp;Iacute;QUIDO, 70% , 1L") == (
        "ALCOOL, ETILICO, LIQUIDO, 70%, 1 L"
    )
    assert normalizar_texto("AÇÚCAR, LÂMPADA, ÇAIXA") == "ACUCAR, LAMPADA, CAIXA"
    assert normalizar_texto("CANECA/FEVERDOR, 6,0 L") == "CANECA/FERVEDOR, 6,0 L"
    assert normalizar_texto("POTENCIONETRO, 10 K") == "POTENCIOMETRO, 10 K"
    assert normalizar_texto("TRASISTOR, 2N2222") == "TRANSISTOR, 2N2222"
    assert normalizar_texto("CONTATORA, 220V") == "CONTACTORA, 220 V"
