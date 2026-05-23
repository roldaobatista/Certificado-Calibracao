# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** Foundation F-A+F-B FECHADAS · Marco 1 `clientes` FECHADO · Marco 2 `equipamentos` FECHADO · **Marco 3 `os`: P1+P2+P3 fechadas + P4 FASES 1+2+3 (Schema + Domain + Predicates authz) FECHADAS (2026-05-23).**
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-23 pós T-OS-023..028)

- Hooks `_test-runner.sh`: **207/207** verdes.
- ruff: All checks passed em `src/infrastructure/ordens_servico/`.
- makemigrations --check: limpo.
- migrate ordens_servico: 0001..0013 OK aplicadas.
- Subset `pytest -k authz`: **58 passed** (zero regressão authz).
- Smoke runtime predicates: 12 cenários PASS.

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

`src/domain/operacao/os/` — 5 arquivos puros sem Django: `value_objects.py` (8 enums + VOs anti-PII), `entities.py` (11 Snapshot frozen), `regras.py` (transições + INVs + canonicalização), `repository.py` (Protocol 22 métodos).

## P4 Fase 3 (Predicates authz + seed) FECHADA (2026-05-23)

`src/infrastructure/ordens_servico/predicates_os.py` — 5 predicates + registro `AppConfig.ready` com escopo declarado (T-FB-01):
- `rt_competencia_cobre` (T-OS-023) — INV-OS-ATIV-005-EXEC-COMP. Self-guard `grandeza` vazia → não aplica. Consulta `ResponsavelTecnicoTenant` + `RTCompetencia` por (tenant, user, grandeza, data).
- `tenant_dentro_escopo_acreditado` (T-OS-024) — STUB Wave A (GATE-RBC-ESCOPO-1). Contrato cravado; bloqueio duro entra com módulo `licencas-acreditacoes`.
- `pode_estender_janela_cal_link_atividade` (T-OS-025) — restringe a `gerente_operacional/rt_signatario/signatario/admin_tenant`.
- `pode_dispensar_aceite` (T-OS-026) — P-OS-A4. Exige precedente em `EventoDeOS` (no_show) ou `EvidenciaFotoAtividade` (recusa); `impossibilidade_tecnica` exige só autorização gerente (validada na camada de aplicação).
- `pode_criar_os_produtiva_balancas` (T-OS-027) — P-OS-S1 / GATE-SEG-BPT-1. Self-guard: só aplica ao tenant `balancas-solution`; consulta `FeatureFlag(OS_PRODUTIVO_DOGFOODING_BS)`.

`ordens_servico/migrations/0013_seed_authz_os.py` (T-OS-028) — 27 linhas perfil×ação (8 ações × 5 perfis seedados real: admin_tenant, gerente_operacional, atendente, metrologista_bancada, tecnico). Aplicada com `authz/0007_seed_perfis_marco_3_4`.

## Próximo passo

**P4 Fase 4 (Consumers + sagas)** — T-OS-029..039 (11 tarefas): consumers `Orcamento.Aprovado`, `Cliente.Anonimizado`, `Calibracao.Iniciada/Concluida`, `OS.Faturada/Paga`, `Tenant.Suspenso/Encerrado`, `Equipamento.Baixado/Descartado`, `Acreditacao.Vencida/Suspensa`, `EquipamentoRecebimento.Registrado` + 3 sagas (anonimização bloqueada, reabertura sucessão M&A, sync mobile LWW).
