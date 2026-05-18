---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: reference
audiencia: agente
us: US-EQP-001
plano: docs/dominios/suporte-plataforma/modulos/equipamentos/planos/US-EQP-001.md
historico:
  - 2026-05-18 noite final — criado forward-looking (Marco 2 Wave A — fundação módulo equipamentos).
---

# Tasks T-EQP-001..T-EQP-015 — US-EQP-001 (cadastrar equipamento + QR HMAC + snapshot perfil_tenant)

> Forward-looking. Implementação acontece na fase `/implement` desta US. Sequência revisada vem do plano stable (15 originais + 5 novas — TL1/TL3/TL5 tech-lead + R2 advogado).

## Mapa task → arquivo/migration → AC → INV → endereça ressalva

| Task | Descrição | Arquivo/Migration | AC | INV | Endereça |
|---|---|---|---|---|---|
| T-EQP-001 | App Django `src/infrastructure/equipamentos/` (apps.py, models.py, urls.py) | `src/infrastructure/equipamentos/` | AC-1 | — | — |
| T-EQP-002 | Entidade domain `Equipamento` (dataclass + invariantes) | `src/domain/suporte_plataforma/equipamentos/entities.py` | AC-1 | — | TL3 (camada domínio) |
| T-EQP-003 | Migration 0001_initial — tabela `equipamento` + UNIQUE `(tenant_id, tag)` + RLS `equipamento_tenant_isolation` | `0001_initial.py` | AC-1 | INV-049, INV-TENANT-001 | hook `migration-rls-check` + `policy-test-coverage` |
| T-EQP-004 | Migration 0002 — `perfil_tenant_no_momento_cadastro` enum + trigger `equipamento_anti_update_perfil_snapshot` (RBC B4) | `0002_perfil_tenant_snapshot.py` | AC-3 | RBC B4 | TL4 (trigger sintaxe `IS DISTINCT FROM` + ERRCODE) |
| T-EQP-005 | VO `Tag` (≤30 chars, alfanumérico + hífen) | `src/domain/suporte_plataforma/equipamentos/value_objects.py` | AC-1 | INV-049 | — |
| T-EQP-006 | Regex anti-PII em `localizacao_fisica` (reusa `src/domain/shared/pii_guard.py` Marco 1) | `pii_guard.py` (estendido) | AC-1 | INV-EQP-LOC-001 | R1 advogado (texto PT) |
| T-EQP-007 | `qr_token.py` — `gerar_hash_qr(equipamento_id, tenant_id, emitido_em) -> str` (HMAC-SHA256 + `settings.KMS_QR_SECRET`) | `src/infrastructure/equipamentos/qr_token.py` | AC-2 | INV-051 | TL1 (env-only em prod) |
| T-EQP-007a (NOVA) | Hook `qr-hmac-check.sh` + 4 casos `_test-runner.sh` (4 regras TL1) | `.claude/hooks/qr-hmac-check.sh` + `_test-runner.sh` | AC-2 | INV-051 | TL1 (BLOQUEADOR) |
| T-EQP-008 | Model `QrCode` + migration 0003 — UNIQUE `hash` + RLS + trigger `bloquear_update_revogado_em_para_null` | `0003_qrcode.py` | AC-2 | INV-051 | — |
| T-EQP-009 | Porta `CertificadoQueryService` (Protocol) + `EmptyCertificadoQueryServiceAdapter` + binding `PORT_BINDINGS` | `src/domain/.../ports/certificado_query_service.py` + `src/infrastructure/equipamentos/adapters/` | AC-1 | — | TL3 (naming `Empty<Port>Adapter`) |
| T-EQP-010 | Porta `OSQueryService` + `EmptyOSQueryServiceAdapter` | `src/domain/.../ports/os_query_service.py` + adapter | AC-1 | — | TL3 |
| T-EQP-010a (NOVA) | `PORT_BINDINGS` em `config/settings/base.py` + `resolve_port()` em `src/infrastructure/shared/port_registry.py` | `base.py` + `port_registry.py` | AC-1 | — | TL3 (ALTA — naming portas) |
| T-EQP-011 | Use case `CadastrarEquipamento` (validação anti-PII + unicidade TAG + perfil snapshot + gera QR + audit sanitizado) | `src/application/suporte_plataforma/equipamentos/cadastrar_equipamento.py` | AC-1, AC-2, AC-3 | INV-049, INV-051, INV-EQP-LOC-001 | R2 advogado (payload sanitizado), R5 (409 anti-oracle) |
| T-EQP-011a (NOVA) | Teste regressão `test_audit_cadastrado_payload_sanitizado` + estender hook `audit-pii-salt-check` | `tests/equipamentos/test_audit_payload_sanitizado.py` + hook | AC-3 | INV-051 | R2 advogado (BLOQUEADOR) |
| T-EQP-012 | `EquipamentoSerializer` + `EquipamentoViewSet` (POST/GET-list/GET-detail) com authz | `serializers.py` + `views.py` | AC-1 | INV-AUTHZ-001 | — |
| T-EQP-013 | Migration 0004_seed_authz_equipamento — actions `equipamento.criar/ler/listar/imprimir_etiqueta` + perfis | `0004_seed_authz_equipamento.py` | AC-1 | SEC-LEAST-PRIV | TL6 (vincular `imprimir_etiqueta` ao endpoint `/qr`) |
| T-EQP-014 | Endpoint `GET /v1/equipamentos/{id}/qr` — PDF etiqueta com WeasyPrint (TL5) | `views.py` + Dockerfile (`libpango`) | AC-2 | — | TL5 (WeasyPrint reúso pra cert ISO 17025) |
| T-EQP-014a (NOVA) | Teste regressão hash SHA-256 do PDF | `tests/equipamentos/test_pdf_etiqueta_hash.py` | AC-2 | — | TL5 |
| T-EQP-015 | Suite de testes (~15+): happy path, TAG dup tenant, TAG dup cross-tenant, QR hash determinístico, ≥22 chars base64url, localização com CPF/nome próprio, perfil snapshot imutável, cliente outro tenant 422 sem oracle, audit sem PII, authz, PDF etiqueta, **+ cross-tenant mesma TAG retorna 201 ambas (R5)** **+ KMS_QR_SECRET dev warning (TL1)** **+ payload audit só hashes/públicos (R2)** | `tests/equipamentos/test_us_eqp_001_completa.py` | AC-1, AC-2, AC-3 | INV-049, INV-051, INV-EQP-LOC-001, INV-TENANT-001 | todas |

## Pareceres aplicados

- `revisoes/US-EQP-001-tech-lead.md` — APROVADO COM RESSALVAS (TL1 BLOC env-only KMS, TL2 BLOC cadastro provisório non-goal, TL3 portas naming, TL4 trigger PG, TL5 WeasyPrint, TL6 NIT action)
- `revisoes/US-EQP-001-advogado.md` — APROVADO COM RESSALVAS (R1 texto PT anti-PII, R2 BLOC payload sanitizado, R3 base legal, R4 NIT non-goal LGPD, R5 409 anti-oracle)

## Total

20 tasks (15 originais + 5 novas) · ~18 testes · 4 migrations · 1 hook novo (`qr-hmac-check.sh`).
