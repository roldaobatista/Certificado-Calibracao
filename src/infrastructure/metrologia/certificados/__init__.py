"""Lógica de infra do módulo `metrologia/certificados` (ADR-0078 / ADR-0072).

Path ANINHADO que hospeda a LÓGICA (mappers, repositories, query_service, use
cases REST na Fatia 2) — a TABELA física `certificados` + o trigger INV-025 ficam
no app FLAT `infrastructure/certificados/` (contrato cross-app). NÃO é um app
Django (sem models próprios): importa os models flat. Domain não conhece Django
(ADR-0007 — mappers convertem Model<->Snapshot).
"""
