"""Dominio puro - Ordens de Servico (Wave A Marco 3).

Composto por:
- `value_objects.py`: enums + VOs imutaveis (EstadoOS, EstadoAtividade,
  TipoAtividade, MotivoCancelamento, NumeroOSFormatado).
- `entities.py`: Snapshots DTO imutaveis (OSSnapshot, AtividadeSnapshot,
  AceiteAtividadeSnapshot, etc).
- `regras.py`: regras de transicao estado-maquina + validacao INVs.
- `repository.py`: Protocol pra DI (use cases consomem; adapter Django
  implementa em `src/infrastructure/ordens_servico/repositories.py`).

NAO importar django.* — camada pura.

ADRs ancorando:
- ADR-0023 (OS com Atividades)
- ADR-0026 (2a conferencia + independencia)
- ADR-0029 (canonicalizacao texto probatorio)
- ADR-0030 (vigencia temporal canonica)
- ADR-0031 (soft-delete 3 padroes)
- ADR-0032 (FK cross-modulo anonimizacao)
- ADR-0041 (concorrencia atividades)
- ADR-0042 (cancelamento parcial x faturamento)
- ADR-0056 (numeracao OS — buracos aceitos)

INVs centrais:
- INV-OS-ATIV-001..005 (terminal, cross-tenant, enum, checklist, executor)
- INV-OS-CONC-001 (concorrencia unique partial index)
- INV-OS-FAT-001 (faturamento por atividades nao canceladas)
- INV-OS-CONSBIO-001 (consentimento art. 11 LGPD)
- INV-OS-CAL-LINK-001 (watchdog cal-link)
- INV-DOC-CANON-001 (canonicalizacao texto)
"""
