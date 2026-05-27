---
owner: roldao
status: stable
revisado-em: 2026-05-27
proximo_review: 2026-08-27
diataxis: explanation
audiencia: agente
marco: Saneamento pré-Wave A — perfil regulatório do tenant
tipo: plan-ritual-spec-kit-P2-P3
relacionados:
  - docs/faseamento/SAN-PERFIL-TENANT/spec.md
  - docs/faseamento/SAN-PERFIL-TENANT/reviews/tech-lead.md
  - docs/faseamento/SAN-PERFIL-TENANT/reviews/advogado.md
  - docs/faseamento/SAN-PERFIL-TENANT/reviews/corretora.md
  - docs/faseamento/SAN-PERFIL-TENANT/reviews/rbc.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
---

# Saneamento perfil regulatório do tenant — Plan P2/P3 (4 reviews paralelos)

> **P2 do ritual Spec Kit (2026-05-27):** spec FORWARD criada em P1 (`spec.md`) foi revisada em PARALELO pelos 4 subagentes humano-substitutos: `tech-lead-saas-regulado`, `advogado-saas-regulado`, `corretora-seguros-saas`, `consultor-rbc-iso17025`. Esta ata registra as decisões absorvidas — **13 BLOQUEANTES viram correções na spec; 17 MÉDIOs (INV-RITUAL-001) viram ACs/INVs; 10 ALTOs viram GATEs Wave A; 1 ACEITE registra risco**.

## Sumário dos vereditos

| Revisor | BLOQUEANTE | MÉDIO INV-RITUAL-001 | ALTO Wave A / GATE | ACEITE | Total |
|---|---|---|---|---|---|
| `tech-lead-saas-regulado` | 5 (T1, T2, T3, T4, T6) | 6 (T7, T8, T9, T10, T11, T12) | 3 (T5, T13, T14) | 1 (T15) | 15 |
| `advogado-saas-regulado` | 3 (A1, A2, A3) | 3 (A6, A7, A8) | 2 (A4, A5) | 0 | 8 |
| `corretora-seguros-saas` | 2 (S1, S2) | 3 (S6, S7, S8) | 3 (S3, S4, S5) | 0 | 8 |
| `consultor-rbc-iso17025` | 3 (R1, R3, R10) | 5 (R2, R5, R6, R8, R9) | 2 (R4, R7) | 0 | 10 |
| **Total** | **13** | **17** | **10** | **1** | **41** |

**Densidade vs M4 calibração:** M4 produziu 45 achados em P2; este saneamento produziu **41 — densidade equivalente**. Coerente: saneamento toca schema fundador + 4 lentes (RBC + LGPD + seguros + arquitetura).

**Convergências cross-revisor:**
- **PDF certificado CGCRE no provisionamento A** — A5 (advogado) ↔ S4 (corretora). Decisão única: AC retrofitado em US-SAN-PERFIL-004.
- **Mudança de retenção 5a↔25a** — A3 (LGPD aviso titular) ↔ R10 (HMAC 25a invariante) ↔ S6 (Cyber diferenciado). Decisão única: matriz de retenção explícita com camadas (PII em PII vs hash-chain WORM).
- **Webhook out / evento de mudança de perfil** — S2 (corretora material change) ↔ A3 (notificar titular) ↔ T9 (snapshot WORM). Decisão única: evento `TenantPerfilAlterado` em outbox transacional + 3 consumers (corretora SUSEP, notificar titular, atualizar snapshot).

---

## Decisões absorvidas na spec (retrofit pré-P3)

### Bloco A — Schema & integridade (tech-lead + RBC)

#### P-SAN-T1 — Schema multi-step com ADD NULL → backfill → SET NOT NULL (BLOQUEANTE)

**Análise:** spec original tinha "Migration adiciona coluna NOT NULL" em 1 step. Quebra ambientes mid-migration (Balanças Solution + tenants de teste com linhas existentes).

**Decisão:** AC-SAN-PERFIL-001-1 vira 3 ACs sequenciais (001-1a, 001-1b, 001-1c):
- `001-1a` — migration `tenant/0003_perfil_regulatorio_add_nullable.py` faz `ADD COLUMN perfil_regulatorio CHAR(1) NULL`.
- `001-1b` — migration `tenant/0004_perfil_regulatorio_backfill.py` faz `RunPython` lendo `Tenant.objects.select_for_update().all()` + INSERT em `TenantPerfilHistorico` com `direcao=PROVISIONAMENTO_INICIAL`.
- `001-1c` — migration `tenant/0005_perfil_regulatorio_not_null.py` faz `ALTER COLUMN perfil_regulatorio SET NOT NULL` + adiciona `CHECK (perfil_regulatorio IN ('A','B','C','D'))`.

Cada step idempotente. Se 1b falhar, sistema continua funcionando com NULL (degraded, mas operável).

#### P-SAN-R1 — Acreditação CGCRE é por ESCOPO, não por empresa (BLOQUEANTE)

**Análise:** CGCRE acredita escopo `(grandeza × faixa × incerteza CMC × procedimento × padrão)`, não a empresa. Lab típico tem 3-15 escopos com vigências distintas; ampliação parcial é regra. Coluna escalar `acreditacao_vigencia_fim` em `Tenant` quebra na 1ª ampliação real.

**Decisão:** REMOVER de `Tenant` as colunas `acreditacao_vigencia_inicio` e `acreditacao_vigencia_fim`. Mantém apenas:
- `Tenant.perfil_regulatorio` (cache do perfil agregado — fonte do predicate)
- `Tenant.acreditacao_cgcre_numero` (cache do número RBC principal — display)
- `Tenant.acreditacao_suspensa_em` (DATE NULL — preenchido em suspensão temporária)
- `Tenant.acreditacao_suspensa_ate` (DATE NULL — fim previsto da suspensão)
- `Tenant.ilac_mra_aderido` (BOOLEAN NOT NULL DEFAULT FALSE — RBC R9)

Vigência por escopo **migra para módulo `licencas-acreditacoes` Wave A** com entidade `EscopoAcreditado(grandeza, faixa_min, faixa_max, incerteza_cmc, vigencia_inicio, vigencia_fim, procedimento_id, padrao_id)`. Predicate `tenant_perfil_e({"A"})` continua aqui; predicate `escopo_cgcre_cobre(grandeza, faixa)` fica em `licencas-acreditacoes` com **fail-open lazy** (padrão ADR-0063/0066) até módulo entrar em vigor.

AC-SAN-PERFIL-002-3 atualizada: `emitir_certificado_rbc` exige `tenant_perfil_e({"A"})` AND `acreditacao_suspensa_em IS NULL OR today > acreditacao_suspensa_ate` AND delega vigência por escopo a `escopo_cgcre_cobre(...)` (fail-open lazy).

**Non-goal adicionado §2.2:** "Modelagem de escopo CGCRE (grandeza × faixa × CMC × vigência por escopo) é responsabilidade do módulo `licencas-acreditacoes` Wave A."

#### P-SAN-R3 — Suspensão temporária ≠ cancelamento ≠ redução escopo (BLOQUEANTE)

**Análise:** NIT-DICLA-005 §7.4 distingue 3 fluxos distintos:
- Suspensão temporária (1-180 dias, lab CESSA emissão mas mantém status A na CGCRE — pode reabilitar sem nova auditoria).
- Cancelamento (lab perde acreditação, vira ex-A → B).
- Redução de escopo (perde grandeza X mas mantém Y — não muda perfil).

Spec original colapsa em 1 fluxo `REBAIXAMENTO_POR_SUSPENSAO_CGCRE`.

**Decisão:** Enum `TenantPerfilHistorico.direcao` expandido:
- `PROVISIONAMENTO_INICIAL`
- `PROMOCAO_REGULATORIA`
- `SUSPENSAO_TEMPORARIA_CGCRE` (preserva perfil A; seta `acreditacao_suspensa_em/ate`)
- `CANCELAMENTO_CGCRE` (rebaixa A→B)
- `REDUCAO_ESCOPO_CGCRE` (não muda perfil; atualiza escopos em `licencas-acreditacoes`)
- `CORRECAO_ADMINISTRATIVA`
- `REBAIXAMENTO_VOLUNTARIO_CLIENTE` (novo — vide P-SAN-A1)

Função SECURITY DEFINER renomeada: `rebaixar_perfil_tenant_por_suspensao_cgcre` → `aplicar_evento_cgcre(direcao, ...)` com lógica de máquina de estados.

AC-SAN-PERFIL-002-7 novo: predicate `tenant_perfil_e({"A"})` retorna False se `acreditacao_suspensa_em IS NOT NULL AND today < acreditacao_suspensa_ate`.

#### P-SAN-R10 — Retenção HMAC 25a invariante vs PII por perfil (BLOQUEANTE)

**Análise:** ADR-0064 (aceita) fixa HMAC rotação anual + KMS 25a como INVARIANTE (INV-HMAC-001..005, hook ativo). Spec original dizia "perfil D → retenção 5a" sem distinguir camadas — entrava em conflito.

**Decisão:** AC-SAN-PERFIL-005-4 matriz de retenção ganha 2 dimensões explícitas:

| Camada | A | B | C | D |
|---|---|---|---|---|
| **PII de cliente / titular** (ADR-0021 zona A/B/C) | 25a (ISO 8.4) | 25a (recomendado) | 25a | **5a (Receita)** + anonimização |
| **Eventos WORM hash-chain** (INV-HMAC-001..005) | 25a (invariante) | 25a (invariante) | 25a (invariante) | **25a (invariante)** |
| **Geo-truncamento** (job `geo_truncamento_calibracao_5a`) | NUNCA trunca | 5a | 5a | 5a + anonimização |

Hash-chain WORM SEMPRE 25a (INV-HMAC vence). PII de cliente perfil D pode ser anonimizada em 5a — eventos antigos continuam verificáveis hash-chain, mas PII referenciada substituída por hash. Documentar em ADR-0021 §novo "Camadas de retenção condicional por perfil".

#### P-SAN-T2 — Predicate ContextVar + timeout 50ms + fail-closed (BLOQUEANTE)

**Análise:** INV-TENANT-PERFIL-004 "DB indisponível → DENY" conflita com graceful degradation. PG hiccup de 200ms = derruba tenant inteiro. Sem cache, N+1 a cada use case.

**Decisão:** AC-SAN-PERFIL-002-5 reescrito:
- Predicate consulta `Tenant.perfil_regulatorio` via cache do middleware (`perfil_tenant_context: ContextVar[str]` populado em `TenantMiddleware`).
- Cache miss = re-fetch com `select_for_share` + timeout 50ms.
- Timeout/erro = DENY com reason `tenant_perfil_indisponivel` + log WARN.
- Linha encontrada com `perfil_regulatorio IS NULL` (estado inválido pós-backfill) = DENY com reason `tenant_perfil_nao_definido` + log ERROR + alerta.
- NÃO usa retry/circuit-breaker — caller decide.

AC-SAN-PERFIL-002-8 novo: "Predicate é consultado UMA vez por request via ContextVar — elimina N+1."

#### P-SAN-T3 — Plano de migração de 67 testes M4 + compat-shim (BLOQUEANTE)

**Análise:** retrofit `cmc_cobre` quebra 67 ocorrências em testes + 8 arquivos de aplicação. Sem plano explícito = suite vermelha = INV-RITUAL-001 violado (mascaramento causa-raiz proibido).

**Decisão:** US-SAN-PERFIL-006 nova no Sprint 2:

> **Como** mantenedor da suite,
> **Quero** que a migração para o predicate canônico não quebre a suite 629/629,
> **Para** preservar INV-RITUAL-001 (causa-raiz, nunca mascarar).

- **AC-SAN-PERFIL-006-1** — Fixture `tenant_a/b/c/d` em `conftest.py` raiz; `TenantFactory` ganha traits factory-boy `.perfil_a()` `.perfil_b()` `.perfil_c()` `.perfil_d()`.
- **AC-SAN-PERFIL-006-2** — Testes M4 que literalizam `tipo_acreditacao=RBC` no payload retrofitados para usar fixture `tenant_a`.
- **AC-SAN-PERFIL-006-3** — Compat-shim: se payload ainda mandar `tipo_acreditacao`, predicate IGNORA e loga WARN `payload_tipo_acreditacao_obsoleto`. Compat-shim vigora por 1 Marco (Sprint 2 → fim de Wave A módulo `certificados`).
- **AC-SAN-PERFIL-006-4** — Hook novo `payload-tipo-acreditacao-obsoleto-check` bloqueia commit de código novo que use o campo.
- **AC-SAN-PERFIL-006-5** — Marcador `@pytest.mark.perfil("A")` + parametrize matrix em testes que tocam regras ISO 17025 (mínimo 40 testes M4 retrofitados).

#### P-SAN-T4 — Backfill WORM via GENERATED ALWAYS AS STORED (BLOQUEANTE)

**Análise:** AC-003-1 adiciona `perfil_no_evento NOT NULL` em `auditoria`. Tabela tem trigger `auditoria_anti_*` que BLOQUEIA UPDATE. Spec original não explica como contorna.

**Decisão:** AC-SAN-PERFIL-003-3 reescrito — backfill via:

```sql
ALTER TABLE auditoria ADD COLUMN perfil_no_evento CHAR(1)
  GENERATED ALWAYS AS ((SELECT perfil_regulatorio FROM tenants WHERE id = auditoria.tenant_id)) STORED;
-- Após backfill completo:
ALTER TABLE auditoria ALTER COLUMN perfil_no_evento DROP EXPRESSION;
ALTER TABLE auditoria ALTER COLUMN perfil_no_evento SET NOT NULL;
```

NÃO emite UPDATE — não dispara trigger anti-mutação. Requer PG 12+ (já é requisito do projeto).

**Fallback documentado:** se GENERATED não cobrir caso (ex: schema sem FK direta), usar GUC `app.backfill_perfil_no_evento_permitido` (padrão equipamentos 0006). Decisão final em P4 tasks.

#### P-SAN-T6 — Ordem de migrations cross-app + idempotência (BLOQUEANTE)

**Análise:** M1-M4 estão fechados. Em Balanças Solution dogfooding + CI, migrations já rodaram. Spec não declara ordem cross-app.

**Decisão:** §2.1 Sprint 1 ganha sub-bullet "Ordem de migrations cross-app":

```
tenant/0003 (add nullable)
  → tenant/0004 (backfill + TenantPerfilHistorico)
  → tenant/0005 (set not null + check)
  → audit/00XX (perfil_no_evento)
  → calibracao/00XX (perfil_no_evento em evento_de_calibracao)
  → os/00XX (perfil_no_evento em evento_de_os)
  → equipamentos/00XX (retrofit snapshot COPY de Tenant)
```

Cada migration declara `dependencies = [...]` Django explícito do app upstream.

AC-SAN-PERFIL-001-7 novo: drill `validar_san_perfil_tenant_migrations` aplica migrations em ambiente zerado E em ambiente já-M4; ambos terminam em estado idêntico (snapshot do schema + COUNT(*) em TenantPerfilHistorico).

### Bloco B — Operação contratual / autonomia tenant (advogado)

#### P-SAN-A1 — Rebaixamento voluntário do cliente (BLOQUEANTE)

**Análise:** INV-002 trava UPDATE direto. Mas spec não diz se tenant pode pedir rebaixamento unilateralmente (ex: B → D para pagar menos). CDC art. 51 IV (cláusula abusiva) + Lei 14.181/2021.

**Decisão:** Adicionar direção `REBAIXAMENTO_VOLUNTARIO_CLIENTE` (já listada em P-SAN-R3). Função SECURITY DEFINER própria com:
- Cooldown ≥30 dias entre rebaixamentos.
- Aviso de impacto antes da execução (perda de acesso a features A; histórico WORM preservado por 25a).
- Cláusula em `termo-de-uso-afere-v1.0.md` §X.Y (Sprint 6 Wave A) "Mudança de perfil regulatório".

AC-SAN-PERFIL-001-9 novo.

#### P-SAN-A2 — Base legal nomeada na recusa de eliminação (BLOQUEANTE)

**Análise:** Resolução CD/ANPD 2/2022 art. 8 exige fundamentação nomeada.

**Decisão:** AC novo no Sprint 6 (Wave A módulo `direitos-titular` ou similar):

> **AC-SAN-PERFIL-006-X (Sprint 6)** — resposta padrão de recusa de eliminação para titular vinculado a tenant Perfil A inclui literalmente: (1) base legal LGPD art. 16 II (cumprimento de obrigação legal/regulatória — ISO 17025 cl. 8.4 + RBC CGCRE NIT-DICLA-016) + ADR-0021 zona B; (2) nº RBC + vigência; (3) prazo após o qual eliminação fica possível (25a) com data exata; (4) canal de contestação DPO; (5) menção que dados foram anonimizados-em-lugar para zona B.

Antecipa redação modelo no template `docs/runbooks/dpo-encarregado-resposta-padrao.md` mesmo que Wave A ainda não implemente o módulo.

#### P-SAN-A3 — Aviso ao titular em promoção D→A (BLOQUEANTE)

**Análise:** LGPD art. 9 (informação clara). Mudança material no tratamento (retenção 5a → 25a) exige comunicação ativa ao titular.

**Decisão:** US-SAN-PERFIL-007 nova (Sprint 6 Wave A):

> **Como** titular de dados de cliente vinculado a tenant que promove de D para A,
> **Quero** ser notificado sobre a mudança de retenção,
> **Para** entender o impacto e meus direitos.

- AC: job assíncrono notifica titulares ativos via email/SMS em 15 dias antes da promoção efetivar OU 5 dias úteis após (se urgente).

### Bloco C — Seguros / risco assegurável (corretora)

#### P-SAN-S1 — Exportação trimestral de distribuição book (BLOQUEANTE)

**Análise:** Apólice E&O+Cyber+D&O (ADR-0028) subscreve risco assumindo distribuição declarada. Cláusula `material change` exige notificação ≤90 dias.

**Decisão:** US-SAN-PERFIL-008 nova:

- Comando `python manage.py exportar_distribuicao_perfil_seguradora --trimestre YYYY-Q` produz CSV agregado + PDF/A-3 assinado A3 com 4 linhas (A/B/C/D) + delta + total + hash SHA-256 + TSA-ITI.
- Job procrastinate trimestral agendado.
- Retenção do arquivo: 25a (B2 WORM).

#### P-SAN-S2 — Evento `TenantPerfilAlterado` + webhook out corretora (BLOQUEANTE)

**Análise:** Mudança de perfil pode mover prêmio E&O em 2-3x. Cláusula `material change` exige notificação ≤30 dias.

**Decisão:**
- AC-SAN-PERFIL-001-6 novo: funções SECURITY DEFINER emitem evento `TenantPerfilAlterado` em outbox na mesma transação.
- Consumer `notificar_corretora_susep_material_change` publica via `OutboundWebhookProvider` (ADR-0054) com `event_type=material_change` + payload anonimizado (slug hash + perfil_anterior + perfil_novo + direcao + registrado_em + assinatura_a3_id). Sem PII.
- INV-TENANT-PERFIL-006 nova: toda mutação em `Tenant.perfil_regulatorio` emite evento em outbox transacional.
- GATE-TENANT-PERFIL-WEBHOOK-CORRETORA Wave A para configuração real.

### Bloco D — MÉDIO INV-RITUAL-001 (viram AC binário explícito)

Os 17 achados MÉDIO consolidados em ACs binários adicionados à spec:

| ID | Tema | Local |
|---|---|---|
| T7 | Latência <5ms benchmark | AC-001-4b |
| T8 | CHAR(1) + CHECK vs PG ENUM | AC-001-1b |
| T9 | ContextVar em todos WORM helpers | AC-003-2b |
| T10 | Tenant.perfil_regulatorio é fonte da verdade; histórico é trilha | §2.1 nota |
| T11 | Matriz de transições válidas | AC-001-8 |
| T12 | Hook heurística por path + grep US- | AC-005-3 reescrito |
| A6 | Capacidade contratual operador | AC-004-7 |
| A7 | Trilha D→A manual = RT do tenant decide | Sprint 6 plan nota |
| A8 | TenantPerfilHistorico sanitizado | AC-001-6, AC-001-7 |
| S6 | Cyber diferenciado já implícito via US-008 | nota ADR-0028 |
| S7 | D&O notificação em rebaixamento | AC-002-7b |
| S8 | BPT não-conflito documentado | §2.2 non-goal |
| R2 | Validação formato CRL NNNN | AC-001-1c regex |
| R5 | 2ª conferência só com regra_decisao != NENHUMA | AC-002-4 refinada |
| R6 | Validação software matriz 4 colunas | AC-005-4 expandida |
| R8 | cl. 8.4.2 + NIT-DICLA-030 citação | AC-003-1 enriched |
| R9 | ILAC-MRA não-universal | AC-001-1 + AC-templates Sprint 5 |

### Bloco E — ALTO Wave A (viram GATE rastreado)

Os 10 achados ALTO viram gates rastreados em §6 da spec:

| ID | GATE | Sprint origem |
|---|---|---|
| T5 | GATE-TENANT-PERFIL-CONCORRENCIA-PROMOCAO | Sprint 1 |
| T13 | GATE-TENANT-PERFIL-CERT-SNAPSHOT | Sprint 5 |
| T14 | GATE-TENANT-PERFIL-DRILL-PG-REAL | Wave A |
| A4 | GATE-TENANT-PERFIL-EVIDENCIA-EVENTOS-PRE-SANEAMENTO | Sprint 4 |
| A5 | GATE-TENANT-PERFIL-PDF-CERT-CGCRE | Sprint 3 |
| S3 | GATE-TENANT-PERFIL-EXPORT-EVIDENCIA-SINISTRO | Sprint 6 |
| S4 | (mesmo que A5 — convergência) | Sprint 3 |
| S5 | GATE-TENANT-PERFIL-VERIFICACAO-PERIODICA-VIGENCIA | Sprint 3 |
| R4 | GATE-LICENCAS-SUBESTADOS-C1-C5 | Wave A módulo `licencas-acreditacoes` |
| R7 | GATE-TENANT-PERFIL-SNAPSHOT-ESCOPOS-VIGENTES | Sprint 4 |

### Bloco F — ACEITE registrar risco

| ID | Tema | Decisão |
|---|---|---|
| T15 | Estimativa 5-10 dias subestima | Ajustar §"Plano" da ADR-0067 para **8-14 dias com causa-raiz**. Registrar em §8 Histórico da spec. |

---

## Próximos passos

1. **P3 reconciliação:** spec.md reescrita absorvendo 13 BLOQUEANTES (próximo passo imediato).
2. **P4 tasks.md:** desdobrar ACs em T-SAN-PERFIL-NNN.
3. **P5 implementação:** Sprint 1 inicia migrations (causa-raiz pelos 13 BLOQUEANTES).
4. **P5 fechamento:** 10 auditores Família 5 + drill `validar_san_perfil_tenant` PASS ZERO CRÍTICO/ALTO/MÉDIO.

## Histórico

- **2026-05-27** — P1 spec criada. P2 4 reviews paralelos disparados.
- **2026-05-27** — P2 retornado: 41 achados (13 BLOQ + 17 MÉDIO + 10 ALTO + 1 ACEITE).
- **2026-05-27** — Plan.md (este documento) consolida P2 → P3.
- **Próximo:** reescrita spec.md (P3).
