"""T-CAL-122 — Management command wrapper dos 9 jobs M4 P4 Fase 7.

Uso:
    python manage.py processar_jobs_calibracao [--tenant <uuid>] [--job <nome>]

Jobs registrados:
  alertar_reclamacao_vencendo            (T-CAL-116 / AC-CAL-018-3)
  pseudonimizar_responsavel_nc           (T-CAL-117 / P-CAL-A2)
  analisar_uso_excecao_2a_conferencia    (T-CAL-121 / AC-CAL-008-5)
  verificar_avaliacoes_subcontratados_vencendo (T-CAL-115 / P-CAL-R5)
  analisar_padrao_medicoes_controle      (T-CAL-118 / P-CAL-R8)
  analisar_correlacao_componentes        (T-CAL-119 / INV-CAL-INC-004)
  geo_truncamento_calibracao_5a          (T-CAL-120 / P-CAL-A8)

Nao-implementados aqui (Wave A — exigem infra externa):
  executar_backup_metrologico            (T-CAL-114) — exige B2 + KMS reais.

Sem --job: roda todos.

Padrao Wave A:
  - Carregamento de snapshots via Django ORM (Calibracao, NaoConformidade,
    ReclamacaoCalibracao, AvaliacaoPeriodicaSubcontratado, MedicaoControle).
  - Chamada da funcao pura (src/application/.../jobs/).
  - Processamento das acoes retornadas: emite UPDATE / publica evento /
    log stub P3 quando consumer real ainda nao existir.

Este management command opera em modo STUB-WAVE-A: invoca os jobs com
listas vazias e emite log informativo. Adapters Django reais (Calibracao
existe; NaoConformidade/Reclamacao/Avaliacao/MedicaoControle ainda nao)
serao plugados em fases subsequentes (Fase 8 REST + adapters).
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


def _stub_alertar_reclamacao_vencendo(tenant_id: UUID, agora: datetime) -> dict[str, int]:
    """STUB Wave A — quando DjangoReclamacaoCalibracaoRepository existir,
    carrega `ReclamacaoCalibracao.objects.filter(tenant_id=t, estado__in=[RECEBIDA, EM_ANALISE])`
    + chama `alertar_reclamacao_vencendo.executar(reclamacoes_abertas=qs, agora=agora)`.
    Por enquanto retorna metrica vazia."""
    from src.application.metrologia.calibracao.jobs.alertar_reclamacao_vencendo import (
        executar,
    )

    alertas = executar(reclamacoes_abertas=[], agora=agora)
    logger.info(
        "processar_jobs_calibracao: alertar_reclamacao_vencendo tenant=%s "
        "alertas=%d (STUB Wave A)",
        tenant_id,
        len(alertas),
    )
    return {"alertas_emitidos": len(alertas)}


def _stub_pseudonimizar_responsavel_nc(
    tenant_id: UUID, agora: datetime
) -> dict[str, int]:
    from src.application.metrologia.calibracao.jobs.pseudonimizar_responsavel_nc import (
        executar,
    )

    acoes = executar(ncs_com_responsavel=[], agora=agora)
    logger.info(
        "processar_jobs_calibracao: pseudonimizar_responsavel_nc tenant=%s "
        "acoes=%d (STUB Wave A)",
        tenant_id,
        len(acoes),
    )
    return {"pseudonimizacoes": len(acoes)}


def _stub_analisar_uso_excecao_2a_conferencia(
    tenant_id: UUID, agora: datetime
) -> dict[str, str]:
    from src.application.metrologia.calibracao.jobs.analisar_uso_excecao_2a_conferencia import (
        executar,
    )

    analise = executar(
        tenant_id=tenant_id,
        calibracoes_aprovadas_janela=[],
        agora=agora,
    )
    logger.info(
        "processar_jobs_calibracao: analisar_uso_excecao_2a_conferencia "
        "tenant=%s severidade=%s percentual=%s (STUB Wave A)",
        tenant_id,
        analise.severidade,
        analise.percentual,
    )
    return {"severidade": analise.severidade}


def _stub_verificar_avaliacoes_subcontratados_vencendo(
    tenant_id: UUID, agora: datetime
) -> dict[str, int]:
    from src.application.metrologia.calibracao.jobs.verificar_avaliacoes_subcontratados_vencendo import (
        executar,
    )

    alertas = executar(ultimas_avaliacoes=[], agora=agora)
    logger.info(
        "processar_jobs_calibracao: verificar_avaliacoes_subcontratados_vencendo "
        "tenant=%s alertas=%d (STUB Wave A)",
        tenant_id,
        len(alertas),
    )
    return {"alertas_emitidos": len(alertas)}


def _stub_analisar_padrao_medicoes_controle(
    tenant_id: UUID, agora: datetime
) -> dict[str, int]:
    """Trigger por evento. No management command, opera em modo varredura
    (revalida ultimas 30 medicoes de cada padrao) — Wave A consumer real
    eh procrastinate listener de MedicaoControle.Inserida."""
    logger.info(
        "processar_jobs_calibracao: analisar_padrao_medicoes_controle "
        "tenant=%s (STUB Wave A - trigger por evento)",
        tenant_id,
    )
    return {"medicoes_analisadas": 0}


def _stub_analisar_correlacao_componentes(
    tenant_id: UUID, agora: datetime
) -> dict[str, int]:
    """Trigger por evento OrcamentoIncerteza.ComponenteInserido."""
    logger.info(
        "processar_jobs_calibracao: analisar_correlacao_componentes "
        "tenant=%s (STUB Wave A - trigger por evento)",
        tenant_id,
    )
    return {"alertas_emitidos": 0}


def _stub_geo_truncamento_calibracao_5a(
    tenant_id: UUID, agora: datetime
) -> dict[str, int]:
    from src.application.metrologia.calibracao.jobs.geo_truncamento_calibracao_5a import (
        executar,
    )

    acoes = executar(calibracoes_aprovadas=[], agora=agora)
    logger.info(
        "processar_jobs_calibracao: geo_truncamento_calibracao_5a "
        "tenant=%s acoes=%d (STUB Wave A)",
        tenant_id,
        len(acoes),
    )
    return {"truncamentos_geo": len(acoes)}


JOBS: dict[str, Callable[..., Any]] = {
    "alertar_reclamacao_vencendo": _stub_alertar_reclamacao_vencendo,
    "pseudonimizar_responsavel_nc": _stub_pseudonimizar_responsavel_nc,
    "analisar_uso_excecao_2a_conferencia": _stub_analisar_uso_excecao_2a_conferencia,
    "verificar_avaliacoes_subcontratados_vencendo": (
        _stub_verificar_avaliacoes_subcontratados_vencendo
    ),
    "analisar_padrao_medicoes_controle": _stub_analisar_padrao_medicoes_controle,
    "analisar_correlacao_componentes": _stub_analisar_correlacao_componentes,
    "geo_truncamento_calibracao_5a": _stub_geo_truncamento_calibracao_5a,
}


class Command(BaseCommand):
    help = "Roda jobs periodicos M4 P4 Fase 7 (T-CAL-115..121) por tenant."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--tenant",
            type=str,
            help="Processa apenas o tenant_id especificado (UUID).",
        )
        parser.add_argument(
            "--job",
            type=str,
            choices=list(JOBS.keys()),
            help="Executa apenas o job nomeado (default: todos).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        from src.infrastructure.tenant.models import Tenant

        tenant_filter = options.get("tenant")
        job_filter = options.get("job")

        if tenant_filter:
            try:
                tenant_uuid = UUID(tenant_filter)
            except (ValueError, TypeError) as exc:
                raise CommandError(f"--tenant invalido: {exc}") from exc
            tenants = Tenant.objects.filter(id=tenant_uuid)
            if not tenants.exists():
                raise CommandError(f"Tenant {tenant_uuid} nao encontrado.")
        else:
            tenants = Tenant.objects.all()

        jobs_a_rodar = [job_filter] if job_filter else list(JOBS.keys())
        agora = datetime.now(UTC)

        for tenant in tenants:
            for nome in jobs_a_rodar:
                fn = JOBS[nome]
                try:
                    resultado = fn(tenant.id, agora)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  OK  {nome} tenant={tenant.id} -> {resultado}"
                        )
                    )
                except Exception as exc:  # — wrapper top-level
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ERR {nome} tenant={tenant.id} -> {exc}"
                        )
                    )
                    logger.exception(
                        "processar_jobs_calibracao falhou em %s tenant=%s",
                        nome,
                        tenant.id,
                    )
