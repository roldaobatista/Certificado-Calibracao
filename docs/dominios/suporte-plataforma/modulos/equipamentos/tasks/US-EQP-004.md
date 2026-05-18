---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-EQP-004
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-004.md
historico:
  - 2026-05-18 noite final — criado forward-looking. Dívida portal-cliente OTP fica Wave B+ (transferencia-aceite-presencial-marco2.md).
---

# Tasks T-EQP-038..T-EQP-051a — US-EQP-004 (transferir equipamento intra-tenant com aceite duplo)

> Forward-looking. Pré-requisitos: US-EQP-001 + US-EQP-002 + Marco 1 clientes (`BloqueioClienteQueryService`).

## Mapa task → arquivo/migration → AC → INV → endereça ressalva

| Task | Descrição | Arquivo/Migration | AC | INV | Endereça |
|---|---|---|---|---|---|
| T-EQP-038 | Model `TransferenciaEquipamentoAceite` (migration 0013) — campos cravados modelo v3: `equipamento_id`, `cliente_origem_id_hash`, `cliente_destino_id_hash`, `motivo_categoria`, `motivo_detalhe_hash`, `consentimento_compartilhamento` (imutável — TL4), `aceite_origem_em/versao_texto_id/ip_hash/via/atendente_user_id/evidencia_storage_key` + mesmo pra destino, `usuario_id_tenant` + RLS + trigger `bloquear_update_aceite_apos_concretizado` estendido pra `texto_renderizado_hash` (R5) | `0013_transferencia_aceite.py` | AC-1, AC-2, AC-3 | INV-050, INV-025 | TL4 (consentimento imutável), R2 (campos atendente + evidência), R5 (texto renderizado hash) |
| T-EQP-039 | `texto_versao_transferencia.py` — `VERSAO_VIGENTE = "v1.0-2026-05-18"` + `TEXTOS_HISTORICOS` com termo completo R1 advogado (cláusulas LGPD art. 18, Lei 14.063/2020 art. 4º I, não-cessão NF-e/cert/responsabilidades) | `src/infrastructure/equipamentos/texto_versao_transferencia.py` | AC-2 | — | R1 advogado (BLOQUEANTE — texto v1.0) |
| T-EQP-040 | Enum `motivo_categoria_transferencia` em domain enums: `venda / comodato / doacao / correcao_cadastral / outro` | `src/domain/.../enums.py` | AC-3 | — | — |
| T-EQP-041 | Regex anti-PII em `motivo_detalhe` (reusa `pii_guard.py`; limite 300 chars — R3) | `pii_guard.py` (consumido) | AC-3 | INV-EQP-LOC-001 análoga | R3 advogado (300 chars) |
| T-EQP-042 | Adapter `DjangoBloqueioClienteQueryService` reusa Marco 1 (`cliente.bloqueado` + `cliente.tem_fatura_aberta`) | `src/infrastructure/equipamentos/adapters/django_bloqueio_cliente.py` | AC-1 | — | — |
| T-EQP-043 | Porta `FinanceiroQueryService` + `EmptyFinanceiroQueryServiceAdapter` (sempre `tem_fatura_aberta=False`) + binding allowed em dev/test via `# port-binding: empty-allowed -- modulo financeiro ainda nao existe`; **bloqueado em prod até módulo financeiro nascer** | `src/domain/.../ports/financeiro_query_service.py` + adapter | AC-1 | — | TL5 ADR-0015 |
| T-EQP-044 | Use case `TransferirEquipamento` com `@transaction.atomic` + `select_for_update()` no Equipamento + **1 SELECT tenant-scoped único** (TL2) + ordem dura TL5 (Idempotency-Key → payload sintático → authz → existência 422 → bloqueio 412 → lock+update); reason 422 idêntico anti-oracle; `cliente_id_original_hash` permanece imutável; setar `mostrar_historico_anterior` conforme aceite cedente (default false — RBC B6); audit `equipamento.transferido` payload sanitizado | `src/application/.../transferir_equipamento.py` | AC-1, AC-2, AC-3, AC-4 | INV-050, INV-025 | TL1 (atomicidade), TL2 (oracle), TL5 (ordem), R4 advogado (payload `texto_versao_id` + `aceite_*_via`) |
| T-EQP-045 | `EquipamentoSerializer` (ficha 360°) — se cessionário visualiza e `mostrar_historico_anterior=false`, oculta certs anteriores à transferência + banner "histórico anterior preservado mas confidencial" | `src/infrastructure/equipamentos/serializers.py` | AC-2 | — | TL4 (derivada `mostrar_historico_anterior`), RBC B6 |
| T-EQP-046 | Action `equipamento.transferir` no seed authz (migration 0014); perfis admin/metrologista/atendente; predicate `tenant_nao_suspenso` (ADR-0015) | `0014_seed_authz_transferir.py` | AC-1 | SEC-LEAST-PRIV | ADR-0015 |
| T-EQP-047 | Rate limit 10 req/min/usuário (mutação destrutiva — Redis) | `src/infrastructure/equipamentos/middleware.py` (estendido) | AC-1 | — | — |
| T-EQP-047a (NOVA) | Aviso UX checkbox ciência CLT art. 482 "a" + CP art. 299 obrigatório (Tela 8 `ui.md` v3) — texto `mensagens_aceite_presencial.py` | `mensagens_aceite_presencial.py` | AC-2 | — | R2 advogado (BLOQ — aceite presencial = fraude mitigação) |
| T-EQP-048 | Suite 19 testes: happy path, cross-tenant 422 sem oracle (+ fuzzing 100 UUIDs respostas byte-idênticas — TL2), cliente bloqueado 412, fatura aberta 412 (stub fixa True), sem aceite origem/destino 400, motivo_detalhe com CPF 400, motivo_categoria inválido 400, `cliente_id_original_hash` imutável, cessionário sem consentimento não vê certs, cessionário com consentimento vê, payload audit só hashes/categorias, aceite_versao_texto_id referencia constante, authz, idempotency-key 24h, **+ 4 testes R6 advogado** **+ 1 fuzzing TL2** | `tests/equipamentos/test_us_eqp_004_transferencia.py` | AC-1, AC-2, AC-3, AC-4 | INV-050, INV-025 | todas |
| T-EQP-049 (NOVA) | Migration `idempotency_key` (PG, NÃO Redis — durabilidade transacional) + RLS | `0015_idempotency_key.py` | AC-1 | — | TL3 (ALTA — Idempotency-Key durável) |
| T-EQP-050 (NOVA) | Decorator `@idempotent` em `src/infrastructure/shared/idempotency.py` (TTL 24h; mensagem PT 409 R6) | `src/infrastructure/shared/idempotency.py` | AC-1 | — | TL3 + R6 advogado |
| T-EQP-051a (NOVA) | Trigger `bloquear_update_aceite_apos_concretizado` estendido pra `texto_renderizado_hash` (R5) | `0013_transferencia_aceite.py` (mesma migration) | AC-2 | — | R5 advogado |

## Pareceres aplicados

- `revisoes/US-EQP-004-tech-lead.md` — APROVADO COM RESSALVAS (TL1 CRÍTICA atomicidade, TL2 CRÍTICA oracle, TL3 ALTA idempotency PG, TL4 ALTA consentimento imutável + derivada, TL5 ordem dura, TL6 ip_hash canonização IPv6)
- `revisoes/US-EQP-004-advogado.md` — APROVADO COM RESSALVAS (R1 BLOQ texto v1.0, R2 BLOQ aceite presencial mitigação tríplice, R3 motivo 300 chars, R4 payload `via`/`texto_versao_id`, R5 trigger estendido, R6 mensagem PT 409)

## Total

16 tasks (12 originais + 4 novas) · 19 testes · 3 migrations + `idempotency_key` · 1 termo v1.0 versionado.
