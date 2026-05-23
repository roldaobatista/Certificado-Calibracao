"""Bus de eventos — primitivas reusaveis pra consumers e producers.

Ponto de entrada do INV-BUS-001 (idempotencia de consumer obrigatoria).
Producers gravam em `bus_outbox` via `audit.event_helpers.publicar_evento`;
consumers consomem via `dispatch_event` do `audit.outbox_worker` e
proteg em-se com `consumer_idempotente` deste pacote.
"""
