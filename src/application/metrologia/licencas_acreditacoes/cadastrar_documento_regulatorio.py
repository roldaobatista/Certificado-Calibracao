"""Use case `cadastrar_documento_regulatorio` — US-LIC-001 (M9 T-LIC-040).

Cadastra um DocumentoRegulatorio novo (raiz) + RevisaoDocumento v1 (CADASTRO_INICIAL)
em UMA transação (repo.salvar_novo). Use case PURO (ADR-0007): Input frozen +
Repository Protocol. Guards de domínio:
  - anexo sha256 obrigatório (INV-LIC-ANEXO-001 → 422);
  - tipo×perfil (INV-LIC-PERFIL-001 — acreditação CGCRE exige perfil A/B/C + escopo);
  - `bloqueante` é DERIVADO da fronteira por tipo (D-LIC-5) — NUNCA do payload;
  - idempotência por chave natural (tenant, tipo, numero, orgao_emissor).
O perfil vem server-side (ADR-0067). NÃO chama AuthorizationProvider (caller=guard).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID, uuid4

from src.domain.metrologia.licencas_acreditacoes.entities import (
    DocumentoRegulatorio,
    RevisaoDocumento,
)
from src.domain.metrologia.licencas_acreditacoes.enums import (
    MotivoRevisao,
    TipoBloqueio,
    TipoDocumentoRegulatorio,
)
from src.domain.metrologia.licencas_acreditacoes.repository import (
    DocumentoRegulatorioRepository,
)
from src.domain.metrologia.licencas_acreditacoes.transicoes import (
    fronteira_bloqueio,
    validar_anexo,
    validar_tipo_x_perfil,
)


class DocumentoDuplicadoError(Exception):
    """Idempotência — já existe documento (tenant, tipo, numero, orgao_emissor)."""

    def __init__(self) -> None:
        super().__init__(
            "já existe documento regulatório com este tipo+número+órgão "
            "(use renovar para nova revisão)."
        )


@dataclass(frozen=True, slots=True)
class CadastrarDocumentoInput:
    tenant_id: UUID
    tipo: TipoDocumentoRegulatorio
    numero: str
    orgao_emissor: str
    vigencia_inicio: date
    vigencia_fim: date
    perfil: str  # server-side (A/B/C/D) — NUNCA payload (ADR-0067)
    anexo_id: UUID
    anexo_sha256: str  # recalculado server-side (INV-LIC-ANEXO-001)
    criado_por: UUID
    criado_em: datetime
    correlation_id: UUID
    escopo: str = ""
    numero_cgcre: str = ""
    ilac_mra_aderido: bool = False
    titular_referencia_hash: str = ""
    titular_referencia_key_id: str = ""
    responsavel_id: UUID | None = None
    observacao: str = ""

    def __post_init__(self) -> None:
        if self.criado_em.tzinfo is None:
            raise ValueError(
                "cadastrar_documento: criado_em exige datetime tz-aware (INV-VIG-004)."
            )


@dataclass(frozen=True, slots=True)
class CadastrarDocumentoOutput:
    documento: DocumentoRegulatorio
    revisao: RevisaoDocumento


def executar(
    inp: CadastrarDocumentoInput, repo: DocumentoRegulatorioRepository
) -> CadastrarDocumentoOutput:
    # 1. Anexo probatório obrigatório (422).
    validar_anexo(anexo_sha256=inp.anexo_sha256)
    # 2. tipo×perfil (acreditação CGCRE exige A/B/C + escopo) — defesa L6 (403).
    validar_tipo_x_perfil(tipo=inp.tipo, perfil=inp.perfil, escopo=inp.escopo)
    # 3. Idempotência por chave natural.
    if repo.existe_chave(
        tenant_id=inp.tenant_id,
        tipo=inp.tipo.value,
        numero=inp.numero,
        orgao_emissor=inp.orgao_emissor,
    ):
        raise DocumentoDuplicadoError
    # 4. `bloqueante` DERIVADO da fronteira por tipo (nunca payload — D-LIC-5).
    bloqueante = fronteira_bloqueio(inp.tipo) is not TipoBloqueio.NENHUM

    documento_id = uuid4()
    documento = DocumentoRegulatorio(
        id=documento_id,
        tenant_id=inp.tenant_id,
        tipo=inp.tipo,
        numero=inp.numero,
        orgao_emissor=inp.orgao_emissor,
        vigencia_inicio=inp.vigencia_inicio,
        vigencia_fim=inp.vigencia_fim,
        bloqueante=bloqueante,
        criado_em=inp.criado_em,
        criado_por=inp.criado_por,
        escopo=inp.escopo,
        numero_cgcre=inp.numero_cgcre,
        ilac_mra_aderido=inp.ilac_mra_aderido,
        titular_referencia_hash=inp.titular_referencia_hash,
        titular_referencia_key_id=inp.titular_referencia_key_id,
        responsavel_id=inp.responsavel_id,
        observacao=inp.observacao,
        perfil_no_evento=inp.perfil,
        correlation_id=inp.correlation_id,
    )
    revisao = RevisaoDocumento(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        documento_id=documento_id,
        numero_revisao=1,
        data_emissao=inp.vigencia_inicio,
        data_validade=inp.vigencia_fim,
        anexo_id=inp.anexo_id,
        anexo_sha256=inp.anexo_sha256,
        motivo=MotivoRevisao.CADASTRO_INICIAL,
        criado_em=inp.criado_em,
        criado_por=inp.criado_por,
    )
    repo.salvar_novo(documento, revisao)
    return CadastrarDocumentoOutput(documento=documento, revisao=revisao)
