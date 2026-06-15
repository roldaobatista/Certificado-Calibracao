"""Wave A — frente `contas-receber` (títulos a receber, cobrança, baixa).

Path flat `src/infrastructure/contas_receber/` (D-CR-1 / molde fiscal).
Núcleo autossuficiente: lançamento manual + boleto/PIX Mock + webhook HMAC
idempotente (Fatia 2). Integrações cross-módulo (OS/clientes) = Fatia 3.
"""

from __future__ import annotations

from django.apps import AppConfig


class ContasReceberConfig(AppConfig):
    """Frente `contas-receber` — títulos, cobranças, baixas (D-CR-1/2/13)."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.contas_receber"
    label = "contas_receber"
    verbose_name = "Contas a Receber (títulos, cobranças, baixas)"

    def ready(self) -> None:
        # TODO Fatia 3: registrar consumers cross-módulo
        # (os.concluida, os.reaberta, contas_receber.pago → clientes)
        pass
