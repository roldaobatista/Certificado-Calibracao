"""Modulo `qualidade` — stub Marco 2.

Marco 2 expoe apenas a porta `capa_query_service` (consumida por
`EquipamentoRecebimento` para link de nao-conformidade em P-EQP-R3 /
AC-EQP-006-7b). Wave A constroi o modulo completo (ISO 17025 cl. 8.7
gestao de nao conformidades + CAPA + auditoria interna).

Nao registrado em INSTALLED_APPS — modulo Python puro, sem modelos.
Quando Wave A construir o modulo completo, promove para Django app
com migrations sem quebrar consumidores (ADR-0007).
"""
