"""Entidades persistíveis do domínio certificados (M8 Fatia 1a, T-CER-012..014).

Snapshots WORM (frozen + slots, mesmo padrão de `calibracao.entities`):
imutáveis pós-INSERT (trigger PG — INV-CER-WORM-001). A LÓGICA vive aqui (ADR-0072
aninhado); a TABELA física `certificados` permanece achatada em
`infrastructure/certificados/` (contrato trigger INV-025 — ADR-0078).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from .enums import (
    CategoriaMotivoExclusao,
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
    EstadoCertificado,
    TipoAcreditacao,
)
from .reconciliacao import PontoReconciliado


@dataclass(frozen=True, slots=True)
class PontoReconciliadoSnapshot:
    """Linha 1:N do certificado (WORM) — um ponto reportado (T-CER-012). Carrega
    `{U, k, nivel_confianca, nu_eff}` por ponto (NC-05 / NIT-DICLA-030 8.2.6), a
    classificação metrológica, a flag anti-cópia (NC-06) e a `ressalva_nao_rbc`
    (C-03 / cl. 8.1.3): texto obrigatório quando o RT decide
    `EMITIR_NAO_RBC_NO_PONTO` — impede o documento exibir ponto não-RBC como RBC.
    """

    id: UUID
    tenant_id: UUID
    certificado_id: UUID
    ponto_calibracao: Decimal
    valor_reportado: Decimal
    U_no_ponto: Decimal  # — U é notação metrológica canônica
    k_no_ponto: Decimal
    nivel_confianca_no_ponto: Decimal
    grau_liberdade_efetivo_no_ponto: Decimal  # nu_eff (999999 = infinito prático)
    cmc_no_ponto: Decimal | None
    classificacao: ClassificacaoPonto
    u_igual_cmc_suspeita: bool
    incluido_no_certificado: bool
    ressalva_nao_rbc: str = ""

    @classmethod
    def de_reconciliado(
        cls,
        pr: PontoReconciliado,
        *,
        id: UUID,
        tenant_id: UUID,
        certificado_id: UUID,
        ressalva_nao_rbc: str = "",
        classificacao: ClassificacaoPonto | None = None,
        incluido_no_certificado: bool | None = None,
    ) -> PontoReconciliadoSnapshot:
        """Constrói o snapshot a partir do resultado puro (Fatia 0) — fonte única,
        sem reescrever os campos de cálculo. `classificacao`/`incluido` podem ser
        sobrescritos pela decisão do RT (ex.: `EXCLUIR_PONTO` → `EXCLUIDO`)."""
        return cls(
            id=id,
            tenant_id=tenant_id,
            certificado_id=certificado_id,
            ponto_calibracao=pr.ponto_calibracao,
            valor_reportado=pr.valor_reportado,
            U_no_ponto=pr.U_no_ponto,
            k_no_ponto=pr.k_no_ponto,
            nivel_confianca_no_ponto=pr.nivel_confianca_no_ponto,
            grau_liberdade_efetivo_no_ponto=pr.grau_liberdade_efetivo_no_ponto,
            cmc_no_ponto=pr.cmc_no_ponto,
            classificacao=classificacao if classificacao is not None else pr.classificacao,
            u_igual_cmc_suspeita=pr.u_igual_cmc_suspeita,
            incluido_no_certificado=(
                incluido_no_certificado
                if incluido_no_certificado is not None
                else pr.incluido_no_certificado
            ),
            ressalva_nao_rbc=ressalva_nao_rbc,
        )


@dataclass(frozen=True, slots=True)
class CertificadoSnapshot:
    """Certificado emitido (WORM, T-CER-013). `status='emitido'` desde a emissão
    LÓGICA (contrato trigger ADR-0078 + trava equipamento INV-025). A entrega
    normativa cl. 7.8 (RBC) só na assinatura A3 (Wave A — `DocumentoCertificado`).
    """

    id: UUID
    tenant_id: UUID
    calibracao_id: UUID
    equipamento_id: UUID
    numero_interno: int  # sequence PG (buracos OK — INV-CER-NUM-002)
    numero_certificado: str  # valor do VO NumeroCertificado (sem buracos visíveis)
    versao: int
    versao_anterior_id: UUID | None  # None p/ v1
    status: EstadoCertificado
    perfil_emissor_no_momento: str  # CHAR(1) — INV-CER-SNAPSHOT-PERFIL-001 / ADR-0067
    faixa_certificado_min: Decimal | None
    faixa_certificado_max: Decimal | None
    tipo_acreditacao: TipoAcreditacao
    snapshot_equipamento_json: Mapping[str, object]  # paridade pós-baixa (US-CER-013)
    # NC-07 (cl. 6.5): lista de {padrao_id, calibracao_padrao_vigencia_fim} congelada
    # — confirma a vigência da calibração de cada padrão usado NA data de emissão.
    snapshot_padroes_usados_json: Sequence[Mapping[str, object]]
    cliente_ref_hash: str
    reconciliacao_hash: str  # fecho WORM da tabela ponto-a-ponto (T-CER-011)
    emitido_em: datetime
    correlation_id: UUID
    # NC-04: regra de decisão (cl. 7.8.6 / ADR-0024) congelada quando aplicável.
    regra_decisao_snapshot: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class AnaliseReconciliacaoCertificado:
    """Decisão WORM do RT sobre um ponto problemático (T-CER-014, padrão ADR-0070).

    Ligada a `calibracao_id` (existe ANTES da emissão — pré-condição, não a
    `certificado_id`). `categoria_motivo` (C-02 / cl. 7.10.1) é enum estruturado
    para auditoria CGCRE. Justificativa canonicalizada (INV-DOC-CANON-001) + hash
    (A3 da decisão diferida Wave A).
    """

    id: UUID
    tenant_id: UUID
    calibracao_id: UUID
    ponto_calibracao: Decimal
    decisao_rt: DecisaoReconciliacaoRT
    categoria_motivo: CategoriaMotivoExclusao
    justificativa_canonicalizada: str
    justificativa_hash: str
    criado_em: datetime
    correlation_id: UUID
    ressalva_nao_rbc: str = ""  # obrigatória quando decisao_rt=EMITIR_NAO_RBC_NO_PONTO
    decisor_id_hash: str = field(default="")  # HashVersionado(user.id) — A3 Wave A
