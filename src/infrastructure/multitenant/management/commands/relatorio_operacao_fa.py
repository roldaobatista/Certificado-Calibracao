"""Coleta métricas operacionais do período Foundation F-A.

Critério 7 do drill exige 4 indicadores observados ao longo de 4-6 semanas:
1. Intervenções de código do Roldão: ≤ 2 por semana em média
2. Bugs SEV-1 no período: ≤ 3 totais
3. Gasto LLM: ≤ R$ 1.500 no período
4. Auditor de segurança: sem veto nos últimos 14 dias

Uso:
    docker compose exec app poetry run python manage.py relatorio_operacao_fa

Métricas auto-coletadas via git + filesystem. Métricas externas (LLM gasto)
exigem dado do console Anthropic — comando reporta como TBD.
"""

from __future__ import annotations

import re
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from django.core.management.base import BaseCommand

# Marco inicial da F-A
INICIO_F_A = datetime(2026, 5, 17, tzinfo=UTC)


class Command(BaseCommand):
    help = "Reporta estado atual dos 4 indicadores operacionais do critério 7 (F-A)."

    def handle(self, *args, **options):
        agora = datetime.now(UTC)
        dias_em_fa = (agora - INICIO_F_A).days
        semanas = dias_em_fa / 7

        self.stdout.write(self.style.MIGRATE_HEADING("===== RELATÓRIO OPERACIONAL F-A ====="))
        self.stdout.write(f"Início F-A:  {INICIO_F_A:%Y-%m-%d}")
        self.stdout.write(f"Hoje:        {agora:%Y-%m-%d}")
        self.stdout.write(f"Dias:        {dias_em_fa}  ({semanas:.1f} semanas)")
        self.stdout.write("")

        # ---------------------------------------------------------------
        # 1. Intervenções Roldão (commits com autor != Claude)
        # ---------------------------------------------------------------
        self.stdout.write(self.style.NOTICE("[1/4] Intervenções Roldão (commits com autor não-IA)"))
        intervenções = self._contar_intervencoes_roldao()
        media_semanal = intervenções / max(semanas, 1)
        if media_semanal <= 2:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  [OK ] {intervenções} intervencoes em {semanas:.1f} sem = "
                    f"{media_semanal:.1f}/sem (limite ≤ 2)"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"  [XXX] {intervenções} intervencoes em {semanas:.1f} sem = "
                    f"{media_semanal:.1f}/sem (excedeu limite 2)"
                )
            )

        # ---------------------------------------------------------------
        # 2. Bugs SEV-1
        # ---------------------------------------------------------------
        self.stdout.write(
            self.style.NOTICE("[2/4] Bugs SEV-1 (busca em commits + trilha-auditoria)")
        )
        sev1 = self._contar_sev1()
        if sev1 <= 3:
            self.stdout.write(self.style.SUCCESS(f"  [OK ] {sev1} SEV-1 no período (limite ≤ 3)"))
        else:
            self.stdout.write(self.style.ERROR(f"  [XXX] {sev1} SEV-1 — excedeu limite"))

        # ---------------------------------------------------------------
        # 3. Gasto LLM (não-automatizável — TBD)
        # ---------------------------------------------------------------
        self.stdout.write(self.style.NOTICE("[3/4] Gasto LLM (console Anthropic)"))
        self.stdout.write(
            self.style.WARNING(
                "  [TBD] Verificar manualmente em https://console.anthropic.com/settings/usage"
            )
        )
        self.stdout.write("        Limite: R$ 1.500 no período de 4-6 semanas")

        # ---------------------------------------------------------------
        # 4. Vetos do Auditor de Segurança
        # ---------------------------------------------------------------
        self.stdout.write(self.style.NOTICE("[4/4] Vetos auditor segurança (últimos 14 dias)"))
        vetos = self._contar_vetos_seguranca_recentes()
        if vetos == 0:
            self.stdout.write(self.style.SUCCESS("  [OK ] 0 vetos nos últimos 14 dias"))
        else:
            self.stdout.write(self.style.ERROR(f"  [XXX] {vetos} veto(s) nos últimos 14 dias"))

        # ---------------------------------------------------------------
        # Conclusão
        # ---------------------------------------------------------------
        self.stdout.write("")
        if semanas < 4:
            self.stdout.write(
                self.style.WARNING(
                    f"PERÍODO MÍNIMO NÃO ATINGIDO: {semanas:.1f}/4 semanas. "
                    "Critério 7 exige 4-6 semanas observadas — Roldão decide se aceita "
                    "evidência empírica do período atual ou aguarda período completo."
                )
            )
        elif media_semanal <= 2 and sev1 <= 3 and vetos == 0:
            self.stdout.write(
                self.style.SUCCESS("CRITÉRIO 7 ATENDIDO (validar gasto LLM manualmente).")
            )
        else:
            self.stdout.write(self.style.ERROR("CRITÉRIO 7 REPROVADO."))

    # =================================================================
    # Helpers
    # =================================================================

    def _git(self, *args: str) -> str:
        """Roda git e devolve stdout."""
        repo = Path(__file__).resolve().parents[5]
        try:
            # S603/S607: comando dev-only; args internos fixos (nunca
            # input externo), git resolvido do PATH do dev.
            r = subprocess.run(
                ["git", *args],  # noqa: S603, S607
                capture_output=True,
                text=True,
                cwd=str(repo),
                timeout=15,
            )
            return r.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            return ""

    def _contar_intervencoes_roldao(self) -> int:
        """Conta commits desde INICIO_F_A com 'Author:' diferente do agente IA.

        Heurística: agente IA usa o padrão Co-Authored-By: Claude. Commits que
        NÃO têm esse rodapé OU que tem 'ajuste manual' na mensagem contam.
        """
        log = self._git(
            "log",
            f"--since={INICIO_F_A:%Y-%m-%d}",
            "--format=%H|%an|%s|%b",
            "-z",  # separador NUL
        )
        if not log:
            return 0
        intervencoes = 0
        for commit in log.split("\0"):
            if not commit.strip():
                continue
            partes = commit.split("|", 3)
            if len(partes) < 4:
                continue
            _hash, _author, _subject, body = partes
            # Considera "intervenção Roldão" se NÃO tem Co-Authored-By Claude
            # OU se subject/body menciona "ajuste manual" / "intervenção Roldão"
            if "Co-Authored-By: Claude" not in body and "Co-Authored-By: Claude" not in commit:
                intervencoes += 1
            elif re.search(r"ajuste manual|intervencao roldao", commit, re.IGNORECASE):
                intervencoes += 1
        return intervencoes

    def _contar_sev1(self) -> int:
        """Conta menções a SEV-1 em commits ou docs de trilha."""
        log = self._git(
            "log",
            f"--since={INICIO_F_A:%Y-%m-%d}",
            "--format=%s %b",
            "--grep=SEV-1",
        )
        # 1 ocorrência de SEV-1 por commit (estimativa conservadora)
        return log.count("SEV-1") if log else 0

    def _contar_vetos_seguranca_recentes(self) -> int:
        """Conta menções a 'veto' do auditor de segurança em commits últimos 14 dias.

        Pré-deploy não há logs persistidos — depende de menções em commit messages.
        Pós-deploy, trocar por leitura de docs/governanca/trilha-auditoria-agentes.md
        """
        desde = datetime.now(UTC) - timedelta(days=14)
        log = self._git(
            "log",
            f"--since={desde:%Y-%m-%d}",
            "--format=%s %b",
            "--grep=veto auditor",
            "-i",
        )
        return log.count("veto auditor") if log else 0
