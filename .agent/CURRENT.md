# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** Foundation F-A+F-B FECHADAS · Marco 1 `clientes` FECHADO · Marco 2 `equipamentos` FECHADO · **Marco 3 `os`: P1+P2+P3 fechadas + P4 FASES 1+2 (Schema + Domain) FECHADAS (2026-05-23).**
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-23 pós T-OS-001/002)

- Suite completa: **904 passed em 13min27s** (sem coverage). Zero regressão.
- Hooks `_test-runner.sh`: **207/207** verdes.
- ruff: All checks passed em `src/infrastructure/ordens_servico/`.
- makemigrations --check: limpo.
- migrate ordens_servico: 0001 + 0002 OK aplicadas.

## Marcos fechados

- **M1 `clientes`** — P5 10 auditores ZERO C/A/M. `docs/faseamento/M1-clientes/auditoria-familia5.md`.
- **M2 `equipamentos`** — 65 T-EQP, P5 2ª passada ZERO C/A/M (CVE-2025-68616 WeasyPrint mitigado). `docs/faseamento/M2-equipamentos/auditoria-familia5.md`.

## Marco 3 OS — P1+P2+P3 + P4 inicial entregues (2026-05-23)

- **P1 spec FORWARD stable** — 15 US, 10 entidades, 17 INVs, 14 eventos, 10 sagas, drill 24 verificações. `docs/faseamento/M3-os/spec.md`.
- **P2 4 reviews paralelos** — tech-lead (6) + advogado (7) + corretora (6) + RBC (8) = **27 achados** (6 BLOQ + 12 MÉD + 9 GATE/ACEITE). `docs/faseamento/M3-os/reviews/{tech-lead,advogado,corretora,rbc}.md` + `plan.md` ata.
- **P3 retrofit** absorvendo 6 BLOQ + 12 MÉD: ADR-0056 NOVA (numeração buracos aceitos), spec retrofit, REGRAS 5 INVs novos + 3 estendidos, PRD 10 ACs novos, ADR-0012 5 predicates novos, ADR-0028 rev 2 com 6 cláusulas seguráveis novas, matriz reconciliação zero conflito, 9 GATEs Wave A. `docs/faseamento/M3-os/matriz-reconciliacao.md`.
- **3 decisões Roldão tomadas:** D-M3-1 = (A) buracos aceitos, D-M3-2 = (A) 72h/15d watchdog, D-M3-3 = (A) BPT bloqueia produção.
- **P4 FASE 1 (Schema) FECHADA:** 11 tabelas + 12 migrations aplicadas (T-OS-001..011):
  - `ordens_servico` (OS) + sequence global `os_numero_seq_global` (ADR-0056)
  - `atividade_da_os` + unique partial index INV-OS-CONC-001 + triggers desnormalização
  - `tipo_atividade_config` + seed 6 tipos x 9 tenants = 54 linhas
  - `consentimento_biometria_touch` (Padrão B + FK 1:1 → AceiteAtividade — INV-OS-CONSBIO-001)
  - `aceite_atividade` (Padrão B + trigger valida consentimento quando bio touch)
  - `evidencia_foto_atividade` (Padrão B append-only; UPDATE só revogado_em LGPD art. 18)
  - `evento_de_os` (append-only sanitizada — INV-OS-AUD-001)
  - `dispensa_aceite_atividade` (P-OS-A4 — precedente_tipo + A3 gerente)
  - `checklist_da_atividade` (Padrão A — estado por item)
  - `nao_conformidade_atividade` (5 campos CAPA P-OS-R5)
  - `sla_contrato` (vigência ADR-0030)
- ~40 policies RLS pattern v2 + ~10 triggers PG. Fix lateral: drift QR_IP_RATELIMIT_SALT pré-existente.

## Pendências rastreadas (não bloqueiam Marco 3 dogfooding)

- **T-OS-003..147** restantes em `docs/faseamento/M3-os/tasks.md` (12 fases).
- **51 GATEs Wave A** em `gates-wave-a-consolidado.md` + 9 GATEs novos do M3 (BPT, CONSBIO-OAB, ESCOPO-RBC, CAPA, FOTO-BLUR, SUCESSAO-EVIDENCIA, TENANT-SUSPENSO, INMETRO-PRAZO, CYBER-EO ampliados).
- **ADR-0018 PWA QR** + ADR-0019 Pilar 2 apólice (Marco 2 GATEs).

## P4 Fase 2 (Domain) FECHADA

`src/domain/operacao/os/` entregue — 5 arquivos puros sem Django:
- `value_objects.py`: 8 enums + `NumeroOSFormatado` + `MotivoCancelamento` (anti-PII estendida P-OS-A3 + palavras-chave saúde)
- `entities.py`: 11 Snapshot dataclasses frozen (DTOs imutáveis)
- `regras.py`: transições estado-máquina + INV-OS-ATIV-001/002/005 + INV-OS-FAT-001 + canonicalização ADR-0029
- `repository.py`: `OSRepository` Protocol (22 métodos DI)
- ruff verde + smoke test runtime OK + hooks 207/207

## Próximo passo

**P4 Fase 3 (Predicates authz)** — `src/infrastructure/authz/predicates_os.py` com 5 predicates: `rt_competencia_cobre`, `tenant_dentro_escopo_acreditado`, `pode_estender_janela_cal_link_atividade`, `pode_dispensar_aceite`, `pode_criar_os_produtiva_balancas`. Depois Fase 4 (consumers + sagas), Fase 5 (use cases — 15 US).
