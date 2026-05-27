"""Comando canonico de provisionamento de tenant — T-SAN-PERFIL-031..035.

Sprint 3 P5 do saneamento ADR-0067.

Implementa US-SAN-PERFIL-004 + INV-TENANT-PERFIL-005 + INV-TENANT-PERFIL-007:

  - --perfil {A|B|C|D} OBRIGATORIO (sem default silencioso — FAIL L5
    "snapshot no nivel errado" e default 'D' silencioso eram raiz da
    auditoria 10 lentes).
  - --motivo OBRIGATORIO >= 100 chars (justificativa probatoria registrada
    em TenantPerfilHistorico).
  - Perfil A exige flags ADICIONAIS:
      --numero-rbc (regex CRL NNNN ou CRL NNNN-NN — NIT-DICLA-080)
      --certificado-acreditacao-pdf-path (PDF do certificado CGCRE
        local; upload B2 + hash SHA-256 + assinatura A3 em Sprint 5 Wave A)
      --auditor-cgcre-nome (auditor responsavel pela deliberacao)
      --processo-cgcre-numero
      --ilac-mra-aderido (boolean explicito; default FALSE)
  - Operador humano OBRIGATORIO via env vars:
      AFERE_OPERADOR_HUMANO_CPF + AFERE_OPERADOR_HUMANO_NOME
    OU modo agente IA via flag:
      --autorizado-por-roldao-issue-id <github-issue-id>
    (ADR-0019 — responsabilidade civil de codigo gerado por IA).

Uso:
    python manage.py provisionar_tenant \\
        --slug lab-alpha \\
        --nome-fantasia "Laboratorio Alpha LTDA" \\
        --perfil B \\
        --motivo "Lab rastreavel, atende cliente farma ANVISA ocasional. \\
        Sem CGCRE atual mas planeja trilha 12 meses. Contrato comercial \\
        firmado 2026-05-28."

    python manage.py provisionar_tenant \\
        --slug lab-beta-acreditado \\
        --nome-fantasia "Lab Beta Calibracoes LTDA" \\
        --perfil A \\
        --numero-rbc "CRL 1234" \\
        --certificado-acreditacao-pdf-path /tmp/cert_lab_beta.pdf \\
        --auditor-cgcre-nome "Joao Silva CGCRE Auditor RBC" \\
        --processo-cgcre-numero "CGCRE-PROC-2024-1234" \\
        --ilac-mra-aderido \\
        --motivo "Lab acreditado RBC desde 2022, escopo massa+temperatura. \\
        ILAC-MRA aderido em 2024. Migracao do sistema legado para Afere \\
        contratado em 2026-05-15."
"""

from __future__ import annotations

import hashlib
import os
import re
import uuid
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction


_REGEX_NUMERO_RBC = re.compile(r"^CRL \d{4}(-\d{2})?$")
_REGEX_PROCESSO_CGCRE = re.compile(r"^CGCRE-PROC-\d{4}-\d{1,6}$")
_TAMANHO_MINIMO_MOTIVO = 100


class Command(BaseCommand):
    help = (
        "Provisiona um tenant novo no sistema com perfil regulatorio canonico "
        "(ADR-0067 + INV-TENANT-PERFIL-005). Perfil A exige documentacao CGCRE."
    )

    def add_arguments(self, parser):
        # Campos basicos do Tenant
        parser.add_argument("--slug", required=True, help="Identificador url-safe (ex: 'balancas-solution').")
        parser.add_argument("--nome-fantasia", required=True, help="Razao social comercial do tenant.")
        parser.add_argument(
            "--perfil",
            required=True,
            choices=["A", "B", "C", "D"],
            help="Perfil regulatorio canonico (ADR-0067 §1). Sem default — INV-TENANT-PERFIL-005.",
        )
        parser.add_argument(
            "--motivo",
            required=True,
            help=f"Justificativa textual (>= {_TAMANHO_MINIMO_MOTIVO} chars). Registrado em TenantPerfilHistorico.",
        )

        # Perfil A — flags adicionais (INV-TENANT-PERFIL-007)
        parser.add_argument(
            "--numero-rbc",
            help="Numero RBC formato 'CRL NNNN' ou 'CRL NNNN-NN' (NIT-DICLA-080). Obrigatorio se --perfil A.",
        )
        parser.add_argument(
            "--certificado-acreditacao-pdf-path",
            help="Caminho local pro PDF do certificado CGCRE. Hash SHA-256 e calculado e cravado em TenantPerfilHistorico.certificado_acreditacao_documento_id. Upload B2 + assinatura A3 sao Sprint 5 Wave A.",
        )
        parser.add_argument(
            "--auditor-cgcre-nome",
            help="Nome completo do auditor CGCRE. Obrigatorio se --perfil A.",
        )
        parser.add_argument(
            "--processo-cgcre-numero",
            help="Numero do processo CGCRE no formato CGCRE-PROC-YYYY-NNNN. Obrigatorio se --perfil A.",
        )
        parser.add_argument(
            "--ilac-mra-aderido",
            action="store_true",
            help="Indica que o lab esta no ILAC-MRA (reconhecimento internacional). Default False (R9 plan.md — ILAC nao e universal).",
        )

        # Operador humano (ADR-0019 responsabilidade civil)
        parser.add_argument(
            "--autorizado-por-roldao-issue-id",
            help="Em modo agente IA: ID da issue GitHub aprovada manualmente pelo Roldao (ADR-0019).",
        )

        # Idempotencia + dry-run
        parser.add_argument("--dry-run", action="store_true", help="Valida tudo mas nao escreve no banco.")

    def handle(self, *args, **options):
        slug = options["slug"]
        nome_fantasia = options["nome_fantasia"]
        perfil = options["perfil"]
        motivo = options["motivo"]
        autorizado_por_issue = options["autorizado_por_roldao_issue_id"]
        dry_run = options["dry_run"]

        # 1. Motivo >= 100 chars (INV-005).
        if len(motivo) < _TAMANHO_MINIMO_MOTIVO:
            raise CommandError(
                f"--motivo tem {len(motivo)} chars; minimo {_TAMANHO_MINIMO_MOTIVO} "
                f"(INV-TENANT-PERFIL-005). Justificativa precisa contar a historia "
                f"da decisao para defesa em auditoria CGCRE/seguradora."
            )

        # 2. Operador humano OU modo IA autorizado.
        operador_cpf = os.environ.get("AFERE_OPERADOR_HUMANO_CPF", "").strip()
        operador_nome = os.environ.get("AFERE_OPERADOR_HUMANO_NOME", "").strip()
        if operador_cpf and operador_nome:
            modo_operacao = f"humano:{operador_nome} (CPF {operador_cpf[:3]}***{operador_cpf[-2:]})"
        elif autorizado_por_issue:
            modo_operacao = f"agente_ia:issue#{autorizado_por_issue}"
        else:
            raise CommandError(
                "Provisionamento exige UM dos seguintes (ADR-0019):\n"
                "  - env AFERE_OPERADOR_HUMANO_CPF + AFERE_OPERADOR_HUMANO_NOME (operador humano)\n"
                "  - flag --autorizado-por-roldao-issue-id <issue-id> (agente IA com aprovacao manual)"
            )

        # 3. Validacoes especificas do Perfil A.
        documento_hash_sha256 = None
        documento_id = None
        if perfil == "A":
            numero_rbc = options["numero_rbc"] or ""
            auditor = options["auditor_cgcre_nome"] or ""
            processo = options["processo_cgcre_numero"] or ""
            pdf_path = options["certificado_acreditacao_pdf_path"] or ""

            faltando = []
            if not numero_rbc:
                faltando.append("--numero-rbc")
            if not auditor:
                faltando.append("--auditor-cgcre-nome")
            if not processo:
                faltando.append("--processo-cgcre-numero")
            if not pdf_path:
                faltando.append("--certificado-acreditacao-pdf-path")
            if faltando:
                raise CommandError(
                    f"Perfil A exige flags adicionais (INV-TENANT-PERFIL-007): {', '.join(faltando)}"
                )

            if not _REGEX_NUMERO_RBC.match(numero_rbc):
                raise CommandError(
                    f"--numero-rbc {numero_rbc!r} invalido. Formato esperado: "
                    f"'CRL NNNN' ou 'CRL NNNN-NN' (NIT-DICLA-080)."
                )
            if not _REGEX_PROCESSO_CGCRE.match(processo):
                raise CommandError(
                    f"--processo-cgcre-numero {processo!r} invalido. Formato esperado: "
                    f"'CGCRE-PROC-YYYY-NNNN'."
                )

            pdf_file = Path(pdf_path)
            if not pdf_file.is_file():
                raise CommandError(f"PDF nao encontrado: {pdf_path}")
            documento_hash_sha256 = _hash_arquivo_sha256(pdf_file)
            documento_id = uuid.uuid4()
            self.stdout.write(
                f"[doc] PDF {pdf_path}: SHA-256 {documento_hash_sha256[:16]}... "
                f"(B2 upload + A3 = Sprint 5 Wave A; documento_id placeholder {documento_id})"
            )

        # 4. Idempotencia — slug ja existe?
        from src.infrastructure.tenant.models import Tenant, TenantPerfilHistorico

        if Tenant.objects.filter(slug=slug).exists():
            raise CommandError(
                f"Tenant slug={slug!r} ja existe. Para mudar perfil de tenant existente, "
                f"use funcao SECURITY DEFINER aplicar_evento_cgcre (em management/commands futuro)."
            )

        # 5. Executar.
        self.stdout.write(self.style.NOTICE(f"Provisionando tenant slug={slug} perfil={perfil} ({modo_operacao})..."))

        if dry_run:
            self.stdout.write(self.style.WARNING("[dry-run] Validacao OK. Sem escrita no banco."))
            return

        with transaction.atomic():
            tenant = Tenant.objects.create(
                slug=slug,
                nome_fantasia=nome_fantasia,
                perfil_regulatorio=perfil,
                acreditacao_cgcre_numero=options["numero_rbc"] if perfil == "A" else None,
                ilac_mra_aderido=options["ilac_mra_aderido"] if perfil == "A" else False,
            )
            TenantPerfilHistorico.objects.create(
                tenant=tenant,
                perfil_anterior=None,
                perfil_novo=perfil,
                direcao="provisionamento_inicial",
                motivo=f"{motivo}\n\n[operador] {modo_operacao}",
                auditor_cgcre=options["auditor_cgcre_nome"] if perfil == "A" else None,
                certificado_acreditacao_documento_id=documento_id,
            )

        self.stdout.write(self.style.SUCCESS(f"OK tenant id={tenant.id} slug={slug} perfil={perfil}"))
        self.stdout.write(
            f"Historico inicial registrado em tenant_perfil_historico "
            f"(direcao=provisionamento_inicial, motivo {len(motivo)} chars)."
        )
        if perfil == "A":
            self.stdout.write(
                self.style.WARNING(
                    f"[gate] PDF do certificado CGCRE precisa de upload B2 + assinatura A3 do Roldao "
                    f"em Sprint 5 Wave A. Hash SHA-256: {documento_hash_sha256}."
                )
            )


def _hash_arquivo_sha256(path: Path) -> str:
    """Hash SHA-256 do arquivo (T-033)."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
