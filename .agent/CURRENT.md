# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Fase/Marco/US.

**Fase:** **FOUNDATION F-A + F-B FECHADA via ritual Spec Kit**
(2026-05-19). Próximo: backlog Wave-A (#7/#8) → Marco 1 `clientes`
definitivo → Marco 2 `equipamentos`. **Modo:** AUTÔNOMO.

## Virada de método (decisão Roldão 2026-05-19)

Remendo auditoria-a-auditoria não convergia — causa de fundo: o ritual
Spec Kit foi pulado em F-A/F-B. Decisão: recriar spec FORWARD do zero
(governa o código) + ritual completo + reconciliar código existente.
Programa P1..P9: F-A primeiro, F-B sobre F-A fechada (lição C1⇄C3).

Trabalho válido anterior NÃO descartado — foi validado pela spec
(FB-C1+C3 `32aa278`, FB-C2 `53e3cc2`, FB-C4+C5 `7924390` seguem de pé).

## F-A FECHADA via ritual (commits `4951389`..`f3711d7`)

- P1 spec forward `docs/faseamento/F-A/spec.md` (substitui stories-f-a).
- P2 plan + review 3 subagentes (tech-lead/advogado/RBC) → bloqueantes
  absorvidos (eliminação×imutabilidade LGPD, marco de corte CGCRE,
  grants test=prod, etc.).
- P3 matriz: núcleo OK; 8 GAPs → T-FA-01..08.
- P4: 7 fechados causa-raiz + T-FA-08→ADR-0020. Suite 280, hooks
  130/130, makemigrations limpo.
- P5: **3 auditores Família 5 = PASS, ZERO CRÍTICO/ALTO/MÉDIO.**
  Reparos MÉDIO/BAIXO resolvidos na causa-raiz (INV-RITUAL-001 —
  MÉDIO bloqueia fechamento). Consolidado:
  `docs/faseamento/F-A/auditoria-familia5.md`.

Gates Wave A rastreados (não bloqueiam F-A dogfooding): GATE-1..7
(B2/WORM, verificação periódica, NTP, ciclo chave PII, hash
AcessoDadosCliente, ADR-0020, higiene pattern `::uuid`).

## F-B FECHADA via ritual (P6..P9)

P6 spec forward → P7 plan + review tech-lead+advogado (bloqueantes
absorvidos: binding, vigência única, ip_hash HMAC contexto,
atomicidade≠commit, allowlist anti-PII, GATE-FB-2/3/4) → P8 matriz +
6 T-FB causa-raiz (T-FB-01..06) → P9 **3 auditores Família 5 = PASS,
ZERO CRÍTICO/ALTO/MÉDIO**. Suite 293, cobertura 85.60%, hooks 130/130,
drills verdes. Consolidado: `docs/faseamento/F-B/auditoria-familia5.md`.
Gate de fechamento de fase = INV-RITUAL-001 (MÉDIO bloqueia igual a
CRÍTICO/ALTO; hook `ritual-gate-check.sh`).

**FOUNDATION (F-A + F-B) FECHADA pelo ritual completo.** A virada de
método convergiu — o ritual fechou de forma coerente o que o remendo
não fechava.

## Feito nesta sessão (2026-05-19)

- **INV-RITUAL-001** (commit `ca8909e`, no servidor): MÉDIO bloqueia
  avanço de fase, igual a CRÍTICO/ALTO. Regra em REGRAS-INEGOCIAVEIS +
  hook `ritual-gate-check.sh` (PreToolUse Write|Edit) + 3 prompts de
  auditor + ritual. _test-runner 130/130. Pedido explícito do Roldão.
- **Lint sweep #7** (commit `3aeb3d4`, no servidor): ruff 193→0,
  format 100%, avisos de critério na causa-raiz. Suíte 293 verde em
  ordem fixa. NÃO reabre Foundation.
- **Expansão Família 5: 4 → 10 auditores** (commit `3fb9caa`, no
  servidor): Tier 1+2+3 completo motivado pelo bug `sanitizar_payload_audit`
  que passou em PASS dos auditores 1.0.0. Tier 1 endurece 3 prompts
  existentes (bump 1.1.0 stable) com TST-005..007 + SEC-SANITIZE-001.
  Tier 2 cria `auditor-llm-correctness` (LLM-001..003, Opus 4.7). Tier 3
  cria 5 auditores novos: performance (PERF-001..003), observabilidade
  (OBS-001..003), idempotência (IDEMP-001..002), supply chain
  (DEP-001..003), conformidade-LGPD mecânico (LGPD-MEC-001..003).
  Severidade consistente com INV-RITUAL-001 — MÉDIO+ bloqueia fechamento.
  AGENTS §5 + catálogo + memória `project_no_human_consultants` alinhados.
  130/130 hooks verdes. Pendências rastreadas (não bloqueiam): hook
  pre-commit orquestrador, 10 GitHub Actions, métricas/trilha de operação.
- **Flake visão-360 RESOLVIDO na causa-raiz** (commit `6c3e7b8`, no
  servidor): bug de PRODUÇÃO, não artefato de teste. `sanitizar_payload_audit`
  redigia `cliente_id` quando o UUID coincidia com regex de CPF/telefone
  (~8,4% dos uuid4). `registrar_auditoria` grava `payload_jsonb` cru; o
  endpoint sanitizava só na leitura → filtro do banco acerta evento, mas
  resposta volta com `cliente_id='[REDACTED]'`, quebrando correlação
  evento↔cliente na timeline da visão-360. Pista "depende de
  `pytest-randomly` seed" era ruído amostral (uuid4 vem de `os.urandom`).
  Fix: guard de UUID no ramo string do sanitizador antes das regexes —
  UUID é identificador surrogate, nunca PII (CPF/CNPJ/telefone/e-mail real
  jamais parseia como UUID). Cobre `cliente_id`, `usuario_id`,
  `causation_id`, qualquer chave UUID-valued. Regressão
  `tests/test_sanitizar_payload_audit.py` varre 5000 uuid4. Suíte
  **299 passed** (293→299), cobertura **85.85%** (85.60→85.85), hooks
  130/130. **MÉDIO sob INV-RITUAL-001 destravado.**
- **#8 médios rodada 2 F-A RESOLVIDOS** (commit `5aa1882`): R2-M1 +
  R2-M2 fechados na causa-raiz. R2-M1 (drill acumula lixo): drill é
  destrutivo-acumulativo por design (Auditoria INSERT-only + Tenant FK
  PROTECT), única limpeza é dropar+recriar banco; conserto = guard
  `--em-banco-descartavel` (aborta exit 2 se NAME ≠ test*) + contagem
  antes/depois honesta (Auditoria iterada por contexto, sem burlar RLS).
  R2-M2 (premissa Tenant globalmente legível): `isolamento-multi-tenant.md`
  §2.3.1 nova subseção explica galinha-e-ovo do middleware multi-tenant +
  segurança preservada (só metadados, sem PII); docstring de
  `verificar_integridade_cadeia` aponta pra §2.3.1. Validado: ruff +
  format + mypy 0 issues, pytest 299/85.85%, hooks 130/130, drill 5/5
  verde com contagem honesta (35T/21U/15093A operacional). Foundation
  intacta — não reabre auditoria.

## Marco 1 `clientes` via ritual Spec Kit — P1+P2+P3 (2026-05-19)

- **P1 spec forward** (commit `065161b`, no servidor): autoritativa
  em `docs/faseamento/M1-clientes/spec.md`. 5 US originais (cadastro,
  visão 360°, importação, bloqueio, dedup) + 12 non-goals + 4 INVs
  novos (INV-CLI-001 identidade canônica, INV-CLI-002 política LGPD
  única, SEC-CSV-001 anti-injection, INV-013-A contagem diária).
- **P2 plan + 4 reviews em paralelo** (commit `7c79295`): tech-lead +
  advogado + RBC + corretora. 10 pontos P-CLI-XN decididos
  (3 AJUSTADOS, 7 ACEITES). 18 bloqueantes adicionais absorvidos
  como AC novos. US-CLI-006 NOVA (direitos do titular, revogação,
  matriz eliminação vs anonimização, incidente ANPD, registro
  operações). Outbox transacional como padrão único Wave A
  cravado. Helper único `audit/event_helpers.py` cravado (SANEA-08).
- **P3 matriz spec↔código** (commit `f0249f0`): 24 OK, 20 GAP →
  T-CLI-101..120, 6 TRACK → GATE-CLI-1..6 (+2 modulares futuros).
  Correção do relatório do Explore: AC-CLI-001-4 e 003-7 estavam
  marcados OK; verificação direta no `lgpd.py:65-68` mostrou enum
  com 2 valores (spec exige 5) — GAP confirmado.

## Marco 1 P4 — execução T-CLI causa-raiz (em andamento)

- **T-CLI-103 ✅ FECHADO** (commit `4124a81`, no servidor):
  identidade canônica via `cliente_canonico_id`. Migration 0017 cria
  coluna NOT NULL com backfill `GENERATED ALWAYS AS (id) STORED` +
  `DROP EXPRESSION` (PG 12+) — preenche sem precisar UPDATE sob RLS.
  Trigger BEFORE INSERT defesa em profundidade. Model `save()` atribui
  `cliente_canonico_id=self.id` se None. Novo módulo `canonico.py`
  com `resolver_cliente_canonico` (cap=10, path compression em UPDATE
  quando hops>1, fail-loud `IdentidadeCanonicaCircular` em ciclo).
  6 testes (default, 1 mesclagem, 2 mesclagens com path compression,
  ciclo, cap excedido, property-based 100 cadeias). Suíte 305 passed
  (era 299 → +6), zero regressão US-CLI-005. Lint+mypy+migrations
  zero issues. Hooks 130/130.

## Próximo passo (retomar) — tarefa ativa

**P4 continua — 19 T-CLI restantes**. Sequência sugerida da próxima
sessão:

1. T-CLI-101 (enum LGPD 5 bases + 3 origens + lia_id)
2. T-CLI-102 (ClienteIdentidadeHistorico — depende de save() do
   Cliente já refatorado por T-CLI-103)
3. T-CLI-113 (trigger PG BEFORE UPDATE validando transição
   cliente_canonico_id self→vencedor_vivo + hook `cliente-canonico-
   imutavel.sh`) — defesa em profundidade do T-CLI-103
4. T-CLI-105 (event_helpers.py único + job INV-013-A)
5. T-CLI-107 (bus_outbox) + T-CLI-110 (worker em F-A)
6. T-CLI-104 (circuit breaker AcessoDadosCliente)
7. T-CLI-114..120 (US-CLI-006 inteira — pré-condição dogfooding PII real)
8. T-CLI-111 + T-CLI-112 (GET dedup compare + tipo_mesclagem +
   evidencia_documental_id)
9. T-CLI-106 (importação legada — alinhamento de origens)
10. T-CLI-108 + T-CLI-109 (payload Cliente.Bloqueado + predicate
    bloqueado_para_entrega) — gates de módulos futuros

P5 (10 auditores Família 5, loop até PASS zero CRÍTICO/ALTO/MÉDIO) só
quando P4 concluído e drill `validar_m1_clientes` (T-CLI a desenhar)
verde.

## Fila

#6 flake visão-360 ✅ + #7 lint sweep ✅ + #8 médios rodada 2 F-A ✅ +
Marco 1 P1+P2+P3 ✅ + T-CLI-103 ✅. Próxima: T-CLI-101..120 restantes
(19 tarefas) → P5.
