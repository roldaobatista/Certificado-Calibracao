---
owner: roldao
revisado_em: 2026-05-19
proximo_review: 2026-08-19
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 1 — clientes
tipo: plano-tecnico
relacionados:
  - docs/faseamento/M1-clientes/spec.md
  - docs/faseamento/F-A/spec.md
  - docs/faseamento/F-B/spec.md
---

# Marco 1 (clientes) — Plano técnico (P2)

> **Pra quê:** traduz cada US-CLI-NNN da `spec.md` em decisão técnica
> concreta (onde mora, fronteiras transacionais, contratos de evento,
> hooks). Plano é input dos 4 revisores subagentes (tech-lead, advogado,
> RBC, corretora). Pontos abertos da spec §6 marcados aqui pra cada
> revisor responder. Reconciliação spec↔código fica em P3 (`tasks.md`).

---

## Decisão arquitetural geral

- **Camada de domínio** (`src/domain/comercial/clientes/`, ADR-0007):
  agregado `Cliente` com invariantes (`assert_invariant_lgpd`,
  `assert_invariant_documento`, `assert_invariant_identidade_canonica`).
  Boundary `application/comercial/clientes/use_cases/` orquestra. Views
  DRF são fina camada de adaptação (Visitante/Caso de uso → DTO).
- **Sem ORM no domínio.** Repositório `RepositorioCliente` em
  `infrastructure/clientes/repositories.py` traduz domain↔ORM.
- **Helper único de evento** (SANEA-08 — DECIDIDO tech-lead §D):
  `src/infrastructure/audit/event_helpers.py` com função
  `publicar_evento(*, acao, escopo=Literal["auditoria","authz"]="auditoria",
  payload, causation_id, tenant_id, cadeia=True, outbox=True)` →
  `EventoPublicado`. Garantias não-negociáveis:
  1. Aplica `sanitizar_payload_audit` em ESCRITA (resolve
     `SEC-SANITIZE-001` — bug do flake visão-360).
  2. Valida `tenant_id` == contexto ativo (raise `TenantMismatch`).
  3. Cadeia + outbox no **mesmo `transaction.atomic` do chamador**
     (helper não abre transação própria).
  4. Idempotente em `(causation_id, acao)` (UNIQUE no outbox).
  Quando é OK NÃO usar o helper: (a) dentro de `audit/` e
  `multitenant/` (circular import — usar `registrar_em_cadeia` direto),
  (b) testes que exercitam a primitiva, (c) management commands de
  migração one-off com `audit-immutability: skip` documentado. Hook
  `event-helper-unico.sh` bloqueia chamada direta a `registrar_em_cadeia`
  ou INSERT em `bus_outbox` fora da allowlist.
- **Outbox transacional como padrão único Wave A** (DECIDIDO
  tech-lead §A P-CLI-T2): tabela `bus_outbox(causation_id, acao,
  envelope_jsonb, tenant_id, criado_em, processado_em)` local ao
  schema tenant. Worker dedicado em `src/infrastructure/audit/
  outbox_worker.py` opera via helper `processar_outbox_em_contexto_tenant
  (linha)` morando na F-A (não em `clientes/`) — assegura
  `INV-TENANT-001..004` no caminho do worker. Cadeia F-A guarda a
  evidência regulatória (imutável, 25a); outbox guarda intenção de
  publicação (mutável até consumido).
- **Política LGPD num único lar** (SANEA-07, `INV-CLI-002`):
  `domain/comercial/clientes/lgpd_policy.py` — função pura
  `aplicar_base_legal(aceite_em, base_legal, declaracao_id, origem,
  lia_id_opcional) → AceiteLGPD`; chamada por (a)
  `CadastrarCliente`, (b) `AtualizarCliente`, (c)
  `ImportarClientesCSV`, (d) `RegularizarAceiteLegado`. Nenhuma
  cópia. `DeclaracaoLGPD` tem `controlador_id` (tenant_id ou
  `AFERE_PLATFORM`) + `tipo_titular` ∈ {`CLIENTE_FINAL_DO_TENANT`,
  `USUARIO_OPERADOR`, `CONTATO_TENANT`} — tenant publica declaração
  para clientes; Aferê publica para operadores.

## US-CLI-001 — Cadastro PF/PJ

- **Onde:** `application/comercial/clientes/cadastrar.py` (use case);
  `domain/comercial/clientes/cliente.py` (agregado);
  `infrastructure/clientes/views.py` `ClienteViewSet.create`.
- **Validação CPF/CNPJ:** VOs `CPF` e `CNPJ` em
  `domain/comercial/clientes/vo/` — `CNPJ` aceita alfanumérico
  (`[A-Z0-9]{14}` + DV) por ADR-0017. Construtor falha com
  `DocumentoInvalido` (mapped para HTTP 400 no adapter).
- **Dedup AC-CLI-001-3:** índice parcial existente
  `unique_doc_ativo` (migration 0006) — `INV-024`. Conflito = 409 +
  link.
- **Aceite LGPD AC-CLI-001-4:** `aceite_lgpd_em` + base_legal +
  declaracao_id obrigatórios — `assert_invariant_lgpd` no agregado;
  política única em `lgpd_policy.py`.
- **Evento + audit:** `cadastrar()` retorna `Cliente` + lista de
  eventos. Use case publica via helper único (SANEA-08); helper grava
  cadeia tenant (F-A) + bus (in-memory ou Celery, conforme
  configuração).

## US-CLI-002 — Visão 360°

- **Onde:** `application/comercial/clientes/visao360.py`;
  view `ClienteViewSet.visao360`.
- **Projeção `EventoTimeline`:** tabela `eventos_timeline` (já existe;
  populada por consumers de OS/Certificado/Fatura/NPS); leitura por
  `(tenant_id, cliente_resolvido_id, -timestamp)` (Wave A índice
  composto + cursor de paginação).
- **Resolução canônica AC-CLI-002-5** (`INV-CLI-001`): use case
  resolve `cliente_id` via `resolver_canonico` antes de filtrar.
  Política: encadeada com cap 10 hops, fail-loud se circular (não
  silenciar).
- **AcessoDadosCliente AC-CLI-002-3:** registrar
  `acessos_dados_cliente` (F-A `registrar_acesso_dados_cliente`)
  ANTES de renderizar — bloqueia resposta em caso de falha de
  gravação. Lock `pg_advisory_xact_lock` desnecessário (tabela é
  protegida por trigger anti-mutation, sem hash chain por
  AC-FA-005-7).
- **Paginação:** cursor por `(timestamp, id)` — limite 100/janela.

## US-CLI-003 — Importação CSV/XLSX

- **Onde:** `infrastructure/clientes/csv_io.py` + `csv_safety.py`
  (já existem); use case `application/comercial/clientes/importar.py`.
- **Idempotência (`IDEMP-001`):** `Idempotency-Key` obrigatório.
  Replay = mesmo `import_id`.
- **Lock transacional AC-CLI-003-3:** bulk_upsert dentro de
  `transaction.atomic` + `pg_advisory_xact_lock(<classe>,
  hashtext(tenant_id))` — SANEA-01 já fechado em `ef7d3c1`.
- **Anti-injection CSV `SEC-CSV-001`:** `sanitizar_celula_csv` em
  qualquer export de cliente — SANEA-03 fechado; spec formaliza ID
  novo.
- **HMAC importação AC-CLI-003-6:** `PII_HASH_KEY` server-side
  (F-A) — SANEA-02 fechado.

## US-CLI-004 — Bloqueio comercial

- **Onde:** `domain/comercial/clientes/bloqueio.py` (políticas);
  `infrastructure/clientes/management/commands/job_inadimplencia_alertas.py`
  (job Celery); endpoint `POST /clientes/{id}/bloquear/`.
- **Predicate `cliente.bloqueado` (F-B authz):** registrado em
  `predicates_authz.py` — retorna `denied` com `reason` específica
  (`AC-CLI-004-2`).
- **Outbox vs commit-na-cadeia (P-CLI-T2):** plano = commit-na-cadeia
  F-A — `registrar_em_cadeia(action="cliente.bloqueado", payload=...)`
  + publish via `Outbox` simples (tabela `bus_outbox`, processada por
  worker dedicado em Wave A). Atomicidade real: o registro na cadeia e
  o INSERT no outbox acontecem dentro da mesma `transaction.atomic`.
- **Job daily AC-CLI-004-3:** Celery cron 02:00 BRT,
  `Idempotency-Key=<data-iso>-<tenant_id>` — replay seguro.
- **Régua AC-CLI-004-4:** plano = job emite `RéguaCobrancaDispachada`
  em D+30, D+60, D+89; consumer `omnichannel` envia mensagem. Marco 1
  só publica; envio real é `comunicacao-omnichannel` (futuro). Em
  Marco 1 fica o predicate + emissor.
- **Reativação AC-CLI-004-5:** consumer
  `consumir_contas_receber_pago` (em
  `application/comercial/clientes/consumer_pagamento.py`) reavalia
  inadimplência; se zerou, publica `Cliente.Desbloqueado`.

## US-CLI-005 — Dedup manual

- **Onde:** `application/comercial/clientes/dedup.py` (use case);
  `infrastructure/clientes/mesclagem.py` (já existe — vai ser
  refatorado pra usar helper de evento único, SANEA-08).
- **Identidade canônica AC-CLI-005-3** (`INV-CLI-001`): coluna nova
  `cliente.cliente_canonico_id UUID NOT NULL DEFAULT id` (migration
  0017) — imutável após criar (constraint CHECK proibindo UPDATE de
  `cliente_canonico_id` exceto pra apontar pra vencedor na mesclagem;
  trigger PG valida transição válida: `self → vencedor_id_vivo`).
- **Resolver canônico** (`resolver_cliente_canonico`):
  `domain/comercial/clientes/canonico.py` — função pura recursiva,
  cap=10, raise `IdentidadeCanonicaCircular` se ciclo.
- **Histórico não migra** (AC-CLI-005-3 bullet 3): FK em OS/cert/
  fatura/contato/NPS continua apontando para `cliente.id` original;
  consultas usam o resolver. Decisão: zero update destrutivo, leitura
  paga o custo.
- **Atomicidade:** mesclagem inteira dentro de `transaction.atomic` +
  `pg_advisory_xact_lock(<classe_dedup>, hashtext(tenant_id))` (não
  reusar a classe da importação — locks distintos por domínio de
  contenção).

---

## Hooks novos / atualizações (P4)

| Hook | Status | Conserto |
|------|--------|----------|
| `lgpd-policy-unica.sh` | a criar | bloqueia chamada direta a `aceite_lgpd_*` fora de `lgpd_policy.py` (INV-CLI-002) |
| `cliente-canonico-imutavel.sh` | a criar | bloqueia migration que `ALTER COLUMN cliente_canonico_id` sem allow explícito (INV-CLI-001) |
| `csv-safety-import.sh` | a criar | bloqueia geração de CSV sem chamar `sanitizar_celula_csv` (SEC-CSV-001) — alvo: arquivos `*export*.py`/`*csv*.py` em path crítico |
| `event-helper-unico.sh` | a criar | bloqueia chamada direta a `registrar_em_cadeia` ou INSERT em `bus_outbox` fora da allowlist (audit/, multitenant/, testes da primitiva) — SANEA-08 / tech-lead §D |
| `inv-013a-contagem-diaria.sh` | a criar | valida que `OperacaoTratamentoCliente` e `AcessoDadosCliente` têm migração-irmã que cria job daily de contagem imutável (INV-013-A) |
| `migration-rls-check` (existente) | já cobre | nova tabela com tenant_id sem policy = block |
| `audit-immutability-check` (existente) | já cobre | trigger/policy auditoria intocada |
| Trigger PG `cliente_canonico_imutavel` | a criar (migration nova) | runtime — bloqueia UPDATE indevido de `cliente_canonico_id` (AC-CLI-005-7) |
| Trigger PG `cliente_identidade_historico_anti_mutation` | a criar | preserva trilha de mudança de razão social (AC-CLI-001-7) |

---

## Decisões dos 4 revisores (P2 concluído 2026-05-19)

Reviews dos 4 subagentes humano-substitutos absorvidas. Texto auditável
de cada P-CLI-XN em `spec.md` §6 ("Decisões dos 4 revisores"). Resumo
operacional aqui:

| Ponto | Veredito | Onde foi cravado |
|-------|----------|------------------|
| P-CLI-T1 (resolução canônica) | AJUSTADO — encadeada + materialização preguiçosa | spec AC-CLI-002-5 |
| P-CLI-T2 (outbox vs cadeia) | AJUSTADO — outbox transacional único | spec AC-CLI-004-7 + plan §"Decisão arquitetural" |
| P-CLI-T3 (god-class views) | ACEITE — refactor parte do Marco | spec §3 item 8 |
| P-CLI-A1 (bases legais) | AJUSTADO — 5 valores no enum | spec AC-CLI-001-4 |
| P-CLI-A2 (retenção 25a) | ACEITE fundamentação reforçada | spec AC-CLI-005-6 |
| P-CLI-A3 (fail-loud acesso) | ACEITE | spec AC-CLI-002-3 |
| P-CLI-R1 (certificado dedup) | AJUSTADO — snapshot + cadeia | spec AC-CLI-005-3 |
| P-CLI-R2 (bloqueio≠recall) | ACEITE com ressalva | spec AC-CLI-004-8 |
| P-CLI-S1 (hash chain) | AJUSTADO — INV-013-A | spec AC-CLI-002-7 |
| P-CLI-S2 (dedup segurável) | ACEITE 2 ajustes | spec AC-CLI-005-3 |

Bloqueantes novos absorvidos como AC adicionais (`spec.md`):
- Tech-lead B1 → AC-CLI-005-7 (trigger PG runtime + hook).
- Tech-lead B2 → AC-CLI-002-6 (circuit breaker observado).
- Tech-lead B3 → AC-CLI-004-11 (helper outbox em F-A — multi-tenant
  safe no worker).
- Tech-lead B4 (race recadastro) → detalhe de implementação P4
  (`pg_advisory_xact_lock(hashtext(tenant_id||documento))` no use
  case `CadastrarCliente`).
- Tech-lead B5 (ciclo canônico) → T-CLI operacional `runbook-
  quebrar-ciclo-canonico` em P3, com management command +
  auditoria especial. Não bloqueia fechamento; obrigatório antes
  do 1º tenant externo.
- Tech-lead B6 → SANEA-04 confirmado FECHADO via F-A FA-C1; P5
  reconfirma com 10 auditores.
- Advogado B1-B7 → US-CLI-006 (Direitos do titular, revogação,
  eliminação vs anonimização, dados sensíveis, criança, incidente
  ANPD, registro operações).
- RBC B1 → AC-CLI-001-7 (`ClienteIdentidadeHistorico`).
- RBC E1 → AC-CLI-004-9 (cancelar agenda futura).
- RBC E2 → AC-CLI-004-10 (calibração em execução conclui).
- Corretora D1 → spec §3 item 9 (suite anti-regressão dos 4 INVs).
- Corretora D2 → spec §3 item 10 (property-based resolver canônico).

---

## Critérios de saída do P2 (concluídos 2026-05-19)

- [x] 4 reviews concluídas; bloqueantes absorvidos.
- [x] Spec corrigida cravando os 10 vereditos + 18 bloqueantes
      adicionais.
- [x] Plan finalizado com decisões cravadas e hooks novos enumerados.
- [x] Helper único + outbox transacional cravados na §"Decisão
      arquitetural geral" como padrão Wave A.

**P3 começa.**
