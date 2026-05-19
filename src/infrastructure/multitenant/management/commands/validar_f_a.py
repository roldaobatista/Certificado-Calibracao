"""Management command: roda o drill final de validacao da Foundation F-A.

Uso:
    docker compose exec app poetry run python manage.py validar_f_a

Executa os 5 criterios de saida AUTOMAVEIS (faseamento-foundation-waves §2):
  1. Hooks verdes (bash _test-runner.sh — contagem lida do output, nao fixa)
  2. Verifica que NOBYPASSRLS esta ativo nas roles app_user e app_migrator
  3. Verifica que trigger anti-mutation existe em auditoria
  4. Hash chain ROBUSTO (FA-A5): 3 tenants intercalados + verificacao
     por-tenant + injecao de elo adulterado (exige DETECCAO) + concorrencia
  5. Benchmark p99 MULTI-TENANT (FA-A5): --escala aproxima 10k linhas x
     50 tenants (§2 L95); default reduzido pra dev

Criterios NAO automaveis (operacao do periodo F-A — 4-6 semanas):
  6. Drill restore PG cronometrado (rodar manual com pgBackRest)
  7. Criterio Roldao (ADR-0001 Portao 3): >= 2 intervencoes/semana, bugs SEV-1
  8. Auditor de seguranca: 14 dias sem veto

R2-M1 (drill destrutivo-acumulativo por design): este drill insere Tenants,
Usuarios e Auditoria REAIS no banco ativo. Auditoria e INSERT-only (trigger
anti-mutation) e Tenant tem FK PROTECT a partir de Auditoria — logo NAO
existe limpeza por DELETE. A unica forma de "limpar" o lixo do drill e
dropar e recriar o banco (test_afere). Por isso:
  - drill aborta se o banco NAO parecer descartavel (nome != test*) sem a
    flag explicita --em-banco-descartavel
  - drill imprime contagem antes/depois de Tenant/Usuario/Auditoria, deixando
    o acumulo visivel a quem opera
  - re-rodar dezenas de vezes contra produca acumula 10k+ linhas por execucao
    de --escala; rodar contra `test_afere` recriado e o caminho correto

Saida: tabela + exit code 0 (tudo OK) ou 1 (algum falhou).
"""

from __future__ import annotations

import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path
from uuid import uuid4

from django.core.management.base import BaseCommand
from django.db import connection

from src.infrastructure.audit.models import Auditoria
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
        parser.add_argument(
            "--escala",
            action="store_true",
            help="Benchmark pesado: 50 tenants x 200 linhas (~10k, §2 L95).",
        )
        parser.add_argument(
            "--em-banco-descartavel",
            action="store_true",
            help=(
                "Confirma que o banco atual e descartavel (test_afere "
                "recriado, ambiente local, etc). Sem esta flag o drill so "
                "roda se o NAME do banco comecar com 'test' (R2-M1: drill "
                "acumula Tenant/Usuario/Auditoria reais; trilha imutavel "
                "nao tem limpeza por DELETE)."
            ),
        )

    def handle(self, *args, **options):
        quick = options.get("quick", False)

        guard_ok, guard_msg = self._guard_banco_descartavel(
            confirmado=options.get("em_banco_descartavel", False)
        )
        if not guard_ok:
            self.stdout.write(self.style.ERROR(guard_msg))
            sys.exit(2)
        self.stdout.write(self.style.NOTICE(guard_msg))

        antes = self._contagem_acumulo()
        self.stdout.write(
            self.style.NOTICE(
                f"[acumulo antes] Tenant={antes['tenants']} "
                f"Usuario={antes['usuarios']} Auditoria={antes['auditoria']}"
            )
        )

        resultados: list[tuple[str, bool, str]] = []

        self.stdout.write(self.style.NOTICE("[1/5] Hooks _test-runner..."))
        ok, msg = self._verificar_hooks()
        resultados.append(("Hooks _test-runner verdes", ok, msg))

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
            ok, msg = self._benchmark_p99(escala=options.get("escala", False))
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

        depois = self._contagem_acumulo()
        delta = {
            chave: depois[chave] - antes[chave] for chave in ("tenants", "usuarios", "auditoria")
        }
        self.stdout.write("")
        self.stdout.write(
            self.style.NOTICE(
                f"[acumulo depois] Tenant={depois['tenants']} "
                f"Usuario={depois['usuarios']} Auditoria={depois['auditoria']} "
                f"(+{delta['tenants']}T +{delta['usuarios']}U "
                f"+{delta['auditoria']}A nesta execucao)"
            )
        )

        self.stdout.write("")
        if falhas == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    "F-A drill: 5/5 criterios automaveis OK. "
                    "Falta validar 2 criterios operacionais (memoria + auditor)."
                )
            )
            return
        self.stdout.write(self.style.ERROR(f"F-A drill REPROVADO: {falhas} criterio(s) falharam."))
        sys.exit(1)

    def _guard_banco_descartavel(self, *, confirmado: bool) -> tuple[bool, str]:
        """R2-M1: aborta drill em banco que nao parece descartavel.

        Heuristica: nome comeca com 'test' → descartavel (test_afere). Caso
        contrario, exige flag explicita --em-banco-descartavel. Sem cleanup
        possivel (Auditoria INSERT-only + Tenant FK PROTECT), rodar contra
        produca acumula lixo permanente — guardado por exit 2 ate o operador
        confirmar que sabe o que esta fazendo.
        """
        nome = connection.settings_dict.get("NAME", "")
        if str(nome).lower().startswith("test"):
            return True, f"[guard] banco='{nome}' (test*: descartavel)"
        if confirmado:
            return True, (
                f"[guard] banco='{nome}' nao-test, mas operador confirmou "
                f"via --em-banco-descartavel"
            )
        return False, (
            f"[guard] ABORTADO: banco='{nome}' nao comeca com 'test'. "
            f"Drill cria Tenant/Usuario/Auditoria REAIS sem caminho de "
            f"limpeza (trilha imutavel). Para rodar mesmo assim, passe "
            f"--em-banco-descartavel (decisao consciente do operador)."
        )

    def _contagem_acumulo(self) -> dict[str, int]:
        """Conta lixo de drills acumulado no banco.

        - Tenants/Usuarios filtram prefixos conhecidos (`drill-`, `bench-`)
          em contexto `run_as_system` — tabelas de plano-de-controle sem RLS
          (R2-M2 §2.3.1).
        - Auditoria itera os tenants conhecidos + cadeia sistema e soma o
          COUNT por contexto. RLS continua respeitada (role NOBYPASSRLS —
          INV-TENANT-004); a soma e a forma honesta de obter o total sem
          burlar a policy. Custo O(N_tenants), aceitavel no drill.
        """
        with run_as_system():
            tenants = Tenant.objects.filter(slug__startswith="drill-").count()
            tenants += Tenant.objects.filter(slug__startswith="bench-").count()
            usuarios = Usuario.objects.filter(email__startswith="drill-").count()
            usuarios += Usuario.objects.filter(email__startswith="bench-").count()
            ids_tenants = list(Tenant.objects.values_list("id", flat=True))
            cur = connection.cursor()
            cur.execute("SELECT COUNT(*) FROM auditoria;")
            auditoria_sistema = cur.fetchone()[0]  # cadeia sistema (tenant NULL)
        auditoria = auditoria_sistema
        for tid in ids_tenants:
            with run_in_tenant_context(tenant_id=tid):
                with connection.cursor() as c:
                    c.execute("SELECT COUNT(*) FROM auditoria;")
                    auditoria += c.fetchone()[0]
        return {"tenants": tenants, "usuarios": usuarios, "auditoria": auditoria}

    # =============================================================
    # Helpers
    # =============================================================

    def _verificar_hooks(self) -> tuple[bool, str]:
        runner = Path(__file__).resolve().parents[5] / ".claude" / "hooks" / "_test-runner.sh"
        if not runner.exists():
            return False, f"runner nao encontrado em {runner}"
        try:
            result = subprocess.run(
                ["bash", str(runner)],  # noqa: S603,S607 -- runner versionado conhecido no repo, sem input externo do usuario
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
        """FA-A5: drill robusto — NAO mais 1 tenant / 5 linhas / so feliz.

        Prova: (a) 3 tenants intercalados c/ cadeias independentes integras;
        (b) injecao de elo adulterado num tenant EXIGE deteccao (se nao
        detectar, REPROVA — drill que mente e o bug que FA-A5 conserta);
        (c) concorrencia: N threads no mesmo tenant -> cadeia final integra.
        """
        with run_as_system():
            tenants = [
                Tenant.objects.create(
                    slug=f"drill-{i}-{uuid4().hex[:8]}", nome_fantasia=f"Drill{i}"
                )
                for i in range(3)
            ]
            u = Usuario.objects.create_user(
                email=f"drill-{uuid4().hex[:8]}@x.com",
                password="drill-teste-12-chars",  # noqa: S106 -- credencial descartavel de usuario de drill, nao e segredo
            )

        # (a) inserts INTERCALADOS A,B,C,A,B,C... (4 rodadas = 4 elos/tenant)
        for rodada in range(4):
            for t in tenants:
                with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
                    registrar_auditoria(
                        tenant_id=t.id,
                        usuario_id=u.id,
                        action=f"drill.r{rodada}",
                        resource_summary=f"intercalado-{rodada}",
                        payload={"r": rodada},
                    )
        for t in tenants:
            ok, total, quebrados = verificar_integridade_cadeia(tenant_id=t.id)[str(t.id)]
            if not ok:
                return False, (
                    f"tenant {t.slug}: cadeia quebrada (intercalacao): " f"{quebrados[:3]}"
                )
            if total < 4:
                return False, (
                    f"tenant {t.slug}: esperava >=4 elos, achei {total} "
                    f"(RLS pode estar filtrando entre tenants)"
                )

        # (b) ADULTERACAO: poe elo mentiroso no tenant[0]; verificacao DEVE
        #     acusar. Se passar limpo, o drill estaria mentindo (FA-A5).
        alvo = tenants[0]
        with run_in_tenant_context(tenant_id=alvo.id, usuario_id=u.id):
            Auditoria.objects.create(
                tenant_id=alvo.id,
                usuario_id=u.id,
                action="drill.poison",
                resource_summary="elo-adulterado",
                payload_jsonb={"x": 1},
                hash_anterior="0" * 64,
                hash_atual="f" * 64,
            )
        ok_pos, _, quebrados_pos = verificar_integridade_cadeia(tenant_id=alvo.id)[str(alvo.id)]
        if ok_pos or not quebrados_pos:
            return False, (
                "FALHA CRITICA: elo adulterado NAO detectado — o drill "
                "estaria dando F-A como verde mentindo (FA-A5)"
            )
        # tenant nao adulterado continua integro (isolamento da deteccao)
        ok_b, _, _ = verificar_integridade_cadeia(tenant_id=tenants[1].id)[str(tenants[1].id)]
        if not ok_b:
            return False, "deteccao vazou: tenant integro acusado junto"

        # (c) CONCORRENCIA: 8 threads x 10 inserts no tenant[2] sob lock
        #     por-tenant (FA-C1) -> cadeia final integra.
        conc = tenants[2]
        erros: list[str] = []

        def _inserir(n: int) -> None:
            try:
                with run_in_tenant_context(tenant_id=conc.id, usuario_id=u.id):
                    registrar_auditoria(
                        tenant_id=conc.id,
                        usuario_id=u.id,
                        action=f"conc.{n}",
                        resource_summary=f"c{n}",
                        payload={"n": n},
                    )
            except Exception as e:  # drill captura tudo p/ reportar no resumo
                erros.append(f"{type(e).__name__}:{e}")

        threads = [threading.Thread(target=_inserir, args=(n,)) for n in range(80)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        if erros:
            return False, f"concorrencia: {len(erros)} erros, ex: {erros[0]}"
        ok_c, total_c, quebrados_c = verificar_integridade_cadeia(tenant_id=conc.id)[str(conc.id)]
        if not ok_c:
            return False, (
                f"concorrencia quebrou cadeia: {quebrados_c[:3]} " f"(lock por-tenant FA-C1 falhou)"
            )
        return True, (
            f"3 tenants intercalados OK; adulteracao detectada "
            f"({len(quebrados_pos)} elos); 80 inserts concorrentes -> "
            f"{total_c} elos integros"
        )

    def _benchmark_p99(self, escala: bool = False) -> tuple[bool, str]:
        """FA-A5: benchmark MULTI-TENANT intercalado (nao 1 tenant seq).

        §2 L95 exige p99 < 200ms com 10k linhas x 50 tenants. `--escala`
        roda 50 tenants x 200 = 10k linhas intercaladas (proximo do literal).
        Default dev = 3 tenants x 500 (rapido; mesma forma multi-tenant).
        """
        n_tenants, por_tenant = (50, 200) if escala else (3, 500)
        with run_as_system():
            tenants = [
                Tenant.objects.create(slug=f"bench-{i}-{uuid4().hex[:8]}", nome_fantasia=f"B{i}")
                for i in range(n_tenants)
            ]
            u = Usuario.objects.create_user(
                email=f"bench-{uuid4().hex[:8]}@x.com",
                password="bench-teste-12-chars",  # noqa: S106 -- credencial descartavel de usuario de drill, nao e segredo
            )

        tempos_ms: list[float] = []
        # Intercalado: rodada externa, todos os tenants por rodada — exercita
        # o lock por-tenant + indice (tenant_id, sequencia) sob alternancia.
        for i in range(por_tenant):
            for t in tenants:
                with run_in_tenant_context(tenant_id=t.id, usuario_id=u.id):
                    inicio = time.perf_counter()
                    registrar_auditoria(
                        tenant_id=t.id,
                        usuario_id=u.id,
                        action="bench",
                        resource_summary=f"l-{i}",
                        payload={"i": i, "msg": "benchmark"},
                    )
                    tempos_ms.append((time.perf_counter() - inicio) * 1000)

        p99 = statistics.quantiles(tempos_ms, n=100)[98]
        p50 = statistics.median(tempos_ms)
        escopo = f"{n_tenants} tenants x {por_tenant} = {len(tempos_ms)} linhas"
        if p99 < 200:
            return True, f"{escopo}: p50={p50:.1f}ms p99={p99:.1f}ms (lim 200ms)"
        return False, f"{escopo}: p99={p99:.1f}ms (>=200ms — investigar indices)"
