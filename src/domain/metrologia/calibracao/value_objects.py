"""Value objects M4 calibracao (P4 Fase 2 — T-CAL-026..030).

VOs puros (sem Django/PG/IO). 5 novos VOs especificos do Marco 4 que
nao caberiam em `src/domain/metrologia/value_objects.py` (esse fica
com grandezas + faixa + incerteza expandida + numero de certificado,
compartilhados com modulo `certificados` Wave A).

Catalogo:
    VersaoMotorCalculo - semver + commit_hash + algoritmo_id + JanelaVigencia.
        Cravado por calibracao (INV-CAL-VERSAO-001 + ADR-0025 cl. 7.11).
    EscoreZ - z-score Western Electric + regra violada (P-CAL-R8 RBC).
    ZonaILACG8 - 6 zonas ILAC G8 + NA (ADR-0024 revisado + INV-CAL-DEC-005).
    HashVersionadoV0 - VO do formato v<NN>$<base64> (ADR-0064). Helper de
        parse/format em hash_versionado.py.
    IncertezaCombinada - u_c (GUM §5.1.2 — combinacao Tipo A + Tipo B
        ponderada por correlacao). Sem expansao (k); IncertezaExpandida
        cobre isso em src/domain/metrologia/value_objects.py.

Referencias normativas:
    - JCGM 100:2008 (GUM cl. 5)
    - NIT-DICLA-030 rev. 15 §7
    - ILAC G8 (regras de decisao) revisada 2019 — 6 zonas
    - NIST/NBS Handbook 91 (Western Electric rules 1-8)
    - ISO/IEC 17025:2017 cl. 7.6 (incerteza), 7.8.6 (regra de decisao),
      7.11 (validacao software)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import ClassVar

from src.domain.shared.value_objects import JanelaVigencia

# =====================================================================
# T-CAL-026 - VersaoMotorCalculo (INV-CAL-VERSAO-001 + ADR-0025 cl. 7.11)
# =====================================================================

_ALGORITMO_ID_ACEITOS = frozenset(
    {
        "GUM_CLASSICO_v1",
        "MONTE_CARLO_v1",
    }
)

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9a-zA-Z\-\.]+)?$")
_COMMIT_HASH_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class VersaoMotorCalculo:
    """Versao do motor de calculo cravada por calibracao (INV-CAL-VERSAO-001).

    Toda OrcamentoIncerteza/Calibracao carrega snapshot da versao do motor
    que rodou o calculo. Sem isso, replay deterministico (ADR-0025) nao
    consegue reproduzir resultados anos depois.

    Invariantes:
      - semver no formato MAJOR.MINOR.PATCH (com pre-release opcional)
      - commit_hash com 40 chars hex (SHA-1 git)
      - algoritmo_id na whitelist (GUM_CLASSICO_v1 | MONTE_CARLO_v1)
      - janela_vigencia obrigatoria (ADR-0030)
    """

    semver: str
    commit_hash: str
    algoritmo_id: str
    janela_vigencia: JanelaVigencia

    _SEMVER_RE: ClassVar[re.Pattern[str]] = _SEMVER_RE
    _COMMIT_HASH_RE: ClassVar[re.Pattern[str]] = _COMMIT_HASH_RE

    def __post_init__(self) -> None:
        if not VersaoMotorCalculo._SEMVER_RE.match(self.semver):
            raise ValueError(
                f"VersaoMotorCalculo.semver invalido: {self.semver!r} "
                f"(esperado MAJOR.MINOR.PATCH; ex: '1.0.0')"
            )
        if not VersaoMotorCalculo._COMMIT_HASH_RE.match(self.commit_hash):
            raise ValueError(
                f"VersaoMotorCalculo.commit_hash invalido: {self.commit_hash!r} "
                f"(esperado SHA-1 git 40 chars hex lowercase)"
            )
        if self.algoritmo_id not in _ALGORITMO_ID_ACEITOS:
            raise ValueError(
                f"VersaoMotorCalculo.algoritmo_id {self.algoritmo_id!r} "
                f"fora da whitelist {sorted(_ALGORITMO_ID_ACEITOS)}"
            )

    def __str__(self) -> str:
        return f"{self.algoritmo_id} {self.semver}@{self.commit_hash[:7]}"


# =====================================================================
# T-CAL-027 - EscoreZ + regra Western Electric (P-CAL-R8 RBC + cl. 5.4)
# =====================================================================

REGRAS_WESTERN_ELECTRIC_ACEITAS = frozenset(
    {
        "RULE_1_3SIGMA",
        "RULE_2_SEVEN_SAME_SIDE",
        "RULE_3_TREND",
        "RULE_5_TWO_OF_THREE",
    }
)


class ClassificacaoZ(str, Enum):
    """3 zonas de severidade do escore z (NIT-DICLA-026 rev. 15 cl. 5.4)."""

    ACEITAVEL = "ACEITAVEL"  # |z| <= 2
    WARNING = "WARNING"  # 2 < |z| <= 3 (plano de acao P-CAL-R8)
    UNACCEPTABLE = "UNACCEPTABLE"  # |z| > 3 (NC formal AnaliseImpactoNCProficiencia)


@dataclass(frozen=True)
class EscoreZ:
    """z-score de medicao de controle + classificacao Western Electric.

    Calculo classico (NIST/NBS HB 91):
        z = (x - mu) / sigma

    Onde:
      - x = medicao atual
      - mu = media historica do padrao
      - sigma = desvio-padrao historico

    Invariantes:
      - z em Decimal (nunca float — erro de arredondamento metrologico)
      - regra_violada in whitelist ou None
      - classificacao derivada determinante de |z|

    Uso:
      ez = EscoreZ(valor=Decimal("2.5"), regra_violada=None)
      assert ez.classificacao == ClassificacaoZ.WARNING
    """

    valor: Decimal
    regra_violada: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal):
            raise ValueError(
                f"EscoreZ.valor deve ser Decimal (achou {type(self.valor).__name__}) "
                f"— float introduz erro de arredondamento metrologico"
            )
        if self.regra_violada is not None and self.regra_violada not in REGRAS_WESTERN_ELECTRIC_ACEITAS:
            raise ValueError(
                f"EscoreZ.regra_violada {self.regra_violada!r} fora da whitelist "
                f"{sorted(REGRAS_WESTERN_ELECTRIC_ACEITAS)}"
            )

    @property
    def magnitude(self) -> Decimal:
        """|z| - magnitude absoluta para classificacao."""
        return abs(self.valor)

    @property
    def classificacao(self) -> ClassificacaoZ:
        """Classificacao por magnitude (NIT-DICLA-026 cl. 5.4)."""
        m = self.magnitude
        if m <= Decimal("2"):
            return ClassificacaoZ.ACEITAVEL
        if m <= Decimal("3"):
            return ClassificacaoZ.WARNING
        return ClassificacaoZ.UNACCEPTABLE

    def __str__(self) -> str:
        return f"z={self.valor} ({self.classificacao.value})"


# =====================================================================
# T-CAL-028 - ZonaILACG8 (ADR-0024 revisado + INV-CAL-DEC-005)
# =====================================================================


class ZonaILACG8(str, Enum):
    """6 zonas ILAC G8 + NA (ADR-0024 revisado 2026-05-25).

    ILAC G8:2019 §4 reconhece 6 zonas de decisao quando se combina:
      - regra de decisao (aceitacao simples vs banda guarda vs risco compartilhado)
      - posicao relativa do (valor +- U) versus limites LSL/USL

    PASS - valor + U totalmente dentro de [LSL, USL]
    CONDITIONAL_PASS - valor dentro, intervalo de U cruza limite
    PASS_COM_RESSALVA - banda de guarda 30% aplicada e passa nessa zona
    CONDITIONAL_FAIL - valor fora, intervalo de U cruza limite
    FAIL_COM_RESSALVA - valor fora, intervalo de U dentro mas com PFA alto
    FAIL - valor + U totalmente fora
    NA - calibracao descritiva (sem limites de especificacao)
    """

    PASS = "PASS"  # noqa: S105 — valor de enum, nao senha
    CONDITIONAL_PASS = "CONDITIONAL_PASS"  # noqa: S105
    PASS_COM_RESSALVA = "PASS_COM_RESSALVA"  # noqa: S105
    CONDITIONAL_FAIL = "CONDITIONAL_FAIL"
    FAIL_COM_RESSALVA = "FAIL_COM_RESSALVA"
    FAIL = "FAIL"
    NA = "NA"

    @property
    def aprova(self) -> bool:
        """True se zona representa aceitacao (qualquer variante de PASS)."""
        return self in {
            ZonaILACG8.PASS,
            ZonaILACG8.CONDITIONAL_PASS,
            ZonaILACG8.PASS_COM_RESSALVA,
        }

    @property
    def reprova(self) -> bool:
        """True se zona representa rejeicao (qualquer variante de FAIL)."""
        return self in {
            ZonaILACG8.CONDITIONAL_FAIL,
            ZonaILACG8.FAIL_COM_RESSALVA,
            ZonaILACG8.FAIL,
        }

    @property
    def exige_pfa_calculada(self) -> bool:
        """Zonas com ressalva/condicional precisam PFA (Probability of False Accept).

        ILAC G8 §4 + JCGM 106 — calcula a partir de regra_decisao + valor + U + limites.
        """
        return self in {
            ZonaILACG8.CONDITIONAL_PASS,
            ZonaILACG8.PASS_COM_RESSALVA,
            ZonaILACG8.CONDITIONAL_FAIL,
            ZonaILACG8.FAIL_COM_RESSALVA,
        }


# =====================================================================
# T-CAL-029 - HashVersionadoV0 (formato v<NN>$<base64> - ADR-0064 + INV-HMAC-002)
# =====================================================================
#
# VO puro - apenas validacao do formato. Operacao real de HMAC com chave
# KMS Multi-Region fica em src/domain/metrologia/calibracao/hash_versionado.py
# (Batch B - T-CAL-031..036).

_HASH_VERSIONADO_RE = re.compile(r"^v(\d{2})\$([A-Za-z0-9+/]+={0,2})$")
_VERSAO_MIN = 1
_VERSAO_MAX = 99


@dataclass(frozen=True)
class HashVersionadoV0:
    """Hash versionado canonico v<NN>$<base64> (ADR-0064 + INV-HMAC-002).

    Formato fixo:
      v<NN>$<base64_hmac_sha256>

    Onde:
      - NN = numero da versao da chave KMS (01..99, rotacao anual)
      - $ = separador unico (nao ocorre em base64)
      - base64 = HMAC-SHA256 do plaintext canonicalizado com chave v<NN>

    Por que versionado:
      - chave HMAC rotacionada anualmente (KMS Multi-Region MRK)
      - retencao 25a (cl. 8.4 ISO 17025) exige verificar hashes antigos
      - sem versao, chave nova nao verifica hash antigo

    Este VO NAO calcula HMAC - so valida formato + extrai versao + base64.
    Helper crypto real em hash_versionado.py (Batch B).
    """

    raw: str

    _RE: ClassVar[re.Pattern[str]] = _HASH_VERSIONADO_RE

    def __post_init__(self) -> None:
        m = HashVersionadoV0._RE.match(self.raw)
        if not m:
            raise ValueError(
                f"HashVersionadoV0 formato invalido: {self.raw!r} "
                f"(esperado v<NN>$<base64>; ex: 'v01$aGVsbG8=')"
            )
        versao = int(m.group(1))
        if not (_VERSAO_MIN <= versao <= _VERSAO_MAX):
            raise ValueError(
                f"HashVersionadoV0 versao {versao} fora de [{_VERSAO_MIN}, {_VERSAO_MAX}]"
            )

    @property
    def versao(self) -> int:
        """Numero da versao da chave KMS (01..99)."""
        m = HashVersionadoV0._RE.match(self.raw)
        assert m is not None  # ja validado em __post_init__
        return int(m.group(1))

    @property
    def base64_hmac(self) -> str:
        """Componente HMAC base64 (sem prefixo de versao)."""
        m = HashVersionadoV0._RE.match(self.raw)
        assert m is not None
        return m.group(2)

    def __str__(self) -> str:
        return self.raw


# =====================================================================
# T-CAL-030 - IncertezaCombinada (GUM cl. 5.1.2 - u_c)
# =====================================================================


@dataclass(frozen=True)
class IncertezaCombinada:
    """Incerteza padrao combinada u_c (GUM cl. 5.1.2).

    Combina contribuicoes Tipo A (estatistica) + Tipo B (avaliacao)
    via lei de propagacao GUM, com correcoes para correlacao (cl. 5.2.2).

    Sem expansao (k) - IncertezaExpandida (src/domain/metrologia/value_objects.py)
    cobre isso aplicando fator de cobertura.

    Invariantes:
      - valor em Decimal >= 0
      - grau_liberdade_efetivo Welch-Satterthwaite > 0 (ou None pra normal)
      - unidade na whitelist (delegado pra IncertezaExpandida ao expandir)
      - tem_contribuicao_tipo_a + qtd_componentes_tipo_b coerentes
    """

    valor: Decimal
    grau_liberdade_efetivo: int | None  # Welch-Satterthwaite; None se normal
    tem_contribuicao_tipo_a: bool
    qtd_componentes_tipo_b: int

    def __post_init__(self) -> None:
        if not isinstance(self.valor, Decimal):
            raise ValueError(
                f"IncertezaCombinada.valor deve ser Decimal (achou "
                f"{type(self.valor).__name__})"
            )
        if self.valor < 0:
            raise ValueError(f"IncertezaCombinada.valor < 0: {self.valor}")
        if self.grau_liberdade_efetivo is not None and self.grau_liberdade_efetivo < 1:
            raise ValueError(
                f"IncertezaCombinada.grau_liberdade_efetivo < 1: "
                f"{self.grau_liberdade_efetivo}"
            )
        if self.qtd_componentes_tipo_b < 0:
            raise ValueError(
                f"IncertezaCombinada.qtd_componentes_tipo_b < 0: "
                f"{self.qtd_componentes_tipo_b}"
            )
        if not self.tem_contribuicao_tipo_a and self.qtd_componentes_tipo_b == 0:
            raise ValueError(
                "IncertezaCombinada exige >=1 contribuicao (Tipo A ou Tipo B) "
                "— u_c=0 sem fonte declarada vai contra GUM cl. 5.1.2"
            )

    def __str__(self) -> str:
        return f"u_c = {self.valor}"
