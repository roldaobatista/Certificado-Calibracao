"""Use case `acionar_modo_emergencial` — US-LIC-003 / INV-033 (M9 T-LIC-043).

Liberação excepcional auditada de uma operação bloqueada por documento vencido.
Pré-condições de domínio (D-LIC-6/7 — `validar_modo_emergencial`): justificativa
≥100 chars + `assinatura_a3_id` presente (validação criptográfica DIFERIDA —
GATE-LIC-EMERGENCIAL-A3-CRIPTO) + janela ≤7d. Para `ACREDITACAO_CGCRE` o emergencial
libera APENAS operação NÃO-RBC (`libera_apenas_nao_rbc=True` — nunca contorna o
rebaixamento do M8, cl. 8.1.3). Registra `EventoEmergencial` WORM (append-only).
Use case PURO (ADR-0007): exige um `BloqueioOperacional` ativo para o documento.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from src.domain.metrologia.calibracao.hash_versionado import (
    VERSAO_HMAC_ATUAL,
    canonicalizar_payload_para_hmac,
    formatar_hash_versionado,
)
from src.domain.metrologia.licencas_acreditacoes.entities import EventoEmergencial
from src.domain.metrologia.licencas_acreditacoes.erros import (
    ModoEmergencialInvalidoError,
)
from src.domain.metrologia.licencas_acreditacoes.repository import (
    BloqueioRepository,
    EventoEmergencialRepository,
)
from src.domain.metrologia.licencas_acreditacoes.transicoes import (
    validar_modo_emergencial,
)


class BloqueioAtivoAusenteError(Exception):
    """Não há bloqueio operacional ativo para o documento (nada a liberar) — 409."""


@dataclass(frozen=True, slots=True)
class AcionarModoEmergencialInput:
    tenant_id: UUID
    documento_id: UUID
    operacao_executada: str
    justificativa: str
    admin_id: UUID
    assinatura_a3_id: UUID
    janela_dias: int
    criado_em: datetime
    correlation_id: UUID

    def __post_init__(self) -> None:
        if self.criado_em.tzinfo is None:
            raise ValueError(
                "acionar_modo_emergencial: criado_em exige datetime tz-aware."
            )


@dataclass(frozen=True, slots=True)
class AcionarModoEmergencialOutput:
    evento: EventoEmergencial


def _hash_justificativa(texto: str) -> str:
    """Hash versionado da justificativa (tamper-evidence WORM — INV-HMAC). Mesmo
    mecanismo do M8 (`decidir_ponto`): canonicaliza o payload e versiona o digest.
    A justificativa é texto técnico/administrativo, NÃO PII (não há lookup por hash)."""
    digest = hashlib.sha256(
        canonicalizar_payload_para_hmac({"justificativa": texto})
    ).digest()
    return formatar_hash_versionado(VERSAO_HMAC_ATUAL, digest)


def executar(
    inp: AcionarModoEmergencialInput,
    *,
    bloqueio_repo: BloqueioRepository,
    evento_repo: EventoEmergencialRepository,
) -> AcionarModoEmergencialOutput:
    bloqueio = bloqueio_repo.obter_ativo(
        tenant_id=inp.tenant_id, documento_id=inp.documento_id
    )
    if bloqueio is None:
        raise BloqueioAtivoAusenteError(str(inp.documento_id))

    # Pré-condições (≥100ch + a3_id + ≤7d). Retorna libera_apenas_nao_rbc por tipo.
    libera_apenas_nao_rbc = validar_modo_emergencial(
        tipo_documento=bloqueio.tipo_documento,
        justificativa=inp.justificativa,
        assinatura_a3_id=inp.assinatura_a3_id,
        janela_dias=inp.janela_dias,
    )

    evento = EventoEmergencial(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        bloqueio_id=bloqueio.id,
        operacao_executada=inp.operacao_executada,
        justificativa=inp.justificativa,
        justificativa_hash=_hash_justificativa(inp.justificativa),
        admin_id=inp.admin_id,
        assinatura_a3_id=inp.assinatura_a3_id,
        expira_em=inp.criado_em + timedelta(days=inp.janela_dias),
        criado_em=inp.criado_em,
        libera_apenas_nao_rbc=libera_apenas_nao_rbc,
    )
    evento_repo.registrar(evento)
    return AcionarModoEmergencialOutput(evento=evento)


__all__ = [
    "AcionarModoEmergencialInput",
    "AcionarModoEmergencialOutput",
    "BloqueioAtivoAusenteError",
    "ModoEmergencialInvalidoError",
    "executar",
]
