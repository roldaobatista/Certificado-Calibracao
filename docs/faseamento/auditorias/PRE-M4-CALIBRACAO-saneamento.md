---
owner: roldao
revisado_em: 2026-05-25
proximo_review: 2026-08-25
status: stable
diataxis: explanation
audiencia: agente
escopo: Wave A Marco 4 — calibracao
tipo: saneamento-pre-marco-4-calibracao
relacionados:
  - docs/faseamento/auditorias/OS-CAL-CONSOLIDADO-rodada-1.md
  - docs/faseamento/auditorias/OS-CAL-CONSOLIDADO-rodada-2.md
  - docs/faseamento/auditorias/OS-CAL-RESOLUCAO-rodada-1.md
  - docs/faseamento/auditorias/OS-CAL-RESOLUCAO-rodada-2.md
  - docs/faseamento/M3-os/auditoria-familia5.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/dominios/metrologia/modulos/calibracao/modelo-de-dominio.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/adr/0026-segunda-conferencia-independencia.md
  - docs/adr/0040-padrao-metrologico-entidade-separada.md
  - docs/adr/0063-rt-competencia-grandeza-diferida-marco4.md
---

# Saneamento pré-Marco 4 (`calibracao`) — dossiê consolidado

> Solicitado por Roldão em **2026-05-25** após o fechamento do Marco 3 OS (10/10 PASS ZERO C/A/M). Lição `feedback_auditar_antes_de_replicar_molde` aplicada: **não copiar molde M3 cego pra M4**.
>
> **Objetivo:** auditar criticamente o que do molde M3 OS é GENÉRICO (replica) vs ESPECÍFICO M3 (não replicar); listar pendências reais do Marco 4 antes da spec FORWARD; consolidar pré-requisitos por gate (P1/P4/P5/fechamento).

---

## 1. Estado real do Marco 4 hoje

### Docs existentes em `docs/dominios/metrologia/modulos/calibracao/`

| Doc | Status | Cobertura |
|---|---|---|
| `prd.md` | `draft` | 16 US (CAL-001..016) incl. US-CAL-016 procedimento vigente (Onda 7 A5-CAL) + AC-CAL-007-3 ADR-0026 + AC-CAL-007-4 consumer trigger + AC-CAL-014-3 análise impacto NC-PT |
| `modelo-de-dominio.md` | `draft` | 14 entidades retrofitadas (Onda 7): `Calibracao.atividade_os_id` (FK tipada), `snapshot_equipamento_json`, `PadraoUsado.snapshot_capturado_at`+lock, `NaoConformidade` ciclo CAPA, `LeituraCorrecao`, `RecepcaoItemCalibracao`, `EventoDeCalibracao`, `ComponenteIncerteza`+`OrcamentoPorPonto` 1:N, `MedicaoControle`, `DelegacaoExecucao` |
| `glossario.md` | — | a auditar status |
| `metricas.md` | — | reescrito Onda 7C com tenant_id label + correlation_id + ciclo CAPA + SLOs CGCRE duros + 4 dashboards persona |
| `personas.md` | — | inclui P-METR-AUDITOR-CGCRE + P-METR-AUDITOR-INMETRO (Onda 7D) |
| `modelo-de-dominio.md` | — | acima |
| `conformidade-iso-17025.md` | — | cl. 6.2.5 / 7.5 / 7.7 / 7.8.6 / 7.11 / 8.7 |
| `validacao-software.md` | — | base ADR-0025 |
| `controle-certificado-emitido.md` | — | retrofit Onda 7B `status: stable` |
| `garantia-validade-7.7.md` | — | retrofit Onda 7B `status: stable` |
| `responsabilidade-tecnica.md` | — | retrofit Onda 7B `status: stable` (já enforce política ADR-0026) |
| `registros-tecnicos-7.5.md` | — | retrofit Onda 7B `status: stable` |
| `politica-verificacao-intermediaria.md` | — | a verificar |

### ADRs Marco 4 — status real (verificado 2026-05-25)

| ADR | Status | Bloqueia | Observação |
|---|---|---|---|
| **0022** RT do tenant | ✅ ACEITA 2026-05-22 | M4 destravado | Marco 2 entregue; predicate `rt_competencia_cobre` existe (stub→ativo via ADR-0063) |
| **0024** Regra decisão 7.8.6 | ✅ ACEITA 2026-05-23 | M4 destravado | 3 modos + override + lock pós-emissão |
| **0025** Validação software 7.11 | ✅ ACEITA 2026-05-23 | M4 destravado | URS/IQ/OQ/PQ + replay determinístico + 2º caminho |
| **0026** 2ª conferência | ✅ ACEITA 2026-05-23 | M4 destravado | Política 4 condições + 5%/mês (AC-CAL-007-3) |
| **0029** Canonicalização texto | ✅ ACEITA 2026-05-23 | M4 destravado | INV-DOC-CANON-001 |
| **0030** Vigência canônica | ✅ ACEITA 2026-05-23 | M4 destravado | JanelaVigencia VO |
| **0031** Soft-delete 3 padrões | ✅ ACEITA 2026-05-23 | M4 destravado | — |
| **0032** ReferenciaPIIAnonimizavel | ✅ ACEITA 2026-05-23 | M4 destravado | Propagação Zona A/B/C |
| **0033** Idempotência consumer | ✅ ACEITA 2026-05-23 | M4 destravado | `consumer_idempotencia` + `dead_letter_events` |
| **0063** RT competência diferida M4 | ✅ ACEITA 2026-05-25 | M4 ativa predicate | Marco 4 PLUGA `AtividadeDaOS.grandeza` → predicate bloqueia |
| **0040** Padrão metrológico entidade separada | ✅ ACEITA 2026-05-25 | M4 destravado | Decisão Roldão: módulo `padroes` separado — INV-PAD-001..006 + estado `EM_RECAL_EXTERNO`/`INTERCOMPARACAO_PT`/`BAIXADO`/`SUCATEADO` + vinculação SI {BIPM, INMETRO, RBC, INTERNACIONAL} |
| **0064** Rotação HMAC + retenção 25a | ✅ ACEITA 2026-05-25 | M4 destravado | NOVO — fecha GATE-CAL-HMAC-RETENCAO. Formato `v<NN>$<base64>` + KMS Multi-Region histórico 25a + INV-HMAC-001..005 |
| **0043** Calibracao→Financeiro + inadimplência | 🟡 PROPOSTA | M5/M6 — pode esperar | Integração financeiro, não bloqueia M4 core |
| **0044** Export ANVISA/SAÚDE | 🟡 PROPOSTA | Marco 5 (certificados) | Não bloqueia M4 |
| **0045** Recall/Suspensão/Errata | 🟡 PROPOSTA | Marco 5 | Recall AC-CAL-014-3 referencia, mas pós-emissão |
| **0046** OCSP/CRL revogação | 🟡 PROPOSTA | Marco 5 (qualquer A3) | Não bloqueia M4 core (afeta apenas assinatura RT) |
| **0047** TSA-ITI PAdES-LTV | 🟡 PROPOSTA | Marco 5 cert | Não bloqueia M4 |
| **0048** A3 e-CPF RT cadastro | 🟡 PROPOSTA | Wave A | Cadastro RT já em Marco 2 — assinatura é Marco 5 |

**Veredito ADRs:** todas as ADRs que bloqueavam M4 P1 agora ACEITAS (ADR-0040 + ADR-0064). ADR-0043..0048 são Marco 5 (não bloqueiam M4 core).

---

## 2. As 10 lições do molde M3 OS — guard-rails antes de M4

Extraídas de `docs/faseamento/M3-os/auditoria-familia5.md` (5 batches conserto causa-raiz + 2ª + 3ª passada). Cada lição vira **invariante de projeto** pro M4.

### G1 — Stubs públicos NÃO podem mentir na docstring
**M3 caiu em:** `sagas/sync_mobile.py`, `sagas/sucessao.py`, `consumers/tenant.py`, `sagas/anonimizacao.py` (Q-OS-08/09) — docstring dizia "BLOQUEIA reabertura" / "republica retry" mas corpo só `logger.info(...)`. Auditor-llm-correctness D2 pegou.

**Regra M4:** todo stub público em saga/consumer/use-case OU implementa OU lança `NotImplementedError("GATE-CAL-* Wave A")` OU tem docstring que diz literalmente "STUB — só loga" + cita GATE. Auditor-llm-correctness vai ler isso.

### G2 — Helper único de sanitização de payload de evento
**M3 caiu em:** 12 call-sites com `sanitizar_payload_audit(...)` ad-hoc + skip marker (SEG-M3-OS-03). Batch 5 criou `sanitizar_payload_evento_os()` único.

**Regra M4:** desde o início, criar `sanitizar_payload_evento_calibracao()` único em `src/infrastructure/calibracao/event_sanitizer.py`. Cobre 12 eventos (`Calibracao.Recepcionada/Aprovada/Rejeitada/LeituraCorrigida/NCAberta/NCFechada/...` + 5 eventos `Padrao.*`). Hook bus-envelope-validator vai checar.

### G3 — Idempotency-Key OBRIGATÓRIA em todo POST crítico
**M3 caiu em:** 7 endpoints (cancelar/reabrir/criar-atividade/iniciar/concluir/reagendar/transferir) sem header (OS-IDEMP-001 família). Auditor-idempotencia pegou.

**Regra M4:** 18 endpoints POST previsíveis em M4 — TODOS com `IdempotencyMixin` + `ACTION_IDEMPOTENT` map desde a 1ª linha:
- `POST /calibracao/{id}/configurar`
- `POST /calibracao/{id}/registrar-leitura` (alto risco — replay = duplica leitura → fere INV-CAL-WORM-001)
- `POST /calibracao/{id}/corrigir-leitura` (LeituraCorrecao — replay = histórico de correções duplicado)
- `POST /calibracao/{id}/calcular-incerteza`
- `POST /calibracao/{id}/avaliar-conformidade`
- `POST /calibracao/{id}/aprovar-revisao` (RT 1ª conferência)
- `POST /calibracao/{id}/aprovar-2a-conferencia` (RT 2ª)
- `POST /calibracao/{id}/rejeitar`
- `POST /calibracao/{id}/marcar-nc` + `/resolver-nc`
- `POST /calibracao/{id}/cancelar`
- `POST /padrao/{id}/registrar-envio-externo` + `/registrar-recebimento`
- `POST /padrao/{id}/verificar-intermediaria`
- `POST /escopo/{id}/atualizar-cmc`
- `POST /proficiencia/{id}/registrar-resultado`

### G4 — UUID literal digit-heavy em TODO teste de sanitização
**M3 caiu em:** `test_inv_os_aud_001_sanitize.py` só com `uuid4()` aleatório (Q-OS-04). O bug-classe `_SEQ_NUMERICA_RE` em 2.6% dos UUIDs (e `_ENDERECO_RE` no slug `5cj2`) só foi detectado em sweep de 5000 amostras + UUID literal digit-heavy (`33333333-3333-4333-8333-333333333333`).

**Regra M4:** desde a 1ª regressão `test_inv_cal_aud_001_*.py`, incluir:
- 5000 UUIDs digit-heavy varredura (`f"{i:08d}-{...}"`)
- 1000 ULIDs varredura
- 1000 slugs (3-8 chars + dígito)
- UUIDs literais explícitos cobrindo `0000...` / `9999...` / `aaaa...` / digit-heavy.

### G5 — `tenant_id` explícito em consumers/sagas, defesa em profundidade
**M3 caiu em:** consumers/sagas executavam `.filter(...)` sem `tenant_id` no WHERE; `consumer_idempotente` não setava `app.tenant_ids` antes do handler (SEG-M3-OS-01).

**Regra M4:** `consumer_idempotente` decorator obrigatório em TODOS os 6 consumers M4 (`Atividade.Iniciada(tipo=calibracao)`, `Cliente.Anonimizado`, `Padrao.CalibracaoExternaVencida`, `Equipamento.PerfilTenantAlterado`, `Colaborador.Desligado`, `RT.CompetenciaRevogada`). Decorator seta `app.tenant_ids` antes do handler. Queries ORM checam tenant_id explícito **mesmo com RLS**.

### G6 — Predicates STUB que nunca são INVOCADOS
**M3 caiu em:** PROD-M3-02 — `rt_competencia_cobre` + `tenant_dentro_escopo_acreditado` existiam como STUB mas não acionados em 4 use cases. ADR-0063 invocou-os com fail-open controlado.

**Regra M4:** 4 predicates M4 precisam ser **invocados** desde a 1ª use case que carrega o dado:
- `cmc_cobre(grandeza, faixa)` — `configurar_calibracao` US-CAL-002
- `padrao_vigente_no_uso(padrao_id, data_execucao)` — `selecionar_padroes` US-CAL-003
- `procedimento_vigente_para(grandeza, faixa, data)` — `configurar_calibracao` US-CAL-016
- `regra_decisao_aplicavel(spec, k)` — `avaliar_conformidade` US-CAL-006
- `rt_competencia_cobre` (já existe, ATIVA via ADR-0063 quando M4 setar `AtividadeDaOS.grandeza`) — `aprovar_revisao` / `aprovar_2a_conferencia` US-CAL-007/008

Auditor-produto vai rastrear AC × invocação.

### G7 — TODOS os use cases precisam endpoint REST OU ADR rebaixando AC
**M3 caiu em:** 7 use cases sem endpoint REST (PROD-M3-01). Batch 4 criou 7 endpoints + 4 ViewSets.

**Regra M4:** desde planejamento, MAP `use case → endpoint` em `plan.md` cobre 100%. Se algum use case fica sem endpoint, ADR explícita rebaixando AC.

### G8 — Drift docs ATIVO durante implementação, não no fim
**M3 caiu em:** 84 linhas de tasks GAP + 4 ADRs `proposta` que já eram `aceito` + AGENTS contagens defasadas (D1-ALTA-1..4, D6-ALTA-1..4, D4-ALTA-1, D2-ALTA-1..2). Auditor-drift-docs viu **8 ALTOS** na 1ª passada.

**Regra M4:** ao terminar CADA fase do tasks.md, mesmo commit:
- Marcar `✅` na linha da task
- Atualizar AGENTS §11/§12 + contagens
- Atualizar `.agent/CURRENT.md` (≤40 linhas)
- Adicionar entrada `docs/faseamento/diario/2026-MM-DD-marco4-fase-N.md`
- Atualizar revisado_em em docs tocados

### G9 — Anti-fraude: `<papel>_id == usuario_id` em ações sensíveis
**M3 caiu em:** INV-OS-ATIV-005 — `concluir_atividade.py` não validava `atividade.tecnico_executor_id == payload.usuario_id` (SEG-M3-OS-05).

**Regra M4 — 4 INVs anti-fraude:**
- `INV-CAL-FRAUDE-EXEC-001`: `registrar_leitura` valida `calibracao.executor_id == request.user.id` OU `DelegacaoExecucao` válida.
- `INV-CAL-FRAUDE-REV-001`: `aprovar_revisao` valida `calibracao.revisor_id == request.user.id`.
- `INV-CAL-FRAUDE-CONF-001`: `aprovar_2a_conferencia` valida `calibracao.conferente_id == request.user.id` + `conferente_id != revisor_id` (cl. 6.2.5).
- `INV-CAL-FRAUDE-COR-001`: `corrigir_leitura` valida `corretor_id == request.user.id`.

### G10 — PRDs A11Y + Product Analytics por tela nova (ADR-0057 + 0058)
**M3 caiu em:** GATE-A11Y-4 + GATE-PRODANALYTICS-4 bloqueavam Fase 5 do M3 antes de PRD preenchido por tela.

**Regra M4:** desde a fase de spec, listar telas M4 candidatas (configurar-calibracao, registro-leitura, painel-orcamento-incerteza, revisão-1ª, revisão-2ª, recepção, gestão-padroes, escopo-CMC, EP-painel) e cravar PRD A11Y + PRD ProductAnalytics binário ANTES da 1ª linha de UI.

---

## 3. Itens específicos M4 — GATEs Wave A criados em Onda 7 (rastreados)

Da `OS-CAL-RESOLUCAO-rodada-2.md`, os GATE-CAL-* aplicáveis ao Marco 4 que entram NATURALMENTE durante codificação (não bloqueiam P1):

| GATE | Tema | Quando atacar |
|---|---|---|
| **GATE-CAL-METODO-VAL** | Fluxo validação método interno (cl. 7.2.2) | Fase US-CAL-002 (Configurar calibração) |
| **GATE-CAL-EP-TEND** | Painel histórico EP + alerta 3z mesmo sentido (cl. 7.7.3) | Fase US-CAL-014 (proficiência) |
| **GATE-CAL-VI-POL** | Política VI por classe (cl. 6.4.10) | Fase US-CAL-012 (verificação intermediária) |
| **GATE-CAL-MIG-CLASSIF** | Hook `migration-metrology-classifier.sh` (cl. 7.11.3 ADR-0025) | Fase 9 (hooks novos M4) |
| **GATE-CAL-MANUAL-QUAL** | Página `/manual-qualidade` no produto (cl. 8.3) | Wave A operacional (não M4 core) |
| **GATE-CAL-SUBCONTR** | Decisão subcontratação (cl. 6.6) — non-goal? Wave A? | **DECISÃO RECOMENDADA antes P1** |
| **GATE-CAL-LEITURA-CORR-TAXA** | Alerta auto Qualidade quando >10% leituras com `LeituraCorrecao` | Fase US-CAL-004 (leituras) |
| **GATE-CAL-HMAC-RETENCAO** | Conflito chave HMAC 10a × audit metrológico 25a | **ADR a criar pré-P4** |
| **GATE-SEC-PORTA-CERT** | Função única `pre_emissao_certificado_check()` amarrando 6 INVs | Marco 5 (emissão), não M4 core |
| **GATE-CAL-EP-IMPACTO** | Já implementado em AC-CAL-014-3 — verificar invocação ATIVA | Fase US-CAL-014 |

---

## 4. Itens MÉDIO/BAIXO da Rodada 2 não-resolvidos que reaparecem em M4

Da `OS-CAL-CONSOLIDADO-rodada-2.md` §"BAIXOs NOVOS" + MÉDIOs não-resolvidos da Onda 7:

- 4 itens drift cosmético em calibracao (`tipo_predominante` doc consistência).
- 4 itens segurança (chave HMAC QR cert vs equipamento docs).
- 3 itens observabilidade (`certificados/metricas.md` stub — Marco 5).
- 2 itens LGPD/biometria — **GATE-LGPD-BIO-DPIA-OAB** mantém-se (advogado humano OAB pré-1º tenant externo).

---

## 5. Pré-requisitos por gate

### 5.1 — Antes de Marco 4 P1 (spec FORWARD) — TODOS ATENDIDOS 2026-05-25

1. ✅ **ADR-0040 aceita** (padrão metrológico entidade separada) — decisão Roldão 2026-05-25. Revisão técnica formal pelos 2 subagentes diferida pós-aceite (não bloqueante).
2. ✅ **GATE-CAL-SUBCONTR resolvido** — Roldão decidiu **US nova Wave A** (US-CAL-017). Adicionada ao PRD calibracao 2026-05-25 com 6 AC binários + entidades `LaboratorioSubcontratado` e `AceiteSubcontratacao` + 2 eventos novos + 4 INV-CAL-SUBC-*.
3. ✅ **ADR-0064 criada e aceita** — rotação anual de chave HMAC + histórico KMS Multi-Region 25a + formato canônico `v<NN>$<base64>` + INV-HMAC-001..005 + 4 GATEs vinculados (RETROFIT-MARCO-2-3, KMS-IAM-LOCK, DRILL, retrofit hashes existentes).

**Marco 4 P1 (spec FORWARD) DESTRAVADO.** Pode arrancar imediatamente após este commit.

### 5.2 — Antes de Marco 4 P4 (codificação) — APLICAR GUARD-RAILS

Aplicar as **10 lições G1..G10** desde a 1ª linha de código M4:

- G1: TODO stub público raises `NotImplementedError("GATE-CAL-*")` ou docstring marca STUB.
- G2: `sanitizar_payload_evento_calibracao()` criado em `src/infrastructure/calibracao/event_sanitizer.py` ANTES do 1º consumer.
- G3: `IdempotencyMixin` aplicado em 18 endpoints POST listados (§G3).
- G4: 1ª regressão `test_inv_cal_aud_001_*.py` já com 5000 UUIDs + 1000 ULIDs + 1000 slugs + literais digit-heavy.
- G5: `consumer_idempotente` decorator em 6 consumers listados.
- G6: 5 predicates invocados desde 1ª use case (incluindo `rt_competencia_cobre` ATIVO via ADR-0063 quando setar `AtividadeDaOS.grandeza`).
- G7: 100% use cases mapeados pra endpoint REST em `plan.md`.
- G8: regra de drift docs ativo (atualizar tasks.md / AGENTS / CURRENT / diário no MESMO commit da fase).
- G9: 4 INVs anti-fraude promovidas em `REGRAS-INEGOCIAVEIS.md`.
- G10: PRD A11Y + Product Analytics por tela nova ANTES da 1ª UI.

### 5.3 — Antes de Marco 4 P5 (auditores)

- Suite chave M4 verde antes de invocar os 10 auditores.
- Drift docs RESET (CURRENT.md ≤40 linhas, AGENTS contagens reais, tasks.md ✅ onde entregue).
- Hooks novos M4 instalados: `migration-metrology-classifier.sh` (GATE-CAL-MIG-CLASSIF) + `cmc-binding-check.sh` (validar `INV-002` na linha) + `incerteza-versao-motor-check.sh` (INV-CAL-VERSAO-001).

### 5.4 — Antes de Marco 4 fechado (10/10 PASS ZERO C/A/M)

- INV-RITUAL-001 satisfeito (MÉDIO+ bloqueia).
- Drill `validar_m4_calibracao` PASS — equivalente a `validar_m3_os`. Criar comando de gerência que executa o caminho feliz E1→E2→E3→...→aprovado→2ª-conferência→emissão (mas emissão é M5, então PARA em APROVADA).
- Anti-replay teste: rodar pytest com `pytest-randomly` 3x; aceitar só se zero flake.

### 5.5 — Antes do 1º tenant externo pago (não bloqueia M4, mas pendente)

- GATE-LGPD-BIO-DPIA-OAB (advogado humano OAB).
- GATE-LGPD-RIPD-OAB (idem).
- GATE-SEG-BPT-1 (apólice BPT — emergencial Balanças Solution dogfooding).
- ADR-0046/0047/0048 aceitas (OCSP/CRL + TSA-ITI + A3 e-CPF RT) — afetam Marco 5 emissão, mas se M5 codar antes de tenant externo precisa estar aceito.

---

## 6. Sumário executivo pro Roldão (linguagem de produto)

**Marco 4 (calibração) está QUASE pronto pra começar a especificar.** O retrofit das Ondas 6+7 (em maio/23) deixou os 28 críticos da auditoria pré-Marco 3 resolvidos, e a maioria das ADRs que o Marco 4 precisa já estão aceitas (8 das 11).

**O que ainda preciso de você ANTES de começar a escrever a spec do Marco 4:**

1. **ADR-0040** (padrão metrológico é módulo separado, não Equipamento do cliente?) — você decide; eu peço review do consultor RBC + tech-lead e te trago a versão final pra OK.
2. **Subcontratação de calibração** (cl. 6.6 ISO 17025) — empresa do tipo X aceita instrumento que ela não consegue calibrar, e manda pra outro lab? Sim/Não/Wave A?
3. **Conflito de retenção:** chaves HMAC duram 10 anos, mas auditoria metrológica precisa durar 25. Como resolver? Recomendação técnica: chave HMAC rotacionada com histórico preservado em KMS Multi-Region.

Com isso decidido, eu arrancho P1 do Marco 4 (spec FORWARD) aplicando as **10 lições do Marco 3 OS** (resumidas na seção 2 deste doc).

**O que eu vou fazer SEM perguntar (já decidido):**

- Aplicar `IdempotencyMixin` em 18 endpoints POST M4 desde a 1ª linha.
- Criar `sanitizar_payload_evento_calibracao()` único.
- Testes anti-PII com 5000 UUIDs digit-heavy desde o início.
- 5 predicates regulatórios INVOCADOS (não-stub).
- 4 INVs anti-fraude promovidas (`INV-CAL-FRAUDE-*`).
- Drift docs ativo (atualizar AGENTS/CURRENT a cada fase, não no fim).

**Pendências que NÃO bloqueiam Marco 4 mas precisam acontecer pré-1º tenant externo pago:**

- Advogado humano OAB ratifica RIPD geolocalização + DPIA biometria touch.
- Corretora SUSEP humana emite apólice BPT + as 4 modalidades da ADR-0028.
- ADRs 0046/0047/0048 aceitas (afeta Marco 5 emissão).

---

## 7. Próximo passo — saneamento CONCLUÍDO 2026-05-25

✅ Roldão respondeu 3 perguntas (ADR-0040 separado, subcontratação como US-CAL-017, HMAC rotação anual + KMS 25a).
✅ ADR-0040 aceita (frontmatter + AGENTS §11 atualizado).
✅ ADR-0064 criada e aceita (rotação HMAC + INV-HMAC-001..005 + 4 GATEs vinculados).
✅ US-CAL-017 (subcontratação cl. 6.6) adicionada ao PRD calibração com 6 AC + 2 entidades + 2 eventos + 4 INV-CAL-SUBC-*.
✅ AGENTS.md §11 atualizado: drift removido (ADRs 0021/0024/0025/0026 → aceito); ADR-0040/0064 adicionadas; §12 cita dossiê.

**Marco 4 P1 (spec FORWARD do `calibracao`) DESTRAVADO.**

Pendências que NÃO bloqueiam P1 mas precisam acontecer:

1. **Revisão técnica formal ADR-0040 + ADR-0064** pelos 2 subagentes (tech-lead-saas-regulado + consultor-rbc-iso17025) — diferida pós-aceite.
2. **Aplicar 10 lições do M3 OS (§2 deste dossiê)** desde a 1ª linha de código M4 P4.
3. **Pendências externas (humano OAB + corretora SUSEP):** GATE-LGPD-BIO-DPIA-OAB + GATE-LGPD-RIPD-OAB + GATE-SEG-BPT-1 — pré-1º tenant externo pago.
