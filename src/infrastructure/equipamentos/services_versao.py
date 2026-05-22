"""Service de criacao de `EquipamentoVersao` + publicacao de evento
sanitizado (T-EQP-017 / AC-EQP-002-6 / INV-EQP-VERSAO-002).

Orquestra:
1. INSERT em `equipamentos_versao` (T-EQP-012) com pre-hashing dos
   `valor_anterior` / `valor_novo` em claro -> HMAC do tenant.
2. Publica `equipamento.versao_criada` no bus_outbox com **lista positiva
   FECHADA de 5 campos** (P-EQP-T5 + AC-EQP-002-6).
3. Defesa em profundidade: assert anti-vaza varre o payload final e
   levanta `PayloadVazandoPII` se qualquer um dos **7 campos
   proibidos** aparecer.

INV-EQP-VERSAO-002 — lista FECHADA:
- POSITIVA (permitidos): `tenant_id`, `equipamento_id`, `versao_id`,
  `campo`, `motivo_mudanca`.
- NEGATIVA (proibidos): `motivo_detalhe` cru, `valor_anterior` cru,
  `valor_novo` cru, `cliente_atual_id` cru, `assinatura_a3_hash`
  truncado, `numero_serie` cru, qualquer hash A3 cru.

Decisao P-EQP-T5: assinatura A3 entra como UUID OPACO referencia, nunca
hash truncado. Aqui o evento traz `assinatura_a3_referencia` (UUID) +
`assinatura_a3_certificado_emissor_hash` (HMAC ja sanitizado no modelo).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid4

from django.db import transaction

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.equipamentos.models import (
    MOTIVOS_QUE_OBRIGAM_APROVACAO,
    AprovacaoPendenteEquipamentoVersao,
    Equipamento,
    EquipamentoVersao,
    MotivoMudancaEquipamentoVersao,
)


class PayloadVazandoPII(Exception):
    """INV-EQP-VERSAO-002 — payload do evento contem campo proibido.

    Levanta em tempo de assert do service (defesa em profundidade alem
    da lista positiva). Indica bug que precisa correcao imediata.
    """


# Lista FECHADA positiva (INV-EQP-VERSAO-002).
CAMPOS_PAYLOAD_PERMITIDOS: frozenset[str] = frozenset(
    {
        "tenant_id",
        "equipamento_id",
        "versao_id",
        "campo",
        "motivo_mudanca",
        # Campos HMAC ja sanitizados (hash do tenant - sem PII em claro).
        "valor_anterior_hash",
        "valor_novo_hash",
        "motivo_detalhe_hash",
        "cliente_atual_id_no_momento_hash",
        # P-EQP-T5: assinatura A3 e UUID opaco + hash do emissor (ja
        # hash de servidor, nao truncado).
        "assinatura_a3_referencia",
        "assinatura_a3_certificado_emissor_hash",
        "criado_em",
        "criado_por_id_hash",
        "snapshot_schema_version",
    }
)

# Lista negativa explicita (5 + 2 — defesa em profundidade alem do
# whitelist; fail-loud se aparecer).
CAMPOS_PAYLOAD_PROIBIDOS: frozenset[str] = frozenset(
    {
        "motivo_detalhe",
        "valor_anterior",
        "valor_novo",
        "cliente_atual_id",
        "cliente_atual_id_no_momento",
        "assinatura_a3_hash",
        "numero_serie",
    }
)


@dataclass(frozen=True)
class DadosCriacaoVersao:
    """Payload de criacao de versao agnostico de HTTP."""

    campo: str
    valor_anterior: str
    valor_novo: str
    motivo_mudanca: str
    motivo_detalhe: str = ""
    snapshot: dict[str, Any] | None = None
    snapshot_schema_version: str = "1.0.0"
    assinatura_a3_referencia: UUID | None = None
    assinatura_a3_assinada_em: Any = None  # datetime
    assinatura_a3_certificado_emissor_hash: str = ""


@dataclass(frozen=True)
class ResultadoCriacaoVersao:
    """Versao criada + identificador da cadeia."""

    versao: EquipamentoVersao
    cadeia_linha_id: UUID
    outbox_enfileirado: bool


@dataclass(frozen=True)
class ResultadoVersionamento:
    """T-EQP-015 (AC-EQP-002-4 / P-EQP-R2) — resultado do despacho.

    Quando `motivo_mudanca` em `MOTIVOS_QUE_OBRIGAM_APROVACAO` o service
    NAO cria EquipamentoVersao direto: cria
    `AprovacaoPendenteEquipamentoVersao` e devolve `aprovacao_id`.
    Caller (viewset) responde 202 nesse caso.

    Quando motivo livre, cria versao direto e devolve `versao_id`
    (caller responde 201).
    """

    exige_aprovacao: bool
    versao_id: UUID | None
    aprovacao_id: UUID | None
    cadeia_linha_id: UUID | None
    outbox_enfileirado: bool


def _validar_payload_anti_vaza(payload: dict[str, Any]) -> None:
    """Defesa em profundidade INV-EQP-VERSAO-002."""
    for chave in payload:
        if chave in CAMPOS_PAYLOAD_PROIBIDOS:
            raise PayloadVazandoPII(
                f"INV-EQP-VERSAO-002: campo proibido '{chave}' no payload "
                "de `equipamento.versao_criada`."
            )
        if chave not in CAMPOS_PAYLOAD_PERMITIDOS:
            raise PayloadVazandoPII(
                f"INV-EQP-VERSAO-002: campo '{chave}' fora da lista positiva "
                "fechada (5 base + 9 derivados/hashes). Atualize a lista em "
                "`services_versao.CAMPOS_PAYLOAD_PERMITIDOS` se a inclusao "
                "for legitima (revisao do tech-lead + auditor obrigatoria)."
            )


def criar_versao_equipamento(
    *,
    tenant_id: UUID,
    equipamento: Equipamento,
    criado_por_id: UUID,
    dados: DadosCriacaoVersao,
    causation_id: UUID | None = None,
) -> ResultadoCriacaoVersao:
    """Cria EquipamentoVersao + publica `equipamento.versao_criada`.

    Pre-condicoes:
    - `motivo_mudanca` em `MotivoMudancaEquipamentoVersao.values`.
    - `valor_anterior` / `valor_novo`: sao texto cru; o service os
      converte em HMAC antes de gravar (modelo nunca enxerga valor cru).

    Garantias:
    - INV-EQP-VERSAO-001: `clean()` do modelo valida motivo_detalhe
      anti-PII + tamanho minimo.
    - INV-EQP-VERSAO-002: payload do evento passa por
      `_validar_payload_anti_vaza`.
    - Cadeia + outbox dentro do MESMO `transaction.atomic`
      (INV-INT-010).
    """
    if dados.motivo_mudanca not in MotivoMudancaEquipamentoVersao.values:
        raise ValueError(
            f"motivo_mudanca '{dados.motivo_mudanca}' fora do enum "
            "MotivoMudancaEquipamentoVersao (P-EQP-R2 — 9 valores)."
        )

    causation_id = causation_id or uuid4()

    valor_anterior_hash = hashear_pii_com_salt_tenant(
        dados.valor_anterior, tenant_id
    )
    valor_novo_hash = hashear_pii_com_salt_tenant(dados.valor_novo, tenant_id)

    with transaction.atomic():
        versao = EquipamentoVersao(
            tenant_id=tenant_id,
            equipamento=equipamento,
            campo=dados.campo,
            valor_anterior_hash=valor_anterior_hash,
            valor_novo_hash=valor_novo_hash,
            motivo_mudanca=dados.motivo_mudanca,
            motivo_detalhe=dados.motivo_detalhe,
            snapshot_jsonb=dados.snapshot or {},
            cliente_atual_id_no_momento=equipamento.cliente_atual_id,
            criado_por_id=criado_por_id,
            assinatura_a3_referencia=dados.assinatura_a3_referencia,
            assinatura_a3_assinada_em=dados.assinatura_a3_assinada_em,
            assinatura_a3_certificado_emissor_hash=(
                dados.assinatura_a3_certificado_emissor_hash
            ),
        )
        versao.save()  # save() chama clean() — INV-EQP-VERSAO-001 enforce.

        payload: dict[str, Any] = {
            "tenant_id": str(tenant_id),
            "equipamento_id": str(equipamento.id),
            "versao_id": str(versao.id),
            "campo": dados.campo,
            "motivo_mudanca": dados.motivo_mudanca,
            "valor_anterior_hash": valor_anterior_hash,
            "valor_novo_hash": valor_novo_hash,
            "motivo_detalhe_hash": (
                hashear_pii_com_salt_tenant(dados.motivo_detalhe, tenant_id)
                if dados.motivo_detalhe
                else ""
            ),
            "cliente_atual_id_no_momento_hash": (
                hashear_pii_com_salt_tenant(
                    str(equipamento.cliente_atual_id), tenant_id
                )
                if equipamento.cliente_atual_id
                else ""
            ),
            "assinatura_a3_referencia": (
                str(dados.assinatura_a3_referencia)
                if dados.assinatura_a3_referencia
                else None
            ),
            "assinatura_a3_certificado_emissor_hash": (
                dados.assinatura_a3_certificado_emissor_hash or ""
            ),
            "criado_em": versao.criado_em.isoformat(),
            "criado_por_id_hash": hashear_pii_com_salt_tenant(
                str(criado_por_id), tenant_id
            ),
            "snapshot_schema_version": dados.snapshot_schema_version,
        }

        # Defesa em profundidade INV-EQP-VERSAO-002.
        _validar_payload_anti_vaza(payload)

        evento = publicar_evento(
            acao="equipamento.versao_criada",
            tenant_id=tenant_id,
            usuario_id=criado_por_id,
            causation_id=causation_id,
            payload=payload,
            resource_summary=f"equipamento:{equipamento.id}:versao:{versao.id}",
        )

    return ResultadoCriacaoVersao(
        versao=versao,
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )


def criar_ou_solicitar_versao_equipamento(
    *,
    tenant_id: UUID,
    equipamento: Equipamento,
    solicitante_id: UUID,
    dados: DadosCriacaoVersao,
    tem_cert_vigente: bool = False,
    evidencia_documental_id: UUID | None = None,
    causation_id: UUID | None = None,
) -> ResultadoVersionamento:
    """T-EQP-015 (AC-EQP-002-4 / P-EQP-R2) — despacha entre criacao
    direta de versao e solicitacao de aprovacao.

    Regra:
    - `motivo_mudanca` em `MOTIVOS_QUE_OBRIGAM_APROVACAO` (`outros`,
      `substituicao_componente_critico`, `atualizacao_firmware`) →
      cria `AprovacaoPendenteEquipamentoVersao` PENDENTE e NAO cria
      `EquipamentoVersao`. Caller responde 202.
    - Motivo livre (6 valores restantes) → cria EquipamentoVersao
      direto + publica `equipamento.versao_criada`. Caller responde 201.

    A efetivacao da versao a partir de uma aprovacao APROVADA acontece
    em `efetivar_versao_a_partir_de_aprovacao` (services_aprovacao).
    """
    # Import tardio evita ciclo services_versao <-> services_aprovacao.
    from src.infrastructure.equipamentos.services_aprovacao import (
        DadosSolicitacaoAprovacao,
        solicitar_aprovacao,
    )

    if dados.motivo_mudanca in MOTIVOS_QUE_OBRIGAM_APROVACAO:
        aprovacao = solicitar_aprovacao(
            tenant_id=tenant_id,
            equipamento=equipamento,
            solicitante_id=solicitante_id,
            dados=DadosSolicitacaoAprovacao(
                campo=dados.campo,
                valor_anterior=dados.valor_anterior,
                valor_novo=dados.valor_novo,
                motivo_mudanca=dados.motivo_mudanca,
                motivo_detalhe=dados.motivo_detalhe,
                evidencia_documental_id=evidencia_documental_id,
            ),
            tem_cert_vigente=tem_cert_vigente,
        )
        return ResultadoVersionamento(
            exige_aprovacao=True,
            versao_id=None,
            aprovacao_id=aprovacao.id,
            cadeia_linha_id=None,
            outbox_enfileirado=False,
        )

    resultado = criar_versao_equipamento(
        tenant_id=tenant_id,
        equipamento=equipamento,
        criado_por_id=solicitante_id,
        dados=dados,
        causation_id=causation_id,
    )
    return ResultadoVersionamento(
        exige_aprovacao=False,
        versao_id=resultado.versao.id,
        aprovacao_id=None,
        cadeia_linha_id=resultado.cadeia_linha_id,
        outbox_enfileirado=resultado.outbox_enfileirado,
    )


def efetivar_versao_a_partir_de_aprovacao(
    *,
    aprovacao: AprovacaoPendenteEquipamentoVersao,
    valor_anterior_cru: str,
    valor_novo_cru: str,
    motivo_detalhe_cru: str | None = None,
    snapshot: dict[str, Any] | None = None,
    causation_id: UUID | None = None,
) -> ResultadoCriacaoVersao:
    """T-EQP-015 — apos aprovacao chegar em status APROVADA, cria
    `EquipamentoVersao` reusando os mesmos dados.

    Importante: os valores crus de `valor_anterior`/`valor_novo`/
    `motivo_detalhe` NAO ficam gravados na aprovacao (apenas o
    motivo_detalhe que e textual fica, e os valores ficam como hash).
    Como Marco 2 nao tem ainda um endpoint de aprovacao com os campos
    crus em sessao server-side, exigimos que o caller (Wave A: endpoint
    `POST /aprovacoes/{id}/aprovar/` com payload reauxiliar) forneca
    novamente. Wave A pode tambem optar por anexar os dados crus a
    aprovacao em campo `payload_solicitacao_jsonb` (P-EQP-A4 derivado).

    Pre-condicao: aprovacao.status == APROVADA. Caller responsavel.
    """
    equipamento = Equipamento.objects.get(id=aprovacao.equipamento_id)
    return criar_versao_equipamento(
        tenant_id=aprovacao.tenant_id,
        equipamento=equipamento,
        criado_por_id=aprovacao.solicitante_id,
        dados=DadosCriacaoVersao(
            campo=aprovacao.campo,
            valor_anterior=valor_anterior_cru,
            valor_novo=valor_novo_cru,
            motivo_mudanca=aprovacao.motivo_mudanca,
            motivo_detalhe=motivo_detalhe_cru or aprovacao.motivo_detalhe,
            snapshot=snapshot,
        ),
        causation_id=causation_id,
    )
