"""Service de transferencia de equipamento (US-EQP-004 / T-EQP-034..040).

Orquestra:
1. Pre-validacao: INV-050 (cessionario mesmo tenant) + INV-INT-010
   (cessionario e cedente nao bloqueados — predicate Marco 1).
2. Cria `TransferenciaEquipamentoAceite` em PENDENTE.
3. Se ambos aceites validos no payload: efetiva imediatamente
   (atualiza `Equipamento.cliente_atual_id` + publica
   `equipamento.transferido` + status -> EFETIVADA).
4. Se so um aceite (ou nenhum): mantem PENDENTE (Wave A: endpoint de
   aceite tardio + job de expiracao SLA).

Defesas:
- INV-050 (AC-EQP-004-2): cessionario.tenant_id == equipamento.tenant_id.
  RLS bloqueia leitura cross-tenant; aqui validamos via use case +
  retorno generico 422 "cliente nao encontrado neste tenant" sem
  oracle.
- INV-INT-010 (AC-EQP-004-3): cedente E cessionario passam pelo
  predicate `cliente_nao_bloqueado` Marco 1. 412 com motivo estavel.
- Status quente (cedente == cessionario, equipamento ja transferido
  pra cessionario, motivo=outro sem motivo_detalhe) -> ValueError.

Evento publicado:
- `equipamento.transferido` com payload sanitizado: tenant_id,
  equipamento_id, cedente_id_hash, cessionario_id_hash,
  motivo_categoria, transferencia_id, texto_termo_versao_id,
  causation_id, transferido_em. NUNCA texto motivo_detalhe cru.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from django.db import transaction
from django.utils import timezone

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.clientes.models import Cliente
from src.infrastructure.clientes.predicates_authz import cliente_nao_bloqueado
from src.infrastructure.equipamentos.models import (
    Equipamento,
    MotivoCategoriaTransferencia,
    StatusTransferencia,
    TransferenciaEquipamentoAceite,
    ViaAceiteTransferencia,
)


class TransferenciaInvalida(Exception):
    """Base de erros do service de transferencia."""


class CessionarioCrossTenant(TransferenciaInvalida):
    """INV-050 — cessionario.tenant_id != equipamento.tenant_id.
    Mensagem GENERICA (sem oracle cross-tenant)."""


class ClienteBloqueado(TransferenciaInvalida):
    """INV-INT-010 — cedente ou cessionario com bloqueio comercial ativo."""

    def __init__(self, lado: str, motivo: str) -> None:
        super().__init__(f"{lado} bloqueado: {motivo}")
        self.lado = lado
        self.motivo = motivo


class CessionarioIgualCedente(TransferenciaInvalida):
    """Cessionario == cedente — sem efeito."""


class MotivoDetalheObrigatorio(TransferenciaInvalida):
    """motivo_categoria='outro' exige motivo_detalhe."""


@dataclass(frozen=True)
class Aceite:
    """Schema canonico do JSONB de aceite (cedente ou cessionario).

    Campo `nivel_consentimento_historico` (T-EQP-039 / P-EQP-R6): 3
    niveis granulares ('nada' / 'resumo' / 'completo'). Quando vazio,
    o service deriva via `consentimento_historico_expresso` (legacy bool
    do termo v1.0 — True=completo, False=nada).
    """

    tipo: str  # ViaAceiteTransferencia.value
    usuario_id_atendente: UUID
    observacao: str = ""
    consentimento_historico_expresso: bool = False
    nivel_consentimento_historico: str = ""

    def como_jsonb(self) -> dict[str, Any]:
        return {
            "tipo": self.tipo,
            "usuario_id_atendente": str(self.usuario_id_atendente),
            "observacao": self.observacao,
            "consentimento_historico_expresso": self.consentimento_historico_expresso,
            "nivel_consentimento_historico": self.nivel_consentimento_historico,
        }


@dataclass(frozen=True)
class DadosSolicitacaoTransferencia:
    cessionario_cliente_id: UUID
    motivo_categoria: str
    motivo_detalhe: str = ""
    aceite_cedente: Aceite | None = None
    aceite_cessionario: Aceite | None = None
    texto_termo_versao_id: str = "v1.0-2026-05-22"


@dataclass(frozen=True)
class ResultadoTransferencia:
    transferencia: TransferenciaEquipamentoAceite
    foi_efetivada: bool
    cadeia_linha_id: UUID | None
    outbox_enfileirado: bool


def _aceite_valido(aceite_dump: dict[str, Any]) -> bool:
    """Aceite e considerado valido quando tem `tipo` reconhecido e
    `usuario_id_atendente`."""
    if not aceite_dump:
        return False
    tipo = aceite_dump.get("tipo", "")
    if tipo not in ViaAceiteTransferencia.values:
        return False
    if not aceite_dump.get("usuario_id_atendente"):
        return False
    return True


def solicitar_transferencia(
    *,
    tenant_id: UUID,
    equipamento: Equipamento,
    solicitado_por_id: UUID,
    dados: DadosSolicitacaoTransferencia,
    causation_id: UUID | None = None,
) -> ResultadoTransferencia:
    """Cria `TransferenciaEquipamentoAceite` + efetiva se ambos aceites
    validos.

    Pre-condicoes (fail-fast):
    - motivo_categoria em enum.
    - motivo_detalhe obrigatorio quando motivo='outro'.
    - cessionario != cedente (no momento da solicitacao).
    - cessionario.tenant_id == equipamento.tenant_id (INV-050).
    - cedente nao bloqueado (se existe — INV-INT-010).
    - cessionario nao bloqueado (INV-INT-010).
    """
    if dados.motivo_categoria not in MotivoCategoriaTransferencia.values:
        raise TransferenciaInvalida(
            f"motivo_categoria '{dados.motivo_categoria}' invalido."
        )
    if (
        dados.motivo_categoria == MotivoCategoriaTransferencia.OUTRO.value
        and not (dados.motivo_detalhe or "").strip()
    ):
        raise MotivoDetalheObrigatorio(
            "motivo_categoria='outro' exige motivo_detalhe nao-vazio."
        )

    # INV-050: cessionario tem que existir NO MESMO tenant (RLS aplica).
    # Se RLS bloqueia (outro tenant), filter retorna empty -> 422 generico.
    cessionario = (
        Cliente.objects.filter(id=dados.cessionario_cliente_id).only("id", "tenant_id").first()
    )
    if cessionario is None or cessionario.tenant_id != equipamento.tenant_id:
        raise CessionarioCrossTenant(
            "cliente nao encontrado neste tenant"
        )

    cedente_id = equipamento.cliente_atual_id
    if cedente_id == dados.cessionario_cliente_id:
        raise CessionarioIgualCedente(
            "cessionario igual ao cedente — sem efeito."
        )

    # INV-INT-010: cedente bloqueado bloqueia.
    if cedente_id is not None:
        ok, motivo = cliente_nao_bloqueado({"cliente_id": str(cedente_id)})
        if not ok:
            raise ClienteBloqueado(lado="cedente", motivo=motivo)
    # INV-INT-010: cessionario bloqueado bloqueia.
    ok, motivo = cliente_nao_bloqueado({"cliente_id": str(cessionario.id)})
    if not ok:
        raise ClienteBloqueado(lado="cessionario", motivo=motivo)

    causation_id = causation_id or uuid4()

    aceite_cedente_jsonb = (
        dados.aceite_cedente.como_jsonb() if dados.aceite_cedente else {}
    )
    aceite_cessionario_jsonb = (
        dados.aceite_cessionario.como_jsonb() if dados.aceite_cessionario else {}
    )

    with transaction.atomic():
        transferencia = TransferenciaEquipamentoAceite.objects.create(
            tenant_id=tenant_id,
            equipamento=equipamento,
            cedente_cliente_id=cedente_id,
            cessionario_cliente=cessionario,
            motivo_categoria=dados.motivo_categoria,
            motivo_detalhe=dados.motivo_detalhe,
            aceite_cedente=aceite_cedente_jsonb,
            aceite_cessionario=aceite_cessionario_jsonb,
            solicitado_por_id=solicitado_por_id,
            texto_termo_versao_id=dados.texto_termo_versao_id,
        )

        if _aceite_valido(aceite_cedente_jsonb) and _aceite_valido(
            aceite_cessionario_jsonb
        ):
            # Efetiva imediatamente: atualiza Equipamento.cliente_atual_id
            # + publica evento.
            Equipamento.objects.filter(id=equipamento.id).update(
                cliente_atual=cessionario
            )
            transferencia.status = StatusTransferencia.EFETIVADA.value
            transferencia.efetivada_em = timezone.now()
            transferencia.save(update_fields=["status", "efetivada_em"])

            evento = publicar_evento(
                acao="equipamento.transferido",
                tenant_id=tenant_id,
                usuario_id=solicitado_por_id,
                causation_id=causation_id,
                payload={
                    "tenant_id": str(tenant_id),
                    "equipamento_id": str(equipamento.id),
                    "transferencia_id": str(transferencia.id),
                    "cedente_id_hash": (
                        hashear_pii_com_salt_tenant(str(cedente_id), tenant_id)
                        if cedente_id
                        else ""
                    ),
                    "cessionario_id_hash": hashear_pii_com_salt_tenant(
                        str(cessionario.id), tenant_id
                    ),
                    "motivo_categoria": dados.motivo_categoria,
                    "texto_termo_versao_id": dados.texto_termo_versao_id,
                    "transferido_em": transferencia.efetivada_em.isoformat(),
                },
                resource_summary=(
                    f"equipamento:{equipamento.id}:transferido:{transferencia.id}"
                ),
            )

            # T-EQP-039 (P-EQP-R6) — efetivacao automatica grava 1
            # consentimento granular do cedente no MESMO bloco transacional.
            # Bem-derivado: nivel vem do aceite_cedente do JSONB (campo
            # novo) ou retrocompat de `consentimento_historico_expresso`.
            from src.infrastructure.equipamentos.services_consentimento_historico import (
                conceder_consentimento_historico,
                derivar_nivel_do_aceite_dump,
            )

            nivel = derivar_nivel_do_aceite_dump(aceite_cedente_jsonb)
            via_concessao = aceite_cedente_jsonb.get("tipo", "")
            conceder_consentimento_historico(
                tenant_id=tenant_id,
                equipamento=equipamento,
                transferencia=transferencia,
                cedente_cliente_id=cedente_id,
                nivel=nivel,
                concedido_por_id=solicitado_por_id,
                via_concessao=via_concessao,
                causation_id=causation_id,
            )

            return ResultadoTransferencia(
                transferencia=transferencia,
                foi_efetivada=True,
                cadeia_linha_id=evento.cadeia_linha_id,
                outbox_enfileirado=evento.outbox_enfileirado,
            )

    return ResultadoTransferencia(
        transferencia=transferencia,
        foi_efetivada=False,
        cadeia_linha_id=None,
        outbox_enfileirado=False,
    )
