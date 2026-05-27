---
adr: 0069
titulo: Bypass de competência ISO 17025 cl. 6.2 — 4 condições objetivas + 5%/mês + lock pós-aceite
owner: roldao
status: aceito
data: 2026-05-27
aceito-em: 2026-05-27
proposto-por: agente (auditoria 10 lentes pré-Wave A — L1#5 + L3-cl.6.2)
revisado-por: tech-lead-saas-regulado + consultor-rbc-iso17025 (offline)
bloqueia-fase: Wave A módulo `rh-frota-qualidade/treinamentos` US-TRE-007
depende-de: ADR-0026 (2ª conferência + independência RT — modelo análogo), ADR-0067 (perfil regulatório do tenant)
---

# ADR-0069 — Bypass de competência ISO 17025 cl. 6.2 (4 condições objetivas)

> **Status:** ACEITO 2026-05-27 (auditoria 10 lentes pré-Wave A — Onda PRE-A.2). Resolve achado **CRÍTICO L1#5** (AC-TRE-007-3 permite bypass com justificativa + aprovação gerente Qualidade sem ADR objetiva).

## 1. Problema

PRD `rh-frota-qualidade/treinamentos` AC-TRE-007-3 declara: *"sistema bloqueia técnico sem NR válida; bypass exige justificativa + aprovação do gerente Qualidade"*. Mesma classe de risco que ADR-0026 já resolveu pra 2ª conferência: **bypass arbitrário não é admitido pela ISO 17025 cl. 6.2**. Sem ADR objetiva declarando as condições, CGCRE em supervisão pergunta "por que esse técnico calibrou X em 2026-03-15 sem o treinamento Y vigente?" e tenant não tem resposta documentável.

## 2. Decisão (paralela ao padrão ADR-0026)

### 2.1 Quatro condições objetivas (TODAS obrigatórias) pra bypass de competência

Bypass de competência só é aceito se **TODAS** as 4 condições simultâneas:

1. **Supervisão presencial documentada:** outro técnico do mesmo tenant com `RTCompetencia.{grandeza, metodo}` vigente acompanha presencialmente a atividade. Registro em `Atividade.supervisor_presencial_id` + foto da bancada com 2 pessoas (timestamp ≤15min do início da atividade).
2. **Treinamento expirado há ≤ 90 dias:** se NR/treinamento vencido há mais de 90 dias, bypass NÃO é admitido. Tem que renovar antes.
3. **Justificativa categorizada em enum** (não texto livre): `EMERGENCIA_OPERACIONAL_CLIENTE` / `TREINAMENTO_AGENDADO_ATE_DATA` / `SUBSTITUICAO_TEMPORARIA_RT_ATIVO`. Cada uma vincula evidência mínima diferente.
4. **A3 do gestor de qualidade** registrando bypass — não basta clique de aprovação. Gestor responde solidariamente.

### 2.2 Cota mensal — 5% das atividades

Mesmo cumpridas as 4 condições, tenant não pode acumular mais de **5% das atividades calibração/OS do mês** em bypass. Cota acumulativa rolling 30d. Atingiu 5% → bloqueio duro até proximo mês (mesmo se condições 1-4 OK).

### 2.3 Lock pós-aceite

Atividade marcada como `competencia_bypass=True` é **imutável** após `Atividade.aceita_pelo_cliente_em`. Auditoria CGCRE consegue contar todos os bypass nos últimos 5 anos.

### 2.4 Matriz feature × perfil ADR-0067

- **Perfil A (RBC acreditado):** cota 5%/mês + 4 condições. Bypass > 2 meses consecutivos com cota cheia dispara notificação CGCRE síncrona.
- **Perfil B (rastreável):** cota 10%/mês + 4 condições (tolerância maior — sem CGCRE).
- **Perfil C (em preparação RBC):** mesmas regras do A (treinamento).
- **Perfil D (comercial puro):** cota 20%/mês + condição 3 (justificativa enum) + condição 4 (A3 gestor). Condições 1+2 OPCIONAIS (sem ISO 17025 envolvido).

## 3. INVs novas

- **INV-COMP-BYPASS-001** — bypass exige TODAS as 4 condições registradas (perfil A/B/C) ou 2 (perfil D).
- **INV-COMP-BYPASS-002** — cota mensal por perfil enforced em hook pre-commit + DB trigger.
- **INV-COMP-BYPASS-003** — atividade com bypass imutável pós-aceite cliente.
- **INV-COMP-BYPASS-004** — bypass perfil A > 2 meses dispara consumer `Tenant.BypassRecorrente → NotificacaoCGCRE`.

## 4. Bloqueios desbloqueados

- L1#5 (TRE-007 bypass sem ADR objetiva): FECHADO.
- L3-cl.6.2 (RBC pergunta "por que esse técnico calibrou X sem treinamento"): tenant tem trilha.
- US-TRE-007 do PRD `treinamentos` ganha base normativa pra reescrever AC binário (caminho crítico Sprint 3 Wave A).

## 5. Tarefas Wave A bloqueantes (T-COMP-BYPASS-001..008)

1. T-COMP-BYPASS-001 — migration `Atividade.competencia_bypass` + 4 colunas (`supervisor_presencial_id`, `justificativa_enum`, `a3_gestor_id`, `treinamento_dias_expirado`).
2. T-COMP-BYPASS-002 — use case `aplicar_bypass_competencia(atividade_id, ...)` validando 4 condições + cota mensal.
3. T-COMP-BYPASS-003 — predicate `cota_bypass_mensal_excedida_por_perfil(tenant_id)` com perfil-aware.
4. T-COMP-BYPASS-004 — hook `migration-bypass-cota-perfil-validator`.
5. T-COMP-BYPASS-005 — consumer `Tenant.BypassRecorrente`.
6. T-COMP-BYPASS-006 — admin Django + endpoint REST.
7. T-COMP-BYPASS-007 — dashboard "% bypass no mês" por perfil (5/10/20%).
8. T-COMP-BYPASS-008 — 8 testes regressão (INVs + matriz perfil + cota cheia).

## 6. Non-goals

- Bypass de competência por delegação cross-tenant (RT vendor) — V2.
- Cota anual além da mensal — V2 se demanda real.
- Bypass automático por "emergência sistema indisponível" — vetado por design (CGCRE não aceita justificativa de outage).
