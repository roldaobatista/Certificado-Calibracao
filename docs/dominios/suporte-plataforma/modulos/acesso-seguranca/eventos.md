---
modulo: acesso-seguranca
dominio: suporte-plataforma
documento: eventos canônicos publicados pelo módulo (catálogo v10)
status: draft
owner: tech-lead-saas-regulado
revisado-em: 2026-05-23
revisado-por: auditor-seguranca + advogado-saas-regulado (Onda 3 saneamento F-B)
relacionado:
  - docs/comum/integracoes-inter-modulos.md (catálogo mestre v10)
  - docs/adr/0038-familia-inv-auth.md (INV-AUTH-001..005)
  - docs/adr/0012-autorizacao-unificada.md (INV-AUTHZ-001..004)
  - REGRAS-INEGOCIAVEIS.md (INV-AUTH-*, INV-AUTHZ-*)
---

# Eventos canônicos — módulo `acesso-seguranca`

> **Origem:** Auditor 2 (Onda 3 saneamento pré-Marco 3 OS) detectou que login/MFA/troca-de-senha **não emitiam evento** apesar de constarem no catálogo v10. Sem evento, auditoria LGPD ("quem fez login em X?") fica incompleta e INV-AUTHZ-002 não cobre — INV-AUTHZ-002 é **autorização**, autenticação fica fora.
>
> Este doc é a **fonte de verdade** dos payloads dos 14 eventos `AcessoSeguranca.*` do catálogo v10. Quem implementa publisher (Marco 3+) consome este arquivo, não o catálogo (catálogo só lista nomes).

---

## Envelope comum (v10)

Todos os eventos seguem envelope canônico v10:

```json
{
  "envelope_version": "v10",
  "event_id": "<uuid4>",
  "event_type": "AcessoSeguranca.LoginSucesso",
  "event_version": "v1",
  "tenant_id": "<uuid|null>",
  "correlation_id": "<uuid>",
  "occurred_at": "<ISO8601 UTC>",
  "published_at": "<ISO8601 UTC>",
  "producer": {
    "modulo": "acesso-seguranca",
    "instancia": "<hostname>",
    "versao_app": "<semver>"
  },
  "payload": { ... }
}
```

`tenant_id` pode ser `null` para eventos de usuário ainda não-vinculado a tenant (ex.: `UsuarioCriado` antes do primeiro vínculo em `auth_usuario_perfil`).

---

## 1. `AcessoSeguranca.UsuarioCriado` — v1

**Quando:** novo registro em `auth_usuario` (Wave A admin cria, ou cliente externo se auto-cadastra).
**Consumidores canônicos:** `onboarding` (welcome flow), `email` (envio boas-vindas), `audit-sink` (WORM).

```json
{
  "usuario_id": "<uuid>",
  "email_hash": "<sha256_hex>",
  "criado_por_usuario_id": "<uuid|null>",
  "tenant_inicial_id": "<uuid|null>",
  "perfis_iniciais": ["atendente"],
  "metodo_criacao": "admin_manual | autocadastro | sso_provisionado | seed_migration"
}
```

PII direto (e-mail bruto) **proibido** — só `email_hash` (HMAC-SHA256 com salt rotativo).

## 2. `AcessoSeguranca.UsuarioDesativado` — v1

**Quando:** `auth_usuario.ativo = false` (LGPD art. 18 V, desligamento RH, fim de contrato).
**Consumidores:** `sessoes` (encerra todas as sessões ativas), `notificacoes` (e-mail ao admin), `audit-sink`.

```json
{
  "usuario_id": "<uuid>",
  "desativado_por_usuario_id": "<uuid|null>",
  "motivo": "rh_desligamento | lgpd_titular | inatividade_180d | bloqueio_seguranca | admin_manual",
  "sessoes_encerradas": 2
}
```

## 3. `AcessoSeguranca.LoginSucesso` — v1

**Quando:** autenticação completou (senha + MFA quando exigido).
**Consumidores:** `metricas` (dashboard), `alerta-localizacao` (login em país/IP novo), `audit-sink`.
**Relacionado:** INV-AUTH-001 (lockout), INV-AUTHZ-002 (audit síncrono cobre autorização subsequente).

```json
{
  "usuario_id": "<uuid>",
  "tenant_id_sessao": "<uuid>",
  "tenants_disponiveis": ["<uuid1>", "<uuid2>"],
  "metodo": "senha | sso_oidc | sso_saml | passkey_webauthn",
  "mfa_verificado": true,
  "mfa_metodo": "totp | recovery_code | bypass_dev | null",
  "ip_hash": "<hmac_sha256_hex>",
  "user_agent_hash": "<sha256_hex_primeiros_64>",
  "geo_country_code": "BR | XX"
}
```

## 4. `AcessoSeguranca.LoginFalha` — v1

**Quando:** tentativa de login não passou (senha errada, MFA errado, conta inativa, conta bloqueada).
**Consumidores:** `rate-limit` (lockout INV-AUTH-001), `alerta-burst` (>10 falhas/min mesmo IP), `audit-sink`.

```json
{
  "email_hash": "<sha256_hex>",
  "usuario_id_se_existe": "<uuid|null>",
  "motivo": "senha_errada | mfa_errado | conta_inativa | conta_bloqueada | usuario_inexistente",
  "tentativas_na_janela_15min": 3,
  "ip_hash": "<hmac_sha256_hex>",
  "user_agent_hash": "<sha256_hex>"
}
```

`motivo: "usuario_inexistente"` **nunca** é exposto na resposta HTTP (defesa contra enumeração) — só no evento canônico interno.

## 5. `AcessoSeguranca.LoginBloqueado` — v1

**Quando:** INV-AUTH-001 dispara (5 falhas em 15min) ou admin bloqueia manualmente.
**Consumidores:** `seguranca-saas` (incidente), `email` (notifica titular), `audit-sink`.

```json
{
  "usuario_id": "<uuid|null>",
  "email_hash": "<sha256_hex>",
  "motivo": "tentativas_excedidas | admin_manual | suspeita_credential_stuffing",
  "duracao_seg": 1800,
  "desbloqueio_previsto_em": "<ISO8601>",
  "ip_hash_origem": "<hmac_sha256_hex>"
}
```

## 6. `AcessoSeguranca.MfaVerificado` — v1

**Quando:** segundo fator validou após senha correta (passo intermediário antes de `LoginSucesso`).
**Consumidores:** `metricas`, `audit-sink`.

```json
{
  "usuario_id": "<uuid>",
  "metodo": "totp | recovery_code | bypass_dev",
  "device_id_hash": "<sha256_hex|null>",
  "tentativa_numero": 1
}
```

`metodo: "bypass_dev"` só aceito quando `settings.DEBUG=True` E `MFA_BYPASS_PREFIX` casa — produção rejeita.

## 7. `AcessoSeguranca.SessaoEncerrada` — v1

**Quando:** logout explícito, idle timeout (INV-AUTH-003), máximo absoluto, desativação de usuário, troca de senha.
**Consumidores:** `audit-sink`.

```json
{
  "usuario_id": "<uuid>",
  "sessao_id": "<uuid>",
  "motivo": "logout_explicito | idle_timeout | max_absoluto | desativacao_usuario | troca_senha | admin_revogou",
  "duracao_sessao_seg": 4837
}
```

## 8. `AcessoSeguranca.SenhaTrocada` — v1

**Quando:** usuário troca senha (self-service ou troca forçada INV-AUTH-004).
**Consumidores:** `email` (notifica titular), `sessoes` (revoga todas — exige re-login), `audit-sink`.

```json
{
  "usuario_id": "<uuid>",
  "motivo": "self_service | forcada_180d | forcada_admin | reset_via_email",
  "alterada_por_usuario_id": "<uuid>",
  "ip_hash": "<hmac_sha256_hex>",
  "sessoes_revogadas": 3
}
```

## 9. `AcessoSeguranca.SessaoRepudiada` — v1

**Quando:** titular reporta sessão suspeita ("não fui eu") ou detecção automática de fraude.
**Consumidores:** `seguranca-saas` (P1), `admin-tenant` (alerta), `audit-sink`.

```json
{
  "usuario_id": "<uuid>",
  "sessao_id": "<uuid>",
  "reportado_por": "titular | deteccao_automatica | admin_tenant",
  "indicios": ["geo_anomalo", "user_agent_novo", "horario_atipico"]
}
```

## 10. `AcessoSeguranca.PermissaoAlterada` — v1

**Quando:** matriz `authz_perfil_acao` muda (raro — migration) ou vínculo `auth_usuario_perfil` muda (vigência).
**Consumidores:** `cache-rbac` (invalida), `audit-sink`.

```json
{
  "tipo_alteracao": "matriz_perfil_acao | vinculo_usuario_perfil | vigencia_alterada",
  "perfil_id": "<uuid|null>",
  "usuario_id": "<uuid|null>",
  "antes": { "...": "..." },
  "depois": { "...": "..." }
}
```

## 11. `AcessoSeguranca.AcessoNegado` — v1

**Quando:** `AuthorizationProvider.can() = false` (autorização). Complementa INV-AUTHZ-002 (audit síncrono): este evento canônico vai pro bus, audit_decisions vai pra tabela WORM.
**Consumidores:** `metricas`, `alerta-anormal` (burst de negados), `audit-sink`.

```json
{
  "usuario_id": "<uuid>",
  "tenant_id": "<uuid>",
  "action": "certificado.emitir",
  "resource_kind": "Certificado",
  "resource_id": "<uuid>",
  "motivo": "perfil_sem_acao | tenant_diferente | escopo_recurso | vigencia_expirada"
}
```

## 12. `AcessoSeguranca.RegistroAlterado` — v1

**Quando:** registros em `auth_*` mudam (perfil de usuário, ativo/inativo, vínculo). Substitui audit genérico para a área de identidade.
**Consumidores:** `audit-sink`, `indexador-busca`.

```json
{
  "entidade": "auth_usuario | auth_usuario_perfil | auth_perfil",
  "entidade_id": "<uuid>",
  "alterado_por_usuario_id": "<uuid>",
  "campos_alterados": ["ativo", "perfis"],
  "antes": { "...": "..." },
  "depois": { "...": "..." }
}
```

## 13. `AcessoSeguranca.ConsentimentoAceito` / `.ConsentimentoRevogado` — v1

**Quando:** titular aceita/revoga finalidade LGPD específica (marketing, parceiros, biometria comercial).
**Consumidores:** módulos sensíveis (marketing-suite, parceiros, biometria), `audit-sink`.

```json
{
  "titular_id": "<uuid>",
  "finalidade_codigo": "marketing_email | parceiros_terceiros | biometria_comercial",
  "base_legal": "consentimento_art_7_I",
  "canal_aceite": "web_formulario | mobile_app | papel_digitalizado",
  "evidencia_hash": "<sha256_hex>"
}
```

## 14. `AcessoSeguranca.LGPDSolicitacaoAberta` / `.LGPDSolicitacaoConcluida` — v1

**Quando:** titular abre/conclui solicitação art. 18 (acesso, correção, eliminação, portabilidade).
**Consumidores:** workflow LGPD interno, `email` (titular), `audit-sink`.

```json
{
  "solicitacao_id": "<uuid>",
  "titular_id": "<uuid>",
  "tipo": "acesso | correcao | eliminacao | portabilidade | informacao",
  "prazo_legal_em": "<ISO8601 + 15d ou +5d conforme tipo>",
  "concluida_em": "<ISO8601|null>",
  "resultado": "atendida | parcialmente_atendida | recusada | pendente"
}
```

---

## Mapeamento INV-AUTH × evento

| Invariante | Evento(s) emitido(s) |
|---|---|
| INV-AUTH-001 (lockout) | `LoginFalha` (a cada tentativa), `LoginBloqueado` (no 5º) |
| INV-AUTH-002 (política senha) | `SenhaTrocada` (motivo `forcada_180d` ou `self_service`) |
| INV-AUTH-003 (sessão idle/máx) | `SessaoEncerrada` (motivo `idle_timeout` ou `max_absoluto`) |
| INV-AUTH-004 (troca forçada 90d) | `SenhaTrocada` (motivo `forcada_admin` ou `forcada_180d`) |
| INV-AUTH-005 (retenção 365d) | n/a — política de expurgo da tabela `auth_login_tentativa`, não evento |

---

## Non-goals

- Eventos de autorização granular (`Acesso.X.Lido`) — ficam em INV-AUTHZ-002 (audit síncrono WORM), não bus.
- Notificação push pra app mobile — consumida pelo módulo `notificacoes`, não duplicada aqui.
- Telemetria de performance (latência login, etc.) — Grafana/Axiom, não bus canônico.

## Itens a fazer (Wave A)

- [ ] Publisher Django signal pós-`login` / pós-`login_failed` / pós-`logout` emite os 14 eventos.
- [ ] Hook `event-publisher-check.sh` valida que módulo `acesso-seguranca` cita estes nomes ao chamar `EventBus.publish()`.
- [ ] Teste E2E `test_acesso_seguranca_eventos_canonicos_v10` cobre os 14 nomes.
- [ ] Consumer `audit-sink` grava todos em WORM B2.
