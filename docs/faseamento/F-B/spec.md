---
owner: roldao
revisado_em: 2026-05-19
proximo_review: 2026-08-19
status: stable
diataxis: reference
audiencia: agente
fase: Foundation F-B
tipo: especificacao-forward
substitui: docs/faseamento/stories-f-b.md (retrofit retroativo — vira histórico)
relacionados:
  - .specify/memory/constitution.md
  - docs/faseamento-foundation-waves.md
  - docs/faseamento/F-A/spec.md
  - docs/adr/0006-feature-flags.md
  - docs/adr/0012-autorizacao-unificada.md
  - REGRAS-INEGOCIAVEIS.md
---

# Foundation F-B — Especificação (forward, autoritativa)

> **O que é (Constituição §1, §2):** fonte da verdade do que F-B
> **deve fazer**. Spec-as-source: código é derivado/validado contra
> esta spec. Onde divergir (após review subagentes), **o código é
> corrigido**.
>
> **Por que (decisão Roldão 2026-05-19):** F-B também foi entregue sem
> ritual Spec Kit (`stories-f-b.md` admite "mapeia retroativamente").
> Recriada forward, **depois** de F-A FECHADA (lição C1⇄C3: travar a
> camada inferior antes da superior — FB-C1 dependia de FA-C1).
>
> **Pra Roldão (uma frase):** o "contrato" do controle de quem-pode-
> o-quê: login sabe em quais empresas você está, cada perfil faz só o
> que pode, e **toda** decisão passa por um ponto único e fica
> registrada à prova de adulteração (pra responder à LGPD/ISO).

---

## 1. Escopo

`AuthorizationProvider` (porta + adapter Django) + RBAC 4 perfis +
RLS authz + trilha de decisões `authz_decisions` imutável (hash chain)
+ MFA TOTP pros perfis sensíveis + `RequireAuthz` deny-by-default na
borda DRF. **Sobre F-A fechada**, local (dogfooding).

### Non-goals explícitos (NG-FB)

- **NG-FB-1**: provedor de autorização externo (OPA/Cerbos/Casbin) —
  só porta + adapter local; externo é V2 se ADR-0012 reabrir.
- **NG-FB-2**: ABAC contextual rico (acreditação vigente, matriz de
  treinamento) — F-B só tem o **gancho** de predicates; atributos reais
  são Wave A.
- **NG-FB-3**: fluxos completos `django-allauth` (reset senha, social,
  e-mail) — diferido (ajuste de aceitação ADR-0012); F-B entrega login
  + sessão + MFA TOTP via `django-otp`.
- **NG-FB-4**: cache Redis — F-B usa `LocMemCache` (ajuste ADR-0012);
  Redis é troca de backend em Wave A sem mexer no provider.
- **NG-FB-5**: export `authz_decisions` para Backblaze B2 **real** —
  **mesmo gate de F-A (GATE-1)**: diferido enquanto dogfooding-only;
  em F-B a imutabilidade é trigger PG + hash chain + verificação.
- **NG-FB-6**: perfis tenant-specific — F-B só perfis globais
  (`tenant_id IS NULL`); `INV-AUTHZ-004` só ativa quando Wave A criar
  o 1º perfil de tenant (gate rastreado).
- **NG-FB-7**: mobile, fiscal, módulos de produto — Wave A.

### Invariantes governados (citar IDs — Regra mestre 2)

`INV-AUTHZ-001` (porta única `can()`), `INV-AUTHZ-002` (audit síncrono
imutável + hash chain), `INV-AUTHZ-003` (RLS lista de tenants),
`INV-AUTHZ-004` (matriz cross-tenant safe — preventivo, só Wave A),
`SEC-MFA-001` (MFA TOTP perfis sensíveis). Herda de F-A:
`INV-TENANT-001..004`, `INV-001`, contexto fail-loud, hash chain
(helper único `registrar_em_cadeia`), `run_in_user_context`.

---

## 2. Como ler

`US-FB-NNN` → `AC-FB-NNN-N` binário. Convenção de ID hifenizada (idem
F-A spec §2). Estado de reconciliação preenchido em P8 (`tasks.md`):
`OK` / `GAP`→`T-FB-NNN` / `TRACK`. Mortalidade: reprovar critério de
saída = debug pontual (escopo pequeno; foundation-waves §3 "se
reprovar") — só ADR-0012 reabre se `can()` p99 inviável.

---

## US-FB-001 — Porta `AuthorizationProvider` em domínio puro

**Como** arquiteto, **quero** o contrato como Protocol Python sem
Django em `src/domain/authz/`, **para** trocar adapter sem reescrever
domínio (ADR-0012).

- **AC-FB-001-1**: `src/domain/authz/provider.py` define Protocol
  `AuthorizationProvider.can(usuario_id, action, resource, tenant_id,
  purpose, at_time) -> AuthDecision`.
- **AC-FB-001-2**: `AuthDecision` `frozen=True` (allowed, reason,
  perfis_aplicados, escopo_avaliado, audit_id).
- **AC-FB-001-3**: zero import `django.*` em `src/domain/authz/`.

## US-FB-002 — Adapter Django + 3 tabelas authz (RLS + imutabilidade)

**Como** infra, **quero** `DjangoAuthorizationProvider` consultando
`Perfil`/`PerfilAcao`/`AuthzDecision`, **para** materializar
INV-AUTHZ-001/002.

- **AC-FB-002-1**: modelos `Perfil` (codigo unique, tenant_id NULL =
  global), `PerfilAcao` (perfil×ação), `AuthzDecision` (audit síncrono
  + `sequencia` monotônica + `hash_anterior` nullable).
- **AC-FB-002-2**: RLS nas 3 tabelas + trigger PG
  `authz_decisions_anti_update`/`anti_delete` (2 triggers).
- **AC-FB-002-3**: `can()` grava `AuthzDecision` **antes** de retornar
  (mesma transação — INV-AUTHZ-002); SEM `transaction.atomic` aninhado
  redundante (helper é a fronteira).
- **AC-FB-002-4**: cache `LocMemCache` TTL 5min + `invalidate_user_
  cache()`.
- **AC-FB-002-5**: `makemigrations --check` limpo; migra from-scratch
  (authz/0001..0005) na ordem correta.

## US-FB-003 — Hash chain authz por-tenant + pré-tenant POR-USUÁRIO

**Como** sistema, **quero** a cadeia `authz_decisions` no **mesmo
algoritmo único** da auditoria (FA-C1), por-tenant, e pré-tenant
**por-usuário** (decisão pré-login tem dono), **para** não bifurcar e
ser verificável.

- **AC-FB-003-1**: `_gravar_audit` delega a `registrar_em_cadeia`
  (algoritmo único `calcular_hash`+`canonicalizar`; classe de lock
  `_ADVISORY_LOCK_CLASSE_AUTHZ` distinta de auditoria).
- **AC-FB-003-2**: cadeia particionada: tenant → `{tenant_id}`;
  pré-tenant → `{tenant_id__isnull, usuario_id}` (POR-USUÁRIO).
  `can()` pré-tenant sem usuário → **fail-loud** (não reinicia cadeia).
- **AC-FB-003-3**: policy `authz_decisions` via **fonte única**
  `rls_templates.py` (builder dedicado): `modo_sistema='1'` canônico
  (não proxy `usuario_id=''`) + pré-tenant por-usuário + tenant na
  lista; INSERT sem branch `modo_sistema` (sem permissivo morto).
- **AC-FB-003-4**: `resource` normalizado JSON-safe na borda de `can()`
  — fonte ÚNICA p/ hash E persistência (round-trip íntegro);
  fail-loud cedo (fora da transação) p/ tipo inválido.
- **AC-FB-003-5**: invariante T-FA-01 herdado (≤1 cadeia/classe-lock
  por transação).

## US-FB-004 — Seed 4 perfis + matriz

- **AC-FB-004-1**: migration seed 4 perfis globais (`admin_tenant`,
  `tecnico`, `rt_signatario`, `cliente_externo_leitura`).
- **AC-FB-004-2**: matriz `PerfilAcao` cobrindo as 4 ações dos E2E
  (os.criar, os.ler, certificado.emitir, fatura.estornar).
- **AC-FB-004-3**: seed não regride RLS (padrão SANEA-04 — não deixar
  DISABLE/DROP POLICY órfão).

## US-FB-005 — `RequireAuthz` deny-by-default + válvula pública única

**Como** sistema, **quero** toda view DRF passar pelo provider, com
válvula pública canônica única, **para** materializar INV-AUTHZ-001 na
borda.

- **AC-FB-005-1**: `RequireAuthz` em `DEFAULT_PERMISSION_CLASSES`.
- **AC-FB-005-2**: view sem `authz_action` nem marca pública → negada.
- **AC-FB-005-3**: válvula pública **única** `is_public(view,request)`
  reconhece `@public` (função), `PublicEndpoint` (mixin CBV/DRF),
  função embrulhada e handler do método — fim do `authz_public` vs
  `_authz_public` divergente (FB-C2).
- **AC-FB-005-4**: hook `authz-check.sh` rejeita endpoint sem `can()`
  e reconhece a válvula pública canônica; `_test-runner` cobre.
- **AC-FB-005-5**: `RequireAuthz.has_permission` testado:
  público→True, sem action→False, denied→False, allowed→True.

## US-FB-006 — RBAC + ABAC ligados à ação (predicate binding)

**Como** sistema, **quero** RBAC clássico + predicates ABAC que só
rodam para a `action`/recurso a que pertencem, **para** não negar
indevidamente (predicate de `cliente.*` NÃO pode rodar em `os.criar`).

- **AC-FB-006-1**: pipeline `_decidir`: sem perfil →
  `sem_perfil_no_tenant`; RBAC nega → `rbac_denied`; ABAC nega →
  `abac_denied:<nome>`.
- **AC-FB-006-2**: predicate ABAC só é avaliado quando **vinculado à
  action/recurso corrente** (binding) — não varredura global cega
  (corrige FB-A1).
- **AC-FB-006-3**: `_resolver_perfis_vigentes` filtra janela
  `valido_de`/`valido_ate` (helper único de vigência).

## US-FB-007 — MFA TOTP obrigatório (SEC-MFA-001)

**Como** sistema, **quero** middleware que barre perfil sensível sem
TOTP verificado, **para** SEC-MFA-001.

- **AC-FB-007-1**: usuário `mfa_obrigatorio=True` sem `is_verified()`
  → 401 `mfa_required_user`.
- **AC-FB-007-2**: perfil em `PERFIS_SENSIVEIS`
  ({admin_tenant, rt_signatario, financeiro}) sem TOTP → 401
  `mfa_required_perfil_sensivel`.
- **AC-FB-007-3**: a checagem de perfil sensível filtra `valido_ate`
  (mesma regra de vigência do provider — corrige FB-A4: não barrar por
  perfil expirado nem liberar por divergência).
- **AC-FB-007-4**: técnico (não-sensível) sem TOTP passa.
- **AC-FB-007-5**: paths públicos (`/healthz`, `/admin/login`,
  `/api/schema`, `/api/docs`, `/static/`, `/media/`, `/accounts/`)
  bypassam o middleware.
- **AC-FB-007-6**: teste exercita `django-otp` `is_verified()` **real**
  (não stub que mascara integração — corrige FB-A6).

## US-FB-008 — `ip_hash` preenchido na decisão (INV-AUTHZ-002)

**Como** DPO, **quero** `authz_decisions.ip_hash` preenchido (não 100%
vazio), **para** responder ANPD "de qual origem" sem IP cru.

- **AC-FB-008-1**: `ip_hash` = SHA-256 do IP do request, propagado
  request→permission→`can()`; nunca IP cru persistido.
- **AC-FB-008-2**: chamadas sem request (tasks) → `ip_hash` vazio
  documentado (não é violação; só request HTTP tem IP).

## US-FB-009 — Suite + drill `validar_f_b` robusto

- **AC-FB-009-1**: 16 E2E (4 perfis × 4 ações × pos/neg) sem flake.
- **AC-FB-009-2**: prova criptográfica INV-AUTHZ-002:
  `verificar_integridade_cadeia_authz` recomputa sha256; teste de
  adulteração no meio quebra esse elo e os seguintes (Q-02).
- **AC-FB-009-3**: `validar_f_b` robusto: por-tenant + pré-tenant
  por-usuário, injeção de elo adulterado **exige detecção**, guarda
  anti-falso-verde (reprova se cadeia vazia), concorrência, hooks por
  **exit code**, critério de cobertura authz.
- **AC-FB-009-4**: fuzzing concorrente: usuário multi-tenant {A,B}
  tenta tenant C → bloqueado (INV-AUTHZ-003).
- **AC-FB-009-5**: teste que prova `can()` retorna **só após commit**
  do audit (linha existe no banco).

---

## 3. Critérios de saída (mortalidade — espelham foundation-waves §3)

F-B fecha quando, sobre código reconciliado:

1. 16 E2E perfil×ação×pos/neg sem flake (AC-FB-009-1).
2. `authz-check.sh` rejeita 100% endpoints sem `can()` no
   `_test-runner` (AC-FB-005-4).
3. RLS authz por lista regerada; fuzzing {A,B}→C bloqueado
   (AC-FB-009-4 / INV-AUTHZ-003).
4. `can()` grava audit **antes** do retorno — provado por teste
   (AC-FB-009-5 / INV-AUTHZ-002).
5. MFA TOTP obrigatório pros perfis sensíveis, com `is_verified()`
   real (AC-FB-007-*).
6. Drill `validar_f_b` robusto verde sem falso-verde (AC-FB-009-3).
7. Ambiente de teste = matriz roles/grants de produção (herdado
   AC-FA-008-6 — senão fuzzing falso-verde).
8. 3 auditores Família 5 sem CRÍTICO/ALTO (P9).

### 3.1 Risco aceito (dogfooding local-only)

Idem F-A §3.1: imutabilidade de `authz_decisions` repousa em trigger
PG + hash chain + verificação, num PG local. Export WORM externo
diferido (NG-FB-5) — aceito **só** por dogfooding sem dado de titular
externo.

### 3.2 Gates rastreados (não bloqueiam F-B; pré-1º tenant real)

Herda GATE-1..7 de F-A (B2/WORM cobre `authz_decisions` também;
ADR-0020; NTP; etc.) + **GATE-FB-1**: ao criar 1º perfil
tenant-specific (Wave A), regenerar policy `authz_perfil_acao_select`
(`INV-AUTHZ-004`) — hook + teste E2E quando aparecer.

---

## 4. Reconciliação (P8) — GAPs já conhecidos

Frentes desta sessão já reconciliaram parte do código ao que esta spec
exige (validadas, não descartadas):
- **FB-C1+C3** (`32aa278`): AC-FB-003-* (cadeia por-tenant/pré-tenant
  por-usuário, helper único, policy fonte única).
- **FB-C2** (`53e3cc2`): AC-FB-005-3/5 (válvula pública única + teste).
- **FB-C4+C5** (`7924390`): AC-FB-009-2/3 (drill robusto + cripto).

ALTOs F-B rodada 1 ainda **abertos** → viram `T-FB` em P8:
- **FB-A1** → AC-FB-006-2 (predicate binding por action).
- **FB-A4** → AC-FB-007-3 (MFA filtra `valido_ate`).
- **FB-A5** → AC-FB-008-1 (`ip_hash` preenchido).
- **FB-A6** → AC-FB-007-6 (teste `django-otp` real, não stub).
- **FB-A7** → AC-FB-005-5 (**já fechado** em FB-C2 —
  `test_authz_require_authz.py`; P8 confirma OK).

> **Próximo (P7):** `plan.md` revisado por `tech-lead-saas-regulado`
> (concorrência cadeia authz, binding ABAC) + `advogado-saas-regulado`
> (INV-AUTHZ-002 trilha de decisão LGPD, `ip_hash`/minimização). Só
> então P8 (matriz + conserto dos T-FB) → P9 (Família 5 + fechar
> Foundation).
