"""Repository Protocol para Calibracao — DOMINIO puro (ADR-0007).

Domain layer NAO importa django.* nem psycopg. Aqui mora apenas o
CONTRATO; a implementacao concreta (adapter Django) vai em
src/infrastructure/calibracao/repositories.py.

Use cases (src/application/metrologia/calibracao/) consomem este Protocol
e nunca conhecem Django/PG.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from .entities import CalibracaoSnapshot


@runtime_checkable
class CalibracaoRepository(Protocol):
    """Repository de Calibracao — read + write operations.

    Implementacao concreta: DjangoCalibracaoRepository
    (src/infrastructure/calibracao/repositories.py).

    Convencao:
    - Metodos `obter_*` retornam snapshot ou None (sem levantar excecao).
    - Metodos `salvar_*` inserem/atualizam via Django ORM com lock CAS
      (ADR-0065 — UPDATE ... WHERE revision = old_revision).
    - Snapshots sao imutaveis; mutacao = criar novo snapshot + chamar
      `salvar_*`.
    """

    def obter_por_id(self, calibracao_id: UUID) -> CalibracaoSnapshot | None:
        """Retorna snapshot da Calibracao se existir no tenant ativo (RLS)."""
        ...

    def proximo_numero_interno(self) -> int:
        """Reserva proximo numero da sequence global calibracao_numero_seq_global.

        Chama nextval() — consome o numero mesmo se transacao rollback
        (ADR-0056 — buracos por rollback sao aceitos por design para
        evitar serializacao single-row).
        """
        ...

    def salvar_nova(self, snapshot: CalibracaoSnapshot) -> None:
        """INSERT da Calibracao + trigger PG preenche numero_exibido.

        Levanta:
          - IntegrityError se tenant_id != app.active_tenant_id (RLS).
          - IntegrityError em violacao de UNIQUE constraint.
        """
        ...

    def atualizar_com_lock(
        self, snapshot: CalibracaoSnapshot, revision_anterior: int
    ) -> bool:
        """UPDATE com lock CAS (ADR-0065 — INV-CAL-CONC-001).

        UPDATE ... SET revision = revision + 1, ... WHERE id = %s
        AND revision = revision_anterior

        Retorna:
          True  - update aplicou (linhas afetadas == 1).
          False - update perdeu race (linhas afetadas == 0).

        Caller decide:
          - retry com obter_por_id + recomputar (default optimistic).
          - falhar com 409 Conflict (em endpoints POST sem idempotencia).
        """
        ...
