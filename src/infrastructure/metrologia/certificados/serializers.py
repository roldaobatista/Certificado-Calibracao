"""Serializers DRF do M8 certificados (T-CER-044).

Validam o payload das actions do `CertificadoViewSet`. O perfil regulatório, o
`tipo_acreditacao` e a vigência da acreditação NUNCA vêm do payload (ADR-0067/0075 —
defesa L6): são derivados server-side do `Tenant`. `snapshot_padroes_usados_json` é
metadado do laboratório (não do cliente final). O read-path (`retrieve`) usa as
funções `serializar_certificado_leitura`/`serializar_ponto_reconciliado` (NÃO
Serializers DRF) lendo SÓ campos persistidos — nunca reconsulta
`cmc_para`/`tenant_perfil_e` (INV-CER-SNAPSHOT-CMC-001).
"""

from __future__ import annotations

from collections.abc import Sequence

from rest_framework import serializers

from src.domain.metrologia.certificados.entities import (
    CertificadoSnapshot,
    PontoReconciliadoSnapshot,
)
from src.domain.metrologia.certificados.enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
)

_CLASSIFICACAO_CHOICES = [c.value for c in ClassificacaoPonto]
_DECISAO_CHOICES = [d.value for d in DecisaoReconciliacaoRT]
_CATEGORIA_CHOICES = [c.value for c in CategoriaMotivoExclusao]


class EmitirCertificadoSerializer(serializers.Serializer):
    """US-CER-001 — emissão metrológica. Perfil/tipo/vigência server-side."""

    calibracao_id = serializers.UUIDField()
    # Metadado do lab: lista de {padrao_id, calibracao_padrao_vigencia_fim}. Default
    # vazio (fail-open lazy do INV-CER-PADRAO-VIG-001 até o wiring com M5 padroes).
    snapshot_padroes_usados_json = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )
    data_emissao = serializers.DateField(required=False, allow_null=True, default=None)
    correlation_id = serializers.UUIDField()


class ReemitirCertificadoSerializer(serializers.Serializer):
    """US-CER-004 — reemissão versionada. `motivo` >= 50 chars (validado também no
    domínio). `certificado_anterior_id` vem da URL (pk)."""

    motivo = serializers.CharField(min_length=50, max_length=2000)
    snapshot_padroes_usados_json = serializers.ListField(
        child=serializers.DictField(), required=False, allow_null=True, default=None
    )
    data_emissao = serializers.DateField(required=False, allow_null=True, default=None)
    correlation_id = serializers.UUIDField()


class DecidirPontoSerializer(serializers.Serializer):
    """NC-03 — decisão WORM do RT por ponto (pré-condição da emissão)."""

    calibracao_id = serializers.UUIDField()
    ponto_calibracao = serializers.DecimalField(max_digits=30, decimal_places=12)
    classificacao = serializers.ChoiceField(choices=_CLASSIFICACAO_CHOICES)
    decisao_rt = serializers.ChoiceField(choices=_DECISAO_CHOICES)
    categoria_motivo = serializers.ChoiceField(choices=_CATEGORIA_CHOICES)
    justificativa = serializers.CharField(min_length=20, max_length=2000)
    ressalva_nao_rbc = serializers.CharField(
        required=False, allow_blank=True, default="", max_length=2000
    )
    correlation_id = serializers.UUIDField()


def serializar_ponto_reconciliado(p: PontoReconciliadoSnapshot) -> dict[str, object]:
    """Read-path de um `PontoReconciliadoSnapshot` — SÓ campos persistidos
    (INV-CER-SNAPSHOT-CMC-001: `cmc_no_ponto` é o do snapshot, nunca reconsultado)."""
    return {
        "ponto_calibracao": str(p.ponto_calibracao),
        "valor_reportado": str(p.valor_reportado),
        "U_no_ponto": str(p.U_no_ponto),
        "k_no_ponto": str(p.k_no_ponto),
        "nivel_confianca_no_ponto": str(p.nivel_confianca_no_ponto),
        "grau_liberdade_efetivo_no_ponto": str(p.grau_liberdade_efetivo_no_ponto),
        "cmc_no_ponto": str(p.cmc_no_ponto) if p.cmc_no_ponto is not None else None,
        "classificacao": p.classificacao.value,
        "u_igual_cmc_suspeita": p.u_igual_cmc_suspeita,
        "incluido_no_certificado": p.incluido_no_certificado,
        "ressalva_nao_rbc": p.ressalva_nao_rbc,
    }


def serializar_certificado_leitura(
    cert: CertificadoSnapshot, pontos: Sequence[PontoReconciliadoSnapshot]
) -> dict[str, object]:
    """Read-path do certificado emitido (T-CER-044/045). Lê SOMENTE do snapshot
    persistido — NUNCA invoca `cmc_para`/`tenant_perfil_e` (INV-CER-SNAPSHOT-CMC-001:
    WORM furado por LEITURA seria bug). Rótulos PT ficam na camada de apresentação."""
    return {
        "id": str(cert.id),
        "numero_certificado": cert.numero_certificado,
        "numero_interno": cert.numero_interno,
        "versao": cert.versao,
        "versao_anterior_id": (
            str(cert.versao_anterior_id) if cert.versao_anterior_id else None
        ),
        "status": cert.status.value,
        "tipo_acreditacao": cert.tipo_acreditacao.value,
        "perfil_emissor_no_momento": cert.perfil_emissor_no_momento,
        "faixa_certificado_min": (
            str(cert.faixa_certificado_min)
            if cert.faixa_certificado_min is not None
            else None
        ),
        "faixa_certificado_max": (
            str(cert.faixa_certificado_max)
            if cert.faixa_certificado_max is not None
            else None
        ),
        "reconciliacao_hash": cert.reconciliacao_hash,
        "calibracao_id": str(cert.calibracao_id),
        "equipamento_id": str(cert.equipamento_id),
        "emitido_em": cert.emitido_em.isoformat(),
        "pontos": [serializar_ponto_reconciliado(p) for p in pontos],
    }
