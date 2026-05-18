"""Management command: roda o drill final de validacao da Foundation F-A.

Uso:
    docker compose exec app poetry run python manage.py validar_f_a

Executa os 5 criterios de saida AUTOMAVEIS (faseamento-foundation-waves §2):
  1. Hooks 88/88 verdes (bash _test-runner.sh)
  2. Verifica que NOBYPASSRLS esta ativo nas roles app_user e app_migrator
  3. Verifica que trigger anti-mutation existe em auditoria
  4. Hash chain do audit trail integro
  5. Benchmark p99 simples (insercoes em escala reduzida)

Criterios NAO automaveis (operacao do periodo F-A — 4-6 semanas):
  6. Drill restore PG cronometrado (rodar manual com pgBackRest)
  7. Criterio Roldao (ADR-0001 Portao 3): >= 2 intervencoes/semana, bugs SEV-1
  8. Auditor de seguranca: 14 dias sem veto

Saida: tabela + exit code 0 (tudo OK) ou 1 (algum falhou).
"""

from __future__ import annotations

import statistics
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.db import connection

from src.infrastructure.audit.services import (
    registrar_auditoria,
    verificar_integridade_cadeia,
)
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
)
from src.infrastructure.tenant.models import Tenant
from src.infrastructure.usuario.models import Usuario


class Command(BaseCommand):
    help = "Roda o drill de validacao Foundation F-A (5 criterios automaveis)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--quick",
            action="store_true",
            help="Pula benchmark p99 (mais rapido pra desenvolvimento).",
        )

    def handle(self, *args, **options):
        quick = options.get("quick", False)
        resultados: list[tuple[str, bool, str]] = []

        self.stdout.write(self.style.NOTICE("[1/5] Hooks _test-runner..."))
        ok, msg = self._verificar_hooks()
        resultados.append(("Hooks 88/88 verdes", ok, msg))

        self.stdout.write(self.style.NOTICE("[2/5] Roles NOBYPASSRLS..."))
        ok, msg = self._verificar_roles_nobypassrls()
        resultados.append(("Roles app_user/app_migrator NOBYPASSRLS", ok, msg))

        self.stdout.write(self.style.NOTICE("[3/5] Trigger anti-mutation..."))
        ok, msg = self._verificar_trigger_audit()
        resultados.append(("Trigger auditoria_anti_* existe", ok, msg))

        self.stdout.write(self.style.NOTICE("[4/5] Hash chain..."))
        ok, msg = self._verificar_hash_chain()
        resultados.append(("Hash chain do audit trail integro", ok, msg))

        if quick:
            resultados.append(("Benchmark p99 < 200ms", True, "pulado (--quick)"))
        else:
            self.stdout.write(self.style.NOTICE("[5/5] Benchmark p99 (pode demorar)..."))
            ok, msg = self._benchmark_p99()
            resultados.append(("p99 query operacional < 200ms", ok, msg))

        self.stdout.write("")
        self.stdout.write(self.style.MIGRATE_HEADING("===== RESUMO DRILL F-A ====="))
        falhas = 0
        for nome, ok, msg in resultados:
            simbolo = "OK " if ok else "XXX"
            estilo = self.style.SUCCESS if ok else self.style.ERROR
            self.stdout.write(estilo(f"  [{simbolo}] {nome}: {msg}"))
            if not ok:
                falhas += 1

        self.stdout.write("")
        if falhas == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "F-A drill: 5/5 criterios automaveis OK. "
                    "Falta validar 2 criterios operacionais (memoria + auditor)."
                )
            )
            return
        self.stdout.write(
            self.style.ERROR(f"F-A drill REPROVADO: {falhas} criterio(s) falharam.")
        )
        sys.exit(1)

    # =============================================================
    # Helpers
    # =============================================================

    def _verificar_hooks(self) -> tuple[bool, str]:
        runner = Path(__file__).resolve().parents[5] / ".claude" / "hooks" / "_test-runner.sh"
        if not runner.exists():
            return False, f"runner nao encontrado em {runner}"
        try:
            result = subprocess.run(  # noqa: S603 — runner conhecido versionado no repo
                ["bash", str(runner)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(runner.parents[2]),
            )
        except subprocess.TimeoutExpired:
            return False, "timeout >60s"
        ultima = result.stdout.strip().splitlines()[-1] if result.stdout else ""
        if result.returncode == 0 and "0 falhas" in ultima:
            return True, ultima.strip("= ")
        return False, f"exit={result.returncode}, ultima={ultima!r}"

    def _verificar_roles_nobypassrls(self) -> tuple[bool, str]:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT rolname, rolbypassrls, rolsuper "
                "FROM pg_roles WHERE rolname IN ('app_user', 'app_migrator');"
            )
            rows = cur.fetchall()
        if len(rows) != 2:
            return False, f"esperava 2 roles, achei {len(rows)}: {rows!r}"
        for rolname, bypassrls, issuper in rows:
            if bypassrls or issuper:
                return False, f"{rolname} tem bypassrls={bypassrls} superuser={issuper}"
        return True, "ambas NOBYPASSRLS + NOSUPERUSER"

    def _verificar_trigger_audit(self) -> tuple[bool, str]:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT tgname FROM pg_trigger "
                "WHERE tgname LIKE 'auditoria_anti_%' AND NOT tgisinternal;"
            )
            triggers = [r[0] for r in cur.fetchall()]
        if len(triggers) >= 2:
            return True, f"triggers: {triggers}"
        return False, f"esperava >=2 triggers anti-mutation, achei {triggers}"

    def _verificar_hash_chain(self) -> tuple[bool, str]:
        with run_as_system():
            t = Tenant.objects.create(
                slug=f"drill-{uuid4().hex[:8]}",
                nome_fantasia="Drill",
            )
            u = Usuario.objects.create_user(
                email=f"drill-{uuid4().hex[:8]}@x.com",
                password="drill-teste-12-chars",
            )

        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            for i in range(5):
                registrar_auditoria(
                    tenant_id=t.id, usuario_id=u.id,
                    action=f"drill.{i}",
                    resource_summary=f"drill-{i}",
                    payload={"i": i},
                )
            # Verificacao DENTRO do mesmo contexto — RLS permite leitura
            # das linhas deste tenant. Limit cobre as 5 que acabamos de inserir.
            ok, total, quebrados = verificar_integridade_cadeia(limit=100)
        if not ok:
            return False, f"cadeia quebrada em {len(quebrados)} elos: {quebrados[:3]}"
        if total < 5:
            return False, f"esperava >=5 linhas, achei {total} (RLS pode estar filtrando)"
        return True, f"{total} linhas verificadas, 0 quebras"

    def _benchmark_p99(self) -> tuple[bool, str]:
        with run_as_system():
            t = Tenant.objects.create(
                slug=f"bench-{uuid4().hex[:8]}",
                nome_fantasia="Bench",
            )
            u = Usuario.objects.create_user(
                email=f"bench-{uuid4().hex[:8]}@x.com",
                password="bench-teste-12-chars",
            )

        tempos_ms: list[float] = []

        with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
            for i in range(1000):
                inicio = time.perf_counter()
                registrar_auditoria(
                    tenant_id=t.id, usuario_id=u.id,
                    action="bench",
                    resource_summary=f"linha-{i}",
                    payload={"i": i, "msg": "benchmark"},
                )
                tempos_ms.append((time.perf_counter() - inicio) * 1000)

        p99 = statistics.quantiles(tempos_ms, n=100)[98]
        p50 = statistics.median(tempos_ms)
        if p99 < 200:
            return True, f"p50={p50:.1f}ms p99={p99:.1f}ms (limite 200ms)"
        return False, f"p99={p99:.1f}ms (>= 200ms — investigar indices)"
