"""Portas (Protocols) do domínio caixa_tecnico (Fatia 1a — T-CT-015).

5 Protocols ``@runtime_checkable`` — seams para adapters reais (Fatia 3a)
e fakes de teste (Fatia 2 / T-CT-030).

Zero Django. Zero I/O.

Refs: D-CT-4/5/6/12; plan §2; spec §4/§6.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID


@runtime_checkable
class FotoComprovanteStoragePort(Protocol):
    """Port para storage de foto-comprovante da despesa (D-CT-4 / TL-CT-01).

    NÃO é ``AnexoStoragePort`` (que é para PDF) — port próprio com pipeline
    específico: JPG/PNG + EXIF strip + HMAC-tenant + content-address.

    Implementação real: ``FotoComprovanteStorageLocal`` (Fatia 3a — T-CT-040).
    Implementação fake: ``FotoComprovanteStorageFake`` (T-CT-030 em ``tests/fakes/``).
    """

    def validar_e_processar(
        self,
        bytes_foto: bytes,
        mime_type: str,
    ) -> tuple[bytes, str]:
        """Valida e processa a foto-comprovante.

        Pipeline:
          1. Valida tipo: JPG/PNG + MIME allowlist + ≤5MB.
          2. EXIF strip obrigatório via Pillow (NUNCA canal de GPS — D-CT-6).
          3. ``foto_hash = HMAC-SHA256(bytes_pós-strip, chave_tenant)`` (ADR-0064).

        Args:
            bytes_foto: bytes brutos recebidos do cliente.
            mime_type:  MIME type declarado (``image/jpeg`` ou ``image/png``).

        Returns:
            ``(bytes_limpos, foto_hash)`` — bytes sem EXIF + HMAC hex.

        Raises:
            FotoComprovanteObrigatoria: tipo inválido, >5MB ou EXIF comprometido.
        """
        ...

    def salvar(
        self,
        tenant_id: UUID,
        foto_hash: str,
        bytes_limpos: bytes,
    ) -> str:
        """Salva a foto content-addressed por tenant.

        Idempotente: ``if not exists`` — replay não re-grava (D-CT-4 / D-CT-5).
        Path: ``media/caixa_tecnico/<tenant>/<hmac[:2]>/<hmac>`` (filesystem local Wave A;
        B2 = GATE pré-prod).

        Args:
            tenant_id:    UUID do tenant.
            foto_hash:    HMAC hex calculado em ``validar_e_processar``.
            bytes_limpos: bytes sem EXIF.

        Returns:
            URL relativa da foto salva.
        """
        ...


@runtime_checkable
class OSReferenciaPort(Protocol):
    """Port para verificar existência de OS no módulo ordens_servico (D-CT-11).

    Seam de leitura pura — não estende módulo fechado; query simples
    ``OrdemServico.objects.filter(tenant_id=..., id=os_id).exists()``.

    Implementação real: ``OSReferenciaAdapter`` (Fatia 3a — T-CT-042).
    """

    def existe_os(self, os_id: UUID, tenant_id: UUID) -> bool:
        """Verifica se a OS existe e pertence ao tenant.

        Non-goal: despesa NÃO segue cancelamento da OS — vínculo é rastro
        histórico (D-CT-11 / spec §7).

        Args:
            os_id:     UUID da OS vinculada.
            tenant_id: UUID do tenant (RLS — OS de outro tenant → False).

        Returns:
            True se a OS existe e pertence ao tenant; False caso contrário.
        """
        ...


@runtime_checkable
class ConsentimentoGpsPort(Protocol):
    """Port para verificar opt-in GPS do colaborador server-side (D-CT-6).

    NUNCA do payload nem do EXIF (INV-LGPD-CONSENT-001).
    Porta desenhada para promoção a ``shared`` quando app-tecnico (N6) nascer
    (spec §8 ação P3.2 — sem ADR nova agora).

    IA NUNCA grava opt-in — apenas o fluxo de RH/colaborador (ADV-CT-06).

    Implementação real: ``ConsentimentoGpsAdapter`` (Fatia 3a — T-CT-041).
    """

    def opt_in_vigente(
        self,
        tenant_id: UUID,
        colaborador_id: UUID,
        na_data: object,  # date ou datetime
    ) -> bool:
        """Verifica se o colaborador tem opt-in GPS ativo na data.

        Verificação server-side: ``vigencia_inicio ≤ na_data`` + ausência de revogação.
        NULL / sem registro → False (coleta GPS off, 403 ``GpsConsentimentoAusente``
        mas despesa segue — D-CT-6).

        Args:
            tenant_id:       UUID do tenant.
            colaborador_id:  UUID do colaborador (id concreto, não hash).
            na_data:         date ou datetime para verificação de vigência.

        Returns:
            True se opt-in vigente; False se ausente ou revogado.
        """
        ...


@runtime_checkable
class ColaboradorCaixaPort(Protocol):
    """Port para verificar papel de técnico do colaborador (D-CT-2).

    Acoplamento de leitura — molde ``ColaboradorAgendaAdapter``.
    Não estende módulo ``colaboradores`` fechado.

    Implementação real: ``ColaboradorCaixaAdapter`` (Fatia 3a — T-CT-041).
    """

    def e_tecnico(self, tenant_id: UUID, colaborador_id: UUID) -> bool:
        """Verifica se o colaborador tem papel ``TECNICO`` no tenant.

        Args:
            tenant_id:      UUID do tenant.
            colaborador_id: UUID do colaborador.

        Returns:
            True se o colaborador é técnico no tenant; False caso contrário.
        """
        ...


@runtime_checkable
class ColaboradorReferenciadoPort(Protocol):
    """Port para guard de referência do colaborador no caixa_tecnico (D-CT-12 / INV-CT-REF-001).

    Molde ``D-AGE-12`` (agenda usa padrão idêntico). Técnico com caixa aberto,
    despesas pendentes/validadas ou adiantamentos ativos NÃO é hard-deletado.

    Implementação real: ``ColaboradorCaixaAdapter`` (mesmo adapter — Fatia 3a).
    """

    def esta_referenciado(self, tenant_id: UUID, colaborador_id: UUID) -> bool:
        """Verifica se o colaborador está referenciado no caixa_tecnico.

        Verifica existência de:
          - ``CaixaTecnico`` ativo (sem ``desligado_em``).
          - ``Despesa`` com estado ``pendente`` ou ``validada``.
          - ``Adiantamento`` com estado ``solicitado``, ``aprovado`` ou ``entregue``.

        Args:
            tenant_id:      UUID do tenant.
            colaborador_id: UUID do colaborador.

        Returns:
            True se existe qualquer vínculo ativo; False se pode ser hard-deletado.
        """
        ...
