"""Snapshot DTOs imutaveis (T-OS-014..020) — atravessam fronteiras de camada.

Adapter Django converte Model <-> Snapshot. Domain layer NUNCA importa
django.* — recebe sempre snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from .value_objects import (
    EstadoAtividade,
    EstadoChecklistItem,
    EstadoOS,
    PrecedenteDispensa,
    PrioridadeSLA,
    TipoAtividade,
    TipoEventoDeOS,
    TipoFotoEvidencia,
    TipoItemComercial,
)


@dataclass(frozen=True, slots=True)
class OSSnapshot:
    """Snapshot da OS (ADR-0023 — container comercial/financeiro)."""

    id: UUID
    tenant_id: UUID
    numero_os: int  # da sequence global os_numero_seq_global (ADR-0056)
    cliente_id: UUID | None  # NULL pos-anonimizacao (ADR-0032)
    cliente_referencia_hash: str  # HMAC-SHA256
    cliente_key_id: str
    equipamento_id: UUID | None  # NULL em OS multi-equipamento (ADR-0082 / D-OSME-2); OS legada/avulsa single-equip pode manter
    equipamento_recebimento_id: UUID | None  # NULL em OS de campo (P-OS-R4)
    orcamento_origem_id: UUID | None
    os_origem_id: UUID | None  # FK reabertura (US-OS-006)
    sucessao_societaria_id: UUID | None  # M&A (INV-OS-SUC-001)
    estado: EstadoOS
    tipo_predominante: str  # calculado em transicao -> CONCLUIDA
    nao_conformidade_global: bool
    valor_total: Decimal
    valor_total_atualizado: Decimal
    analise_critica_id: UUID | None
    analise_critica_snapshot_hash: str
    regra_decisao_acordada: str  # ADR-0024 snapshot
    criada_em: datetime
    atualizada_em: datetime
    criada_por_user_id: UUID | None


@dataclass(frozen=True, slots=True)
class AtividadeSnapshot:
    """Snapshot da AtividadeDaOS (ADR-0023). N por OS."""

    id: UUID
    tenant_id: UUID
    os_id: UUID
    tipo: TipoAtividade
    sequencia: int
    estado: EstadoAtividade
    tecnico_executor_id: UUID | None
    agendada_para: datetime | None
    iniciada_em: datetime | None
    concluida_em: datetime | None
    valor_unitario_snapshot: Decimal
    link_modulo_tecnico_id: UUID | None  # FK reversa Calibracao/Manutencao
    geo_lat: float | None
    geo_long: float | None
    geo_municipio_hash: str
    # Proprio da atividade; fallback via trigger COALESCE p/ OS.equipamento_id (ADR-0082 / INV-OS-CONC-001)
    equipamento_id: UUID | None
    tipo_bloqueia_concorrencia: bool
    # Recebimento POR INSTRUMENTO (cl. 7.4.3/7.8.2.1 — D-OSME-5 / ADR-0082). Ponteiro do
    # item calibrando recebido, no nível da atividade (estrutura conforme INV-OSME-RCB-001).
    # NULL até o seam de preenchimento ser ativado (GATE-OSME-RECEBIMENTO-7.5): hoje o
    # recebimento é populado em OS.equipamento_recebimento_id (degeneração OS-level, válida
    # em OS single-instrumento — AC-OS-001-8). Quando o produtor `criar_recebimento` publicar
    # `atividade_id`, o consumer popula este campo por instrumento.
    equipamento_recebimento_id: UUID | None = None
    # Grandeza metrológica da atividade (ADR-0063). Vazio até `configurar_calibracao`
    # (M4) propagar; quando populada, o predicate `rt_competencia_cobre` passa a
    # bloquear transferências de técnico (ADR-0063 ponto 3 — drop-in).
    grandeza: str = ""


@dataclass(frozen=True, slots=True)
class ItemComercialOSSnapshot:
    """Snapshot de item comercial sem equipamento (D-OSME-3 / spec os-multi-equipamento §4).

    Linha propria na OS — deslocamento, taxa de visita ou outro custo comercial.
    Nunca possui equipamento_id nem entra no indice de concorrencia
    (INV-OSME-ITEMCOM-001). Soma em OS.valor_total_atualizado (valor corrente;
    OS.valor_total e o original imutavel do orcamento).
    """

    id: UUID
    tenant_id: UUID
    os_id: UUID
    tipo: TipoItemComercial
    descricao_publica: str
    valor: Decimal
    quantidade: int
    origem_item_id: UUID | None  # rastreio do item de orcamento de origem


@dataclass(frozen=True, slots=True)
class ConsentimentoBiometriaTouchSnapshot:
    """Snapshot do consentimento art. 11 LGPD (INV-OS-CONSBIO-001).

    FK 1:1 com AceiteAtividade — pre-requisito formal quando bio touch.
    """

    id: UUID
    tenant_id: UUID
    atividade_id: UUID
    cliente_referencia_hash: str
    cliente_key_id: str
    texto_canonico_id: UUID
    texto_hash: str  # SHA-256 do texto exibido (INV-DOC-CANON-001)
    versao_politica: str  # semver
    concedido_em: datetime
    tela_renderizada_evidencia: bytes | None
    criado_em: datetime


@dataclass(frozen=True, slots=True)
class AceiteAtividadeSnapshot:
    """Snapshot do aceite do cliente (Padrao B imutavel)."""

    id: UUID
    tenant_id: UUID
    atividade_id: UUID
    consentimento_id: UUID | None  # NOT NULL quando biometria
    cliente_referencia_hash: str
    cliente_key_id: str
    texto_canonicalizado: str  # ADR-0029
    texto_hash: str  # INV-DOC-CANON-001
    biometria_payload_encrypted: bytes | None
    biometria_key_id: str
    coletado_em: datetime
    geo_lat: float | None
    geo_long: float | None
    geo_municipio_hash: str
    criado_em: datetime


@dataclass(frozen=True, slots=True)
class DispensaAceiteAtividadeSnapshot:
    """Snapshot da dispensa formal (US-OS-013 + P-OS-A4)."""

    id: UUID
    tenant_id: UUID
    atividade_id: UUID
    motivo_hash: str
    autorizado_por_gerente_id: UUID
    a3_assinatura_hash: str
    a3_certificado_emissor_hash: str
    a3_assinada_em: datetime
    termo_pdf_b2_uri: str
    termo_pdf_sha256: str
    precedente_tipo: PrecedenteDispensa
    precedente_evento_id: UUID | None
    criado_em: datetime


@dataclass(frozen=True, slots=True)
class EvidenciaFotoAtividadeSnapshot:
    """Snapshot de foto evidencia (Padrao B append-only)."""

    id: UUID
    tenant_id: UUID
    atividade_id: UUID
    tipo: TipoFotoEvidencia
    b2_uri: str
    foto_sha256: str
    client_event_id: UUID
    client_event_created_at: datetime
    enviada_em: datetime
    tecnico_executor_id: UUID | None
    geo_lat: float | None
    geo_long: float | None
    geo_municipio_hash: str
    revogado_em: datetime | None  # LGPD art. 18
    criado_em: datetime


@dataclass(frozen=True, slots=True)
class EventoDeOSSnapshot:
    """Snapshot de evento na timeline da OS (append-only sanitizada)."""

    id: UUID
    tenant_id: UUID
    os_id: UUID
    atividade_id: UUID | None
    tipo: TipoEventoDeOS
    payload_hash: str
    payload_data: dict[str, object]  # sanitizado — sem PII cru
    correlation_id: UUID
    actor_user_id: UUID | None
    occurred_at: datetime
    criado_em: datetime


@dataclass(frozen=True, slots=True)
class ChecklistItemSnapshot:
    """Snapshot de item de checklist (Padrao A — mutavel via service)."""

    id: UUID
    tenant_id: UUID
    atividade_id: UUID
    ordem: int
    descricao_hash: str
    descricao_publica: str
    estado: EstadoChecklistItem
    valor_hash: str
    valor_publico: str
    preenchido_por_user_id: UUID | None
    preenchido_em: datetime | None
    evidencia_foto_id: UUID | None
    criado_em: datetime
    atualizado_em: datetime


@dataclass(frozen=True, slots=True)
class NaoConformidadeAtividadeSnapshot:
    """Snapshot de NC (cl. 8.7 + ciclo CAPA P-OS-R5)."""

    id: UUID
    tenant_id: UUID
    atividade_id: UUID
    razao_nao_conformidade_hash: str
    marcada_em: datetime
    marcada_por_user_id: UUID
    registro_capa_id: UUID | None  # Wave B
    causa_raiz_hash: str
    acao_corretiva_descricao_hash: str
    eficacia_verificada_em: datetime | None
    eficacia_verificada_por_user_id: UUID | None
    revogado_em: datetime | None
    criado_em: datetime

    @property
    def capa_completo(self) -> bool:
        """AC-OS-005-5: resolverNC exige TODOS os 4 campos CAPA."""
        return (
            bool(self.causa_raiz_hash)
            and bool(self.acao_corretiva_descricao_hash)
            and self.eficacia_verificada_em is not None
            and self.eficacia_verificada_por_user_id is not None
        )


@dataclass(frozen=True, slots=True)
class SLAContratoSnapshot:
    """Snapshot de SLA (vigencia ADR-0030)."""

    id: UUID
    tenant_id: UUID
    cliente_id: UUID
    prioridade: PrioridadeSLA
    prazo_atendimento_horas: int
    prazo_conclusao_horas: int
    descricao_publica: str
    vigencia_inicio: datetime
    vigencia_fim: datetime | None
    revogado_em: datetime | None
    motivo_revogacao_hash: str
    criado_em: datetime
    atualizado_em: datetime

    def vigente_em(self, data: datetime) -> bool:
        """Aplica ADR-0030 — janela canonica."""
        if self.revogado_em is not None and data >= self.revogado_em:
            return False
        if data < self.vigencia_inicio:
            return False
        if self.vigencia_fim is not None and data >= self.vigencia_fim:
            return False
        return True


@dataclass(frozen=True, slots=True)
class TipoAtividadeConfigSnapshot:
    """Snapshot de config por tipo (matriz ADR-0041 + INV-CAL-RT)."""

    id: int
    tenant_id: UUID
    tipo: TipoAtividade
    requer_competencia_rt: bool
    tipo_bloqueia_concorrencia: bool
    executa_em_campo: bool
    prazo_link_calibracao_alerta_h: int | None
    prazo_link_calibracao_nc_dias_uteis: int | None
    deletado_em: datetime | None  # Padrao C
    criado_em: datetime
    atualizado_em: datetime
