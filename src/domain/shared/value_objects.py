"""Value objects compartilhados (puros, sem Django).

Wave A · Marco 1 (clientes) acrescenta CPF + CNPJ.

CNPJ aceita formato alfanumerico [A-Z0-9]{12}[0-9]{2} desde ja (IN RFB 2.229/2024
— vigencia jul/2026). Algoritmo DV = Modulo 11 com pesos 2-9, valor do caractere
= ord(c) - 48 (retrocompativel com CNPJ numerico antigo). Ver ADR-0017.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_CNPJ_FORMATO_RE = re.compile(r"^[A-Z0-9]{12}[0-9]{2}$")
_CPF_FORMATO_RE = re.compile(r"^[0-9]{11}$")


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


def _so_alfanum(raw: str) -> str:
    """Remove pontuacao comum (., -, /, espaco) e UPPER. Nao filtra letras."""
    return re.sub(r"[\s./\-]", "", raw).upper()


def _valor_caractere_cnpj(c: str) -> int:
    """Mapeia char (digito ou letra) pra valor numerico (algoritmo Serpro).

    '0'..'9' -> 0..9
    'A'..'Z' -> 17..42 (ord(c) - 48)
    """
    return ord(c) - 48


def _dv_modulo11(numeros: list[int], pesos: list[int]) -> int:
    """Modulo 11 generico — usado por CPF e CNPJ."""
    soma = sum(n * p for n, p in zip(numeros, pesos, strict=True))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


@dataclass(frozen=True)
class CNPJ:
    """CNPJ aceitando formato alfanumerico (IN RFB 2.229/2024 — ADR-0017).

    Validacao:
    1. Apos limpar pontuacao, bate ^[A-Z0-9]{12}[0-9]{2}$
    2. Os 2 ultimos digitos (DV1, DV2) sao validos por Modulo 11.

    Algoritmo oficial Serpro:
    - Mapear cada char pra ord(c) - 48
    - DV1 sobre os 12 primeiros chars com pesos [5,4,3,2,9,8,7,6,5,4,3,2]
    - DV2 sobre os 13 primeiros (incluindo DV1) com pesos [6,5,...,2,9,8,...,2]

    Armazenado normalizado (sem pontuacao, UPPER).

    INV-024: dedup entra na camada de banco (UNIQUE(tenant_id, documento)).
    INV-036: idem.
    """

    value: str

    _PESOS_DV1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    _PESOS_DV2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    def __post_init__(self) -> None:
        limpo = _so_alfanum(self.value)
        if not _CNPJ_FORMATO_RE.match(limpo):
            raise ValueError(
                f"CNPJ formato invalido: {self.value!r} -> {limpo!r} "
                f"(esperado 12 alfanumericos + 2 digitos verificadores). "
                f"Documento estrangeiro (passaporte/RNE) sera suportado em V2 — "
                f"nao use CPF/CNPJ de terceiro como workaround."
            )

        # Rejeita sequencias "trivial" (todos iguais) que passam no DV mas
        # nao sao CNPJ reais — pratica padrao Receita.
        if len(set(limpo)) == 1:
            raise ValueError(f"CNPJ invalido (sequencia trivial): {limpo!r}")

        nums = [_valor_caractere_cnpj(c) for c in limpo]
        dv1_calc = _dv_modulo11(nums[:12], CNPJ._PESOS_DV1)
        dv2_calc = _dv_modulo11(nums[:13], CNPJ._PESOS_DV2)
        if nums[12] != dv1_calc or nums[13] != dv2_calc:
            raise ValueError(
                f"CNPJ DV invalido: {limpo!r} "
                f"(DV1 esperado {dv1_calc}, achou {nums[12]}; "
                f"DV2 esperado {dv2_calc}, achou {nums[13]})"
            )

        object.__setattr__(self, "value", limpo)

    def __str__(self) -> str:
        return self.value

    def formatado(self) -> str:
        """Representacao XX.XXX.XXX/XXXX-XX (ou letras nas 12 primeiras posicoes)."""
        v = self.value
        return f"{v[:2]}.{v[2:5]}.{v[5:8]}/{v[8:12]}-{v[12:14]}"

    @property
    def e_alfanumerico(self) -> bool:
        """True se contem alguma letra (CNPJ pos IN RFB 2.229/2024)."""
        return any(c.isalpha() for c in self.value[:12])


@dataclass(frozen=True)
class CPF:
    """CPF numerico padrao Receita Federal (11 digitos + DV).

    Algoritmo: Modulo 11 com pesos decrescentes (10..2 pro DV1, 11..2 pro DV2).
    Armazenado so com numeros.
    """

    value: str

    def __post_init__(self) -> None:
        limpo = re.sub(r"\D", "", self.value)
        if not _CPF_FORMATO_RE.match(limpo):
            raise ValueError(
                f"CPF formato invalido: {self.value!r} (esperado 11 digitos). "
                f"Documento estrangeiro (passaporte/RNE) sera suportado em V2 — "
                f"nao use CPF de terceiro como workaround."
            )
        if len(set(limpo)) == 1:
            raise ValueError(f"CPF invalido (sequencia trivial): {limpo!r}")

        nums = [int(c) for c in limpo]
        pesos_1 = list(range(10, 1, -1))  # [10,9,...,2]
        pesos_2 = list(range(11, 1, -1))  # [11,10,...,2]
        dv1 = _dv_modulo11(nums[:9], pesos_1)
        dv2 = _dv_modulo11(nums[:10], pesos_2)
        if nums[9] != dv1 or nums[10] != dv2:
            raise ValueError(
                f"CPF DV invalido: {limpo!r} "
                f"(DV1 esperado {dv1}, achou {nums[9]}; "
                f"DV2 esperado {dv2}, achou {nums[10]})"
            )

        object.__setattr__(self, "value", limpo)

    def __str__(self) -> str:
        return self.value

    def formatado(self) -> str:
        v = self.value
        return f"{v[:3]}.{v[3:6]}.{v[6:9]}-{v[9:11]}"
