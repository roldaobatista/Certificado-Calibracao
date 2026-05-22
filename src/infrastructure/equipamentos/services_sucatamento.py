"""Service de sucatamento de equipamento (T-EQP-042+043+046 /
US-EQP-005 AC-EQP-005-1+2+5).

Orquestra:
1. Validacao da justificativa (>=30 chars + anti-PII).
2. Consulta porta `certificados.tem_emitido` (snapshot do momento).
3. Cert vigente + (NAO confirmacao_dupla OU NAO ciencia validade
   tecnica registrada) -> 422 com texto canonico do modal.
4. Cria `EquipamentoSucatamento` (1:1 com Equipamento).
5. Atualiza Equipamento.status -> 'sucata' (trigger PG
   `transicao_status_permitida` valida).
6. Publica `equipamento.sucateado` (payload sanitizado).
7. Quando cert vigente: publica `equipamento.sucateado_com_cert_vigente`
   adicional (P-EQP-S9).

Payload sanitizado (whitelist FECHADA — defesa em profundidade WORM
25a NIT-DICLA-021):

SUCATEADO:
    {tenant_id, equipamento_id, sucatamento_id, justificativa_hash,
     sucateado_em, tem_cert_vigente_no_momento}

SUCATEADO_COM_CERT_VIGENTE (adicional quando cert):
    {tenant_id, equipamento_id, sucatamento_id, justificativa_hash,
     texto_modal_versao_id, ciencia_validade_tecnica_registrada,
     sucateado_em}

NUNCA: texto da justificativa cru, dados do cliente, dados do cert.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from django.db import transaction

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.certificados.query_service import tem_emitido
from src.infrastructure.equipamentos.models import (
    Equipamento,
    EquipamentoStatus,
    EquipamentoSucatamento,
)
from src.infrastructure.equipamentos.validators import (
    TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA,
    validar_justificativa_sucatamento,
)


class SucatamentoInvalido(Exception):
    """Base de erros do service de sucatamento."""


class CertVigenteSemConfirmacaoDupla(SucatamentoInvalido):
    """Cert vigente exige `confirmacao_dupla=True` + ciencia validade
    tecnica registrada (P-EQP-R8 / AC-EQP-005-2)."""


class JustificativaInvalida(SucatamentoInvalido):
    """Justificativa <30 chars ou contem PII direta."""


class StatusInvalido(SucatamentoInvalido):
    """Status do equipamento nao permite sucatamento (matriz trigger PG)."""


class SucatamentoDuplicado(SucatamentoInvalido):
    """Equipamento ja sucateado — OneToOne unico."""


@dataclass(frozen=True)
class DadosSucatamento:
    justificativa: str
    confirmacao_dupla: bool = False
    ciencia_validade_tecnica_registrada: bool = False
    texto_modal_versao_id: str = TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA


@dataclass(frozen=True)
class ResultadoSucatamento:
    sucatamento: EquipamentoSucatamento
    tem_cert_vigente_no_momento: bool
    cadeia_linha_id: UUID
    outbox_enfileirado: bool


def sucatear_equipamento(
    *,
    tenant_id: UUID,
    equipamento: Equipamento,
    sucateado_por_id: UUID,
    dados: DadosSucatamento,
    causation_id: UUID | None = None,
) -> ResultadoSucatamento:
    """Sucata o equipamento.

    Pre-condicoes (fail-fast):
    - justificativa >=30 chars + anti-PII.
    - equipamento NAO ja sucateado (OneToOne).
    - status atual permite transicao para 'sucata' (matriz no trigger
      PG `transicao_status_permitida` — validada na hora do UPDATE;
      excecoes mapeadas para `StatusInvalido`).
    - cert vigente -> confirmacao_dupla=True + ciencia_validade=True
      (defesa A no service + B no CHECK `ck_sucatamento_cert_vigente_*`).
    """
    try:
        validar_justificativa_sucatamento(dados.justificativa)
    except ValueError as exc:
        raise JustificativaInvalida(str(exc)) from exc

    if hasattr(equipamento, "sucatamento") and equipamento.sucatamento is not None:
        raise SucatamentoDuplicado(
            "equipamento ja sucateado — sucatamento e terminal e unico."
        )

    tem_cert = tem_emitido(equipamento.id)
    if tem_cert and (
        not dados.confirmacao_dupla
        or not dados.ciencia_validade_tecnica_registrada
    ):
        raise CertVigenteSemConfirmacaoDupla(
            "AC-EQP-005-2 / P-EQP-R8 — sucatamento com certificado "
            "vigente exige `confirmacao_dupla=True` E "
            "`ciencia_validade_tecnica_registrada=True` (modal "
            f"{TEXTO_MODAL_SUCATAMENTO_VERSAO_CANONICA})."
        )

    causation_id = causation_id or uuid4()
    justificativa_hash = hashear_pii_com_salt_tenant(
        dados.justificativa.strip(), tenant_id
    )

    with transaction.atomic():
        sucatamento = EquipamentoSucatamento.objects.create(
            tenant_id=tenant_id,
            equipamento=equipamento,
            justificativa_hash=justificativa_hash,
            tem_cert_vigente_no_momento=tem_cert,
            confirmacao_dupla=dados.confirmacao_dupla if tem_cert else False,
            ciencia_validade_tecnica_registrada=(
                dados.ciencia_validade_tecnica_registrada if tem_cert else False
            ),
            texto_modal_versao_id=dados.texto_modal_versao_id,
            sucateado_por_id=sucateado_por_id,
        )

        # Atualiza Equipamento.status -> 'sucata'. Trigger PG
        # `transicao_status_permitida` valida; se transicao invalida,
        # PG levanta erro que mapeamos para StatusInvalido.
        from django.db import IntegrityError, ProgrammingError

        try:
            Equipamento.objects.filter(id=equipamento.id).update(
                status=EquipamentoStatus.SUCATA.value
            )
        except (IntegrityError, ProgrammingError) as exc:
            raise StatusInvalido(
                f"transicao de status para 'sucata' bloqueada: {exc}"
            ) from exc

        equipamento.refresh_from_db()

        # Evento canonico base (sempre publicado).
        payload_base: dict[str, object] = {
            "tenant_id": str(tenant_id),
            "equipamento_id": str(equipamento.id),
            "sucatamento_id": str(sucatamento.id),
            "justificativa_hash": justificativa_hash,
            "tem_cert_vigente_no_momento": tem_cert,
            "sucateado_em": sucatamento.sucateado_em.isoformat(),
        }
        evento = publicar_evento(
            acao="equipamento.sucateado",
            tenant_id=tenant_id,
            usuario_id=sucateado_por_id,
            causation_id=causation_id,
            payload=payload_base,
            resource_summary=(
                f"equipamento:{equipamento.id}:sucateado:{sucatamento.id}"
            ),
        )

        # P-EQP-S9: evento adicional quando cert vigente.
        if tem_cert:
            publicar_evento(
                acao="equipamento.sucateado_com_cert_vigente",
                tenant_id=tenant_id,
                usuario_id=sucateado_por_id,
                causation_id=causation_id,
                payload={
                    **payload_base,
                    "texto_modal_versao_id": sucatamento.texto_modal_versao_id,
                    "ciencia_validade_tecnica_registrada": True,
                },
                resource_summary=(
                    f"equipamento:{equipamento.id}:"
                    f"sucateado_com_cert_vigente:{sucatamento.id}"
                ),
            )

    return ResultadoSucatamento(
        sucatamento=sucatamento,
        tem_cert_vigente_no_momento=tem_cert,
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )
