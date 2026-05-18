"""Value objects compartilhados (puros, sem Django).

F-A entrega so os mais basicos. Wave A vai expandir com CPF, CNPJ, Money,
NumeroDocumentoFiscal, etc.

CNPJ na Wave A: aceitar formato alfanumerico [A-Z0-9]{12}[0-9]{2} a partir de
jul/2026 (IN RFB 2.229/2024). Algoritmo DV = Modulo 11 com pesos 2-9, valor do
caractere = ord(c) - 48 (retrocompativel com CNPJ numerico antigo). Ver ADR-0017.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


@dataclass(frozen=True)
class Email:
    """Email validado no boundary; armazenado lowercase.

    ValueError eh levantado eagerly — INV-VALIDACAO-001 (a definir): boundary
    rejeita formato invalido antes de chegar no dominio.
    """

    value: str

    def __post_init__(self) -> None:
        if not _EMAIL_RE.match(self.value):
            raise ValueError(f"Email invalido: {self.value!r}")
        # frozen=True forca contornar com object.__setattr__
        object.__setattr__(self, "value", self.value.lower())

    def __str__(self) -> str:
        return self.value
