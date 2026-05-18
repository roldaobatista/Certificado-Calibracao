"""Camada de infraestrutura — adapters concretos Django/Postgres/Celery.

Conforme ADR-0007:
- models/        Django Models (gerados pelo codegen na Wave A; manuais em F-A)
- repositories/  Implementacao Django dos Protocols de src/domain/<ctx>/repository.py
- multitenant/   Middleware + roles + RLS helpers (Marco 3)
- audit/         Hash chain + trigger anti-UPDATE/DELETE (Marco 4)
- eventbus/      Adapter Procrastinate do EventBus Protocol
"""
