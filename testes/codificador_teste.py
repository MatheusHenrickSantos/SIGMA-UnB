"""Codificador falso para testes: dispensa baixar o modelo de linguagem.

Cada palavra do texto soma 1 numa posição do vetor escolhida por hash.
Textos com palavras em comum ficam próximos; não há nenhuma semântica
além disso. Serve para testar o pipeline e o banco, nunca a qualidade
das correspondências.
"""

from __future__ import annotations

import hashlib
import math
import re
from typing import Sequence


class CodificadorDeTeste:
    def __init__(
        self,
        dimensao: int = 384,
        nome: str = "teste/hash-de-palavras",
        falhar_na_chamada: int | None = None,
        devolver_nan: bool = False,
    ) -> None:
        self.nome = nome
        self.revisao = "1"
        self.dimensao = dimensao
        self.prefixos = {"consulta": "", "documento": ""}
        self.metadados = {"tipo": "codificador de teste"}
        self.chamadas: list[list[str]] = []
        self._falhar_na_chamada = falhar_na_chamada
        self._devolver_nan = devolver_nan

    @property
    def textos_enviados(self) -> list[str]:
        return [texto for chamada in self.chamadas for texto in chamada]

    def vetor(self, texto: str) -> list[float]:
        vetor = [0.0] * self.dimensao
        for palavra in re.findall(r"[a-z0-9]+", texto.lower()):
            posicao = int(hashlib.sha256(palavra.encode()).hexdigest()[:8], 16) % self.dimensao
            vetor[posicao] += 1.0
        norma = math.sqrt(sum(v * v for v in vetor))
        return [v / norma for v in vetor] if norma else vetor

    def codificar(self, textos: Sequence[str], papel: str) -> list[list[float]]:
        self.chamadas.append(list(textos))
        if self._falhar_na_chamada == len(self.chamadas):
            raise RuntimeError("falha simulada do modelo")
        if self._devolver_nan:
            return [[float("nan")] * self.dimensao for _ in textos]
        return [self.vetor(texto) for texto in textos]
