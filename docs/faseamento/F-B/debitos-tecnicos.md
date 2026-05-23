---
fase: F-B (Auth + RBAC) — débitos técnicos pra Wave A
status: stable
owner: tech-lead-saas-regulado
revisado-em: 2026-05-23
revisado-por: auditor-qualidade + auditor-seguranca (Onda 3 saneamento)
origem: Auditor 2 — Onda 3 saneamento pré-Marco 3 OS
relacionado:
  - docs/faseamento/F-B/tasks-saneamento.md
  - docs/adr/0038-familia-inv-auth.md
  - docs/adr/0006-feature-flags.md
  - docs/adr/0012-autorizacao-unificada.md
---

# F-B — Débitos técnicos diferidos para Wave A

> Lista os itens que **não bloqueiam** Marco 3 OS, mas precisam ser endereçados **antes do 1º tenant externo pago**. Cada débito tem owner-candidate, story Wave A onde entra e critério de aceite mínimo.

---

## Débito 1 — FK perfil em `auth_usuario_perfil` (T-FB-SAN-09 / F-B-B1)

**Sintoma atual:** `auth_usuario_perfil.perfil` é `CharField(max_length=64)` carregando o `codigo` do perfil (ex.: `"financeiro"`). Não é FK pra `authz_perfil(id)`.

**Risco:** rename de perfil → string fica órfã silenciosa; INSERT com typo (`"finaceiro"`) passa.

**Proposta:**
- Migration Wave A `00XX_authz_usuario_perfil_fk.py`:
  1. ALTER TABLE adiciona `perfil_id UUID NULL REFERENCES authz_perfil(id) ON DELETE PROTECT`.
  2. Data migration: `UPDATE auth_usuario_perfil SET perfil_id = (SELECT id FROM authz_perfil WHERE codigo = auth_usuario_perfil.perfil AND tenant_id IS NULL)`.
  3. ALTER COLUMN `perfil_id` SET NOT NULL.
  4. Mantém `perfil` (codigo) como denormalização — atualizada por trigger pós-INSERT/UPDATE (cache RBAC consulta sem JOIN).
- Hook validador `authz-perfil-fk-check.sh`: bloqueia `auth_usuario_perfil.perfil = "X"` sem `perfil_id` correspondente.

**Story Wave A:** US-FB-COMPL-01 (storage canônico autorização).

**AC mínimo:**
- `INSERT INTO auth_usuario_perfil (perfil = 'inexistente')` → falha (FK ou trigger).
- Rename de `authz_perfil.codigo` → cascateia em `auth_usuario_perfil.perfil` via trigger ou bloqueia rename (RESTRICT).

---

## Débito 2 — Feature flags por usuário/perfil (T-FB-SAN-06 / F-B-M1)

**Sintoma atual:** `tenant_features (tenant_id, codigo, ativo)` é tudo-ou-nada por tenant. Não permite "ativa só pro usuário X em beta" ou "ativa só pro perfil financeiro".

**Risco:** beta de feature crítica vira big-bang ou virada manual fora do sistema (hardcode).

**Proposta:**
- Migration Wave A `00XX_tenant_features_granularidade.py`:
  1. ALTER TABLE adiciona `perfil_id UUID NULL REFERENCES authz_perfil(id) ON DELETE CASCADE`.
  2. ALTER TABLE adiciona `usuario_id UUID NULL REFERENCES auth_usuario(id) ON DELETE CASCADE`.
  3. Constraint: `CHECK (perfil_id IS NULL OR usuario_id IS NULL)` — só um dos dois preenchido (granularidade hierárquica: tenant → perfil → usuário).
  4. `FeatureFlagEvaluator.is_enabled(codigo, usuario, tenant)` resolve em ordem: usuário > perfil > tenant.

**Story Wave A:** US-FB-COMPL-02 (feature flag granular).

**AC mínimo:**
- Flag ativada só pra usuário X: usuário Y do mesmo tenant não vê.
- Flag ativada só pra perfil P: usuário sem P no perfil ativo da sessão não vê.
- `EXPLAIN ANALYZE` da consulta `is_enabled` ≤ 5ms p95 (cache Redis).

---

## Débito 3 — Enroll TOTP real (T-FB-SAN-10 / F-B-B2)

**Sintoma atual:** F-B aceita MFA via django-otp (lib real) mas não tem **endpoint de enroll** — usuário não consegue cadastrar TOTP sozinho. Dev/test usa `MFA_BYPASS_PREFIX`; produção precisa enroll real.

**Risco:** 1º tenant externo não consegue ativar MFA → usa só senha → INV-AUTH-001..002 protegem parcialmente, mas defesa em profundidade ausente.

**Proposta:**
- View `/auth/mfa/enroll` GET → gera secret + QR code (PNG inline via `qrcode` lib + `pyotp`).
- View `/auth/mfa/enroll/verify` POST → recebe código TOTP, valida contra secret pendente, ativa.
- Tabela `auth_mfa_device` (já existe via django-otp `TOTPDevice`) — só plugar.
- Recovery codes: gerar 10 códigos uso-único `auth_mfa_recovery` na ativação; exibir uma única vez.
- Endpoint admin: desativar MFA de usuário (caso recovery perdido) — registra `RegistroAlterado`.

**Story Wave A:** US-FB-COMPL-03 (MFA enroll + recovery).

**AC mínimo:**
- Usuário faz enroll completo (escaneia QR, digita código, ativa) em <2min.
- Recovery code consumido vira inválido.
- Admin pode resetar MFA de outro usuário (registra evento + e-mail ao titular).

---

## Débito 4 — Eventos canônicos publisher (T-FB-SAN-04 continuação)

**Sintoma atual:** doc `acesso-seguranca/eventos.md` está completo (Onda 3) mas **não há publisher real** chamando `EventBus.publish()` nos signals de login.

**Proposta:**
- Signal `user_logged_in` → publica `AcessoSeguranca.LoginSucesso`.
- Signal `user_logged_out` → publica `SessaoEncerrada` (motivo `logout_explicito`).
- Signal `user_login_failed` → publica `LoginFalha`.
- Middleware idle timeout → publica `SessaoEncerrada` (motivo `idle_timeout`).
- Worker `expurga_sessoes_max_absoluto` → publica `SessaoEncerrada` (motivo `max_absoluto`).
- `PasswordChangeView.form_valid` → publica `SenhaTrocada`.
- Hook `event-publisher-check.sh`: valida que `acesso-seguranca/*.py` ao tocar campos sensíveis (`last_login`, `auth_token_revoked_at`, `password`) chama `EventBus.publish()` mesmo.

**Story Wave A:** US-FB-COMPL-04 (publisher canônico auth).

**AC mínimo:**
- Login bem-sucedido → linha em audit-sink + linha no bus.
- 5 falhas em 15min → `LoginBloqueado` no bus + bloqueio efetivo no banco.

---

## Débito 5 — ABAC contextual (T-FB-SAN-02 continuação)

**Sintoma atual:** RBAC plano (perfil × ação binária) cobre cenários canônicos. Mas Marco 4 (US-CAL-006 signatário) exige contexto: "RT signa só se `RTCompetencia.vigencia_em(data_assinatura).cobre(grandeza_certificado)`".

**Proposta:**
- Porta `AuthorizationProvider.can(user, action, resource, contexto: dict)` já existe em ADR-0012.
- Implementação Wave A: `RuleEvaluator` lê `auth_rule_abac` (tabela nova) → expressão DSL (subset Python avaliada com `RestrictedPython` ou `simpleeval`).
- Exemplo regra: `acao = "certificado.emitir"` AND `resource_kind = "Certificado"` → `evaluator: "rt_competencia_cobre(user_id, contexto['grandeza'], contexto['data'])"`.
- Função `rt_competencia_cobre` lê `RTCompetencia` (Marco 2 retrofit ADR-0022).

**Story Wave A:** US-CAL-AUTHZ-01 (ABAC RT competência).

**AC mínimo:**
- RT com competência vigente em "massa" tenta emitir certificado de "tempo" → 403 + evento `AcessoNegado(motivo: "escopo_recurso")`.
- RT com competência expirada (vigência terminou) tenta emitir → 403.
- RT com competência vigente cobrindo grandeza → 200 + certificado emitido + audit síncrono.

---

## Resumo

| # | Débito | Story Wave A | Bloqueia |
|---|---|---|---|
| 1 | FK perfil em UsuarioPerfilTenant | US-FB-COMPL-01 | 1º tenant externo (rename perfil seguro) |
| 2 | Feature flags por usuário/perfil | US-FB-COMPL-02 | nada — qualidade-de-vida operacional |
| 3 | Enroll TOTP + recovery | US-FB-COMPL-03 | 1º tenant externo (defesa em profundidade) |
| 4 | Publisher eventos auth | US-FB-COMPL-04 | auditoria LGPD do 1º tenant externo |
| 5 | ABAC RT competência | US-CAL-AUTHZ-01 | Marco 4 (signatário ISO 17025) |

Total: **5 débitos rastreados**. Nenhum bloqueia Marco 3 OS; débitos 1, 3, 4 bloqueiam 1º tenant externo; débito 5 bloqueia Marco 4.
