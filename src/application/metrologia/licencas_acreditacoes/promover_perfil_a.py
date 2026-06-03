"""Use case `promover_perfil_a` — US-LIC-001 (AC-LIC-001-4) / D-LIC-4 (M9 T-LIC-041).

Cadastra a `Licenca` (ACREDITACAO_CGCRE — fonte rica ADR-0079) E promove o perfil do
tenant para o próximo nível regulatório, em UMA transação atômica (o CALLER abre o
`transaction.atomic`): (1) INSERT documento + revisão v1; (2) `aplicar_evento_cgcre`
(`promocao_regulatoria`) na MESMA transação — única forma de mutar `Tenant.perfil`/
`acreditacao_*` (INV-LIC-VIG-SYNC-001). A função grava `acreditacao_vigencia_fim`
(que o M8 lê → fecha GATE-CER-CGCRE-VIG-DATA-POPULAR) e advisory-lock por tenant.

Idempotência composta: se a Licenca já existe (chave natural), no-op (a retentativa
NÃO re-promove). Use case orquestra repo + porta `AplicarEventoCgcrePort` (adapter
real faz o raw cursor — testável com Fake).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID

from src.domain.metrologia.licencas_acreditacoes.entities import DocumentoRegulatorio
from src.domain.metrologia.licencas_acreditacoes.enums import TipoDocumentoRegulatorio
from src.domain.metrologia.licencas_acreditacoes.repository import (
    DocumentoRegulatorioRepository,
)

from .cadastrar_documento_regulatorio import (
    CadastrarDocumentoInput,
)
from .cadastrar_documento_regulatorio import (
    executar as cadastrar_executar,
)


class AplicarEventoCgcrePort(Protocol):
    """Porta para a função SECURITY DEFINER `aplicar_evento_cgcre` (raw cursor na infra).
    Roda na transação do caller (advisory lock por tenant é interno à função)."""

    def promover(
        self,
        *,
        tenant_id: UUID,
        perfil_novo: str,
        motivo: str,
        documento_cgcre_id: UUID,
        assinatura_a3_id: UUID,
        registrado_por_id: UUID,
        auditor_cgcre: str | None,
        numero_rbc: str,
        ilac_mra_aderido: bool,
        vigencia_fim: date,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class PromoverPerfilAInput:
    tenant_id: UUID
    perfil_atual: str  # server-side (D/C/B) — base da validação tipo×perfil
    perfil_novo: str  # próximo nível monotônico (C/B/A) — validado pela função
    numero: str
    orgao_emissor: str
    vigencia_inicio: date
    vigencia_fim: date
    escopo: str
    numero_cgcre: str
    assinatura_a3_id: UUID
    motivo: str  # ≥100 chars (CHECK da função)
    criado_por: UUID
    criado_em: datetime
    correlation_id: UUID
    auditor_cgcre: str | None = None  # obrigatório p/ promoção a A (função valida)
    ilac_mra_aderido: bool = False
    anexo_id: UUID | None = None
    anexo_sha256: str = ""

    def __post_init__(self) -> None:
        if len(self.motivo.strip()) < 100:
            raise ValueError(
                "promover_perfil_a: motivo exige ≥100 chars (CHECK aplicar_evento_cgcre)."
            )


@dataclass(frozen=True, slots=True)
class PromoverPerfilAOutput:
    documento: DocumentoRegulatorio
    promovido: bool  # False = idempotente (Licenca já existia → não re-promove)


def executar(
    inp: PromoverPerfilAInput,
    *,
    doc_repo: DocumentoRegulatorioRepository,
    aplicar_evento_cgcre: AplicarEventoCgcrePort,
) -> PromoverPerfilAOutput:
    # Idempotência composta: Licenca já cadastrada → no-op (não re-promove).
    existente = doc_repo.obter_por_chave_natural(
        tenant_id=inp.tenant_id,
        tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE.value,
        numero=inp.numero,
        orgao_emissor=inp.orgao_emissor,
    )
    if existente is not None:
        return PromoverPerfilAOutput(documento=existente, promovido=False)

    # 1. Cadastra a Licenca CGCRE (fonte rica) + revisão v1 (valida anexo + tipo×perfil).
    cad = cadastrar_executar(
        CadastrarDocumentoInput(
            tenant_id=inp.tenant_id,
            tipo=TipoDocumentoRegulatorio.ACREDITACAO_CGCRE,
            numero=inp.numero,
            orgao_emissor=inp.orgao_emissor,
            vigencia_inicio=inp.vigencia_inicio,
            vigencia_fim=inp.vigencia_fim,
            perfil=inp.perfil_atual,
            anexo_id=inp.anexo_id or UUID(int=0),
            anexo_sha256=inp.anexo_sha256,
            criado_por=inp.criado_por,
            criado_em=inp.criado_em,
            correlation_id=inp.correlation_id,
            escopo=inp.escopo,
            numero_cgcre=inp.numero_cgcre,
            ilac_mra_aderido=inp.ilac_mra_aderido,
        ),
        doc_repo,
    )
    # 2. Promove o perfil via função SECURITY DEFINER (MESMA transação do caller).
    aplicar_evento_cgcre.promover(
        tenant_id=inp.tenant_id,
        perfil_novo=inp.perfil_novo,
        motivo=inp.motivo,
        documento_cgcre_id=cad.documento.id,
        assinatura_a3_id=inp.assinatura_a3_id,
        registrado_por_id=inp.criado_por,
        auditor_cgcre=inp.auditor_cgcre,
        numero_rbc=inp.numero_cgcre,
        ilac_mra_aderido=inp.ilac_mra_aderido,
        vigencia_fim=inp.vigencia_fim,
    )
    return PromoverPerfilAOutput(documento=cad.documento, promovido=True)
