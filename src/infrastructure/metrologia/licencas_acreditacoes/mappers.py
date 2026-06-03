"""Mappers model PG (colunas tipadas) <-> snapshot de domínio (M9, T-LIC-021).

Molde M6/M7/M8: mapeamento campo-a-campo. `id`/`tenant_id` vão por dentro dos kwargs
de escrita (as 5 tabelas são append/raiz simples — sem FK resolvida por fora). O
`status_cache` (model) é DERIVADO (calcular_status) — não vem do snapshot; o
repositório o calcula na escrita. `revision`/`atualizado_em` são técnicos de
persistência (geridos pelo model/repo). Domain NÃO importa Django (ADR-0007).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.domain.metrologia.licencas_acreditacoes.entities import (
    AlertaVencimento,
    BloqueioOperacional,
    DocumentoRegulatorio,
    EventoEmergencial,
    RevisaoDocumento,
)
from src.domain.metrologia.licencas_acreditacoes.enums import (
    CanalAlerta,
    MotivoRevisao,
    StatusAlerta,
    TipoDocumentoRegulatorio,
)

if TYPE_CHECKING:
    from src.infrastructure.metrologia.licencas_acreditacoes.models import (
        AlertaVencimento as AlertaVencimentoModel,
    )
    from src.infrastructure.metrologia.licencas_acreditacoes.models import (
        BloqueioOperacional as BloqueioOperacionalModel,
    )
    from src.infrastructure.metrologia.licencas_acreditacoes.models import (
        DocumentoRegulatorio as DocumentoRegulatorioModel,
    )
    from src.infrastructure.metrologia.licencas_acreditacoes.models import (
        EventoEmergencialLicenca as EventoEmergencialModel,
    )
    from src.infrastructure.metrologia.licencas_acreditacoes.models import (
        RevisaoDocumento as RevisaoDocumentoModel,
    )


# --- DocumentoRegulatorio -----------------------------------------------------


def documento_model_para_snapshot(m: DocumentoRegulatorioModel) -> DocumentoRegulatorio:
    return DocumentoRegulatorio(
        id=m.id,
        tenant_id=m.tenant_id,
        tipo=TipoDocumentoRegulatorio(m.tipo),
        numero=m.numero,
        orgao_emissor=m.orgao_emissor,
        vigencia_inicio=m.vigencia_inicio,
        vigencia_fim=m.vigencia_fim,
        bloqueante=m.bloqueante,
        criado_em=m.criado_em,
        criado_por=m.criado_por,
        escopo=m.escopo,
        numero_cgcre=m.numero_cgcre,
        ilac_mra_aderido=m.ilac_mra_aderido,
        titular_referencia_hash=m.titular_referencia_hash,
        titular_referencia_key_id=m.titular_referencia_key_id,
        responsavel_id=m.responsavel_id,
        observacao=m.observacao,
        perfil_no_evento=m.perfil_emissor_no_momento or "",
        correlation_id=m.correlation_id,
        revogado_em=m.revogado_em,
        motivo_revogacao=m.motivo_revogacao,
    )


def documento_snapshot_para_campos(s: DocumentoRegulatorio) -> dict[str, Any]:
    """Snapshot -> kwargs do Model (escrita). `status_cache` é derivado pelo
    repositório (calcular_status) — NÃO entra aqui."""
    return {
        "id": s.id,
        "tenant_id": s.tenant_id,
        "tipo": s.tipo.value,
        "numero": s.numero,
        "orgao_emissor": s.orgao_emissor,
        "vigencia_inicio": s.vigencia_inicio,
        "vigencia_fim": s.vigencia_fim,
        "bloqueante": s.bloqueante,
        "escopo": s.escopo,
        "numero_cgcre": s.numero_cgcre,
        "ilac_mra_aderido": s.ilac_mra_aderido,
        "titular_referencia_hash": s.titular_referencia_hash,
        "titular_referencia_key_id": s.titular_referencia_key_id,
        "responsavel_id": s.responsavel_id,
        "observacao": s.observacao,
        "perfil_emissor_no_momento": s.perfil_no_evento,
        "correlation_id": s.correlation_id,
        "criado_por": s.criado_por,
        "revogado_em": s.revogado_em,
        "motivo_revogacao": s.motivo_revogacao,
    }


# --- RevisaoDocumento ---------------------------------------------------------


def revisao_model_para_snapshot(m: RevisaoDocumentoModel) -> RevisaoDocumento:
    return RevisaoDocumento(
        id=m.id,
        tenant_id=m.tenant_id,
        documento_id=m.documento_id,
        numero_revisao=m.numero_revisao,
        data_emissao=m.data_emissao,
        data_validade=m.data_validade,
        anexo_id=m.anexo_id,
        anexo_sha256=m.anexo_sha256,
        motivo=MotivoRevisao(m.motivo),
        criado_em=m.criado_em,
        criado_por=m.criado_por,
    )


def revisao_snapshot_para_campos(s: RevisaoDocumento) -> dict[str, Any]:
    return {
        "id": s.id,
        "tenant_id": s.tenant_id,
        "documento_id": s.documento_id,
        "numero_revisao": s.numero_revisao,
        "data_emissao": s.data_emissao,
        "data_validade": s.data_validade,
        "anexo_id": s.anexo_id,
        "anexo_sha256": s.anexo_sha256,
        "motivo": s.motivo.value,
        "criado_por": s.criado_por,
    }


# --- AlertaVencimento ---------------------------------------------------------


def alerta_model_para_snapshot(m: AlertaVencimentoModel) -> AlertaVencimento:
    return AlertaVencimento(
        id=m.id,
        tenant_id=m.tenant_id,
        documento_id=m.documento_id,
        data_disparo=m.data_disparo,
        janela_dias=m.janela_dias,
        canal=CanalAlerta(m.canal),
        destinatario_id=m.destinatario_id,
        status=StatusAlerta(m.status),
        tentativas=m.tentativas,
    )


def alerta_snapshot_para_campos(s: AlertaVencimento) -> dict[str, Any]:
    return {
        "id": s.id,
        "tenant_id": s.tenant_id,
        "documento_id": s.documento_id,
        "data_disparo": s.data_disparo,
        "janela_dias": s.janela_dias,
        "canal": s.canal.value,
        "destinatario_id": s.destinatario_id,
        "status": s.status.value,
        "tentativas": s.tentativas,
    }


# --- BloqueioOperacional ------------------------------------------------------


def bloqueio_model_para_snapshot(m: BloqueioOperacionalModel) -> BloqueioOperacional:
    return BloqueioOperacional(
        id=m.id,
        tenant_id=m.tenant_id,
        documento_id=m.documento_id,
        tipo_documento=TipoDocumentoRegulatorio(m.tipo_documento),
        operacao_bloqueada=m.operacao_bloqueada,
        data_inicio_bloqueio=m.data_inicio_bloqueio,
        data_fim_bloqueio=m.data_fim_bloqueio,
    )


def bloqueio_snapshot_para_campos(s: BloqueioOperacional) -> dict[str, Any]:
    return {
        "id": s.id,
        "tenant_id": s.tenant_id,
        "documento_id": s.documento_id,
        "tipo_documento": s.tipo_documento.value,
        "operacao_bloqueada": s.operacao_bloqueada,
        "data_inicio_bloqueio": s.data_inicio_bloqueio,
        "data_fim_bloqueio": s.data_fim_bloqueio,
    }


# --- EventoEmergencial --------------------------------------------------------


def evento_emergencial_snapshot_para_campos(s: EventoEmergencial) -> dict[str, Any]:
    return {
        "id": s.id,
        "tenant_id": s.tenant_id,
        "bloqueio_id": s.bloqueio_id,
        "operacao_executada": s.operacao_executada,
        "justificativa": s.justificativa,
        "justificativa_hash": s.justificativa_hash,
        "admin_id": s.admin_id,
        "assinatura_a3_id": s.assinatura_a3_id,
        "libera_apenas_nao_rbc": s.libera_apenas_nao_rbc,
        "expira_em": s.expira_em,
    }


def evento_emergencial_model_para_snapshot(m: EventoEmergencialModel) -> EventoEmergencial:
    return EventoEmergencial(
        id=m.id,
        tenant_id=m.tenant_id,
        bloqueio_id=m.bloqueio_id,
        operacao_executada=m.operacao_executada,
        justificativa=m.justificativa,
        justificativa_hash=m.justificativa_hash,
        admin_id=m.admin_id,
        assinatura_a3_id=m.assinatura_a3_id,
        expira_em=m.expira_em,
        criado_em=m.criado_em,
        libera_apenas_nao_rbc=m.libera_apenas_nao_rbc,
    )
