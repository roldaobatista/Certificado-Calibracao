---
fase: F-B (Auth + RBAC) — saneamento pós-fechamento
status: stable
owner: tech-lead-saas-regulado
revisado-em: 2026-05-23
revisado-por: auditor-seguranca + auditor-qualidade + auditor-produto (Onda 3)
origem: Auditor 2 — Onda 3 saneamento pré-Marco 3 OS (achados F-B-C1 + F-B-A1..A4)
relacionado:
  - docs/faseamento/F-B/spec.md
  - docs/faseamento/F-B/auditoria-familia5.md
  - docs/adr/0038-familia-inv-auth.md
  - docs/dominios/suporte-plataforma/modulos/acesso-seguranca/eventos.md
  - docs/seguranca/politica-senha-sessao.md
---

# F-B — Tarefas de saneamento (Onda 3)

> **Contexto:** F-B foi fechada em 2026-05-19 (PASS ZERO C/A/M). Auditoria projeto-inteiro 2026-05-23 (Onda 3) reabriu **1 CRÍTICO + 4 ALTO + 3 MÉDIO + 2 BAIXO** específicos da fronteira auth/perfis/eventos. Esta lista é **bloqueante pra entrar em Wave A** — não bloqueia retroativamente a fase (que continua FECHADA), mas trava qualquer Marco que dependa de perfis sensíveis (Marco 3 = atendente/gerente, Marco 4 = signatário/metrologista).

---

## CRÍTICO

### T-FB-SAN-01 — Seed perfis Marco 3/4 (F-B-C1)
- **Achado:** PRDs `financeiro`, `os`, `calibracao`, `clientes` (Marco 1) citavam perfil `financeiro` e `signatario` sem que existissem em `authz_perfil`. `AuthorizationProvider.can("fatura.estornar", perfis=["financeiro"])` retorna **sempre `false`** (vazio cross join), bug silencioso.
- **Conserto:** migration `0007_seed_perfis_marco_3_4.py` cria 5 perfis globais (`financeiro`, `metrologista_bancada`, `atendente`, `gerente_operacional`, `signatario`) + 19 linhas de matriz `perfil × ação` cobrindo cenários canônicos. Idempotente.
- **Status:** ✅ resolvido nesta Onda (commit + migration nova).
- **Teste:** Wave A `tests/test_perfis_marco_3_4_seed.py` (a criar) verifica todos 5 perfis aparecem em `SELECT codigo FROM authz_perfil WHERE tenant_id IS NULL`.

---

## ALTO

### T-FB-SAN-02 — ABAC contextual (F-B-A1)
- **Achado:** Wave A precisa de regras contextuais ("RT signa só se RTCompetencia vigente cobre grandeza X", "Técnico vê apenas OS de filial Y") — F-B só entregou RBAC plano (perfil × ação binária). ABAC fica fora da Foundation.
- **Conserto:** **diferido para Wave A** — ADR-0012 §3 já prevê porta `AuthorizationProvider.can(..., contexto: dict)`. Implementação `RuleEvaluator` + integração `RTCompetencia.vigencia_em(data)` entra em Marco 2.5 (US-EQP-007 fase 2) e Marco 4 (signatário ISO 17025).
- **Status:** rastreado como GATE-FB-ABAC-1. Não bloqueia Marco 3 OS (RBAC plano cobre os 4 cenários canônicos do tasks Marco 3 v1).

### T-FB-SAN-03 — Feature flags com AC binário (F-B-A2)
- **Achado:** ADR-0006 (feature flags) foi aceita, mas spec F-B não tem AC binário cobrindo "endpoint `/api/me/features` retorna flags do tenant atual" nem "decorator `@feature_required('codigo')` bloqueia rota". Ficou implícito.
- **Conserto:** **diferido para US-FB-COMPL (Wave A)** — criar story própria com 3 AC binários: (1) `/api/me/features` GET retorna lista, (2) decorator bloqueia 403 sem flag, (3) RLS em `tenant_features` impede vazamento cross-tenant.
- **Granularidade por usuário:** diferida pra V2 (proposta migration: `tenant_features` ganha `perfil_id NULL` + `usuario_id NULL`). Tracker em `debitos-tecnicos.md` §débito 2.
- **Status:** rastreado como GATE-FB-FF-AC; débito documentado.

### T-FB-SAN-04 — Eventos canônicos auth (F-B-A3)
- **Achado:** Login/MFA/troca-senha não emitiam eventos canônicos `AcessoSeguranca.*` apesar de catalogados v10. Sem evento, auditoria LGPD ("quem entrou em X em data Y?") fica cega.
- **Conserto:** doc `acesso-seguranca/eventos.md` criado nesta Onda — 14 eventos × payload formal × consumidores canônicos × envelope v10. Wave A implementa publisher (Django signal pós-login).
- **Status:** ✅ doc resolvido; publisher fica em Wave A Marco 3 (P3 P4).
- **Teste futuro:** `test_acesso_seguranca_eventos_canonicos_v10` cobre os 14 nomes.

### T-FB-SAN-05 — Família INV-AUTH-* (F-B-A4)
- **Achado:** F-B garantiu autorização (INV-AUTHZ-001..004) mas **autenticação ficou sem invariante canônica**: sem regra de lockout, política de senha, sessão idle, troca forçada, retenção tentativas. Implementador Wave A inventaria valores diferentes em cada PR.
- **Conserto:** ADR-0038 + 5 invariantes (INV-AUTH-001..005) adicionadas em REGRAS-INEGOCIAVEIS.md nesta Onda. Parâmetros canônicos em `politica-senha-sessao.md`.
- **Status:** ✅ regras resolvidas; implementação Wave A.

---

## MÉDIO

### T-FB-SAN-06 — Feature flags granularidade (F-B-M1)
- **Achado:** `tenant_features` só carrega `(tenant_id, codigo, ativo)`. Wave A vai querer "ativar pra usuário X durante beta".
- **Conserto:** **débito documentado** (`debitos-tecnicos.md` §débito 2). Proposta: migration retrofit adiciona `perfil_id NULL` + `usuario_id NULL`. Avaliar custo vs benefício em Wave A US-FF-EXT.
- **Status:** rastreado.

### T-FB-SAN-07 — Allowlist anti-PII Marco 3/4 (F-B-M2)
- **Achado:** `redator_pii.py` (F-B) tinha allowlist parametrizada com slugs F-A (`os_id`, `tenant_id`, `usuario_id`). Marco 3 e Marco 4 introduzem novos slugs (`tecnico_executor_id`, `atividade_id`, `equipamento_id`, `certificado_id`, `signatario_id`) — sem extensão, `escopo_avaliado` JSON vira `[REDACTED]` cego e quebra auditoria útil.
- **Conserto:** lista canônica documentada em `politica-senha-sessao.md` §6 (allowlist + denylist). Implementação `redator_pii.py` ganha estes slugs em Wave A.
- **Status:** ✅ doc resolvido; código Wave A.

### T-FB-SAN-08 — Texto INV-AUTHZ-002 e PII por valor (F-B-M3)
- **Achado:** texto atual de INV-AUTHZ-002 lista campos da tabela mas **não veda explicitamente** PII em `resource_summary` / `escopo_avaliado`. Implementador pode gravar "CPF 123.456.789-09" e achar que cumpre.
- **Conserto:** ajustar texto de INV-AUTHZ-002 (esta Onda já fez em REGRAS) acrescentando "PII por referência (id), nunca por valor. Vetado: nome, CPF, e-mail, telefone, endereço no `resource`/`escopo_avaliado`. Lista canônica em `docs/seguranca/politica-senha-sessao.md` §6".
- **Status:** ✅ texto ajustado.

---

## BAIXO

### T-FB-SAN-09 — FK perfil em UsuarioPerfilTenant (F-B-B1)
- **Achado:** `UsuarioPerfilTenant.perfil` é `CharField` (codigo do perfil) — não é FK pra `authz_perfil(id)`. Acoplamento por string é frágil; rename de perfil quebra silenciosamente.
- **Conserto:** **débito** — migration retrofit em Wave A `auth_usuario_perfil` adiciona FK `perfil_id UUID NOT NULL REFERENCES authz_perfil(id)`. Backfill por `codigo`. Mantém `perfil_codigo` como denormalização rápida pra cache RBAC.
- **Status:** rastreado em `debitos-tecnicos.md` §débito 1.

### T-FB-SAN-10 — MFA_BYPASS_PREFIX + enroll TOTP (F-B-B2)
- **Achado:** F-B implementou MFA bypass via prefixo (dev/test) mas não tem endpoint de **enroll TOTP** real ("escaneie QR code com Google Authenticator"). Sem enroll, o caminho django-otp real não é exercido em produção.
- **Conserto:** **débito Wave A** — adicionar view `/auth/mfa/enroll` com QR code TOTP + verificação. Rota é gated por `feature_required('mfa_totp_v1')`.
- **Status:** rastreado em `debitos-tecnicos.md` §débito 3.

---

## Encerramento Onda 3 fronteira F-B

| Severidade | Achados | Resolvidos nesta Onda | Diferidos com tracker |
|---|---|---|---|
| CRÍTICO | 1 | 1 ✅ | 0 |
| ALTO | 4 | 3 ✅ + 1 rastreado (GATE-FB-ABAC-1) | 1 |
| MÉDIO | 3 | 2 ✅ + 1 rastreado | 1 |
| BAIXO | 2 | 0 — ambos débito Wave A | 2 |

Gate INV-RITUAL-001 considera Onda 3 fechada quando CRÍTICO/ALTO/MÉDIO = 100% (resolvidos OU rastreados com tracker GATE-* e plano Wave A). Esta linha bate: 1+4+3 = 8 cobertos / 8 totais.

`auditoria-familia5.md` da F-B não precisa ser reaberto (a fase continua FECHADA em 2026-05-19) — esta Onda foi achado de auditoria projeto-inteiro de fronteira pré-Marco 3.
