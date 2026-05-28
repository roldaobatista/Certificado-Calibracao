---
owner: roldao
revisado-em: 2026-05-28
status: draft
fase: M5-padroes
dominio: metrologia
modulo: padroes
ritual: specify
versao: 1
fontes:
  - docs/dominios/metrologia/modulos/padroes/prd.md (stable v2)
  - docs/dominios/metrologia/modulos/padroes/modelo-de-dominio.md (draft v1)
adrs:
  - 0002 (RLS) / 0007 (codegen) / 0022 v2 (RT competência) / 0025 v2 (validação software)
  - 0030 (vigência canônica) / 0031 (soft-delete B) / 0040 (padrão entidade separada)
  - 0064 (HMAC 25a) / 0066 (fail-open lazy) / 0067 (perfil) / 0068 (sucessão RT)
---

# Spec de faseamento — M5 `metrologia/padroes` (1º módulo Wave A)

> **Ritual (memória `feedback_ritual_orquestrador`):** este é o passo `/specify`.
> Próximos passos OBRIGATÓRIOS antes de qualquer código: `plan` revisado pelos
> 4 subagentes (`tech-lead-saas-regulado`, `consultor-rbc-iso17025`,
> `advogado-saas-regulado`, `corretora-seguros-saas`) → `tasks` → `implement`
> → 10 auditores Família 5. **Nada de código antes do plan revisado.**
>
> **Por que este módulo abre a Wave A:** ADR-0040 separa o padrão metrológico
> do equipamento do cliente. `padroes` destrava INV-002 (cadeia de
> rastreabilidade na emissão de cert), INV-011 (cert bloqueia se padrão tem cal
> vencida), INV-021..023 (classe + VI + PT) e a porta
> `PadraoMetrologicoQueryService` que o Marco 4 (`calibracao`, já fechado)
> consome via adapter vazio hoje. Também destrava o ViewSet T-CAL-130
> (`PadraoViewSet`), que ficou pendente sem use cases na Onda 4.

## 1. Objetivo

Construir o cadastro e o ciclo de vida dos **padrões metrológicos do
laboratório do tenant** (pesos OIML R111, termômetros/manômetros padrão,
blocos padrão, padrões elétricos), com rastreabilidade ao SI, recal externo
periódico, verificação intermediária (cl. 6.4.10), intercomparação PT
(perfil A — cl. 6.6), cartas controle Shewhart (perfil A), equipamentos
auxiliares (cl. 6.4.5) e 2º caminho de cálculo do valor convencional
(ADR-0025 v2). Tudo perfil-aware (ADR-0067) e WORM auditável 25a (ADR-0064).

## 2. Escopo (deriva do PRD §5 — não duplicar AC aqui)

- CRUD de `PadraoMetrologico` (UNIQUE `(tenant_id, numero_serie)`).
- Recal externo (envio → retorno; update transacional de incertezas/validade
  só via evento `padrao.recal_externo_concluido`).
- Verificação intermediária periódica (bloqueia uso se REPROVADO).
- Intercomparação PT (perfil A).
- Cartas controle Shewhart + regras Western Electric (perfil A).
- Equipamentos auxiliares cl. 6.4.5 (subtipo `AUXILIAR`).
- 2º caminho de cálculo do valor convencional (ADR-0025 v2).
- Baixa/sucatamento (soft-delete padrão B WORM).
- Porta `PadraoMetrologicoQueryService` consumida pelo Marco 4.
- Exportação dossiê CGCRE — **só dados estruturados (JSON)**; PDF/A é Wave B+.

## 3. Non-goals (deriva do PRD §6 — explícito)

NÃO: calibração interna de padrão; padrão emprestado/alugado; emissão de cert
(é Marco 4 + `certificados`); modelar equipamento do cliente; PDF/A do dossiê;
scanner QR de padrão; substituir SGQ ISO 9001.

## 4. Entidades + agregado (deriva do modelo-de-domínio)

**Agregado raiz `PadraoMetrologico`** + filhas `RecalExternoPadrao`,
`VerificacaoIntermediaria`, `IntercomparacaoPT`. Estados:
`EM_USO` ↔ `EM_RECAL_EXTERNO` ↔ `INTERCOMPARACAO_PT_EM_CURSO` →
`BAIXADO` (reversível) / `SUCATEADO` (terminal). Soft-delete padrão B
(`revogado_em` + `motivo_revogacao`; DELETE bloqueado por trigger PG —
ADR-0031/INV-SOFT-002). Vigência canônica ADR-0030.

VOs reusados de `src/domain/metrologia/value_objects.py`: `Grandeza`,
`FaixaMedicao`, `IncertezaExpandida`. **Não recriar.**

Subtipo `AUXILIAR` (US-PAD-007) no mesmo agregado (`subtipo` discrimina
`PRINCIPAL` vs `AUXILIAR_AMBIENTAL`/`AUXILIAR_ELETRICO`/`AUXILIAR_TERMOMETRICO`).

Cartas Shewhart (US-PAD-008): derivadas das VIs/recals — **read-model
calculado**, não entidade persistida nova (pontos vêm de
`VerificacaoIntermediaria` + `RecalExternoPadrao`). Decisão a confirmar no
`plan` com `consultor-rbc-iso17025` (vs persistir pontos).

## 5. User Stories → mapa de implementação (AC detalhado no PRD §7)

| US | Tema | Bloqueia | Perfil |
|----|------|----------|--------|
| US-PAD-001 | Cadastrar padrão | porta M4 + T-CAL-130 | A/B/C/D (RBC→A) |
| US-PAD-002 | Recal externo (envio+retorno) | INV-002 cadeia | todos |
| US-PAD-003 | Verificação intermediária | INV-022 | todos |
| US-PAD-004 | Baixar/sucatar | — | todos |
| US-PAD-005 | Intercomparação PT | INV-023 | **A** |
| US-PAD-006 | Dossiê CGCRE (JSON) | supervisão | **A** |
| US-PAD-007 | Equipamentos auxiliares cl. 6.4.5 | L3#7 crítico | todos |
| US-PAD-008 | Cartas controle Shewhart | L3#A9 | **A** |
| US-PAD-009 | 2º caminho valor convencional | ADR-0025 v2 | A/B |

## 6. Invariantes (a cravar em REGRAS-INEGOCIÁVEIS no `implement`)

- **INV-PAD-001** — UNIQUE `(tenant_id, numero_serie)`.
- **INV-PAD-002** — cadastro exige incerteza + valor convencional (NIT-DICLA-030 item 8.2.6).
- **INV-PAD-003** — baixa/sucatamento bloqueada se calibração em curso usa o padrão.
- **INV-PAD-005** — `vinculacao=RBC` exige `tenant_perfil_e(["A"])` (ADR-0067).
- **INV-PAD-006** — `incertezas_certificado` só muta via evento `padrao.recal_externo_concluido` (trigger PG).
- **INV-PAD-007** — equipamento auxiliar com calibração vencida bloqueia uso do padrão principal que o consome (US-PAD-007).
- **INV-PAD-008** — cartas Shewhart exclusivas perfil A.
- **INV-PAD-009** — 2º caminho de cálculo obrigatório (perfil A/B) com investigação se desvio > k·u_combined.
- **Reusadas:** INV-021..023, INV-CAL-SNAP-001, INV-CAL-RAST-001, INV-CAL-VI-001,
  INV-CAL-WORM-001, INV-VIG-001..004, INV-SOFT-001/002, INV-HMAC-001..005,
  INV-PERFIL-001, INV-VAL-001, INV-TENANT-001.

## 7. Porta exposta (crítica — porta NOVA; M4 hoje só tem `padrao_id` solto)

> **Correção pós-review tech-lead (C-6 drift-docs):** `EmptyPadraoMetrologicoQueryService`
> **não existe no código** — só em docs/ADR-0040 (proposta). O M4 fechado só
> persiste `PadraoUsado.padrao_id` solto (`models.py:1151`) +
> `ComponenteIncerteza.fonte_default_padrao_id` (`:1006`), SEM porta plugada e
> SEM validar disponibilidade. Logo a porta é **nova adição**, não substituição.

Porta read-only como **funções de módulo** em `query_service.py` (estilo
`certificados/query_service.py` — padrão real do projeto), NÃO Protocol+adapter
injetado: `buscar_disponivel_para_calibracao`, `snapshot_para_uso` (retorna
`PadraoUsadoSnapshot` imutável — INV-CAL-SNAP-001), `padrao_bloqueado_para_uso`
(**fail-CLOSED** — padrão é barreira de segurança metrológica; NÃO replicar
fail-open ADR-0063/0066).
**GATE-PAD-PORTA-M4:** M4 passa a CHAMAR `padrao_bloqueado_para_uso` antes de
gravar `PadraoUsado` (adição) + **testes NOVOS** do caminho bloqueado (a suíte
629 não cobre — não há padrão real hoje) + suíte 629 reverde.

## 8. Eventos (hash-chain HMAC ADR-0064 — ver modelo §Eventos)

8 eventos `padrao.*` (cadastrado, recal_externo_iniciado/concluido,
verificacao_intermediaria_registrada, intercomparacao_iniciada/concluida,
baixado, sucateado). Sanitização na escrita (INV-CAL-AUD-001 pattern): sem
`localizacao_lab` em claro, sem cert PDF em claro, `responsavel_envio` só hash.
`perfil_no_evento` no envelope (Sprint 4 SAN-PERFIL / INT-03).

## 9. Faseamento proposto (detalhar no `tasks` pós-`plan`)

- **P1 — Domínio puro:** entidades + VOs + enums + máquina de estados +
  invariantes puras (sem Django). Testes de domínio.
- **P2 — Schema + migrations:** `padrao_metrologico` + 3 filhas + RLS pattern v2
  + triggers WORM (INV-PAD-006, INV-SOFT-002) + UNIQUE + extensões já presentes.
- **P3 — Use cases:** cadastrar / recal (envio+retorno) / VI / PT / baixar /
  sucatar / 2º caminho cálculo / Shewhart read-model. Helpers crypto HMAC reuso.
- **P4 — Porta + adapter Django** (`PadraoMetrologicoQueryService` real) +
  **GATE-PAD-PORTA-M4** (Marco 4 reverde).
- **P5 — REST:** `PadraoViewSet` (T-CAL-130 — 6 POSTs) + serializers + urls +
  paginação F-C3 herdada.
- **P6 — Jobs procrastinate:** alerta recal vencendo (P2), VI pendente (P2),
  recal pendente > 90d (P2).
- **P7 — Hooks/INV:** cravar INV-PAD-* em REGRAS + hooks (incertezas-só-via-recal,
  auxiliar-em-controle, shewhart-perfil-A).
- **P8 — Reconciliação + drill** `validar_m5_padroes` (estrutural + PG real
  GATE-PAD-DRILL-LOCAL).
- **P9 — Ritual auditores:** 10 auditores Família 5; INV-RITUAL-001 (MÉDIO+ bloqueia).

## 10. Gates

- **GATE-PAD-PORTA-M4** — adapter real plugado no Marco 4 + suíte M4 reverde.
- **GATE-CAL-CMC-PREDICATE / GATE-CAL-PROC-VIGENTE-PREDICATE** (ADR-0066) —
  destravam quando `escopos-cmc` + `procedimentos` (próximos módulos Wave A)
  existirem; `padroes` não os fecha sozinho.
- **GATE-PAD-DRILL-LOCAL** — drill PG real (conexão real, RLS, triggers WORM).
- **GATE-PAD-SHEWHART-RBC** — texto/estatística Shewhart revisado por
  `consultor-rbc-iso17025` (Western Electric correto).

## 11. Critérios de validação (drill `validar_m5_padroes`)

Estrutural (sem PG): entidades + invariantes puras + máquina de estados +
porta declarada. PG real (GATE-PAD-DRILL-LOCAL): UNIQUE + RLS isolamento
cross-tenant + trigger INV-PAD-006 (UPDATE direto bloqueado) + trigger
soft-delete + recal transacional + perfil A bloqueia RBC em B/C/D.

## 12. Dependências e ordem na Wave A

`padroes` é **paralelo a `calibracao` (M4 fechado)** e **pré-requisito** de:
- `escopos-cmc` (CMC referencia padrões) — próximo.
- `procedimentos-calibracao` — próximo.
- T-CAL-130 `PadraoViewSet` (consome use cases deste módulo).
- Fechamento real dos predicates `cmc_cobre` / `procedimento_vigente_para`
  (ADR-0066) depende de `escopos-cmc` + `procedimentos`, não de `padroes`.

## 13. Próximo passo do ritual

`plan` (M5-padroes/plan.md) com revisão dos 4 subagentes — em especial
`consultor-rbc-iso17025` (Shewhart + Western Electric + 2º caminho de cálculo +
cl. 6.4.5/6.4.10/6.6) e `tech-lead-saas-regulado` (porta M4 + concorrência +
triggers WORM). **Sem código antes do plan aprovado.**
