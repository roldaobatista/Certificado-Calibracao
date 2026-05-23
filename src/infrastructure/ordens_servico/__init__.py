"""Wave A Marco 3 — modulo ordens_servico (`os`).

Operacao/os: nucleo operacional do produto. 1 OS contem N
AtividadeDaOS (ADR-0023). Cobre calibracao, manutencao, instalacao,
verificacao INMETRO, vistoria. Multi-tenant via RLS (ADR-0002),
audit imutavel (RAT-08), idempotencia consumer (ADR-0033),
biometria touch art. 11 LGPD (INV-OS-CONSBIO-001).

Nome `ordens_servico` evita colisao com builtin Python `os`.
App label tambem `ordens_servico` — referenciado como
`ordens_servico.OS` em FKs.

Spec: docs/faseamento/M3-os/spec.md (stable v1, retrofit P3).
Plan: docs/faseamento/M3-os/plan.md (ata 27 achados P2).
Tasks: docs/faseamento/M3-os/tasks.md (147 T-OS em 12 fases).
"""
