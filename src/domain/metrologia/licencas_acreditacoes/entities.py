"""Entidades do domínio licencas-acreditacoes (M9 Wave A, T-LIC-012).

Frozen dataclasses (imutáveis) — a lógica de status/fronteira/validação vive em
`transicoes.py` (puro, sem import circular). Vigência canônica ADR-0030
(`vigencia_inicio <= vigencia_fim`); `DocumentoRegulatorio` é Padrão B WORM
(`revogado_em`/`motivo_revogacao`, ADR-0031); `RevisaoDocumento` e
`EventoEmergencial` são append-only. PII de titular (ART/RRT) via par
`titular_referencia_hash`/`key_id` (ADR-0032 — número/órgão NÃO são PII; CPF/nome
sim). Sem Django (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from uuid import UUID, uuid4

from .enums import (
    CanalAlerta,
    MotivoRevisao,
    StatusAlerta,
    TipoDocumentoRegulatorio,
)
from .erros import VigenciaInvalidaError


@dataclass(frozen=True, slots=True)
class DocumentoRegulatorio:
    """Raiz do agregado. `vigencia_inicio/fim` refletem a REVISÃO atual. Campos
    mutáveis em produção (`responsavel_id`, `bloqueante`, `observacao`) são trocados
    criando novo snapshot (frozen). Acreditação CGCRE exige `escopo` (validado em
    `transicoes.validar_tipo_x_perfil`)."""

    id: UUID
    tenant_id: UUID
    tipo: TipoDocumentoRegulatorio
    numero: str
    orgao_emissor: str
    vigencia_inicio: date
    vigencia_fim: date
    bloqueante: bool
    criado_em: datetime
    criado_por: UUID
    escopo: str = ""
    # Acreditação CGCRE — fonte rica (ADR-0079): número RBC + aderência ILAC-MRA. O
    # cache `Tenant.acreditacao_*` espelha estes (sincronizado só via aplicar_evento_cgcre).
    numero_cgcre: str = ""
    ilac_mra_aderido: bool = False
    titular_referencia_hash: str = ""
    titular_referencia_key_id: str = ""
    responsavel_id: UUID | None = None
    observacao: str = ""
    perfil_no_evento: str = ""
    correlation_id: UUID = field(default_factory=uuid4)
    revogado_em: datetime | None = None
    motivo_revogacao: str = ""

    def __post_init__(self) -> None:
        if self.vigencia_fim < self.vigencia_inicio:
            raise VigenciaInvalidaError(
                f"vigencia_fim {self.vigencia_fim} < vigencia_inicio "
                f"{self.vigencia_inicio} (data_validade deve ser > data_emissao)"
            )


@dataclass(frozen=True, slots=True)
class RevisaoDocumento:
    """Histórico versionado append-only (WORM — INV-LIC-WORM-001). Cada renovação/
    retificação é uma nova revisão; a anterior NUNCA é editada nem excluída."""

    id: UUID
    tenant_id: UUID
    documento_id: UUID
    numero_revisao: int
    data_emissao: date
    data_validade: date
    anexo_id: UUID
    anexo_sha256: str
    motivo: MotivoRevisao
    criado_em: datetime
    criado_por: UUID

    def __post_init__(self) -> None:
        if self.data_validade <= self.data_emissao:
            raise VigenciaInvalidaError(
                f"data_validade {self.data_validade} <= data_emissao "
                f"{self.data_emissao} (revisão {self.numero_revisao})"
            )
        if not self.anexo_sha256:
            # Defesa de domínio — a validação canônica é `validar_anexo` (INV-046).
            raise VigenciaInvalidaError("revisão sem anexo_sha256 (INV-LIC-ANEXO-001)")


@dataclass(frozen=True, slots=True)
class AlertaVencimento:
    """Alerta agendado por janela (US-LIC-002). Idempotente por
    `(tenant, documento, janela_dias)` (UNIQUE na Fatia 1b)."""

    id: UUID
    tenant_id: UUID
    documento_id: UUID
    data_disparo: date
    janela_dias: int
    canal: CanalAlerta
    destinatario_id: UUID
    status: StatusAlerta = StatusAlerta.PENDENTE
    tentativas: int = 0


@dataclass(frozen=True, slots=True)
class BloqueioOperacional:
    """Bloqueio ativo quando documento bloqueante vence (INV-032). `tipo_documento`
    determina a fronteira (REBAIXA vs HARD — D-LIC-5). `data_fim_bloqueio is None`
    = ativo; preenchido na renovação (auto-resolve)."""

    id: UUID
    tenant_id: UUID
    documento_id: UUID
    tipo_documento: TipoDocumentoRegulatorio
    operacao_bloqueada: str
    data_inicio_bloqueio: datetime
    data_fim_bloqueio: datetime | None = None

    @property
    def ativo(self) -> bool:
        return self.data_fim_bloqueio is None


@dataclass(frozen=True, slots=True)
class EventoEmergencial:
    """Liberação excepcional auditada (INV-033) — append-only WORM. Registra
    `assinatura_a3_id` (FK) + `justificativa_hash`; validação criptográfica da A3
    é DIFERIDA (GATE-LIC-EMERGENCIAL-A3-CRIPTO Wave B — fail-open lazy declarado).
    Expira em ≤7d (`expira_em`)."""

    id: UUID
    tenant_id: UUID
    bloqueio_id: UUID
    operacao_executada: str
    justificativa: str
    justificativa_hash: str
    admin_id: UUID
    assinatura_a3_id: UUID
    expira_em: datetime
    criado_em: datetime
    # libera apenas operação NÃO-RBC quando o bloqueio é de acreditação CGCRE (D-LIC-6).
    libera_apenas_nao_rbc: bool = field(default=False)
