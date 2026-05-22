"""Service de consentimento historico granular do cedente (US-EQP-004
T-EQP-039 + T-EQP-041 / P-EQP-R6).

Duas operacoes:

1. `conceder_consentimento_historico` — chamada pelo
   `services_transferencia.solicitar_transferencia` quando a
   transferencia e EFETIVADA. Cria registro em
   `ConsentimentoHistoricoEquipamento` + publica
   `equipamento.consentimento_historico_concedido` no bus_outbox.

2. `revogar_consentimento_historico` — chamada pelo endpoint POST
   `/equipamentos/{id}/consentimento-historico/revogar/`. Grava
   `revogado_em` + hash da justificativa + publica
   `equipamento.consentimento_historico_revogado`. One-shot — trigger
   PG bloqueia segunda revogacao.

Payload sanitizado (whitelist FECHADA — defesa em profundidade contra
vazamento de PII via cadeia auditavel WORM 25a):

CONCEDIDO:
    {tenant_id, equipamento_id, transferencia_id, consentimento_id,
     nivel, cedente_id_hash, concedido_em, via_concessao}

REVOGADO:
    {tenant_id, equipamento_id, consentimento_id, cedente_id_hash,
     justificativa_hash, via_revogacao, revogado_em}

NUNCA: texto da justificativa cru, UUID do cedente em claro.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from django.db import transaction
from django.utils import timezone

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.equipamentos.models import (
    ConsentimentoHistoricoEquipamento,
    Equipamento,
    NivelConsentimentoHistorico,
    TransferenciaEquipamentoAceite,
    ViaAceiteTransferencia,
)
from src.infrastructure.equipamentos.validators import (
    validar_justificativa_revogacao_consentimento,
)


class ConsentimentoInvalido(Exception):
    """Base de erros do service de consentimento historico."""


class ConsentimentoJaRevogado(ConsentimentoInvalido):
    """Revogacao e one-shot — segunda tentativa retorna 412."""


class JustificativaInvalida(ConsentimentoInvalido):
    """Justificativa <30 chars ou contem PII direta."""


@dataclass(frozen=True)
class ResultadoConcessao:
    consentimento: ConsentimentoHistoricoEquipamento
    cadeia_linha_id: UUID
    outbox_enfileirado: bool


@dataclass(frozen=True)
class ResultadoRevogacao:
    consentimento: ConsentimentoHistoricoEquipamento
    cadeia_linha_id: UUID
    outbox_enfileirado: bool


def derivar_nivel_do_aceite_dump(aceite_dump: dict) -> str:
    """Backwards-compat: aceite antigo so tinha
    `consentimento_historico_expresso: bool`. Novo aceite tem
    `nivel_consentimento_historico: 'nada'|'resumo'|'completo'`.

    Regra:
    - Se `nivel_consentimento_historico` presente e em enum: usa.
    - Senao se `consentimento_historico_expresso=True`: 'completo'
      (preserva semantica binaria do termo v1.0).
    - Senao: 'nada'.
    """
    nivel_raw = str(aceite_dump.get("nivel_consentimento_historico", "")).strip()
    if nivel_raw in NivelConsentimentoHistorico.values:
        return nivel_raw
    if bool(aceite_dump.get("consentimento_historico_expresso", False)):
        return NivelConsentimentoHistorico.COMPLETO.value
    return NivelConsentimentoHistorico.NADA.value


def conceder_consentimento_historico(
    *,
    tenant_id: UUID,
    equipamento: Equipamento,
    transferencia: TransferenciaEquipamentoAceite,
    cedente_cliente_id: UUID | None,
    nivel: str,
    concedido_por_id: UUID,
    via_concessao: str,
    causation_id: UUID | None = None,
) -> ResultadoConcessao:
    """Grava 1 registro de consentimento + publica evento canonico.

    Pre-condicoes (fail-fast):
    - `nivel` em `NivelConsentimentoHistorico.values`.
    - `via_concessao` em `ViaAceiteTransferencia.values`.
    - Constraint UNIQUE no banco impede 2 consentimentos ativos para a
      mesma transferencia (defesa contra duplicacao por race).
    """
    if nivel not in NivelConsentimentoHistorico.values:
        raise ConsentimentoInvalido(
            f"nivel '{nivel}' invalido — use nada/resumo/completo."
        )
    if via_concessao not in ViaAceiteTransferencia.values:
        raise ConsentimentoInvalido(
            f"via_concessao '{via_concessao}' invalida."
        )

    causation_id = causation_id or uuid4()

    with transaction.atomic():
        consentimento = ConsentimentoHistoricoEquipamento.objects.create(
            tenant_id=tenant_id,
            equipamento=equipamento,
            transferencia_origem=transferencia,
            cedente_cliente_id=cedente_cliente_id,
            nivel=nivel,
            concedido_por_id=concedido_por_id,
            via_concessao=via_concessao,
        )

        evento = publicar_evento(
            acao="equipamento.consentimento_historico_concedido",
            tenant_id=tenant_id,
            usuario_id=concedido_por_id,
            causation_id=causation_id,
            payload={
                "tenant_id": str(tenant_id),
                "equipamento_id": str(equipamento.id),
                "transferencia_id": str(transferencia.id),
                "consentimento_id": str(consentimento.id),
                "nivel": nivel,
                "cedente_id_hash": (
                    hashear_pii_com_salt_tenant(str(cedente_cliente_id), tenant_id)
                    if cedente_cliente_id
                    else ""
                ),
                "via_concessao": via_concessao,
                "concedido_em": consentimento.concedido_em.isoformat(),
            },
            resource_summary=(
                f"equipamento:{equipamento.id}:consentimento_historico:"
                f"{consentimento.id}:concedido"
            ),
        )

    return ResultadoConcessao(
        consentimento=consentimento,
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )


def revogar_consentimento_historico(
    *,
    tenant_id: UUID,
    consentimento: ConsentimentoHistoricoEquipamento,
    revogado_por_id: UUID,
    justificativa: str,
    via_revogacao: str,
    causation_id: UUID | None = None,
) -> ResultadoRevogacao:
    """Marca consentimento como revogado + publica evento canonico.

    Pre-condicoes (fail-fast):
    - `justificativa` >=30 chars + anti-PII (validator dedicado).
    - `via_revogacao` em `ViaAceiteTransferencia.values`.
    - `consentimento.revogado_em` IS NULL (one-shot — trigger PG cobre
      em camada B; aqui camada A clara para o caller mapear 412).
    """
    try:
        validar_justificativa_revogacao_consentimento(justificativa)
    except ValueError as exc:
        raise JustificativaInvalida(str(exc)) from exc

    if via_revogacao not in ViaAceiteTransferencia.values:
        raise ConsentimentoInvalido(
            f"via_revogacao '{via_revogacao}' invalida."
        )

    if consentimento.revogado_em is not None:
        raise ConsentimentoJaRevogado(
            "Consentimento ja revogado — re-revogar nao tem efeito (one-shot)."
        )

    causation_id = causation_id or uuid4()
    justificativa_hash = hashear_pii_com_salt_tenant(
        justificativa.strip(), tenant_id
    )

    with transaction.atomic():
        agora = timezone.now()
        ConsentimentoHistoricoEquipamento.objects.filter(
            id=consentimento.id, tenant_id=tenant_id
        ).update(
            revogado_em=agora,
            revogado_por_id=revogado_por_id,
            revogado_justificativa_hash=justificativa_hash,
            revogado_via=via_revogacao,
        )
        consentimento.refresh_from_db()

        evento = publicar_evento(
            acao="equipamento.consentimento_historico_revogado",
            tenant_id=tenant_id,
            usuario_id=revogado_por_id,
            causation_id=causation_id,
            payload={
                "tenant_id": str(tenant_id),
                "equipamento_id": str(consentimento.equipamento_id),
                "consentimento_id": str(consentimento.id),
                "cedente_id_hash": (
                    hashear_pii_com_salt_tenant(
                        str(consentimento.cedente_cliente_id), tenant_id
                    )
                    if consentimento.cedente_cliente_id
                    else ""
                ),
                "justificativa_hash": justificativa_hash,
                "via_revogacao": via_revogacao,
                "revogado_em": agora.isoformat(),
            },
            resource_summary=(
                f"equipamento:{consentimento.equipamento_id}:"
                f"consentimento_historico:{consentimento.id}:revogado"
            ),
        )

    return ResultadoRevogacao(
        consentimento=consentimento,
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )
