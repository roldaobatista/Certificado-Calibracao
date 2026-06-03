---
owner: agente-ia
revisado-em: 2026-06-01
proximo-review: 2026-09-01
status: stable
diataxis: reference
audiencia: [agente, auditor]
marco: M9-licencas-acreditacoes
tipo: tasks-faseamento
relacionados:
  - docs/faseamento/M9-licencas-acreditacoes/plan.md
  - docs/faseamento/M9-licencas-acreditacoes/spec.md
---

# Tasks — M9 `metrologia/licencas-acreditacoes`

> Geradas do `plan.md` (D-LIC-1..10 + ADR-0079). Ordem por dependência (evita retrabalho).
> Path aninhado ADR-0072 `src/{domain,infrastructure}/metrologia/licencas_acreditacoes/`.

## Fatia 1a — domínio puro (sem Django)

| ID | Tarefa | Cobre |
|----|--------|-------|
| T-LIC-010 | `domain/.../enums.py`: `TipoDocumentoRegulatorio` (12 tipos) + `MotivoRevisao` + `StatusDocumento` (calculado) + `CanalAlerta` + `StatusAlerta` + `TipoBloqueio` (REBAIXA_RBC vs HARD_409 — D-LIC-5) + properties | enums |
| T-LIC-011 | `domain/.../erros.py`: `LicencaError` base + `AnexoObrigatorioError` (INV-LIC-ANEXO-001) + `PerfilNaoAutorizaCGCREError` (INV-LIC-PERFIL-001) + `DocumentoBloqueanteVencidoError` (409 — D-LIC-5b) + `ModoEmergencialInvalidoError` + `TransicaoLicencaInvalidaError` + `VigenciaInvalidaError` | erros |
| T-LIC-012 | `domain/.../entities.py`: `DocumentoRegulatorio` (raiz) + `RevisaoDocumento` + `AlertaVencimento` + `BloqueioOperacional` + `EventoEmergencial` (frozen dataclasses, vigência canônica ADR-0030, `ReferenciaPIIAnonimizavel` p/ titular ART/RRT) | INV-046/032/033 + ADR-0030/0031 |
| T-LIC-013 | `domain/.../transicoes.py`: `calcular_status(vigencia_fim, hoje, em_renovacao)` + `validar_tipo_x_perfil(tipo, perfil)` (D-LIC-10/RBC-M9-06) + `validar_anexo(sha256)` + `fronteira_bloqueio(tipo)` (REBAIXA vs HARD — D-LIC-5) + `validar_modo_emergencial(justificativa, a3_id, tipo)` (D-LIC-6/7, libera só não-RBC p/ CGCRE) + `exigir_transicao` WORM | INV-LIC-* |
| T-LIC-014 | `domain/.../repository.py`: Protocols `DocumentoRegulatorioRepository` + `RevisaoRepository` + `AlertaRepository` + `BloqueioRepository` | portas |
| T-LIC-015 | `tests/test_m9_licencas_dominio_p1.py`: testes puros (status calculado nas 4 bordas; tipo×perfil A/B/C/D incl. D rejeita CGCRE; anexo obrigatório; fronteira REBAIXA vs HARD por tipo; modo emergencial CGCRE→só não-RBC; vigência inválida) | TST-004 |

## Fatia 1b — schema + ADR-0079 (PG real)

| ID | Tarefa |
|----|--------|
| T-LIC-020 | migrations `infrastructure/metrologia/licencas_acreditacoes/`: tabelas + RLS v2 + WORM Padrão B (triggers anti-mutação RevisaoDocumento/EventoEmergencial) + grants app_user + seed authz + UNIQUE idempotência alertas `(tenant, documento, janela_dias)` |
| T-LIC-021 | mappers + repositories Django aninhados + `query_service.py` (`vigente_para_rbc`) |
| T-LIC-022 | drill `validar_licencas_acreditacoes` (colunas + RLS + triggers WORM + grants) |
| T-LIC-023 | **promover ADR-0079 a aceito** (§11 AGENTS) + teste schema PG-real |

## Fatia 1c — extensão função tenant (D-LIC-2/3/8 — TL-M9-01)

| ID | Tarefa |
|----|--------|
| T-LIC-030 | migration `tenant/0012`: `CREATE OR REPLACE aplicar_evento_cgcre` (+ `p_acreditacao_vigencia_inicio/fim` + direção `renovacao_vigencia_cgcre`) — aditivo, backward-compat |
| T-LIC-031 | estender hook `tenant-perfil-imutavel-check.sh` (bloqueia UPDATE direto em `acreditacao_vigencia_*`/`cgcre_numero`/`suspensa_*`/`ilac_mra`) + casos `_test-runner` |
| T-LIC-032 | testes da função (vigência setada via param; `renovacao_vigencia_cgcre` não muda perfil; UPDATE direto bloqueado pelo hook) |

## Fatia 2 — use cases + REST

| ID | Tarefa |
|----|--------|
| T-LIC-040 | `application/.../cadastrar_documento_regulatorio.py` (perfil-aware `tenant_perfil_e(['A','B','C'])` + anexo sha256 + status) |
| T-LIC-041 | `promover_perfil_a.py` — transação atômica D-LIC-4 (INSERT Licenca + `aplicar_evento_cgcre` raw cursor mesma transação + advisory lock + idempotência composta) |
| T-LIC-042 | `renovar_documento.py` (nova revisão + `renovacao_vigencia_cgcre` p/ CGCRE + resolve bloqueio) |
| T-LIC-043 | `acionar_modo_emergencial.py` (D-LIC-6/7 — a3_id + justif ≥100ch + ≤7d + WORM; CGCRE libera só não-RBC) |
| T-LIC-044 | `DocumentoRegulatorioViewSet` REST (CRUD + ações) + serializers + Idempotency-Key + eventos WORM |

## Fatia 3 — sync + porta + job (fecha gate)

| ID | Tarefa |
|----|--------|
| T-LIC-050 | sincronização `Licenca`(CGCRE)→cache via função (no cadastrar/renovar) + `query_service.vigente_para_rbc` (API interna) |
| T-LIC-051 | job `verificar_alertas_licencas` (D-90/60/30/15/7) + refino job perfil A |
| T-LIC-052 | **teste não-drift** `tests/test_licencas_nao_drift.py` (cache == fonte tenant A) — **fecha GATE-CER-CGCRE-VIG-DATA-POPULAR + GATE-LIC-DRIFT** + reverde M8 (cert RBC com vigência populada rebaixa real) |

## Fatia 4 — histórico + ART/RRT + P7

| ID | Tarefa |
|----|--------|
| T-LIC-060 | US-LIC-004 histórico (revisão imutável + listagem) + US-LIC-005 ART/RRT (tipo + vínculo RT + 409 hard D-LIC-5b) |
| T-LIC-061 | família `INV-LIC-*` em REGRAS + **reconciliar INV-033 ≥50→≥100ch** (D-LIC-7) + `TestINV_LIC_*` |
| T-LIC-062 | 3 hooks: `lic-anexo-obrigatorio-check` + `lic-perfil-cgcre-check` + `lic-emergencial-a3-check` + casos `_test-runner` |
| T-LIC-063 | retenção-matriz (D-LIC-9, espelho T-PAD-071) |

## P8/P9

| ID | Tarefa |
|----|--------|
| T-LIC-070 | matriz-reconciliacao (molde M7) + emenda PRD (AC-LIC-003-1 fronteiras D-LIC-5) + URS (ADR-0025 v2) |
| T-LIC-080 | P9 auditores roteados (INV-RITUAL-003) + verificação adversarial — MÉDIO+ bloqueia |

## Veredito
`ready-for-implement`. Ordem por dependência cravada. **Próximo:** implement Fatia 1a (T-LIC-010..015).
