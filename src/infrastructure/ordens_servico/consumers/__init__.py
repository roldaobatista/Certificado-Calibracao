"""Consumers do modulo `ordens_servico` (T-OS-029..036 / Fase 4 Marco 3).

Cada consumer:
- Eh decorado por `@consumer_idempotente` (INV-BUS-001 / ADR-0033).
- Recebe envelope v10 (event_id + tenant_id + payload + correlation_id).
- Eh registrado em `audit.outbox_worker._REGISTRY` via `AppConfig.ready`.
- Worker entra em `run_in_tenant_context(tenant_id)` antes de invocar.

Modulos consumidos (Wave A vai amadurecer):
- orcamentos (Marco 3+): Orcamento.Aprovado
- clientes (Marco 1 ✅): Cliente.Anonimizado
- calibracao (Marco 4): Calibracao.Iniciada/Concluida
- financeiro (Wave A): OS.Faturada/OS.Paga
- tenant (Foundation ✅): Tenant.Suspenso/Encerrado
- equipamentos (Marco 2 ✅): Equipamento.Baixado/Descartado +
                              EquipamentoRecebimento.Registrado
- licencas-acreditacoes (Wave A): Acreditacao.Vencida/Suspensa
"""
