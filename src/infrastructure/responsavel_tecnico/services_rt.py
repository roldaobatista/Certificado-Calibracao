"""Services de dominio do RT (T-EQP-064 — US-EQP-007).

Operacoes:
- `cadastrar_rt`: cria `ResponsavelTecnicoTenant` ativo + publica
  `tenant.rt.cadastrado`.
- `encerrar_rt`: marca encerrado_em/encerrado_por/motivo + publica
  `tenant.rt.encerrado`. (UPDATE permitido pelo trigger pos-INSERT.)
- `trocar_rt`: encerra o atual + cadastra novo na MESMA transacao +
  publica `tenant.rt.trocado` (evento agregador). Wave A consumer
  notifica ANPD/CGCRE em 30 dias uteis.
- `declarar_competencia`: cria `RTCompetencia` + publica
  `tenant.rt.competencia_declarada`. INV-EQP-RT-001 cravado em PG
  via EXCLUDE GIST — sobreposicao retorna `CompetenciaSobreposta`.

Garantias:
- Todas as operacoes rodam em `transaction.atomic()` do chamador
  (helper publicar_evento exige).
- CPF do RT NUNCA persiste cru — pseudonimizacao via
  `hashear_pii_com_salt_tenant`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from django.db import IntegrityError, transaction
from django.utils import timezone

from src.infrastructure.audit.event_helpers import publicar_evento
from src.infrastructure.audit.services import hashear_pii_com_salt_tenant

from .models import (
    MotivoEncerramentoRT,
    RegistroProfissionalTipo,
    ResponsavelTecnicoTenant,
    RTCompetencia,
)


class CompetenciaSobreposta(Exception):
    """Levantada quando EXCLUDE GIST detecta sobreposicao (INV-EQP-RT-001)."""


@dataclass(frozen=True)
class DadosCadastroRT:
    """Payload de cadastro do RT — agnostico de HTTP."""

    nome_completo: str
    cpf: str
    formacao_academica: str
    registro_profissional_tipo: str
    registro_profissional_numero: str
    data_inicio_vigencia: date
    registro_profissional_descricao_outro: str = ""
    data_fim_vigencia: date | None = None


@dataclass(frozen=True)
class DadosCompetencia:
    """Payload de declaracao de competencia."""

    grandeza: str
    declarado_em: date
    vigente_ate: date | None = None
    carta_competencia_anexo_id: UUID | None = None


def cadastrar_rt(
    *,
    tenant_id: UUID,
    usuario_rt_id: UUID,
    criado_por_id: UUID,
    dados: DadosCadastroRT,
    causation_id: UUID | None = None,
) -> ResponsavelTecnicoTenant:
    """Cria RT + publica `tenant.rt.cadastrado` (cadeia + outbox)."""
    if dados.registro_profissional_tipo not in RegistroProfissionalTipo.values:
        raise ValueError(
            f"registro_profissional_tipo invalido: {dados.registro_profissional_tipo!r}"
        )
    causation_id = causation_id or uuid4()
    with transaction.atomic():
        rt = ResponsavelTecnicoTenant.objects.create(
            tenant_id=tenant_id,
            usuario_id=usuario_rt_id,
            nome_completo_snapshot=dados.nome_completo.strip(),
            cpf_hash=hashear_pii_com_salt_tenant(dados.cpf, tenant_id),
            formacao_academica=dados.formacao_academica.strip(),
            registro_profissional_tipo=dados.registro_profissional_tipo,
            registro_profissional_numero=dados.registro_profissional_numero.strip(),
            registro_profissional_descricao_outro=(
                dados.registro_profissional_descricao_outro.strip()
            ),
            data_inicio_vigencia=dados.data_inicio_vigencia,
            data_fim_vigencia=dados.data_fim_vigencia,
            criado_por_id=criado_por_id,
        )
        publicar_evento(
            acao="tenant.rt.cadastrado",
            tenant_id=tenant_id,
            usuario_id=criado_por_id,
            causation_id=causation_id,
            payload=_resumo_rt(rt),
            resource_summary=f"rt:{rt.id}",
        )
    return rt


def encerrar_rt(
    *,
    rt: ResponsavelTecnicoTenant,
    encerrado_por_id: UUID,
    motivo: str,
    motivo_detalhe: str = "",
    causation_id: UUID | None = None,
) -> ResponsavelTecnicoTenant:
    """Marca RT encerrado + publica `tenant.rt.encerrado`."""
    if rt.encerrado_em is not None:
        raise ValueError("RT ja encerrado — operacao recusada (trigger bloqueia)")
    if motivo not in MotivoEncerramentoRT.values:
        raise ValueError(f"motivo invalido: {motivo!r}")
    causation_id = causation_id or uuid4()
    agora: datetime = timezone.now()
    with transaction.atomic():
        ResponsavelTecnicoTenant.objects.filter(id=rt.id, encerrado_em__isnull=True).update(
            encerrado_em=agora,
            encerrado_por_id=encerrado_por_id,
            motivo_encerramento=motivo,
            motivo_detalhe=motivo_detalhe.strip(),
        )
        rt.refresh_from_db()
        publicar_evento(
            acao="tenant.rt.encerrado",
            tenant_id=rt.tenant_id,
            usuario_id=encerrado_por_id,
            causation_id=causation_id,
            payload={
                "rt_id": str(rt.id),
                "motivo_encerramento": motivo,
            },
            resource_summary=f"rt:{rt.id}",
        )
    return rt


def trocar_rt(
    *,
    rt_atual: ResponsavelTecnicoTenant,
    usuario_novo_rt_id: UUID,
    operador_id: UUID,
    dados_novo_rt: DadosCadastroRT,
    motivo_encerramento_anterior: str = MotivoEncerramentoRT.SUBSTITUICAO.value,
    causation_id: UUID | None = None,
) -> tuple[ResponsavelTecnicoTenant, ResponsavelTecnicoTenant]:
    """Encerra `rt_atual` + cadastra novo RT na MESMA transacao.

    Publica `tenant.rt.trocado` (evento agregador) — Wave A consumer
    dispara notificacao ANPD/CGCRE 30 dias uteis (NIT-DICLA-021).
    """
    causation_id = causation_id or uuid4()
    with transaction.atomic():
        encerrar_rt(
            rt=rt_atual,
            encerrado_por_id=operador_id,
            motivo=motivo_encerramento_anterior,
            causation_id=uuid4(),
        )
        novo = cadastrar_rt(
            tenant_id=rt_atual.tenant_id,
            usuario_rt_id=usuario_novo_rt_id,
            criado_por_id=operador_id,
            dados=dados_novo_rt,
            causation_id=uuid4(),
        )
        publicar_evento(
            acao="tenant.rt.trocado",
            tenant_id=rt_atual.tenant_id,
            usuario_id=operador_id,
            causation_id=causation_id,
            payload={
                "rt_anterior_id": str(rt_atual.id),
                "rt_novo_id": str(novo.id),
                "motivo_encerramento": motivo_encerramento_anterior,
                "data_efetivacao": novo.data_inicio_vigencia.isoformat(),
            },
            resource_summary=f"rt:trocado:{rt_atual.id}->{novo.id}",
        )
    return rt_atual, novo


def declarar_competencia(
    *,
    rt: ResponsavelTecnicoTenant,
    criado_por_id: UUID,
    dados: DadosCompetencia,
    causation_id: UUID | None = None,
) -> RTCompetencia:
    """Cria competencia + publica evento. Sobreposicao -> CompetenciaSobreposta."""
    if rt.encerrado_em is not None:
        raise ValueError("RT ja encerrado — competencia nao pode ser declarada")
    causation_id = causation_id or uuid4()
    grandeza_norm = dados.grandeza.strip().lower()
    with transaction.atomic():
        try:
            competencia = RTCompetencia.objects.create(
                tenant_id=rt.tenant_id,
                rt=rt,
                grandeza=grandeza_norm,
                carta_competencia_anexo_id=dados.carta_competencia_anexo_id,
                declarado_em=dados.declarado_em,
                vigente_ate=dados.vigente_ate,
                criado_por_id=criado_por_id,
            )
        except IntegrityError as exc:
            # EXCLUDE GIST `rt_competencia_sem_sobreposicao_temporal`
            if "rt_competencia_sem_sobreposicao_temporal" in str(exc):
                raise CompetenciaSobreposta(
                    f"Ja existe competencia vigente em '{grandeza_norm}' que "
                    "sobrepoe a janela informada (INV-EQP-RT-001)."
                ) from exc
            raise
        publicar_evento(
            acao="tenant.rt.competencia_declarada",
            tenant_id=rt.tenant_id,
            usuario_id=criado_por_id,
            causation_id=causation_id,
            payload={
                "rt_id": str(rt.id),
                "competencia_id": str(competencia.id),
                "grandeza": grandeza_norm,
                "declarado_em": dados.declarado_em.isoformat(),
                "vigente_ate": (
                    dados.vigente_ate.isoformat() if dados.vigente_ate else None
                ),
            },
            resource_summary=f"rt_competencia:{competencia.id}",
        )
    return competencia


def _resumo_rt(rt: ResponsavelTecnicoTenant) -> dict[str, Any]:
    """Payload sanitizavel do RT (sem CPF cru — soh hash).

    UUIDs e dates convertidos pra string — `json.dumps` no outbox falha
    com tipos nativos (event_helpers nao usa default=str).
    """
    return {
        "rt_id": str(rt.id),
        "tenant_id": str(rt.tenant_id),
        "usuario_id": str(rt.usuario_id),
        "registro_profissional_tipo": rt.registro_profissional_tipo,
        "registro_profissional_numero": rt.registro_profissional_numero,
        "data_inicio_vigencia": rt.data_inicio_vigencia.isoformat(),
        "data_fim_vigencia": (
            rt.data_fim_vigencia.isoformat() if rt.data_fim_vigencia else None
        ),
    }
