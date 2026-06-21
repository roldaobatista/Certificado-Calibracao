"""Adapter real do ``ConsentimentoGpsPort`` (Fatia 3a — T-CT-041).

Lê ``ConsentimentoGpsColaborador`` (entidade NO PRÓPRIO ``caixa_tecnico`` — D-CT-6)
via ``ConsentimentoRepository.opt_in_vigente``. Verificação **server-side** do opt-in:
NUNCA do payload nem do EXIF (INV-LGPD-CONSENT-001). Base legal art. 7º IX + V
(ADV-CT-05/06) — não é consentimento do art. 8º.

Resolve ``colaborador_id → colaborador_referencia_hash`` (só o hexdigest) via
``hashear_pii_com_salt_tenant`` — mesmo padrão de gravação do consentimento pelo RH.

IA NUNCA grava opt-in — este adapter apenas LÊ (ADV-CT-06).

**Débito GATE-CT-HASH-ROTACAO-LOOKUP** (sistêmico, não específico da Fatia 3a — mesmo
padrão do ``agenda/adapters.py`` e ``contas_receber``): o lookup resolve o hash do
colaborador com a chave HMAC **ativa**. Após a rotação anual (ADR-0064) consentimentos
gravados sob a chave antiga deixariam de casar. Aceitável em Wave A (chave fixa ``v1``,
write e read usam a mesma chave ativa); a correção transversal (consultar por
``colaborador_key_id`` versionado ou re-hash multi-chave) entra quando a rotação real
existir. Mitigado também porque o opt-in é só aviso (coordenada é sempre None em Wave A).

Refs: T-CT-041; D-CT-6; ADV-CT-05/06; INV-LGPD-CONSENT-001; ADR-0064; GATE-CT-HASH-ROTACAO-LOOKUP.
"""

from __future__ import annotations

from datetime import date, datetime, time
from uuid import UUID

from django.utils import timezone

from src.infrastructure.audit.services import hashear_pii_com_salt_tenant
from src.infrastructure.caixa_tecnico.repositories import ConsentimentoRepository


class ConsentimentoGpsAdapter:
    """Implementação real de ``ConsentimentoGpsPort`` sobre ``ConsentimentoRepository``."""

    def __init__(self, repo: ConsentimentoRepository | None = None) -> None:
        self._repo = repo if repo is not None else ConsentimentoRepository()

    def opt_in_vigente(
        self,
        tenant_id: UUID,
        colaborador_id: UUID,
        na_data: date | datetime,
    ) -> bool:
        """True se há opt-in GPS vigente na data (``vigencia_inicio ≤ na_data`` + sem revogação).

        NULL / sem registro → False (coleta GPS off; despesa segue sem coordenada — D-CT-6).

        ``na_data`` é normalizado para ``datetime`` timezone-aware antes do filtro contra a
        coluna ``DateTimeField`` ``vigencia_inicio`` — um ``date`` puro (caminho real do
        ``LancarDespesaUseCase``, que passa a data da despesa) vira o FIM do dia (opt-in
        iniciado em qualquer hora do dia conta como vigente nesse dia), evitando comparação
        ingênua/ambígua de timezone.
        """
        momento = self._para_datetime_aware(na_data)
        colaborador_hash = hashear_pii_com_salt_tenant(str(colaborador_id), tenant_id).split(
            ":", 1
        )[1]
        return self._repo.opt_in_vigente(
            tenant_id=tenant_id,
            colaborador_referencia_hash=colaborador_hash,
            na_data=momento,
        )

    @staticmethod
    def _para_datetime_aware(na_data: date | datetime) -> datetime:
        """Normaliza ``date``/``datetime`` (naive ou aware) para ``datetime`` aware."""
        # datetime é subclasse de date — checar datetime primeiro.
        if isinstance(na_data, datetime):
            return na_data if timezone.is_aware(na_data) else timezone.make_aware(na_data)
        return timezone.make_aware(datetime.combine(na_data, time.max))
