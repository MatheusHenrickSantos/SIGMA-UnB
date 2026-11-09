# __init__.py
__all__ = [
    "InserirDadosNaCamadaRaw",
    "InicializarEsquema",
    "conectar",
]


def __getattr__(nome: str):
    if nome == "InserirDadosNaCamadaRaw":
        from .inserir_dados_na_camada_raw import InserirDadosNaCamadaRaw

        return InserirDadosNaCamadaRaw
    if nome == "InicializarEsquema":
        from .inicializar_esquema import InicializarEsquema

        return InicializarEsquema
    if nome == "conectar":
        from .conectar_com_banco_de_dados import conectar

        return conectar
    raise AttributeError(f"module {__name__!r} has no attribute {nome!r}")