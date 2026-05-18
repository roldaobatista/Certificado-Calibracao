---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-EQP-005
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-005.md
historico:
  - 2026-05-18 noite final — criado forward-looking. Foto evidência migrou pra US-EQP-006 (TL6).
---

# Tasks T-EQP-049..T-EQP-056 — US-EQP-005 (sucatar equipamento + notificação cliente)

> Forward-looking. Pré-requisitos: US-EQP-001 + porta `OSQueryService` (US-001) + porta `CertificadoQueryService` (US-001). Idempotency-Key reusa `T-EQP-049/050` (decorator `@idempotent` US-EQP-004).

## Mapa task → arquivo/migration → AC → INV → endereça ressalva

| Task | Descrição | Arquivo/Migration | AC | INV | Endereça |
|---|---|---|---|---|---|
| T-EQP-049 | Porta `NotificacaoClienteService` em `src/domain/.../ports/` + `EmptyNotificacaoClienteServiceAdapter` (loga warning + grava audit `notificacao_status="pendente_consumer"`) + binding em settings; override `skip-empty` permitido em dev/test | `src/domain/.../ports/notificacao_cliente_service.py` + adapter | AC-3 | — | TL4 (payload `pendente_consumer` + `controles-compensatorios-codigo-ia.md`) |
| T-EQP-050 | Estender `CertificadoQueryService` com `equipamento_tem_certificado_vigente() -> CertificadoSummary \| None` (`EmptyCertificadoQueryService` retorna `None`) | `src/domain/.../ports/certificado_query_service.py` | AC-2 | — | TL2 (porta correta — fix `api.md:143`) |
| T-EQP-051 | ~~Foto evidência sucatamento~~ → **REMOVIDA** (migra pra US-EQP-006 que cria `FotoStorageService` formal) | — | — | — | TL6 (MÉDIA — foto migra) |
| T-EQP-052 | Trigger PG `bloquear_saida_de_sucata` padrão **`SECURITY DEFINER`** com função `marcar_extraviado_de_sucata()` + flag `set_config('afere.bypass_sucata_trigger', 'on', true)` local à transação (espelho `auditoria_bloqueia_mutation`); migration 0016 | `0016_trigger_sucata_terminal.py` | AC-2 | — | TL1 (CRÍTICA — anti-brechas shell/ORM/raw SQL) |
| T-EQP-053 | Use case `SucatarEquipamento`:<br/>(a) idempotente (mesmo status `sucata` → 200);<br/>(b) sem OS aberta via `OSQueryService` — senão 409;<br/>(c) `confirmacao_dupla` como **objeto** `{ tipo: enum, ts_marcacao, ts_confirmacao, intervalo_min_ms: 1500 }` (Marco 2 só `tipo="checkbox_modal"`; A3 V2);<br/>(d) cert vigente sem confirmação → 412; com confirmação → audit `equipamento.sucateado_com_certificado_vigente` + notifica;<br/>(e) sem cert → audit `equipamento.sucateado`;<br/>(f) dispensa dogfooding: `cliente_atual_id == tenant_proprietario_id` pula notificação + audit variante `_uso_interno`;<br/>(g) payload audit com `notificacao_template_versao` + `notificacao_canal` (enum) | `src/application/.../sucatar_equipamento.py` | AC-1, AC-2, AC-3, AC-4 | — | TL3 (`select_for_update`), TL5 (objeto extensível), R2/R6 advogado |
| T-EQP-053a (NOVA) | Template e-mail PT `notificacao_sucatamento_cert_vigente.html` v1.0-2026-05-18 — whitelist semântica anti-CTA (`agende`, `promoção`, `desconto`, `clique aqui` fail no teste); `{tenant_canal_atendimento}` (NUNCA canal do Aferê — operador) | `src/infrastructure/equipamentos/templates/email/notificacao_sucatamento_cert_vigente.html` | AC-3 | — | R1 advogado (sem CTA) + R5 (Aferê é operador) |
| T-EQP-054 | Action `equipamento.sucatear` no seed authz (migration 0017); perfis admin + metrologista (NÃO atendente, NÃO almoxarife) | `0017_seed_authz_sucatear.py` | AC-1 | SEC-LEAST-PRIV | — |
| T-EQP-055 | Rate limit 10 req/min/usuário (mutação destrutiva) | middleware (já existe US-004) | AC-1 | — | — |
| T-EQP-056 | Suite 16 testes: happy sem cert (audit `equipamento.sucateado`), cert vigente sem confirmação 412, com confirmação grava `_com_certificado_vigente` (RBC B5), dispara notificação via porta (mock), OS aberta 409, idempotente 200 segundo call, terminal (trigger PG bloqueia ativo), admin pode pra `extraviado` (Django), payload audit só `cliente_atual_id_hash` (sem nome/CPF/CNPJ/email — R3), authz metrologista vs atendente, idempotency-key 24h, **+ trigger bypass via set_config (TL1)** **+ dispensa dogfooding `_uso_interno` (R6)** **+ whitelist semântica template (R1)** | `tests/equipamentos/test_us_eqp_005_sucatear.py` | AC-1, AC-2, AC-3, AC-4 | — | todas |

## Pareceres aplicados

- `revisoes/US-EQP-005-tech-lead.md` — APROVADO COM RESSALVAS (TL1 CRÍTICA trigger SECURITY DEFINER, TL2 CRÍTICA porta correta — **JÁ CORRIGIDO** em api.md:143, TL3 ALTA idempotência + select_for_update, TL4 ALTA payload `pendente_consumer`, TL5 MÉDIA confirmacao_dupla objeto extensível, TL6 MÉDIA foto migra US-006)
- `revisoes/US-EQP-005-advogado.md` — APROVADO COM RESSALVAS (R1 CONCERN whitelist anti-CTA, R2 payload completo `template_versao`/`canal`, R3 teste negativo PII, R4 aviso UX foto migra junto, R5 Aferê é operador, R6 dispensa dogfooding)

## Total

10 tasks (9 originais + 1 nova; T-EQP-051 removida) · 16 testes · 1 migration trigger · 1 template e-mail v1.0 versionado.
