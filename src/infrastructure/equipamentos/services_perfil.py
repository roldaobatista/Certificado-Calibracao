"""Service de promocao de perfil do equipamento (T-EQP-009 / P-EQP-T4).

Unica via legitima de Python pra invocar a funcao PG SECURITY DEFINER
`promover_perfil_equipamento_snapshot` (migration 0006). Faz:

1. Pre-validacao Python da justificativa (≥100 chars + anti-PII regex
   via `validators.conter_pii_direta` — defesa em profundidade fora do
   PL/pgSQL onde regex unicode complexa fica deselegante).
2. Chama a funcao PG via cursor `SELECT promover_perfil_...(...)`.
3. Mapeia `raise_exception` PG em sub-tipos `PromocaoInvalida` com
   mensagem PT-BR pra HTTP 422.
4. Publica `equipamento.perfil_promovido` no bus_outbox + cadeia
   (25 anos WORM — ISO 17025 cl. 8.4 + RBC).

NAO cria `EquipamentoVersao` aqui: depende de T-EQP-012 (US-EQP-002).
Quando T-EQP-012 existir, este service ganha INSERT em
`equipamentos_versao` com `motivo_mudanca='mudanca_classe_metrologica'`
+ `assinatura_a3_referencia=p_rt_id_a3_uuid` antes do `publicar_evento`,
dentro da mesma `transaction.atomic`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from django.db import DatabaseError, connection, transaction

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.equipamentos.validators import conter_pii_direta

JUSTIFICATIVA_MIN_CHARS = 100
PERFIS_DESTINO_VALIDOS = frozenset({"C", "B", "A"})


class PromocaoInvalida(Exception):
    """Base de erros do service de promocao (vira HTTP 422 no viewset)."""


class JustificativaInvalida(PromocaoInvalida):
    """Justificativa < 100 chars OU contem PII direta."""


class PerfilDestinoInvalido(PromocaoInvalida):
    """Destino fora de {C, B, A} OU downgrade (nova_ord <= atual_ord)."""


class EvidenciaObrigatoria(PromocaoInvalida):
    """`evidencia_documental_id` ausente."""


class RTObrigatorio(PromocaoInvalida):
    """`rt_id` ausente."""


class EquipamentoNaoEncontrado(PromocaoInvalida):
    """Equipamento nao existe no contexto do tenant ativo."""


@dataclass(frozen=True)
class ResultadoPromocao:
    """Snapshot final pos-promocao + identificador da cadeia."""

    snapshot_atualizado: dict[str, Any]
    cadeia_linha_id: UUID
    outbox_enfileirado: bool


def promover_perfil_equipamento(
    *,
    tenant_id: UUID,
    equipamento_id: UUID,
    decisor_id: UUID,
    rt_id: UUID,
    perfil_novo: str,
    evidencia_documental_id: UUID,
    justificativa: str,
    causation_id: UUID | None = None,
) -> ResultadoPromocao:
    """Promove perfil D→C→B→A do equipamento via funcao PG SECURITY DEFINER.

    Pre-condicoes (fail-fast em Python):
    - `justificativa` ≥100 chars e sem PII direta (CPF/CNPJ/email/telefone/nomes).
    - `perfil_novo` em {C, B, A}.
    - `evidencia_documental_id` e `rt_id` nao-nulos.

    Validacoes PG (raise_exception com prefixo `P-EQP-T4:`):
    - Direcao monotonica crescente (atual_ord < novo_ord).
    - Tenant ativo == equipamento.tenant_id.
    - Equipamento existe e nao soft-deleted.

    Garantia transacional: cadeia + outbox dentro do MESMO
    `transaction.atomic` do UPDATE (INV-INT-010).
    """
    # Pre-validacoes Python.
    if perfil_novo not in PERFIS_DESTINO_VALIDOS:
        raise PerfilDestinoInvalido(
            f"perfil_novo '{perfil_novo}' invalido — destinos validos: "
            "C, B, A (D nao e destino de promocao)."
        )
    if evidencia_documental_id is None:
        raise EvidenciaObrigatoria(
            "evidencia_documental_id obrigatorio (rastreabilidade RBC)."
        )
    if rt_id is None:
        raise RTObrigatorio("rt_id obrigatorio (assinatura RT — US-EQP-007).")
    if not justificativa or len(justificativa) < JUSTIFICATIVA_MIN_CHARS:
        raise JustificativaInvalida(
            f"justificativa exige >={JUSTIFICATIVA_MIN_CHARS} chars "
            f"(atual={len(justificativa or '')})."
        )
    if conter_pii_direta(justificativa):
        raise JustificativaInvalida(
            "LGPD art. 5º I — justificativa contem PII direta (CPF/CNPJ/"
            "email/telefone/nomes proprios). Reformule sem dados pessoais."
        )

    causation_id = causation_id or uuid4()

    with transaction.atomic():
        try:
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT promover_perfil_equipamento_snapshot("
                    "%s::uuid, %s::text, %s::uuid, %s::text, %s::uuid, %s::uuid)",
                    [
                        str(equipamento_id),
                        perfil_novo,
                        str(evidencia_documental_id),
                        justificativa,
                        str(rt_id),
                        str(decisor_id),
                    ],
                )
                row = cur.fetchone()
                raw = row[0] if row else None
                # psycopg3 retorna jsonb como str se nao houver type loader
                # global registrado; normalizamos pra dict aqui.
                if isinstance(raw, str):
                    snapshot_atualizado = json.loads(raw)
                else:
                    snapshot_atualizado = raw or {}
        except DatabaseError as exc:
            # Tipos especificos pra mensagens PG mais comuns (rota
            # HTTP 422 com texto canonico no viewset Wave A).
            msg = str(exc)
            if "P-EQP-T4: equipamento" in msg and "nao encontrado" in msg:
                raise EquipamentoNaoEncontrado(
                    f"equipamento {equipamento_id} nao encontrado no tenant ativo."
                ) from exc
            if "P-EQP-T4: direcao invalida" in msg or "p_perfil_novo invalido" in msg:
                raise PerfilDestinoInvalido(msg) from exc
            if "P-EQP-T4: justificativa" in msg:
                raise JustificativaInvalida(msg) from exc
            if "p_evidencia_documental_id obrigatorio" in msg:
                raise EvidenciaObrigatoria(msg) from exc
            if "p_rt_id obrigatorio" in msg:
                raise RTObrigatorio(msg) from exc
            raise

        # Evento `equipamento.perfil_promovido` (25a WORM — RBC).
        # Payload sanitizado: nada de justificativa em texto cru
        # (hashear via HMAC do tenant — investigacao usa o hash pra
        # casar com a copia mantida na evidencia documental).
        evento = publicar_evento(
            acao="equipamento.perfil_promovido",
            tenant_id=tenant_id,
            usuario_id=decisor_id,
            causation_id=causation_id,
            payload={
                "tenant_id": str(tenant_id),
                "equipamento_id": str(equipamento_id),
                "perfil_novo": perfil_novo,
                "evidencia_documental_id": str(evidencia_documental_id),
                "rt_id": str(rt_id),
                "decisor_id": str(decisor_id),
                "justificativa_hash": hashear_pii_com_salt_tenant(
                    justificativa, tenant_id
                ),
                "snapshot_pos": snapshot_atualizado,
            },
            resource_summary=f"equipamento:{equipamento_id}:perfil_promovido",
        )

    return ResultadoPromocao(
        snapshot_atualizado=snapshot_atualizado or {},
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )
