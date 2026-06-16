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
        # Fatia 3a (T-CR-041): consumers cross-módulo de OS → contas_receber.
        # (`contas_receber.pago` → desbloqueio é consumer do módulo `clientes`, D-CR-11.)
        from src.infrastructure.audit.outbox_worker import registrar_consumer

        from .consumers.os_eventos import handle_os_concluida, handle_os_reaberta

        _MAPA_CONSUMERS = {
            "os.concluida": handle_os_concluida,
            "os.reaberta": handle_os_reaberta,
        }
        for acao, fn in _MAPA_CONSUMERS.items():
            try:
                registrar_consumer(acao, fn)
            except ValueError:
                pass  # já registrado (re-entry em test runner)
