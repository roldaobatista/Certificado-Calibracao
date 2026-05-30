"""Use cases do módulo `metrologia/escopos-cmc` (M6 Wave A — Fatia 2).

Orquestram os Protocols do domínio (ADR-0007): cadastrar / revisar (nova versão) /
revogar escopo. Anti-fraude rbc_efetivo (ADR-0067/0075) aplicado aqui. NÃO chamam
AuthorizationProvider (caller=guard, use_case=transação — molde M4/M5).
"""
