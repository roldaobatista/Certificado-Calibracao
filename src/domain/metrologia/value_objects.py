"""Value objects metrologicos (puros, sem Django).

Criados na Onda 2 saneamento (2026-05-23) pra impedir que Marco 4 (`calibracao`)
e modulo `certificados` Wave A reinventem cada um com validacoes divergentes.

Cobertura:
  - Grandeza (enum fechado das grandezas RBC mais comuns)
  - FaixaMedicao (limite inferior + superior + unidade)
  - IncertezaExpandida (valor + fator k + nivel confianca + unidade)
  - NumeroCertificado (NIT-DICLA-021 — sequencial inviolavel)

Referencias normativas:
  - VIM 3a edicao (Vocabulario Internacional de Metrologia)
  - ISO/IEC 17025:2017 cl. 7.6 (incerteza), 7.8 (relato)
  - JCGM 100:2008 (GUM — Guide to Uncertainty in Measurement)
  - ILAC P14 (regra para fator k variavel)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import ClassVar


class Grandeza(str, Enum):
    """Grandezas RBC mais comuns. Lista AMPLIAVEL via PR + revisao consultor RBC.

    NAO substitui escopo acreditado do tenant — esse vem do CGCRE.
    Whitelist evita drift "massa" vs "Massa" vs "massa_padrao" vs "Massa (kg)".
    """

    MASSA = "massa"
    TEMPERATURA = "temperatura"
    PRESSAO = "pressao"
    VOLUME = "volume"
    COMPRIMENTO = "comprimento"
    ELETRICA_TENSAO = "eletrica_tensao"
    ELETRICA_CORRENTE = "eletrica_corrente"
    ELETRICA_RESISTENCIA = "eletrica_resistencia"
    ELETRICA_POTENCIA = "eletrica_potencia"
    TEMPO = "tempo"
    FREQUENCIA = "frequencia"
    FORCA = "forca"
    TORQUE = "torque"
    DUREZA = "dureza"
    UMIDADE = "umidade"
    PH = "ph"
    DENSIDADE = "densidade"
    VAZAO = "vazao"
    VELOCIDADE = "velocidade"
    ACELERACAO = "aceleracao"

    @classmethod
    def from_string(cls, s: str) -> Grandeza:
        """Normalizacao defensiva — lowercase + trim."""
        try:
            return cls(s.strip().lower())
        except ValueError as e:
            raise ValueError(
                f"Grandeza desconhecida: {s!r}. "
                f"Valores aceitos: {[g.value for g in cls]}. "
                f"Pra adicionar: ADR + revisao consultor-rbc-iso17025."
            ) from e


# Unidades SI + tolerancias comuns RBC. Lista AMPLIAVEL.
_UNIDADES_VALIDAS = frozenset({
    # Massa
    "kg", "g", "mg", "ug", "t",
    # Temperatura
    "K", "C", "F",  # Kelvin, Celsius, Fahrenheit
    # Pressao
    "Pa", "kPa", "MPa", "bar", "mbar", "atm", "psi", "mmHg",
    # Volume
    "m3", "L", "mL", "uL",
    # Comprimento
    "m", "mm", "um", "nm", "km",
    # Eletrica
    "V", "mV", "kV", "A", "mA", "uA", "Ohm", "kOhm", "MOhm", "W", "kW", "MW",
    # Tempo / freq
    "s", "ms", "us", "min", "h", "Hz", "kHz", "MHz", "GHz",
    # Forca / torque
    "N", "kN", "MN", "Nm", "kNm",
    # Dureza
    "HRC", "HRB", "HV", "HB",
    # Outras
    "pct", "ppm", "ppb",  # percentual, partes-por-milhao
    "pH",
    "kg/m3", "g/cm3",
    "L/min", "L/h", "m3/h",
    "m/s", "km/h",
    "m/s2",  # aceleracao (unidade canonica SI; "g" ja listado acima como grama)
    # Adimensional
    "1",
})


@dataclass(frozen=True)
class FaixaMedicao:
    """Faixa de medicao de instrumento ou padrao.

    Limites em unidade SI ou tolerada RBC.

    Exemplo:
      FaixaMedicao(inferior=Decimal("0.0"), superior=Decimal("200.0"), unidade="kg")

    Invariantes:
      - inferior < superior
      - unidade na whitelist
      - decimal com precisao suficiente (NAO float — erro de arredondamento)
    """

    inferior: Decimal
    superior: Decimal
    unidade: str

    def __post_init__(self) -> None:
        if not isinstance(self.inferior, Decimal):
            raise ValueError(
                f"FaixaMedicao.inferior deve ser Decimal (achou {type(self.inferior).__name__}) "
                f"— float introduz erro de arredondamento metrologico"
            )
        if not isinstance(self.superior, Decimal):
            raise ValueError(
                f"FaixaMedicao.superior deve ser Decimal (achou {type(self.superior).__name__})"
            )
        if self.inferior >= self.superior:
            raise ValueError(
                f"FaixaMedicao: inferior {self.inferior} >= superior {self.superior}"
            )
        if self.unidade not in _UNIDADES_VALIDAS:
            raise ValueError(
                f"FaixaMedicao.unidade {self.unidade!r} nao esta na whitelist. "
                f"Aceitas: {sorted(_UNIDADES_VALIDAS)}"
            )

    def amplitude(self) -> Decimal:
        return self.superior - self.inferior

    def contem(self, valor: Decimal) -> bool:
        if not isinstance(valor, Decimal):
            raise ValueError("contem() exige Decimal")
        return self.inferior <= valor <= self.superior

    def __str__(self) -> str:
        return f"[{self.inferior}, {self.superior}] {self.unidade}"


@dataclass(frozen=True)
class IncertezaExpandida:
    """Incerteza expandida (U) com fator k e nivel de confianca declarado.

    Conforme JCGM 100 (GUM):
      U = k * u_c
    onde u_c = incerteza padrao combinada.

    Para distribuicao normal, k=2 corresponde a ~95.45%; k=3 a ~99.73%.
    Para Student-t com graus de liberdade efetivos baixos, k pode ser maior
    (cobertura ILAC P14).

    Invariantes (cl. 7.6 ISO 17025 + ILAC P14):
      - valor >= 0
      - fator_k > 0
      - nivel_confianca in (0, 1) (exclusivo) — declarado como decimal (0.95)
      - unidade na whitelist
      - graus_liberdade >= 1 (ou None se distribuicao normal assumida)
    """

    valor: Decimal
    fator_k: Decimal
    nivel_confianca: Decimal  # ex: Decimal("0.9545")
    unidade: str
    graus_liberdade_efetivos: int | None = None  # None = normal assumida

    def __post_init__(self) -> None:
        for nome in ("valor", "fator_k", "nivel_confianca"):
            v = getattr(self, nome)
            if not isinstance(v, Decimal):
                raise ValueError(
                    f"IncertezaExpandida.{nome} deve ser Decimal (achou {type(v).__name__}) "
                    f"— float introduz erro metrologico"
                )
        if self.valor < 0:
            raise ValueError(f"IncertezaExpandida.valor < 0: {self.valor}")
        if self.fator_k <= 0:
            raise ValueError(f"IncertezaExpandida.fator_k <= 0: {self.fator_k}")
        if not (Decimal("0") < self.nivel_confianca < Decimal("1")):
            raise ValueError(
                f"IncertezaExpandida.nivel_confianca {self.nivel_confianca} fora de (0,1) "
                f"— declarar como decimal (ex: Decimal('0.9545') pra 95.45%)"
            )
        if self.unidade not in _UNIDADES_VALIDAS:
            raise ValueError(
                f"IncertezaExpandida.unidade {self.unidade!r} nao esta na whitelist"
            )
        if self.graus_liberdade_efetivos is not None and self.graus_liberdade_efetivos < 1:
            raise ValueError(
                f"graus_liberdade_efetivos < 1: {self.graus_liberdade_efetivos}"
            )

    def incerteza_padrao_combinada(self) -> Decimal:
        """u_c = U / k"""
        return self.valor / self.fator_k

    def __str__(self) -> str:
        pct = float(self.nivel_confianca * 100)
        return f"U = {self.valor} {self.unidade} (k={self.fator_k}, {pct:.2f}%)"


# Numero de certificado NIT-DICLA-021 — sequencial inviolavel por tenant + ano.
# Formato proposto Aferê: <TENANT_SLUG>-<YYYY>-<NNNNNN>  ex: BALANCAS-2026-000042
_NUM_CERT_RE = re.compile(r"^[A-Z0-9]{2,16}-\d{4}-\d{6}$")


@dataclass(frozen=True)
class NumeroCertificado:
    """Numero de certificado de calibracao — sequencial inviolavel por tenant+ano.

    NIT-DICLA-021: sequencia nao pode ter buracos visiveis (Receita+Mariza).
    Tenant_slug + ano + 6 digitos zerados a esquerda.

    INV-CER-NUM-001 (a criar Onda 4): nenhum certificado pode ser inserido
    com numero fora de sequencia consecutiva — trigger PG valida.
    """

    value: str

    _RE: ClassVar[re.Pattern[str]] = _NUM_CERT_RE

    def __post_init__(self) -> None:
        v = self.value.strip().upper()
        if not NumeroCertificado._RE.match(v):
            raise ValueError(
                f"NumeroCertificado formato invalido: {self.value!r} "
                f"(esperado <TENANT>-<YYYY>-<NNNNNN>, ex: BALANCAS-2026-000042)"
            )
        object.__setattr__(self, "value", v)

    @property
    def tenant_slug(self) -> str:
        return self.value.split("-", 2)[0]

    @property
    def ano(self) -> int:
        return int(self.value.split("-", 2)[1])

    @property
    def sequencial(self) -> int:
        return int(self.value.split("-", 2)[2])

    def __str__(self) -> str:
        return self.value
