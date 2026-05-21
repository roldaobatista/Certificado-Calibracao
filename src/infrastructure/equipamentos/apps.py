"""Wave A · Marco 2 — modulo equipamentos.

Suporte-plataforma / equipamentos: equipamento fisico do cliente
(balanca, paquimetro, termometro etc.) que o tenant calibra. Cadastro
com TAG unica por tenant, QR Code HMAC versionado, vinculo a cliente
(Marco 1), historico imutavel de eventos pos-emissao de certificado
(INV-025), versionamento controlado por enum de motivo e fluxo de
aprovacao gestor_qualidade quando motivo=outros.

Spec: docs/faseamento/M2-equipamentos/spec.md (forward stable v1).
Plan: docs/faseamento/M2-equipamentos/plan.md (P2 — 4 reviews
absorvidos: 3 BLOQUEANTES + ~10 MEDIOS INV-RITUAL-001).
"""

from __future__ import annotations

from django.apps import AppConfig


class EquipamentosConfig(AppConfig):
    """Marco 2 — equipamento fisico do cliente."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "src.infrastructure.equipamentos"
    label = "equipamentos"
    verbose_name = "Equipamentos (suporte-plataforma)"
