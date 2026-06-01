"""Use cases do módulo `metrologia/certificados` (M8 Wave A — Fatia 2).

Camada de aplicação PURA (ADR-0007): orquestra domínio + Protocols injetados, sem
conhecer Django. `decidir_ponto_reconciliacao` (pré-condição WORM do RT) +
`emitir_certificado` (emissão metrológica atômica fail-closed) + reemissão.
"""
