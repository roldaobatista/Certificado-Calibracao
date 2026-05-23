"""Sagas inter-modulares do modulo `ordens_servico` (T-OS-037..039).

Sagas sao orquestracoes que cruzam modulos via bus de eventos. Cada
saga tem:
- Trigger (evento que inicia).
- Estado (rastreado em entidade ou tabela operacional).
- Acoes (cada passo eh consumer/use case com IDEMP-002).
- Compensacao (ADR-0034 — em proposta) quando passo falha.

3 sagas Marco 3:
- `anonimizacao_bloqueada` (T-OS-037) — `cliente_tem_os_aberta` impede
  anonimizacao; watchdog re-tenta quando OS conclui.
- `reabertura_sucessao` (T-OS-038) — INV-OS-SUC-001 — cross-cliente
  M&A exige `SucessaoSocietaria` aprovada antes de reabrir OS de tenant
  sucedido.
- `sync_mobile` (T-OS-039) — LWW por atividade + fotos append-only
  (ADR-0027 + INV-OS-SYNC-001).
"""
