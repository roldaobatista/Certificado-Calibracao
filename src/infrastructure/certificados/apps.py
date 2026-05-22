"""App stub `certificados` — Wave A construira modulo completo.

Marco 2 cria APENAS o necessario para destravar INV-025 (imutabilidade
pos-emissao de certificado em campos criticos do Equipamento) — modelo
minimo `Certificado` + trigger PG `equipamento_imutabilidade_pos_cert`
que consulta a tabela.

Quando Wave A construir o modulo completo (emissao A3, PDF, NIT-DICLA,
RBC), substitui o modelo stub mantendo a tabela existente.
"""

from __future__ import annotations

from django.apps import AppConfig


class CertificadosConfig(AppConfig):
    name = "src.infrastructure.certificados"
    label = "certificados"
    verbose_name = "Certificados (stub Marco 2 — Wave A expandira)"
    default_auto_field = "django.db.models.UUIDField"
