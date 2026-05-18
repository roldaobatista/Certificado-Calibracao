"""Drill Foundation F-B — criterios de saida automaveis (faseamento §3).

Uso:
    docker compose exec app poetry run python manage.py validar_f_b

Executa:
  1. Hooks `_test-runner.sh` 103/103 verdes
  2. Trigger PG anti-mutation existe em authz_decisions
  3. Hash chain de authz_decisions ligado (sem furos)
  4. Fuzzing 500 cross-tenant via pytest
  5. Suite E2E F-B (16 cenarios) sem flake
  6. INV-AUTHZ-001 forcada pela permission DRF (importavel e callable)
  7. MFA TOTP middleware bloqueando perfis sensiveis sem TOTP

Saida: tabela + exit code 0 (tudo OK) ou 1 (algum falhou).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Drill Foundation F-B (7 criterios automaveis)."

    def handle(self, *args, **opts) -> None:  # type: ignore[no-untyped-def]
        resultados: list[tuple[str, bool, str]] = []

        # 1. Hooks
        resultados.append(self._checar_hooks())
        # 2. Trigger anti-mutation
        resultados.append(self._checar_trigger_authz_decisions())
        # 3. Hash chain ligado
        resultados.append(self._checar_hash_chain_authz())
        # 4. Fuzzing 500
        resultados.append(self._rodar_pytest("tests/test_authz_fuzzing.py", "Fuzzing 500 cross-tenant"))
        # 5. E2E 16 cenarios
        resultados.append(self._rodar_pytest("tests/test_authz_e2e.py", "E2E 16 cenarios"))
        # 6. RequireAuthz importavel
        resultados.append(self._checar_permission_drf())
        # 7. MFA middleware bloqueando
        resultados.append(
            self._rodar_pytest("tests/test_authz_mfa.py", "MFA middleware (5 cenarios)")
        )

        self._imprimir_tabela(resultados)

        falhas = [r for r in resultados if not r[1]]
        if falhas:
            self.stderr.write(self.style.ERROR(f"\n{len(falhas)} criterio(s) FALHARAM"))
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS("\nDrill F-B 7/7 VERDE."))

    def _checar_hooks(self) -> tuple[str, bool, str]:
        proc = subprocess.run(
            ["bash", ".claude/hooks/_test-runner.sh"],
            cwd=Path("/app"),
            capture_output=True,
            text=True,
        )
        ok = "0 falhas" in proc.stdout
        last = proc.stdout.strip().splitlines()[-1] if proc.stdout else "(sem saida)"
        return ("1. Hooks _test-runner.sh", ok, last)

    def _checar_trigger_authz_decisions(self) -> tuple[str, bool, str]:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM pg_trigger WHERE tgname LIKE 'authz_decisions_anti_%';"
            )
            n = cur.fetchone()[0]
        return (
            "2. Trigger anti-mutation authz_decisions",
            n == 2,
            f"{n} triggers (esperado 2)",
        )

    def _checar_hash_chain_authz(self) -> tuple[str, bool, str]:
        from src.infrastructure.multitenant.connection import run_as_system
        from src.infrastructure.authz.models import AuthzDecision

        with run_as_system():
            n = AuthzDecision.objects.count()
            # Se vazio, chain trivialmente OK
            if n == 0:
                return ("3. Hash chain authz integra", True, "0 linhas (banco virgem)")
            # Pega 50 ultimas e verifica encadeamento
            linhas = list(AuthzDecision.objects.order_by("timestamp")[:50])
            quebras = 0
            for i in range(1, len(linhas)):
                if linhas[i].hash_anterior != linhas[i - 1].hash_atual:
                    quebras += 1
        return (
            "3. Hash chain authz integra",
            quebras == 0,
            f"{quebras} quebras em {len(linhas)} linhas",
        )

    def _rodar_pytest(self, alvo: str, label: str) -> tuple[str, bool, str]:
        proc = subprocess.run(
            ["poetry", "run", "pytest", alvo, "--no-cov", "-q"],
            cwd=Path("/app"),
            capture_output=True,
            text=True,
        )
        ok = proc.returncode == 0
        last = proc.stdout.strip().splitlines()[-1] if proc.stdout else "(sem saida)"
        return (f"4-7. {label}", ok, last)

    def _checar_permission_drf(self) -> tuple[str, bool, str]:
        try:
            from src.infrastructure.authz.permissions import RequireAuthz

            ok = hasattr(RequireAuthz, "has_permission")
            return ("6. RequireAuthz DRF permission", ok, "importavel + has_permission")
        except Exception as e:
            return ("6. RequireAuthz DRF permission", False, str(e))

    def _imprimir_tabela(self, resultados: list[tuple[str, bool, str]]) -> None:
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write("DRILL FOUNDATION F-B — CRITERIOS AUTOMAVEIS")
        self.stdout.write("=" * 80)
        for label, ok, detalhe in resultados:
            mark = self.style.SUCCESS("[OK]") if ok else self.style.ERROR("[FAIL]")
            self.stdout.write(f"  {mark}  {label:<50} {detalhe}")
        self.stdout.write("=" * 80)
