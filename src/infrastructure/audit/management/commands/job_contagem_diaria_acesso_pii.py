"""T-CLI-105 / INV-013-A — job daily de contagem imutável de
`AcessoDadosCliente` por tenant.

AC-CLI-002-7 (corretora-seguros-saas §A P-CLI-S1): ancora barata anti-
supressão de log de acesso a PII. Sem hash chain dedicada (decisão F-A
AC-FA-005-7), a defesa é estatística — se a contagem diária cai
abruptamente, alguém suprimiu linhas.

Mecânica:
- Roda diariamente (cron Celery ou systemd timer) por volta de 02:00 BRT.
- Itera os tenants ativos.
- Para cada tenant, conta `AcessoDadosCliente` da janela `[D-1 00:00 UTC,
  D 00:00 UTC)`.
- Grava um evento `acessos_pii.contagem_diaria` na cadeia sistema (F-A
  `registrar_auditoria(tenant_id=None)`) com payload `{tenant_id,
  data_referencia, qtd}`. A cadeia sistema é INSERT-only (trigger PG +
  trigger anti-mutation) — qualquer adulteração quebra `hash_atual` e é
  detectada por `verificar_integridade_cadeia`.

Quando GATE-1 (B2 WORM) estiver ativo, o consumer da cadeia sistema
replica essas contagens para o destino imutável — anel de proteção dupla.

Idempotência: se chamado 2× no mesmo dia, gera 2 eventos. Operação humana
deve usar `--data-referencia=YYYY-MM-DD` pra re-execução intencional;
sem flag, usa ontem (D-1) — replays acidentais com cron == mesmo dia
geram duplicata detectável (alerta em métrica downstream Wave A).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from django.core.management.base import BaseCommand, CommandError

from src.infrastructure.audit.services import registrar_auditoria
from src.infrastructure.clientes.models import Cliente  # noqa: F401 -- placeholder p/ ratificar app
from src.infrastructure.multitenant.connection import run_as_system, run_in_tenant_context


class Command(BaseCommand):
    help = (
        "T-CLI-105 / INV-013-A: contagem diaria de AcessoDadosCliente "
        "por tenant gravada na cadeia sistema (ancora anti-supressao)."
    )

    def add_arguments(self, parser) -> None:  # type: ignore[no-untyped-def]  # BaseCommand assina argparse.ArgumentParser; assinatura herdada
        parser.add_argument(
            "--data-referencia",
            type=str,
            default=None,
            help=(
                "Data a contar (formato YYYY-MM-DD). Default: ontem (D-1). "
                "Use pra re-executar manualmente um dia específico."
            ),
        )

    def handle(self, *args, **options) -> None:  # type: ignore[no-untyped-def]  # BaseCommand permite **Any; relaxar pra herdar tipos do framework
        from src.infrastructure.audit.models import AcessoDadosCliente
        from src.infrastructure.tenant.models import StatusLifecycle, Tenant

        data_ref = self._resolver_data_referencia(options.get("data_referencia"))
        inicio = datetime.combine(data_ref, time.min, tzinfo=UTC)
        fim = inicio + timedelta(days=1)

        self.stdout.write(
            self.style.NOTICE(f"[INV-013-A] Janela: [{inicio.isoformat()}, {fim.isoformat()})")
        )

        # `tenants` é tabela de plano-de-controle sem RLS (premissa §2.3.1
        # de isolamento-multi-tenant.md); leitura fora de contexto é OK.
        with run_as_system():
            ids_tenants_ativos = list(
                Tenant.objects.filter(status_lifecycle=StatusLifecycle.ATIVO).values_list(
                    "id", flat=True
                )
            )

        total = 0
        for tid in ids_tenants_ativos:
            with run_in_tenant_context(tenant_id=tid):
                qtd = AcessoDadosCliente.objects.filter(
                    timestamp__gte=inicio, timestamp__lt=fim
                ).count()
            # Grava na cadeia SISTEMA (não na do tenant): operação de plano-de-
            # controle. Sob modo_sistema='1' o registrar_auditoria não exige
            # contexto de tenant.
            with run_as_system():
                registrar_auditoria(
                    tenant_id=None,
                    usuario_id=None,
                    action="acessos_pii.contagem_diaria",
                    resource_summary=f"tenant={tid} data={data_ref.isoformat()}",
                    payload={
                        "tenant_id": str(tid),
                        "data_referencia": data_ref.isoformat(),
                        "qtd": qtd,
                    },
                )
            total += qtd
            self.stdout.write(f"  tenant={tid}  qtd={qtd}")

        self.stdout.write(
            self.style.SUCCESS(
                f"[INV-013-A] Total {total} acessos em {len(ids_tenants_ativos)} tenants "
                f"para {data_ref.isoformat()}."
            )
        )

    def _resolver_data_referencia(self, raw: str | None) -> date:
        if raw is None:
            return (datetime.now(UTC) - timedelta(days=1)).date()
        try:
            return date.fromisoformat(raw)
        except ValueError as e:
            raise CommandError(f"--data-referencia inválida: {raw} (use YYYY-MM-DD)") from e
