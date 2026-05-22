"""Service de aprovacao gestor_qualidade de `EquipamentoVersao`
(US-EQP-002b / T-EQP-018+022).

Orquestra 3 transicoes:
1. `solicitar_aprovacao` (status=PENDENTE; calcula sla_vencimento
   provisorio — T-EQP-019 substituira por workalendar).
2. `aprovar` (status=APROVADA + decisor + parecer + decidida_em;
   publica `equipamento.versao_aprovada`).
3. `rejeitar` (status=REJEITADA + decisor + parecer + decidida_em;
   publica `equipamento.versao_rejeitada`).

`expirar` (status=EXPIRADA) e responsabilidade do job
`job_aprovacao_versionamento_escalacao` em T-EQP-019.

INV-EQP-002 (ISO 17025 cl. 6.2 segregacao): defesa em CHECK + clean()
do modelo + assert no service (3 camadas).

INV-EQP-VERSAO-001: `parecer_gestor_texto` e `motivo_detalhe` passam
por `validar_parecer_gestor_texto` / `validar_motivo_detalhe` no clean()
do modelo (chamado no .save()).

Eventos publicados via `publicar_evento`:
- `equipamento.versao_aprovada` (payload sanitizado — segue padrao
  INV-EQP-VERSAO-002 do `services_versao`).
- `equipamento.versao_rejeitada` (idem).
- `equipamento.versao_expirada` (publicado pelo job — T-EQP-019).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import transaction
from django.utils import timezone
from workalendar.america import Brazil

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.equipamentos.models import (
    MOTIVOS_QUE_OBRIGAM_APROVACAO,
    AprovacaoPendenteEquipamentoVersao,
    Equipamento,
    StatusAprovacaoVersao,
)


class AprovacaoInvalida(Exception):
    """Base de erros do service de aprovacao."""


class MotivoNaoExigeAprovacao(AprovacaoInvalida):
    """Tentou abrir aprovacao com motivo que nao exige fluxo."""


class SegregacaoFuncoesViolada(AprovacaoInvalida):
    """INV-EQP-002 — solicitante == decisor."""


class AprovacaoJaDecidida(AprovacaoInvalida):
    """Tentou aprovar/rejeitar aprovacao ja em estado terminal."""


@dataclass(frozen=True)
class DadosSolicitacaoAprovacao:
    campo: str
    valor_anterior: str
    valor_novo: str
    motivo_mudanca: str
    motivo_detalhe: str
    evidencia_documental_id: UUID | None = None


@dataclass(frozen=True)
class ResultadoAprovacao:
    aprovacao: AprovacaoPendenteEquipamentoVersao
    cadeia_linha_id: UUID
    outbox_enfileirado: bool


# T-EQP-019 (AC-EQP-002b-2 / P-EQP-R5): SLA em dias UTEIS BR via
# workalendar. Defaults — D+3 (sem cert vigente) / D+7 (com cert).
# Extensao estadual cabe a Wave A (quando tenant tiver UF declarada,
# trocar Brazil() por subclass BrazilAcre/BrazilSaoPaulo/...).
SLA_DIAS_UTEIS_SEM_CERT: int = 3
SLA_DIAS_UTEIS_COM_CERT: int = 7

_calendario_brasil = Brazil()


def calcular_sla_vencimento(
    *,
    tem_cert_vigente: bool,
    base: datetime | None = None,
) -> datetime:
    """Retorna `base + N dias uteis BR` (workalendar.america.Brazil).

    - N = 7 quando equipamento tem certificado vigente (mais urgencia
      de revisao porque o cert ja afeta cliente final);
    - N = 3 quando sem cert (revisao interna, menos critica).

    `workalendar` cobre todos os feriados nacionais BR + feriados
    moveis (Carnaval, Corpus Christi). Wave A trocara `Brazil()` por
    subclass estadual quando tenant declarar UF.
    """
    inicio = base or timezone.now()
    dias = SLA_DIAS_UTEIS_COM_CERT if tem_cert_vigente else SLA_DIAS_UTEIS_SEM_CERT
    nova_data = _calendario_brasil.add_working_days(inicio.date(), dias)
    # add_working_days retorna date; preserva hora do `inicio`.
    return datetime.combine(nova_data, inicio.time(), tzinfo=inicio.tzinfo)


def solicitar_aprovacao(
    *,
    tenant_id: UUID,
    equipamento: Equipamento,
    solicitante_id: UUID,
    dados: DadosSolicitacaoAprovacao,
    tem_cert_vigente: bool = False,
) -> AprovacaoPendenteEquipamentoVersao:
    """Cria `AprovacaoPendenteEquipamentoVersao` em status PENDENTE.

    Pre-condicoes:
    - `motivo_mudanca` deve estar em `MOTIVOS_QUE_OBRIGAM_APROVACAO`.
    - Hashes calculados via HMAC do tenant.
    - `motivo_detalhe` validado pelo clean() do modelo (>=100 chars +
      anti-PII — INV-EQP-VERSAO-001).
    """
    if dados.motivo_mudanca not in MOTIVOS_QUE_OBRIGAM_APROVACAO:
        raise MotivoNaoExigeAprovacao(
            f"motivo '{dados.motivo_mudanca}' nao exige fluxo de aprovacao "
            f"(MOTIVOS_QUE_OBRIGAM_APROVACAO={MOTIVOS_QUE_OBRIGAM_APROVACAO})."
        )

    valor_anterior_hash = hashear_pii_com_salt_tenant(
        dados.valor_anterior, tenant_id
    )
    valor_novo_hash = hashear_pii_com_salt_tenant(dados.valor_novo, tenant_id)

    with transaction.atomic():
        aprovacao = AprovacaoPendenteEquipamentoVersao(
            tenant_id=tenant_id,
            equipamento=equipamento,
            solicitante_id=solicitante_id,
            campo=dados.campo,
            valor_anterior_hash=valor_anterior_hash,
            valor_novo_hash=valor_novo_hash,
            motivo_mudanca=dados.motivo_mudanca,
            motivo_detalhe=dados.motivo_detalhe,
            sla_vencimento=calcular_sla_vencimento(
                tem_cert_vigente=tem_cert_vigente
            ),
            evidencia_documental_id=dados.evidencia_documental_id,
        )
        aprovacao.save()  # clean() roda — INV-EQP-VERSAO-001 enforce.
    return aprovacao


def _decidir(
    *,
    tenant_id: UUID,
    aprovacao: AprovacaoPendenteEquipamentoVersao,
    decisor_id: UUID,
    parecer_gestor_texto: str,
    status_destino: str,
    acao_canonica: str,
    causation_id: UUID | None,
) -> ResultadoAprovacao:
    """Implementacao comum de aprovar / rejeitar.

    Defesa em profundidade INV-EQP-002 — alem do CHECK e do clean(),
    valida no service.
    """
    if aprovacao.status != StatusAprovacaoVersao.PENDENTE:
        raise AprovacaoJaDecidida(
            f"aprovacao {aprovacao.id} ja em estado terminal "
            f"({aprovacao.status})."
        )
    if aprovacao.solicitante_id == decisor_id:
        raise SegregacaoFuncoesViolada(
            "INV-EQP-002 (ISO 17025 cl. 6.2) — solicitante nao pode ser "
            "o mesmo que o decisor."
        )

    causation_id = causation_id or uuid4()

    with transaction.atomic():
        aprovacao.status = status_destino
        aprovacao.decisor_id = decisor_id
        aprovacao.parecer_gestor_texto = parecer_gestor_texto
        aprovacao.decidida_em = timezone.now()
        aprovacao.save()  # clean() roda — parecer >=30 chars + anti-PII.

        payload: dict[str, Any] = {
            "tenant_id": str(tenant_id),
            "equipamento_id": str(aprovacao.equipamento_id),
            "aprovacao_id": str(aprovacao.id),
            "campo": aprovacao.campo,
            "motivo_mudanca": aprovacao.motivo_mudanca,
            "valor_anterior_hash": aprovacao.valor_anterior_hash,
            "valor_novo_hash": aprovacao.valor_novo_hash,
            "motivo_detalhe_hash": hashear_pii_com_salt_tenant(
                aprovacao.motivo_detalhe, tenant_id
            ),
            "solicitante_id_hash": hashear_pii_com_salt_tenant(
                str(aprovacao.solicitante_id), tenant_id
            ),
            "decisor_id_hash": hashear_pii_com_salt_tenant(
                str(decisor_id), tenant_id
            ),
            "parecer_gestor_texto_hash": hashear_pii_com_salt_tenant(
                parecer_gestor_texto, tenant_id
            ),
            "decidida_em": aprovacao.decidida_em.isoformat(),
            "evidencia_documental_id": (
                str(aprovacao.evidencia_documental_id)
                if aprovacao.evidencia_documental_id
                else None
            ),
        }

        evento = publicar_evento(
            acao=acao_canonica,
            tenant_id=tenant_id,
            usuario_id=decisor_id,
            causation_id=causation_id,
            payload=payload,
            resource_summary=f"aprovacao:{aprovacao.id}",
        )

    return ResultadoAprovacao(
        aprovacao=aprovacao,
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )


def expirar_aprovacoes_vencidas(
    *,
    tenant_id: UUID,
) -> list[ResultadoAprovacao]:
    """Job-helper T-EQP-019 — itera aprovacoes PENDENTES com
    sla_vencimento <= now() e chama `expirar` em cada uma.

    Pre-condicao: caller deve setar `app.active_tenant_id` (RLS).
    Chamado pelo management command
    `processar_aprovacoes_expiradas_equipamento` em todos os tenants.
    """
    agora = timezone.now()
    pendentes_vencidas = AprovacaoPendenteEquipamentoVersao.objects.filter(
        status=StatusAprovacaoVersao.PENDENTE,
        sla_vencimento__lte=agora,
    )
    resultados: list[ResultadoAprovacao] = []
    for aprovacao in pendentes_vencidas:
        resultados.append(
            expirar(tenant_id=tenant_id, aprovacao=aprovacao)
        )
    return resultados


def aprovar(
    *,
    tenant_id: UUID,
    aprovacao: AprovacaoPendenteEquipamentoVersao,
    decisor_id: UUID,
    parecer_gestor_texto: str,
    causation_id: UUID | None = None,
) -> ResultadoAprovacao:
    """PENDENTE -> APROVADA. Publica `equipamento.versao_aprovada`."""
    return _decidir(
        tenant_id=tenant_id,
        aprovacao=aprovacao,
        decisor_id=decisor_id,
        parecer_gestor_texto=parecer_gestor_texto,
        status_destino=StatusAprovacaoVersao.APROVADA.value,
        acao_canonica="equipamento.versao_aprovada",
        causation_id=causation_id,
    )


def rejeitar(
    *,
    tenant_id: UUID,
    aprovacao: AprovacaoPendenteEquipamentoVersao,
    decisor_id: UUID,
    parecer_gestor_texto: str,
    causation_id: UUID | None = None,
) -> ResultadoAprovacao:
    """PENDENTE -> REJEITADA. Publica `equipamento.versao_rejeitada`."""
    return _decidir(
        tenant_id=tenant_id,
        aprovacao=aprovacao,
        decisor_id=decisor_id,
        parecer_gestor_texto=parecer_gestor_texto,
        status_destino=StatusAprovacaoVersao.REJEITADA.value,
        acao_canonica="equipamento.versao_rejeitada",
        causation_id=causation_id,
    )


def expirar(
    *,
    tenant_id: UUID,
    aprovacao: AprovacaoPendenteEquipamentoVersao,
    causation_id: UUID | None = None,
) -> ResultadoAprovacao:
    """PENDENTE -> EXPIRADA. Publica `equipamento.versao_expirada`.

    Chamado pelo job `job_aprovacao_versionamento_escalacao` em
    T-EQP-019 quando sla_vencimento ultrapassa o presente. NAO precisa
    de decisor humano nem parecer.
    """
    if aprovacao.status != StatusAprovacaoVersao.PENDENTE:
        raise AprovacaoJaDecidida(
            f"aprovacao {aprovacao.id} ja em estado terminal "
            f"({aprovacao.status})."
        )

    causation_id = causation_id or uuid4()

    with transaction.atomic():
        # Defesa: clean() exige parecer/decisor quando status=APROVADA/
        # REJEITADA; EXPIRADA dispensa. update() direto pra evitar
        # full_clean nesse caminho legitimo de sistema.
        aprovacao.status = StatusAprovacaoVersao.EXPIRADA.value
        AprovacaoPendenteEquipamentoVersao.objects.filter(pk=aprovacao.pk).update(
            status=StatusAprovacaoVersao.EXPIRADA.value
        )

        payload: dict[str, Any] = {
            "tenant_id": str(tenant_id),
            "equipamento_id": str(aprovacao.equipamento_id),
            "aprovacao_id": str(aprovacao.id),
            "campo": aprovacao.campo,
            "motivo_mudanca": aprovacao.motivo_mudanca,
            "solicitante_id_hash": hashear_pii_com_salt_tenant(
                str(aprovacao.solicitante_id), tenant_id
            ),
            "sla_vencimento": aprovacao.sla_vencimento.isoformat(),
            "expirada_em": datetime.now(UTC).isoformat(),
        }

        evento = publicar_evento(
            acao="equipamento.versao_expirada",
            tenant_id=tenant_id,
            usuario_id=None,
            causation_id=causation_id,
            payload=payload,
            resource_summary=f"aprovacao:{aprovacao.id}:expirada",
        )

    return ResultadoAprovacao(
        aprovacao=aprovacao,
        cadeia_linha_id=evento.cadeia_linha_id,
        outbox_enfileirado=evento.outbox_enfileirado,
    )
