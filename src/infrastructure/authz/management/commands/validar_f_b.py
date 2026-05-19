"""Drill Foundation F-B — criterios de saida automaveis (faseamento §3).

Uso:
    docker compose exec app poetry run python manage.py validar_f_b
    (--quick pula cobertura; mais rapido em desenvolvimento)

Executa:
  1. Hooks `_test-runner.sh` verdes — EXIT CODE, nao substring (FB-C4)
  2. Trigger PG anti-mutation existe em authz_decisions (2 triggers)
  3. Hash chain authz ROBUSTO (FB-C4/C5): cadeia POR-TENANT + pre-tenant
     POR-USUARIO, recomputa sha256 real, injeta elo adulterado EXIGINDO
     deteccao, concorrencia, guarda anti-falso-verde (REPROVA se 0 linhas)
  4. E2E F-B (16 cenarios) — exit code
  5. INV-AUTHZ-001 na borda DRF: RequireAuthz nega sem action, libera @public
  6. MFA TOTP middleware (5 cenarios) — exit code
  7. Cobertura do modulo authz >= 80% (--cov-fail-under, exit code)

Saida: tabela + exit code 0 (tudo OK) ou 1 (algum falhou).
"""

from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.db import connection

from src.infrastructure.authz.django_provider import (
    DjangoAuthorizationProvider,
    verificar_integridade_cadeia_authz,
)
from src.infrastructure.authz.models import AuthzDecision
from src.infrastructure.multitenant.connection import (
    run_as_system,
    run_in_tenant_context,
    run_in_user_context,
)
from src.infrastructure.tenant.models import Tenant
from src.infrastructure.usuario.models import Usuario

_REPO = Path(__file__).resolve().parents[5]


class Command(BaseCommand):
    help = "Drill Foundation F-B (7 criterios automaveis)."

    def add_arguments(self, parser):  # type: ignore[no-untyped-def]
        parser.add_argument(
            "--quick",
            action="store_true",
            help="Pula o criterio de cobertura (mais rapido em dev).",
        )

    def handle(self, *args, **opts) -> None:  # type: ignore[no-untyped-def]
        quick = opts.get("quick", False)
        resultados: list[tuple[str, bool, str]] = []

        self.stdout.write(self.style.NOTICE("[1/7] Hooks _test-runner..."))
        resultados.append(("1. Hooks _test-runner.sh", *self._checar_hooks()))

        self.stdout.write(self.style.NOTICE("[2/7] Trigger anti-mutation..."))
        resultados.append(("2. Trigger anti-mutation authz_decisions", *self._checar_trigger()))

        self.stdout.write(self.style.NOTICE("[3/7] Hash chain authz (robusto)..."))
        resultados.append(("3. Hash chain authz robusto", *self._checar_hash_chain()))

        self.stdout.write(self.style.NOTICE("[4/7] E2E 16 cenarios..."))
        resultados.append(("4. E2E 16 cenarios", *self._pytest("tests/test_authz_e2e.py")))

        self.stdout.write(self.style.NOTICE("[5/7] RequireAuthz na borda DRF..."))
        resultados.append(
            ("5. RequireAuthz DRF", *self._pytest("tests/test_authz_require_authz.py"))
        )

        self.stdout.write(self.style.NOTICE("[6/7] MFA middleware..."))
        resultados.append(
            ("6. MFA middleware (5 cenarios)", *self._pytest("tests/test_authz_mfa.py"))
        )

        if quick:
            resultados.append(("7. Cobertura authz >= 80%", True, "pulado (--quick)"))
        else:
            self.stdout.write(self.style.NOTICE("[7/7] Cobertura authz..."))
            resultados.append(("7. Cobertura authz >= 80%", *self._checar_cobertura()))

        self._imprimir_tabela(resultados)
        falhas = [r for r in resultados if not r[1]]
        if falhas:
            self.stderr.write(self.style.ERROR(f"\n{len(falhas)} criterio(s) FALHARAM"))
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS("\nDrill F-B 7/7 VERDE."))

    # =============================================================
    # Criterios
    # =============================================================

    def _checar_hooks(self) -> tuple[bool, str]:
        runner = _REPO / ".claude" / "hooks" / "_test-runner.sh"
        if not runner.exists():
            return False, f"runner nao encontrado em {runner}"
        try:
            proc = subprocess.run(
                ["bash", str(runner)],  # noqa: S603,S607 -- runner versionado, sem input externo
                cwd=str(_REPO),
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.TimeoutExpired:
            return False, "timeout >120s"
        ultima = proc.stdout.strip().splitlines()[-1] if proc.stdout else ""
        # FB-C4: EXIT CODE manda — substring "0 falhas" sozinha mascarava.
        if proc.returncode == 0 and "0 falhas" in ultima:
            return True, ultima.strip("= ")
        return False, f"exit={proc.returncode}, ultima={ultima!r}"

    def _checar_trigger(self) -> tuple[bool, str]:
        with connection.cursor() as cur:
            cur.execute(
                "SELECT count(*) FROM pg_trigger "
                "WHERE tgname LIKE 'authz_decisions_anti_%' AND NOT tgisinternal;"
            )
            n = cur.fetchone()[0]
        return (n == 2, f"{n} triggers (esperado 2)")

    def _checar_hash_chain(self) -> tuple[bool, str]:
        """FB-C4/C5: prova criptografica REAL — NAO mais global/timestamp/feliz.

        (a) cadeia POR-TENANT integra (recomputa sha256 via
            verificar_integridade_cadeia_authz);
        (b) cadeia PRE-TENANT POR-USUARIO integra + isolada entre usuarios;
        (c) injecao de elo adulterado EXIGE deteccao (REPROVA se passar
            limpo — era exatamente o falso-verde FB-C4);
        (d) concorrencia no mesmo tenant -> cadeia final integra;
        (e) guarda anti-falso-verde: REPROVA se a cadeia ficou vazia.
        """
        provider = DjangoAuthorizationProvider()
        with run_as_system():
            tenants = [
                Tenant.objects.create(
                    slug=f"fbdrill-{i}-{uuid4().hex[:8]}", nome_fantasia=f"FBDrill{i}"
                )
                for i in range(3)
            ]
            ua = Usuario.objects.create_user(
                email=f"fbdrill-a-{uuid4().hex[:8]}@x.com",
                password="fbdrill-teste-12c",  # noqa: S106 -- usuario descartavel de drill
            )
            ub = Usuario.objects.create_user(
                email=f"fbdrill-b-{uuid4().hex[:8]}@x.com",
                password="fbdrill-teste-12c",  # noqa: S106 -- usuario descartavel de drill
            )

        # (a) decisoes POR-TENANT intercaladas (4 rodadas/tenant)
        for rodada in range(4):
            for t in tenants:
                with run_in_tenant_context(tenant_id=t.id, usuario_id=ua.id):
                    provider.can(
                        usuario_id=ua.id,
                        action=f"drill.r{rodada}",
                        tenant_id=t.id,
                    )
        for t in tenants:
            with run_in_tenant_context(tenant_id=t.id, usuario_id=ua.id):
                ok, total, quebrados = verificar_integridade_cadeia_authz({"tenant_id": t.id})
            if total == 0:  # (e) guarda anti-falso-verde
                return False, f"tenant {t.slug}: 0 linhas — drill vazio mente (FB-C4)"
            if not ok:
                return False, f"tenant {t.slug}: cadeia quebrada {quebrados[:3]}"
            if total < 4:
                return False, f"tenant {t.slug}: {total} elos (<4 — RLS filtrou?)"

        # (b) cadeia PRE-TENANT POR-USUARIO + isolamento entre usuarios
        for _ in range(3):
            with run_in_user_context(ua.id):
                provider.can(usuario_id=ua.id, action="tenant.listar", tenant_id=None)
        with run_in_user_context(ub.id):
            provider.can(usuario_id=ub.id, action="tenant.listar", tenant_id=None)
        with run_in_user_context(ua.id):
            ok_a, tot_a, q_a = verificar_integridade_cadeia_authz(
                {"tenant_id__isnull": True, "usuario_id": ua.id}
            )
        if not ok_a or tot_a < 3:
            return False, f"cadeia pre-tenant usuario A quebrada/curta: {tot_a} {q_a[:3]}"

        # (c) ADULTERACAO: elo mentiroso no tenant[0] -> DEVE acusar.
        alvo = tenants[0]
        with run_in_tenant_context(tenant_id=alvo.id, usuario_id=ua.id):
            AuthzDecision.objects.create(
                usuario_id=ua.id,
                tenant_id=alvo.id,
                action="drill.poison",
                resource_summary={"x": 1},
                purpose="execucao_contrato",
                decision="allowed",
                reason="poison",
                perfis_aplicados=[],
                escopo_avaliado={},
                hash_anterior="0" * 64,
                hash_atual="f" * 64,
            )
            ok_pos, _, q_pos = verificar_integridade_cadeia_authz({"tenant_id": alvo.id})
        if ok_pos or not q_pos:
            return False, (
                "FALHA CRITICA: elo adulterado NAO detectado — o drill daria "
                "F-B verde MENTINDO (FB-C4/C5)"
            )
        with run_in_tenant_context(tenant_id=tenants[1].id, usuario_id=ua.id):
            ok_b, _, _ = verificar_integridade_cadeia_authz({"tenant_id": tenants[1].id})
        if not ok_b:
            return False, "deteccao vazou: tenant integro acusado junto"

        # (d) CONCORRENCIA: 40 threads no tenant[2] sob advisory lock por-cadeia
        conc = tenants[2]
        erros: list[str] = []

        def _inserir(n: int) -> None:
            try:
                with run_in_tenant_context(tenant_id=conc.id, usuario_id=ua.id):
                    provider.can(usuario_id=ua.id, action=f"conc.{n}", tenant_id=conc.id)
            except Exception as e:  # drill agrega p/ reportar
                erros.append(f"{type(e).__name__}:{e}")

        threads = [threading.Thread(target=_inserir, args=(n,)) for n in range(40)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        if erros:
            return False, f"concorrencia: {len(erros)} erros, ex: {erros[0]}"
        with run_in_tenant_context(tenant_id=conc.id, usuario_id=ua.id):
            ok_c, tot_c, q_c = verificar_integridade_cadeia_authz({"tenant_id": conc.id})
        if not ok_c:
            return False, f"concorrencia quebrou cadeia: {q_c[:3]} (advisory lock?)"
        return True, (
            f"3 tenants intercalados OK; pre-tenant A={tot_a} elos; adulteracao "
            f"detectada ({len(q_pos)} elos); 40 inserts concorrentes -> {tot_c} integros"
        )

    def _pytest(self, alvo: str) -> tuple[bool, str]:
        proc = subprocess.run(
            ["poetry", "run", "pytest", alvo, "--no-cov", "-q"],  # noqa: S603,S607
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        ultima = proc.stdout.strip().splitlines()[-1] if proc.stdout else "(sem saida)"
        return (proc.returncode == 0, ultima)

    def _checar_cobertura(self) -> tuple[bool, str]:
        """FB-C5: gate de cobertura DO MODULO authz (exit code do pytest)."""
        proc = subprocess.run(
            [  # noqa: S603,S607
                "poetry",
                "run",
                "pytest",
                "tests/test_authz_e2e.py",
                "tests/test_authz_audit_imutavel.py",
                "tests/test_authz_cadeia_pre_tenant.py",
                "tests/test_authz_require_authz.py",
                "tests/test_authz_isolamento.py",
                "tests/test_authz_mfa.py",
                "--cov=src/infrastructure/authz",
                "--cov-report=",
                "--cov-fail-under=80",
                "-q",
            ],
            cwd=str(_REPO),
            capture_output=True,
            text=True,
        )
        linhas = proc.stdout.strip().splitlines()
        ultima = linhas[-1] if linhas else "(sem saida)"
        return (proc.returncode == 0, ultima)

    def _imprimir_tabela(self, resultados: list[tuple[str, bool, str]]) -> None:
        self.stdout.write("")
        self.stdout.write("=" * 80)
        self.stdout.write("DRILL FOUNDATION F-B — CRITERIOS AUTOMAVEIS")
        self.stdout.write("=" * 80)
        for label, ok, detalhe in resultados:
            mark = self.style.SUCCESS("[OK]") if ok else self.style.ERROR("[FAIL]")
            self.stdout.write(f"  {mark}  {label:<42} {detalhe}")
        self.stdout.write("=" * 80)
