"""Adapter `ColaboradorReferenciadoPort` para a frente `agenda` (T-AGE-045).

Responde: "este colaborador tem evento de agenda FUTURO não-cancelado?"

Implementa o contrato `ColaboradorReferenciadoPort` (domain/rh_frota_qualidade/
colaboradores/portas.py) usando `DjangoEventoAgendaRepository.tem_agenda_futura`
(já existente — D-AGE-12 / plan §5 Fatia 3c).

Estado HONESTO (Wave A): o adapter está PRONTO e correto, mas a proteção
  end-to-end AINDA NÃO está ativa. O `destroy` de `colaboradores` hoje é
  DESLIGAMENTO lógico (revoga papéis + publica `colaborador.desligado`), NÃO
  hard-delete físico, e NÃO consulta nenhum `ColaboradorReferenciadoPort`
  (verificado: zero referências a `esta_referenciado`/atributo de port no fluxo de
  colaboradores). DELETE físico direto não é exposto via API; o schema ainda tem
  `0003_trigger_defensivo` como salvaguarda no banco.

Mecanismo de registro:
  `AgendaConfig.ready()` registra esta instância no atributo de classe
  `ColaboradorViewSet._referenciado_agenda_port` (R11 — toca colaboradores SÓ no
  wiring), via try/except (nunca quebra o boot). É um registro fail-open lazy
  (ADR-0066) PRONTO para quando colaboradores implementar hard-delete físico que
  CONSULTE os ReferenciadoPort registrados — o que ainda não acontece.

  **Débito: GATE-AGE-COLABORADOR-REFERENCIADO** — conectar o fluxo de hard-delete
  de colaboradores à consulta dos ReferenciadoPort. HOJE o atributo registrado NÃO
  é lido por nenhum fluxo (adapter pronto, consumo pendente). O teste exercita o
  adapter diretamente (responde corretamente "tem agenda futura?").

Referências: D-AGE-12, plan §5 Fatia 3c, ADR-0066, INV-COL-INATIVO, GATE-AGE-COLABORADOR-REFERENCIADO.
"""

from __future__ import annotations

import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class AgendaColaboradorReferenciadoAdapter:
    """Implementação concreta de ColaboradorReferenciadoPort para a frente agenda.

    Pergunta: o colaborador tem EventoAgenda FUTURO não-cancelado?
    Se sim, bloqueia hard-delete físico (INV-COL-INATIVO / D-AGE-12 / ADR-0066).

    Reutiliza `DjangoEventoAgendaRepository.tem_agenda_futura` — a query já
    existe no repositório da agenda (inicia_at > now() + estado != 'cancelado').
    """

    def esta_referenciado(self, colaborador_id: UUID, tenant_id: UUID) -> bool:
        """True se o técnico tem agenda futura não-cancelada (bloqueia hard-delete).

        Args:
            colaborador_id: UUID do colaborador (usado como tecnico_id na agenda).
            tenant_id:      UUID do tenant (isolamento multi-tenant ADR-0002).

        Returns:
            True  → colaborador referenciado; hard-delete bloqueado.
            False → sem agenda futura; hard-delete pode prosseguir (se não há
                    outra referência em outros módulos).
        """
        from src.infrastructure.agenda.repositories import DjangoEventoAgendaRepository

        repo = DjangoEventoAgendaRepository()
        return repo.tem_agenda_futura(tenant_id=tenant_id, colaborador_id=colaborador_id)
