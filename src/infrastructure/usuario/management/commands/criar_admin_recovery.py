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
from src.infrastructure.usuario.senha_breakglass import validar_senha_breakglass


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

        senha = getpass(
            prompt="Senha inicial (>=14 chars, 4 categorias; sera trocada no 1o login): "
        )
        # GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA: complexidade + dicionario
        # (mais rigido que INV-AUTH-002 por ser conta de privilegio maximo).
        try:
            validar_senha_breakglass(senha, email=email, nome=nome)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc
        senha_2 = getpass(prompt="Repita: ")
        if senha != senha_2:
            raise CommandError("Senhas nao batem. Conta NAO criada.")

        # INV-ADMIN-003 + OBS-001: criacao crava na cadeia hash imutavel
        # (P5 F-C1 conserto obs-MED-1). Sem isto, auditor LGPD/CGCRE nao
        # consegue responder "quem criou conta break-glass em data Y?" —
        # so sobraria `Usuario.criado_em` mutavel sem hash chain.
        # Atomico: usuario + evento na MESMA transacao (Garantia 3 do
        # publicar_evento — caller responsavel pelo atomic).
        from uuid import uuid4

        from django.db import transaction

        from src.infrastructure.audit.event_helpers import publicar_evento
        from src.infrastructure.multitenant.connection import run_as_system

        with run_as_system(), transaction.atomic():
            usuario = Usuario.objects.create_user(
                email=email,
                password=senha,
                nome_completo=nome,
                is_staff=True,
                is_superuser=True,
                is_break_glass=True,
                mfa_obrigatorio=True,
            )
            publicar_evento(
                acao="Admin.BreakGlass.CONTA_CRIADA",
                payload={
                    "usuario_id": str(usuario.id),
                    "email": usuario.email,
                    "forcar_rotacao_senha": opts.get("forcar_rotacao_senha", False),
                    "criado_via": "manage.py criar_admin_recovery",
                },
                causation_id=uuid4(),
                tenant_id=None,  # conta global, cadeia sistema
                usuario_id=None,  # CLI sem request.user
                resource_summary=f"usuario={usuario.email}",
                outbox=False,  # evento sistema-only, sem fan-out cross-modulo
            )

        # GATE-CYBER-BREAKGLASS-U2F-ENFORCE (INV-ADMIN-003): Wave A liga
        # WebAuthn obrigatorio. Sem U2F, login fica bloqueado pelo
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
