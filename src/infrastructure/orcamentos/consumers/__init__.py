"""Consumers de eventos do bus para o módulo `orcamentos` (Fatia 2 / Onda 2d).

Registrados em ``OrcamentosConfig.ready()`` (``apps.py``) via
``audit.outbox_worker.registrar_consumer``. Cada handler usa
``@consumer_idempotente`` (ADR-0033 / INV-BUS-001).
"""
