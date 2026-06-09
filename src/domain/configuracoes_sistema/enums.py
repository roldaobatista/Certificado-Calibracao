"""Enums fechados do domínio `configuracoes-sistema` (Fatia 1a — T-CFG-010).

str-mixin → serialização JSON nativa (molde `fiscal/enums.py`). Sem Django (ADR-0007).
"""

from __future__ import annotations

from enum import Enum


class RegimeTributario(str, Enum):
    """Regime de apuração tributária da empresa (US-CFG-003; P2/ADV-01/03).

    CFG é o dono ÚNICO e original deste VO (TL-03 — nenhum módulo o possui hoje).
    `ST` (substituição tributária) NÃO é regime — é atributo do `Imposto.tem_st`
    (ADV-03). IMUNE/ISENTO cobrem operação sem incidência (ADV-01). Conjunto final
    exigível para empresa de calibração = validação contador/OAB pré-produção.
    """

    NORMAL = "normal"
    SIMPLES_NACIONAL = "simples_nacional"
    MEI = "mei"
    LUCRO_PRESUMIDO = "lucro_presumido"
    LUCRO_REAL = "lucro_real"
    IMUNE = "imune"
    ISENTO = "isento"


class TipoImposto(str, Enum):
    """Tributos cujo catálogo de alíquota o tenant configura (US-CFG-003)."""

    ICMS = "icms"
    ISS = "iss"
    PIS = "pis"
    COFINS = "cofins"
    IRRF = "irrf"
    CSLL = "csll"
    INSS = "inss"


class TipoDocumento(str, Enum):
    """Tipos de documento que o tenant numera LOCALMENTE (US-CFG-002).

    NFS-e/NF NÃO entram (numeradas pelo BaaS/município — ADR-0008/ADR-0080).
    """

    OS = "os"
    ORCAMENTO = "orcamento"
    FATURA = "fatura"
    CERTIFICADO = "certificado"
    RECIBO = "recibo"
    INTERNO = "interno"


class RegimeNumeracao(str, Enum):
    """Regime de numeração de uma série (ADR-0080), derivado do tipo.

    GAP_LESS = sem buraco algum (exigência fiscal/ISO — fatura/certificado) via
    reserva-TTL. BURACOS_ACEITOS = buraco por rollback tolerado (os/orcamento/
    recibo/interno) via UPDATE atômico (estilo ADR-0056).
    """

    GAP_LESS = "gap_less"
    BURACOS_ACEITOS = "buracos_aceitos"
