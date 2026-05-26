"""Application layer — metrologia/calibracao (Marco 4 — use cases).

Use cases por nome de arquivo, igual M3 OS:
- criar_calibracao.py       (US-CAL-001 — Batch A Fase 5)
- configurar_calibracao.py  (US-CAL-002 — Batch A Fase 5)
- registrar_leitura.py      (US-CAL-004 — Batch B Fase 5)
- ...

Cada use case:
- Recebe Input dataclass frozen.
- Chama AuthorizationProvider.can(action, resource).
- Roda invariantes puros via `regras.py`.
- Chama Repository Protocol (CalibracaoRepository).
- Retorna Output dataclass frozen com snapshot novo + eventos publicados.

Sem Django, sem PG, sem rede. Determinismo total.
"""
