"""Jobs M5 padroes P6 — funcoes puras consumidas por adapters procrastinate.

Padrao M4 calibracao herdado (src/application/metrologia/calibracao/jobs/):
- Funcoes puras recebem snapshots ja carregados (via repository protocol)
  + `agora: datetime` tz-aware.
- Retornam dataclasses de Alerta (sem mutacao; caller publica via bus).
- Adapter `src/infrastructure/metrologia/padroes/management/commands/
  processar_jobs_padroes.py` carrega snapshots do Django ORM (M5 ja tem
  adapters reais — NAO eh stub como M4 Wave A), chama a funcao pura,
  processa os alertas.

Vantagem: jobs testaveis sem DB; logica de vencimento fica no domain.
"""
