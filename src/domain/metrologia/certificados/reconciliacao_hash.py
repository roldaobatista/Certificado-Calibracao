"""Fecho WORM da tabela de reconciliação ponto-a-ponto (M8 Fatia 1a, T-CER-011).

`reconciliacao_hash` é o tamper-evidence da DECISÃO de reconciliação (partição +
exclusões do RT), não só dos números upstream. Replica o padrão `cadeia_pontos_hash`
do ADR-0077 (encadeia os pontos ordenados por `ponto_calibracao` ASC) reusando
`canonicalizar_payload_para_hmac` + `formatar_hash_versionado` (cl. 7.11 replay
determinístico — INV-CER-RECONCILIA-004 / INV-DOC-CANON-001 / INV-HMAC-001..005).

NÃO confundir com:
  - `replay_determinismo_hash` (ADR-0077) = hash do CÁLCULO GUM do agregado/ponto j*.
  - `cadeia_pontos_hash` (ADR-0077) = fecho dos replay_hash dos pontos do orçamento.
`reconciliacao_hash` é o fecho da EMISSÃO (quais pontos entraram, com que classe).

Placeholder SHA-256 (igual `_gerar_replay_hash`/`cadeia_hash` da calibração): quando
`infrastructure/.../hash_kms.py` existir, troca SHA-256 por HMAC com chave KMS.
PURO — Decimal→str / UUID→str ANTES de canonicalizar (json não serializa Decimal).
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from decimal import Decimal
from typing import Protocol

from src.domain.metrologia.calibracao.hash_versionado import (
    VERSAO_HMAC_ATUAL,
    canonicalizar_payload_para_hmac,
    formatar_hash_versionado,
)

from .enums import ClassificacaoPonto


class _PontoReconciliavel(Protocol):
    """Forma estrutural mínima para o hash — serve tanto para `PontoReconciliado`
    (resultado puro Fatia 0) quanto `PontoReconciliadoSnapshot` (persistível).

    Atributos como `@property` (read-only) para que dataclasses FROZEN satisfaçam
    o Protocol (atributo mutável em Protocol exige implementador settable)."""

    @property
    def ponto_calibracao(self) -> Decimal: ...
    @property
    def valor_reportado(self) -> Decimal: ...
    @property
    def U_no_ponto(self) -> Decimal: ...  # U é notação metrológica canônica
    @property
    def k_no_ponto(self) -> Decimal: ...
    @property
    def nivel_confianca_no_ponto(self) -> Decimal: ...
    @property
    def grau_liberdade_efetivo_no_ponto(self) -> Decimal: ...
    @property
    def cmc_no_ponto(self) -> Decimal | None: ...
    @property
    def classificacao(self) -> ClassificacaoPonto: ...
    @property
    def incluido_no_certificado(self) -> bool: ...


def _str_ou_none(valor: Decimal | None) -> str | None:
    """Decimal→str preservando None (NÃO usar truthiness — Decimal('0') é falsy)."""
    return None if valor is None else str(valor)


def reconciliacao_hash(
    *,
    pontos: Sequence[_PontoReconciliavel],
    versao_reconciliacao: str,
    faixa_certificado_min: Decimal | None,
    faixa_certificado_max: Decimal | None,
    tipo_acreditacao: str,
) -> str:
    """Hash versionado do fecho da reconciliação. Determinístico: mesma entrada →
    mesmo hash, independente da ordem dos `pontos` na entrada (ordena ASC antes)."""
    ordenados = sorted(pontos, key=lambda p: p.ponto_calibracao)
    payload = {
        "versao_reconciliacao": versao_reconciliacao,
        "faixa_certificado_min": _str_ou_none(faixa_certificado_min),
        "faixa_certificado_max": _str_ou_none(faixa_certificado_max),
        "tipo_acreditacao": tipo_acreditacao,
        "pontos": [
            {
                "ponto": str(p.ponto_calibracao),
                "valor_reportado": str(p.valor_reportado),
                "U": str(p.U_no_ponto),
                "k": str(p.k_no_ponto),
                "nivel_confianca": str(p.nivel_confianca_no_ponto),
                "nu_eff": str(p.grau_liberdade_efetivo_no_ponto),
                "classificacao": p.classificacao.value,
                "incluido_no_certificado": p.incluido_no_certificado,
                "cmc_no_ponto": _str_ou_none(p.cmc_no_ponto),
            }
            for p in ordenados
        ],
    }
    digest = hashlib.sha256(canonicalizar_payload_para_hmac(payload)).digest()
    return formatar_hash_versionado(VERSAO_HMAC_ATUAL, digest)
