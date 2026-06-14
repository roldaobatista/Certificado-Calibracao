"""Repository protocol pra Ordens de Servico — DOMINIO puro (ADR-0007).

NAO importar django.* nem psycopg. Aqui mora apenas o CONTRATO; a
implementacao concreta (adapter Django) vai em
`src/infrastructure/ordens_servico/repositories.py` (a criar em Fase 5).

Use cases (`src/application/operacao/os/`) consomem este Protocol e
nunca conhecem Django.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol, runtime_checkable
from uuid import UUID

from .entities import (
    AceiteAtividadeSnapshot,
    AtividadeSnapshot,
    ChecklistItemSnapshot,
    ConsentimentoBiometriaTouchSnapshot,
    DispensaAceiteAtividadeSnapshot,
    EventoDeOSSnapshot,
    EvidenciaFotoAtividadeSnapshot,
    ItemComercialOSSnapshot,
    NaoConformidadeAtividadeSnapshot,
    OSSnapshot,
    SLAContratoSnapshot,
    TipoAtividadeConfigSnapshot,
)
from .value_objects import TipoAtividade


@runtime_checkable
class OSRepository(Protocol):
    """Contrato de persistencia do agregado OS + AtividadeDaOS + entidades-filho.

    Use cases recebem isso via DI. Adapter Django (`DjangoOSRepository` —
    Fase 5) implementa.
    """

    # ---- OS ----
    def get_os_by_id(self, os_id: UUID, /) -> OSSnapshot | None: ...

    def listar_os_por_tenant(
        self,
        tenant_id: UUID,
        /,
        *,
        estado: str | None = None,
        cliente_id: UUID | None = None,
        equipamento_id: UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[OSSnapshot]: ...

    def proximo_numero_os(self) -> int:
        """Pega proximo valor da sequence global os_numero_seq_global (ADR-0056)."""
        ...

    def salvar_os(self, snapshot: OSSnapshot, /) -> OSSnapshot:
        """INSERT em RASCUNHO ou UPDATE de estado/valor. Retorna snapshot atualizado."""
        ...

    # ---- AtividadeDaOS ----
    def get_atividade_by_id(self, atividade_id: UUID, /) -> AtividadeSnapshot | None: ...

    def listar_atividades_por_os(self, os_id: UUID, /) -> list[AtividadeSnapshot]: ...

    def listar_atividades_em_execucao_por_equipamento(
        self, tenant_id: UUID, equipamento_id: UUID, /
    ) -> list[AtividadeSnapshot]:
        """INV-OS-CONC-001: verificacao pra matriz tipo x tipo ADR-0041.

        Retorna atividades EM_EXECUCAO no mesmo equipamento (excluindo
        a propria se aplicavel).
        """
        ...

    def salvar_atividade(self, snapshot: AtividadeSnapshot, /) -> AtividadeSnapshot: ...

    # ---- AceiteAtividade ----
    def get_aceite_por_atividade(
        self, atividade_id: UUID, /
    ) -> AceiteAtividadeSnapshot | None: ...

    def salvar_aceite(self, snapshot: AceiteAtividadeSnapshot, /) -> AceiteAtividadeSnapshot:
        """Padrao B imutavel — adapter so faz INSERT, trigger PG bloqueia UPDATE."""
        ...

    # ---- ConsentimentoBiometriaTouch ----
    def get_consentimento_por_atividade(
        self, atividade_id: UUID, /
    ) -> ConsentimentoBiometriaTouchSnapshot | None: ...

    def salvar_consentimento(
        self, snapshot: ConsentimentoBiometriaTouchSnapshot, /
    ) -> ConsentimentoBiometriaTouchSnapshot: ...

    # ---- DispensaAceiteAtividade ----
    def get_dispensa_por_atividade(
        self, atividade_id: UUID, /
    ) -> DispensaAceiteAtividadeSnapshot | None: ...

    def salvar_dispensa(
        self, snapshot: DispensaAceiteAtividadeSnapshot, /
    ) -> DispensaAceiteAtividadeSnapshot: ...

    # ---- EvidenciaFotoAtividade ----
    def listar_evidencias_foto_por_atividade(
        self, atividade_id: UUID, /
    ) -> list[EvidenciaFotoAtividadeSnapshot]: ...

    def salvar_evidencia_foto(
        self, snapshot: EvidenciaFotoAtividadeSnapshot, /
    ) -> EvidenciaFotoAtividadeSnapshot: ...

    def revogar_evidencia_foto(
        self, foto_id: UUID, /
    ) -> EvidenciaFotoAtividadeSnapshot:
        """LGPD art. 18 — UPDATE apenas revogado_em. Trigger PG enforça."""
        ...

    # ---- EventoDeOS ----
    def publicar_evento(self, snapshot: EventoDeOSSnapshot, /) -> EventoDeOSSnapshot:
        """Append-only (trigger PG enforça). Adapter usa
        `audit/event_helpers.publicar_evento` (helper unico — INV-OS-AUD-001).
        """
        ...

    def listar_eventos_por_os(
        self, os_id: UUID, /, *, limit: int = 100
    ) -> list[EventoDeOSSnapshot]: ...

    # ---- ChecklistItem ----
    def listar_checklist_por_atividade(
        self, atividade_id: UUID, /
    ) -> list[ChecklistItemSnapshot]: ...

    def salvar_checklist_item(
        self, snapshot: ChecklistItemSnapshot, /
    ) -> ChecklistItemSnapshot: ...

    # ---- NaoConformidadeAtividade ----
    def get_nc_ativa_por_atividade(
        self, atividade_id: UUID, /
    ) -> NaoConformidadeAtividadeSnapshot | None: ...

    def salvar_nc(
        self, snapshot: NaoConformidadeAtividadeSnapshot, /
    ) -> NaoConformidadeAtividadeSnapshot: ...

    # ---- SLAContrato ----
    def get_sla_vigente(
        self, tenant_id: UUID, cliente_id: UUID, /
    ) -> SLAContratoSnapshot | None: ...

    # ---- TipoAtividadeConfig ----
    def get_tipo_atividade_config(
        self, tenant_id: UUID, tipo: TipoAtividade, /
    ) -> TipoAtividadeConfigSnapshot | None: ...

    def listar_tipos_atividade_config(
        self, tenant_id: UUID, /
    ) -> Iterable[TipoAtividadeConfigSnapshot]: ...

    # ---- ItemComercialOS (D-OSME-3 / INV-OSME-ITEMCOM-001) ----
    def salvar_item_comercial(
        self, snapshot: ItemComercialOSSnapshot, /
    ) -> ItemComercialOSSnapshot:
        """INSERT/UPDATE de item comercial. Padrao A — soft-delete via deletado_em."""
        ...

    def listar_itens_comerciais_por_os(
        self, os_id: UUID, /
    ) -> list[ItemComercialOSSnapshot]:
        """Retorna itens comerciais ativos (nao deletados) da OS, por ordem de criacao."""
        ...
