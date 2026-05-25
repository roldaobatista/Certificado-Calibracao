"""Wave A Marco 4 — modulo `calibracao` (metrologia/calibracao).

Coracao tecnico do produto Afere — calibracao metrologica ISO/IEC 17025
com 17 user stories (US-CAL-001..018 — incluindo US-CAL-018 reclamacao
do cliente CDC art. 26 adicionada em P3 ritual Spec Kit 2026-05-25).

Spec autoritativa: docs/faseamento/M4-calibracao/spec.md
Plan P2: docs/faseamento/M4-calibracao/plan.md
Matriz P3: docs/faseamento/M4-calibracao/matriz-reconciliacao.md
Tarefas P4: docs/faseamento/M4-calibracao/tasks.md (160 T-CAL-NNN)

ADRs aplicadas: 0002 (RLS) + 0007 (camada dominio) + 0012 (authz) +
0021 (anonimizacao 3 zonas) + 0022 (RT tenant) + 0023 (OS com Atividades) +
0024 revisado (regra decisao + 6 zonas ILAC G8 + PFA/PRA) + 0025 (validacao
software cl. 7.11) + 0026 (2a conferencia + independencia RT) +
0029 (canonicalizacao texto probatorio) + 0030 (vigencia temporal) +
0031 (soft-delete 3 padroes) + 0032 (FK cross-modulo anonimizacao) +
0033 (bus idempotencia consumer) + 0040 (padrao metrologico entidade
separada) + 0063 Opcao A (RT competencia diferida — lazy em 3 use cases
pos-config) + 0064 (rotacao HMAC + KMS Multi-Region 25a) + 0065 NOVA
(concorrencia calibracao metrologica — UNIQUE composto + CAS + advisory
lock).
"""

default_app_config = "src.infrastructure.calibracao.apps.CalibracaoConfig"
