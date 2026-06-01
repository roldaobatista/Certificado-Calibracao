"""Mappers model PG (flat) <-> snapshot de domínio (M8 — ADR-0007 / ADR-0078).

Colunas tipadas (molde M6/M7): mapeamento campo-a-campo. Os mappers de LEITURA
assumem certificado EMITIDO completo (campos preenchidos na emissão pelo use case);
`id`/`tenant_id` vão por fora nos mappers de escrita.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.domain.metrologia.certificados.entities import (
    AnaliseReconciliacaoCertificado,
    CertificadoSnapshot,
    PontoReconciliadoSnapshot,
)
from src.domain.metrologia.certificados.enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
    EstadoCertificado,
    TipoAcreditacao,
)

if TYPE_CHECKING:
    from src.infrastructure.certificados.models import (
        AnaliseReconciliacaoCert,
        Certificado,
        PontoReconciliado,
    )


# --- Certificado --------------------------------------------------------------


def certificado_model_para_snapshot(m: Certificado) -> CertificadoSnapshot:
    """Model PG -> snapshot (leitura de cert EMITIDO completo).

    Os campos da emissão são `null=True` no schema (aditivo sobre o stub), mas um
    certificado materializado sempre os tem preenchidos — o guard explícito é defesa
    (e narrowing de tipo) contra ler um stub/rascunho não-emitido como se fosse cert.
    """
    calibracao_id = m.calibracao_id
    numero_interno = m.numero_interno
    emitido_em = m.emitido_em
    tipo_acreditacao = m.tipo_acreditacao
    if calibracao_id is None or numero_interno is None or emitido_em is None or not tipo_acreditacao:
        raise ValueError(
            f"certificado {m.id} sem campos de emissão completos — o mapper de "
            f"leitura espera um certificado EMITIDO (calibracao_id/numero_interno/"
            f"emitido_em/tipo_acreditacao preenchidos)"
        )
    return CertificadoSnapshot(
        id=m.id,
        tenant_id=m.tenant_id,
        calibracao_id=calibracao_id,
        equipamento_id=m.equipamento_id,
        numero_interno=numero_interno,
        numero_certificado=m.numero_certificado,
        versao=m.versao,
        versao_anterior_id=m.versao_anterior_id,
        status=EstadoCertificado(m.status),
        perfil_emissor_no_momento=m.perfil_emissor_no_momento or "",
        faixa_certificado_min=m.faixa_certificado_min,
        faixa_certificado_max=m.faixa_certificado_max,
        tipo_acreditacao=TipoAcreditacao(tipo_acreditacao),
        snapshot_equipamento_json=m.snapshot_equipamento_json,
        snapshot_padroes_usados_json=m.snapshot_padroes_usados_json,
        cliente_ref_hash=getattr(m, "cliente_ref_hash", ""),
        reconciliacao_hash=m.reconciliacao_hash,
        emitido_em=emitido_em,
        correlation_id=m.correlation_id,
        regra_decisao_snapshot=m.regra_decisao_snapshot,
    )


def certificado_snapshot_para_campos(s: CertificadoSnapshot) -> dict[str, Any]:
    """Snapshot -> kwargs do Model (escrita). `id`/`tenant_id`/`equipamento_id`
    vão por fora (FKs resolvidas pelo repositório)."""
    return {
        "calibracao_id": s.calibracao_id,
        "numero_interno": s.numero_interno,
        "numero_certificado": s.numero_certificado,
        "versao": s.versao,
        "versao_anterior_id": s.versao_anterior_id,
        "status": s.status.value,
        "perfil_emissor_no_momento": s.perfil_emissor_no_momento,
        "faixa_certificado_min": s.faixa_certificado_min,
        "faixa_certificado_max": s.faixa_certificado_max,
        "tipo_acreditacao": s.tipo_acreditacao.value,
        "snapshot_equipamento_json": dict(s.snapshot_equipamento_json),
        "snapshot_padroes_usados_json": [dict(p) for p in s.snapshot_padroes_usados_json],
        "reconciliacao_hash": s.reconciliacao_hash,
        "emitido_em": s.emitido_em,
        "correlation_id": s.correlation_id,
        "regra_decisao_snapshot": (
            dict(s.regra_decisao_snapshot) if s.regra_decisao_snapshot is not None else None
        ),
    }


# --- PontoReconciliado --------------------------------------------------------


def ponto_model_para_snapshot(m: PontoReconciliado) -> PontoReconciliadoSnapshot:
    return PontoReconciliadoSnapshot(
        id=m.id,
        tenant_id=m.tenant_id,
        certificado_id=m.certificado_id,
        ponto_calibracao=m.ponto_calibracao,
        valor_reportado=m.valor_reportado,
        U_no_ponto=m.u_no_ponto,
        k_no_ponto=m.k_no_ponto,
        nivel_confianca_no_ponto=m.nivel_confianca_no_ponto,
        grau_liberdade_efetivo_no_ponto=m.grau_liberdade_efetivo_no_ponto,
        cmc_no_ponto=m.cmc_no_ponto,
        classificacao=ClassificacaoPonto(m.classificacao),
        u_igual_cmc_suspeita=m.u_igual_cmc_suspeita,
        incluido_no_certificado=m.incluido_no_certificado,
        ressalva_nao_rbc=m.ressalva_nao_rbc,
    )


def ponto_snapshot_para_campos(s: PontoReconciliadoSnapshot) -> dict[str, Any]:
    """`certificado_id`/`tenant_id`/`id` vão por fora (FKs no repositório)."""
    return {
        "ponto_calibracao": s.ponto_calibracao,
        "valor_reportado": s.valor_reportado,
        "u_no_ponto": s.U_no_ponto,
        "k_no_ponto": s.k_no_ponto,
        "nivel_confianca_no_ponto": s.nivel_confianca_no_ponto,
        "grau_liberdade_efetivo_no_ponto": s.grau_liberdade_efetivo_no_ponto,
        "cmc_no_ponto": s.cmc_no_ponto,
        "classificacao": s.classificacao.value,
        "u_igual_cmc_suspeita": s.u_igual_cmc_suspeita,
        "incluido_no_certificado": s.incluido_no_certificado,
        "ressalva_nao_rbc": s.ressalva_nao_rbc,
    }


# --- AnaliseReconciliacaoCertificado ------------------------------------------


def analise_model_para_snapshot(m: AnaliseReconciliacaoCert) -> AnaliseReconciliacaoCertificado:
    return AnaliseReconciliacaoCertificado(
        id=m.id,
        tenant_id=m.tenant_id,
        calibracao_id=m.calibracao_id,
        ponto_calibracao=m.ponto_calibracao,
        decisao_rt=DecisaoReconciliacaoRT(m.decisao_rt),
        categoria_motivo=CategoriaMotivoExclusao(m.categoria_motivo),
        justificativa_canonicalizada=m.justificativa_canonicalizada,
        justificativa_hash=m.justificativa_hash,
        criado_em=m.criado_em,
        correlation_id=m.correlation_id,
        ressalva_nao_rbc=m.ressalva_nao_rbc,
        decisor_id_hash=m.decisor_id_hash,
    )


def analise_snapshot_para_campos(s: AnaliseReconciliacaoCertificado) -> dict[str, Any]:
    return {
        "calibracao_id": s.calibracao_id,
        "ponto_calibracao": s.ponto_calibracao,
        "decisao_rt": s.decisao_rt.value,
        "categoria_motivo": s.categoria_motivo.value,
        "justificativa_canonicalizada": s.justificativa_canonicalizada,
        "justificativa_hash": s.justificativa_hash,
        "ressalva_nao_rbc": s.ressalva_nao_rbc,
        "decisor_id_hash": s.decisor_id_hash,
        "correlation_id": s.correlation_id,
    }
