"""manage.py criar_admin_recovery — F-C1 P4 T-FC1-13 (US-FC1-006).

Cria conta admin-recovery (break-glass) com:
- is_break_glass=True (AdminHardeningMiddleware reconhece e bypassa IP allowlist)
- is_staff=True (acesso ao /admin/ Django)
- is_superuser=True (admin completo — caso de uso unico de break-glass)
- mfa_obrigatorio=True (forca MFA — U2F WebAuthn quando entrar)

Procedimento operacional em docs/operacao/runbook.md §11.bis.

Uso:
    docker compose exec app poetry run python manage.py criar_admin_recovery \
        --email admin-recovery@afere.local \
        --nome-completo "Conta Recovery Roldão" \
        [--forcar-rotacao-senha]
"""

from __future__ import annotations

from getpass import getpass

from django.core.management.base import BaseCommand, CommandError

from src.infrastructure.usuario.models import Usuario


class Command(BaseCommand):
    help = "Cria conta admin-recovery (break-glass) com is_break_glass=True."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--email",
            required=True,
            help="Email da conta (recomendado: admin-recovery@<tenant>.local).",
        )
        parser.add_argument(
            "--nome-completo",
            required=True,
            help="Nome completo (ex: 'Conta Recovery Roldão Batista').",
        )
        parser.add_argument(
            "--forcar-rotacao-senha",
            action="store_true",
            help="Forca a senha a expirar imediatamente (proximo login obriga troca).",
        )

    def handle(self, *args, **opts) -> None:
        email = opts["email"].lower().strip()
        nome = opts["nome_completo"].strip()

        if Usuario.objects.filter(email=email).exists():
            raise CommandError(
                f"Ja existe Usuario com email={email}. Conta break-glass deve ser UNICA por instalacao."
            )

        contagem_atual = Usuario.objects.filter(is_break_glass=True).count()
        if contagem_atual >= 2:
            raise CommandError(
                f"Ja existem {contagem_atual} contas break-glass. Limite operacional = 2 "
                "(Roldao + DPO Wave A). Desativar uma antes de criar nova."
            )

        self.stdout.write(
            self.style.WARNING(
                "\n=== CRIAR CONTA BREAK-GLASS ===\n"
                "Esta conta tera privilegios MAXIMOS. Cada login dispara alerta critico.\n"
                "Use APENAS em emergencia (MFA principal perdido).\n"
                "Procedimento documentado em docs/operacao/runbook.md §11.bis\n"
            )
        )
        confirmacao = input(
            f"\nDigite 'CRIAR BREAK-GLASS {email}' (exato) para confirmar: "
        ).strip()
        if confirmacao != f"CRIAR BREAK-GLASS {email}":
            raise CommandError("Confirmacao falhou. Conta NAO criada.")

        senha = getpass(prompt="Senha inicial (>=14 chars; sera trocada no 1o login): ")
        if len(senha) < 14:
            raise CommandError("Senha precisa ter >=14 caracteres para conta break-glass.")
        senha_2 = getpass(prompt="Repita: ")
        if senha != senha_2:
            raise CommandError("Senhas nao batem. Conta NAO criada.")

        usuario = Usuario.objects.create_user(
            email=email,
            password=senha,
            nome_completo=nome,
            is_staff=True,
            is_superuser=True,
            is_break_glass=True,
            mfa_obrigatorio=True,
        )

        # TODO Wave A: integracao WebAuthn — cadastrar U2F via fluxo dedicado
        # depois deste comando. Sem U2F, login fica bloqueado pelo
        # MfaRequiredMiddleware (is_verified() = False).

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[OK] Conta break-glass criada: {usuario.email} (id={usuario.id})\n"
                "\nPROXIMOS PASSOS OBRIGATORIOS:\n"
                "  1. Cadastrar U2F (YubiKey ou similar) — Wave A vai entregar fluxo.\n"
                "  2. Guardar U2F em local fisico seguro (cofre, NAO carteira).\n"
                "  3. Documentar criacao em log: docs/operacao/drills/break-glass-criacao-YYYY-MM-DD.md\n"
                "  4. Alerta critico vai disparar em CADA login desta conta.\n"
                "  5. Apos uso emergencial, RESTAURAR MFA da conta principal + revisar audit.\n"
            )
        )
