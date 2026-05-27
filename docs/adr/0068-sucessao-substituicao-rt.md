---
adr: 0068
titulo: Sucessão / substituição temporária do RT (Responsável Técnico) — vigência sobreposta + competência herdada + assinatura paralela
owner: roldao
status: aceito
data: 2026-05-27
aceito-em: 2026-05-27
proposto-por: agente (auditoria 10 lentes pré-Wave A — L1#7 + L3#15 + L3-NIT-DICLA-016)
revisado-por: tech-lead-saas-regulado + consultor-rbc-iso17025 (offline)
bloqueia-fase: Wave A (módulo `agenda` US-AG-006 sugere slot livre técnico competente; módulo `app-tecnico` US-APP-001 atribui OS; módulo `certificados` US-CER-008 assinatura A3)
depende-de: ADR-0022 (RT do tenant), ADR-0030 (vigência temporal canônica), ADR-0067 (perfil regulatório), ADR-0026 (2ª conferência + independência RT)
---

# ADR-0068 — Sucessão / substituição temporária do RT

> **Status:** ACEITO 2026-05-27 (auditoria 10 lentes pré-Wave A — Onda PRE-A.2). Resolve achado **CRÍTICO L1#7** (persona "RT substituto/sucessor" ausente em 14 PRDs Wave A) + **L3#15** (afastamento/substituto RT inexistente — NIT-DICLA-016).

## 1. Problema

ADR-0022 modelou `RTCompetencia` com vigência (`vigencia_inicio`, `vigencia_fim`, `revogado_em`) mas NÃO tratou **substituição temporária** — RT principal em férias por 30 dias, RT afastado por doença, RT em curso de capacitação. Hoje 14 PRDs Wave A (agenda, app-tecnico, certificados, calibração, OS, etc.) consultam predicate `rt_competencia_cobre` sem conhecer "substituto temporário". Sem ADR-0068, casos reais ficam **sem trilha**: ou o substituto assina certificado sem registro formal (NC NIT-DICLA-016) ou tenant perfil A bloqueia operação de calibração durante o afastamento (impacto operacional).

## 2. Decisão

### 2.1 Modelo de domínio

Adicionar entidade `RTSubstituicao` ortogonal a `RT` + `RTCompetencia`:

```
RTSubstituicao(
  id UUID,
  tenant_id UUID NOT NULL,
  rt_titular_id UUID NOT NULL FK → RT,         -- quem é substituído
  rt_substituto_id UUID NOT NULL FK → RT,      -- quem assume
  motivo TEXT NOT NULL,                         -- "Férias 2026-06", "Afastamento médico CID Z", "Capacitação NIT"
  vigencia_inicio TIMESTAMP NOT NULL,
  vigencia_fim TIMESTAMP NOT NULL,              -- obrigatório — substituição é SEMPRE com prazo
  documento_designacao_a3_id UUID FK → DocumentoAssinado,  -- ata + A3 do RT titular OU gestor qualidade
  competencias_herdadas JSONB,                  -- subset de RTCompetencia.{grandeza, metodo_id}
  declaracao_competencia_substituto_a3_id UUID FK → DocumentoAssinado,
  ativo_em TIMESTAMP NOT NULL DEFAULT NOW(),
  encerrado_em TIMESTAMP NULL,
  motivo_encerramento_antecipado TEXT NULL
)
```

### 2.2 Regras canônicas

1. **Vigência sobreposta:** durante `[vigencia_inicio, vigencia_fim]`, predicate `rt_competencia_cobre(tenant_id, atividade)` consulta PRIMEIRO `RTSubstituicao` ativa; se substituto cobre, retorna `(True, "")`; caso contrário cai pra `RTCompetencia` do titular.
2. **Competência herdada subset:** substituto NÃO herda competências automaticamente — declara explicitamente quais grandezas+métodos assume. Subset de `RTCompetencia` do titular OU competências próprias do substituto (se já era RT em outro tenant).
3. **Dupla assinatura A3:** designação exige A3 do titular OU do gestor qualidade (se titular incapacitado — caso médico). Declaração de competência exige A3 do próprio substituto. Hook `feature-perfil-matriz-validator` valida call-site.
4. **Vigência DURA:** substituto não pode operar após `vigencia_fim`. Hook `migration-concorrencia-rt-substituicao` impede UPDATE em `vigencia_fim` (só `encerrado_em` antecipado com motivo).
5. **Notificação CGCRE:** para perfil A (RBC acreditado), substituição > 30 dias dispara consumer `Tenant.RTSubstituicaoProlongada → NotificacaoCGCRE` (ADR-0014 transições regulatórias + GATE-EQP-RT-NOTIF).
6. **Reconciliação certificado:** certificado emitido durante vigência da substituição grava `signatario_substituto_id` + `rt_titular_no_periodo_id` no snapshot WORM (defesa probatória).
7. **Encerramento antecipado:** se titular volta antes da `vigencia_fim`, registrar `encerrado_em` + `motivo_encerramento_antecipado`. Substituto perde competência herdada na hora.

### 2.3 Matriz feature × perfil ADR-0067

- **Perfil A (RBC acreditado):** substituição obrigatoriamente declarada com 30 dias de antecedência (CGCRE NIT-DICLA-016); notificação obrigatória.
- **Perfil B (rastreável):** substituição declarada D+0 aceita; notificação OPCIONAL.
- **Perfil C (em preparação RBC):** mesmas regras do A (treinamento dos processos).
- **Perfil D (comercial puro):** declaração simples sem A3 obrigatório (assinatura simples basta).

## 3. INVs novas

- **INV-RT-SUB-001** — toda operação assinada por substituto exige `RTSubstituicao` ativa no instante da operação.
- **INV-RT-SUB-002** — `vigencia_fim` imutável pós-INSERT (só `encerrado_em` antecipado).
- **INV-RT-SUB-003** — perfil A substituição > 30 dias dispara notificação CGCRE síncrona.

## 4. Bloqueios desbloqueados

- L1#7 (persona RT substituto ausente): FECHADO.
- L3#15 (afastamento RT inexistente): FECHADO.
- GATE-EQP-RT-NOTIF M2 (consumer ANPD/CGCRE 30d): ganha dependência clara.
- Module `agenda` (US-AG-006) pode sugerir slot de técnico considerando substituição.

## 5. Tarefas Wave A bloqueantes (T-RT-SUB-001..010)

1. T-RT-SUB-001 — migration `RTSubstituicao` + RLS tenant_id + EXCLUDE GIST `vigencia_inicio,vigencia_fim` (sem 2 substituições ativas mesma janela mesmo titular).
2. T-RT-SUB-002 — modelo Django + factory.
3. T-RT-SUB-003 — use case `declarar_substituicao_rt(titular_id, substituto_id, motivo, vigencia, competencias_herdadas)`.
4. T-RT-SUB-004 — use case `encerrar_substituicao_antecipada(substituicao_id, motivo)`.
5. T-RT-SUB-005 — predicate `rt_competencia_cobre` atualizado pra consultar substituição primeiro.
6. T-RT-SUB-006 — consumer `Tenant.RTSubstituicaoProlongada` notificação CGCRE.
7. T-RT-SUB-007 — snapshot `signatario_substituto_id` + `rt_titular_no_periodo_id` em certificado.
8. T-RT-SUB-008 — hook `migration-concorrencia-rt-substituicao` (imutabilidade vigencia_fim).
9. T-RT-SUB-009 — admin Django + endpoint REST `/api/tenants/{tenant_id}/rt-substituicoes/`.
10. T-RT-SUB-010 — 12 testes regressão (INV-RT-SUB-001..003 + matriz perfil + reconciliação certificado).

## 6. Non-goals

- Substituição PERMANENTE (sucessão definitiva do RT) — modelada por `RT.encerrado_em` + novo `RT` com `vigencia_inicio` adjacente (ADR-0022 cobre).
- Múltiplos substitutos simultâneos por grandeza — fora do escopo Wave A; revisitar V2 se demanda real.
- Substituição via terceiro tenant (RT vendor) — V2 (depende de ADR-0022 v3).
