"""Jobs M4 Fase 7 — funcoes puras consumidas por adapters procrastinate.

Padrao M3 OS herdado:
- Funcoes puras recebem snapshots ja carregados (via repository protocol)
  + `agora: datetime` tz-aware.
- Retornam dataclass com Acoes a executar (mutacoes + eventos).
- Adapter `src/infrastructure/calibracao/jobs.py` carrega snapshots do
  Django ORM, chama a funcao pura, aplica acoes.

Vantagem: jobs sao testaveis sem DB; logica de negocio fica no domain.
"""
