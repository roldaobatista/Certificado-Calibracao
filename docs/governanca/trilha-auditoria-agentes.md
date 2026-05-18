---
owner: Roldão
revisado-em: 2026-05-17
status: draft
append-only: true
---

# Trilha de auditoria dos agentes

> **Pra quê:** registro **append-only** de cada decisão de auditor + cada drill + cada incidente envolvendo agente IA. Query padrão "quem tocou tenant Y entre HH:MM" testada em drill trimestral.
>
> **Retenção:** 2 anos governance + 5 anos se relacionado a dado regulado.

---

## Formato

```markdown
### YYYY-MM-DD HH:MM — [resumo]
- **Tipo:** veto_seguranca | veto_qualidade | veto_produto | drill | incidente | aprovacao_roldao | decisao_autonoma
- **Quem:** [auditor-segurança | auditor-qualidade | auditor-produto | watchdog | Roldão | ...]
- **O que aconteceu:** [descrição]
- **Tenant afetado:** [T_NN | n/a]
- **Resultado:** [bloqueou | aprovou | falso positivo | escalou]
- **Ação tomada:** [ação concreta]
- **Lição:** [se houver]
- **Link:** [PR / commit / sessão / postmortem]
```

---

## Princípios

1. **Append-only:** nunca editar entradas antigas. Correção entra como nova entrada referenciando a anterior.
2. **Imutável após 30 dias:** WORM B2 absorve (quando deploy autorizado).
3. **Sem PII direta:** usar `user_id_hash`, `tenant_id`, `request_id`.
4. **Toda decisão auditável:** auditor que vetar, drill que rodar, incidente que acontecer — TUDO entra.
5. **Query padrão funciona:** "listar tudo que tenant T_42 envolveu entre 2026-05-17 14:00 e 16:00" → resultado em ≤ 5 min.

---

## Entradas (cronológico reverso — mais recente em cima)

## 2026-05-18 — Auditor de Qualidade — F-A + F-B + Wave A Marco 1 (auditoria retroativa)
- Escopo: commits `65f2bcd..HEAD` (10 commits, 48 arquivos, +3364/-65); foco em `tests/*` (10 arquivos de teste; 1042 linhas novas em testes), `src/infrastructure/authz/*`, `src/infrastructure/clientes/*`, `src/domain/shared/value_objects.py`
- Veredito: **CONCERNS** (não FAIL — código respeita TST-001/002/003; um gap em TST-004 + cobertura global abaixo do threshold por código de drill operacional)
- Itens:
  1. **TST-004 (CONCERN)** — `INV-TENANT-004` está listado em `REGRAS-INEGOCIAVEIS.md` (role app NOBYPASSRLS/NOSUPERUSER + role separada `app_migrator`) mas **nenhum teste do diff cita o ID no nome** (`def test_inv_tenant_004_*`). Cobertura comportamental existe em `tests/test_isolamento_cross_tenant.py` (RLS bloqueia cross-tenant — provando NOBYPASSRLS em runtime) e o drill `validar_f_a` verifica role, mas o critério TST-004 exige citação literal do ID no nome do teste. Como F-A é auditoria retroativa (`debitos-ritual.md` §F-A), não é veto — registrado como concern para regularização junto à Story `US-FA-NNN` que cobre roles PG. Sugestão de fix: renomear/adicionar `test_inv_tenant_004_role_app_user_nao_bypassa_rls` em `test_isolamento_cross_tenant.py` (1 linha cosmética).
  2. **Cobertura (CONCERN)** — `pyproject.toml` exige `--cov-fail-under=80`; execução `docker compose exec -T app poetry run pytest --cov=src --cov-report=term -q` deu **64.72% global** (FAIL no threshold). Mas os 0% concentram em 3 management commands de drill: `popular_drill.py` (0%, 34 linhas), `relatorio_operacao_fa.py` (0%, 74 linhas), `validar_f_a.py` (0%, 109 linhas) — total 217 linhas de ferramenta operacional, não código de produto. Paths críticos auditados (`clientes/`, `authz/`, `multitenant/`, `tenant/`, `usuario/`, `audit/`, `domain/shared/`) todos ≥ 83% e a maioria ≥ 90%. Sugestão: marcar os 3 management commands com `# pragma: no cover` (já permitido por `[tool.coverage.report]`) OU adicionar à `omit` do `[tool.coverage.run]` — não é mascaramento, é exclusão correta de código operacional executado fora da suite.
  3. **Pontos positivos confirmados:**
     - INV-024 ✅ (`test_inv_024_dedup_mesmo_documento_mesmo_tenant_rejeita`, `test_inv_024_mesmo_documento_tenants_diferentes_eh_OK` — happy + unhappy)
     - INV-036 ✅ (12 testes em `test_clientes_value_objects.py` + `test_inv_036_dv_invalido_rejeita_via_api`)
     - INV-AUTHZ-001 ✅ (16 cenários parametrizados em `test_inv_authz_001_matriz_4perfis_x_4acoes` + 4 testes E2E na API)
     - INV-AUTHZ-002 ✅ (5 testes — happy/denied/update-block/delete-block/hash-chain)
     - INV-AUTHZ-003 ✅ (3 testes — sem perfil/multi-tenant fora da lista/isolamento das próprias decisions)
     - INV-TENANT-001 ✅ (3 testes em `test_clientes_isolamento.py` + 1 em `test_clientes_modelo.py` + 1 em `test_clientes_api.py`)
     - SEC-MFA-001 ✅ (5 testes — `_obrigatorio_sem_otp_e_401`, `_perfil_sensivel_sem_otp_e_401`, `_perfil_nao_sensivel_passa_sem_otp`, `_perfil_sensivel_com_otp_passa`, `test_perfis_sensiveis_inclui_admin_rt_financeiro`)
     - **UNHAPPY paths explícitos cravados** conforme exigido pelo drill F-A 2026-05-18 (memória `feedback_nao_declarar_pronto_sem_rodar`): `test_inv_024_dedup_mesmo_documento_mesmo_tenant_rejeita` (`pytest.raises(IntegrityError)`), `test_inv_tenant_001_rls_bloqueia_insert_fora_do_active_tenant` (`pytest.raises(ProgrammingError)`), `test_cliente_clean_rejeita_cnpj_invalido`/`cpf_invalido` (`pytest.raises(ValidationError)`), `test_inv_authz_002_trigger_pg_bloqueia_update/delete`, fuzzing 500× cross-tenant zero vazamento.
     - **TST-001 (skip com justificativa) ✅** — único skip da suite (`tests/test_middleware_e2e.py:39`) tem comentário `# skip 2026-05-17 (Roldao) — endpoint protegido real so existe a partir de Wave A. Reabilitar quando primeiro endpoint DRF aparecer (modulo calibracao).` Data + dono + motivo concreto + condição de reabilitação = aceito.
     - **TST-002 ✅** — nenhuma assertion vazia (`assert True`, `assert 1==1`, `assertTrue(true)`) introduzida no diff. Único match em todo o repo está em `_test-runner.sh` (caso de drill do hook) e em docs.
     - **TST-003 ✅** — `# type: ignore[<categoria>]` sempre com categoria explícita do mypy (`[no-untyped-def]`, `[arg-type]`, `[attr-defined]`, `[assignment]`, `[dict-item]`) — categoria do mypy = motivo técnico concreto, atende a regra. `# noqa: F401/F403/F405` em `config/settings/*.py` e `apps.py` têm justificativa inline ("registra signal `connection_created`", "padrao Django settings overlay"). `# noqa: S603` em management commands com justificativa concreta ("runner conhecido versionado no repo" / "args internos controlados").
  4. **Suite final:** `pytest --no-cov -q` → **127 passed, 1 skipped, 9 warnings em 44.07s**. Nenhum flake detectado (`--reuse-db` + UUIDs em fixtures isolam corretamente). Bate com expectativa do escopo da auditoria.
  5. **Não há mascaramento detectado** (`return True` solto, `pass` em handler público, `time.sleep` pra contornar race, mock de PG em teste de integração).
- Custo (tokens estimados): N/A

---

### 2026-05-18 — Auditor Segurança · F-B + Wave A Marco 1 (authz + clientes)
- **Tipo:** decisao_autonoma (Auditor Segurança rodando retroativamente em código já commitado — ritual de débito)
- **Quem:** auditor-seguranca (Claude Opus 4.7, prompt v1.0.0)
- **Escopo:** diff `65f2bcd..HEAD` — 10 commits, 48 arquivos; foco em `src/infrastructure/authz/`, `src/infrastructure/clientes/`, `src/infrastructure/multitenant/`, `config/settings/`, `.claude/hooks/`
- **O que aconteceu:** auditoria retroativa pós-entrega Foundation F-B + Wave A Marco 1. Avaliou: INV-AUTHZ-001/002/003, INV-TENANT-001..004, SEC-MFA-001, settings cache, bug `7be6e2d`, débito `CREATEDB` nas roles, pattern seed migration `0003_seed_authz_acoes`.
- **Tenant afetado:** n/a (código pré-tenant real; multi-tenant local)
- **Resultado:** **VEREDITO: CONCERNS** — não FAIL. Código respeita todas as regras versionadas; 3 concerns operacionais não-bloqueantes registrados.
- **Ação tomada:** veredito + concerns documentados aqui; retorno ao orquestrador
- **Lição:**
  1. Bug `7be6e2d` (SET LOCAL sem `transaction.atomic`) escapou porque F-A não tinha endpoint protegido real — Wave A acionou. Nenhum hook estático pega isso; sugestão: teste integrado de middleware E2E com endpoint protegido obrigatório (categoria TST, não SEC).
  2. Padrão `DISABLE RLS + DROP POLICY + INSERT + RECREATE POLICY` em seed migration é seguro (roda como `app_migrator` NOBYPASSRLS, dentro de migração), mas se crashar no meio deixa tabela exposta. Sugestão V2: try/except recriando policy no `finally`.
  3. `CREATEDB` nas roles `app_user`/`app_migrator` (débito conhecido) NÃO compromise INV-TENANT-004 — `CREATEDB` só autoriza criar/destruir DBs, não dá BYPASSRLS nem SUPERUSER. Reverter pós-CI continua válido por higiene.
- **Link:** este veredito; commits `faaddaa..7802d58`

#### CONCERN 1 — Hash chain frágil sob concorrência (INV-AUTHZ-002)
- **Arquivo:** `src/infrastructure/authz/django_provider.py:196-198`
- **Estado:** OK literal — audit grava em `transaction.atomic()` ANTES do `return AuthDecision`, trigger PG anti-update/delete cravados. Hash determinístico (`SHA-256(hash_anterior || payload_canonico)`).
- **Risco residual:** `AuthzDecision.objects.order_by("-timestamp").only("hash_atual").first()` lido sem lock. Sob duas requests concorrentes podem pegar o MESMO `hash_anterior` e gerar 2 linhas com mesma "posição" na cadeia (irmãs em vez de sequenciais) — quebra silenciosa da propriedade "cadeia auditável de truncate". Não viola texto da INV (audit gravado, imutável), mas enfraquece a garantia. Sugestão Wave A: `SELECT ... FOR UPDATE` na última linha ou advisory lock por tenant.

#### CONCERN 2 — RLS de `authz_perfil_acao` permissiva (preparando Wave A)
- **Arquivo:** `src/infrastructure/authz/migrations/0002_rls_e_trigger.py:48-52`
- **Estado:** `SELECT USING (true)` — catálogo global lido por todos, correto em F-B (todos perfis são `tenant_id IS NULL`). Mutação bloqueada por `FOR ALL USING (false)`.
- **Risco residual:** quando Wave A introduzir perfis tenant-specific (`Perfil.tenant_id NOT NULL`), `PerfilAcao` continuará lendo a matriz completa cross-tenant — vazamento da arquitetura de permissões do tenant vizinho (não PII direta, mas inteligência competitiva). Sugestão: ao criar primeiro perfil tenant-specific, refazer policy SELECT como `USING (EXISTS (SELECT 1 FROM authz_perfil p WHERE p.id = perfil_id AND (p.tenant_id IS NULL OR p.tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))))`.

#### CONCERN 3 — MFA bypass amplo em `/accounts/`
- **Arquivo:** `src/infrastructure/authz/middleware.py:31`
- **Estado:** ordem do MIDDLEWARE correta (TenantMiddleware → MfaRequiredMiddleware). `MFA_BYPASS_PREFIX` lista `/accounts/` (prefixo aberto).
- **Risco residual:** qualquer view nova montada em `/accounts/*` (ex.: futuro `/accounts/me/`) ganha bypass automático de MFA, mesmo se retornar dado de tenant. SEC-MFA-001 corre risco silencioso. Sugestão: trocar `/accounts/` por paths explícitos (`/accounts/login/`, `/accounts/logout/`, `/accounts/totp/setup/`, `/accounts/totp/verify/`).

#### Pontos positivos confirmados
- INV-AUTHZ-001: porta `AuthorizationProvider.can()` enforced via `RequireAuthz` (DEFAULT_PERMISSION_CLASSES global) + `@requires_authz` + hook `authz-check.sh` (case do path normalizado, allowlist `*/models.py` e `*/apps.py`). `ClienteViewSet` declara `ACTION_MAP` + `get_authz_action`; queryset filtra por `active_tenant` (defesa em profundidade).
- INV-AUTHZ-002: triggers `authz_decisions_anti_update` / `anti_delete` + função `authz_decisions_bloqueia_mutation()` (ERRCODE 23514). Hash chain íntegra, audit ANTES do return.
- INV-AUTHZ-003: todas as policies novas usam `ANY(string_to_array(current_setting('app.tenant_ids'), ','))` — pattern v2 cravado em `clientes`, `authz_perfil`, `authz_decisions`.
- INV-TENANT-001/002/003/004: `clientes.tenant_id` NOT NULL (FK PROTECT); RLS por operação (SELECT/UPDATE/DELETE com lista + INSERT com active_tenant); UNIQUE(tenant, tipo_pessoa, documento) preserva dedup cross-tenant; roles NOBYPASSRLS preservadas (CREATEDB não anula).
- SEC-001: sem segredo hardcoded; `SECRET_KEY` via `env(...)` sem default em prod.
- SEC-LEAST-PRIV-001: matriz seed F-B respeita least privilege (técnico sem `fatura.estornar`; `cliente_externo_leitura` só `os.ler`).
- SEC-LOG-001: middleware retorna mensagens genéricas (`"Autenticacao obrigatoria"`, `"Usuario sem tenant ativo"`) sem revelar estado.
- ADR-0009: nada de A3 server-side no diff.

### 2026-05-18 — Auditor Produto · Wave A Marco 1 (módulo `clientes`)
- **Tipo:** veto_produto
- **Quem:** auditor-produto (Claude Code, Opus 4.7)
- **O que aconteceu:** Pre-merge audit do módulo `clientes` (PRD com 5 Stories US-CLI-001..005). Diff `65f2bcd..HEAD` adiciona modelo + API CRUD + RLS + matriz authz seed + VOs CPF/CNPJ. Auto-avaliação do agente em `debitos-ritual.md` confirmada: US-CLI-001 PARCIAL, US-002..005 NOT-IMPLEMENTED.
- **Tenant afetado:** n/a (módulo, não dado)
- **Resultado:** **MERGE-BLOCK** — FAIL. 9 de 17 ACs do PRD não cumpridos. AC-CLI-001-2 (aceite LGPD RAT-03 + evento `Cliente.Criado` + 409 link duplicada) ⚠️ parcial. US-002 a US-005 totalmente NOT-IMPLEMENTED. Eventos do bus (`Cliente.Criado`, `Cliente.Bloqueado`, `Cliente.Desbloqueado`) ausentes do código embora `Cliente.Bloqueado` esteja catalogado em AUT-005/AUT-007 do `automacoes-catalogo.md` — quebra contrato com módulos consumidores (operação/os, comercial/orcamentos, agenda, omnichannel) listados em AC-CLI-004-4.
- **Ação tomada:** Veredito + tabela AC × status + ordem de regularização anexados nesta entrada.
- **Lição:** PRD existia há 24h e não foi consultado antes de codar (gap mais grave de ritual — ver `debitos-ritual.md`). Auditor de Produto deveria ter sido invocado em pre-merge gate, não pos-fato.
- **Link:** commits `89c8d7a`, `ee75ac0`, `7be6e2d`, `7802d58`

**Tabela AC × status (17 ACs avaliados):**

| AC | Status | Justificativa |
|---|---|---|
| AC-CLI-001-1 | ⚠️ PARCIAL | Algoritmo CPF/CNPJ validado via VOs; dedup via UNIQUE constraint; **falta** response 409 estruturada com `{cliente_existente_id}` + link "este cliente já existe" — hoje retorna 400 IntegrityError genérico. |
| AC-CLI-001-2 | ❌ FAIL | Cliente master criado com `tenant_id` ✅; **aceite LGPD RAT-03 não registrado** (campo inexistente no modelo); **evento `Cliente.Criado` não publicado** (sem bus integration). |
| AC-CLI-002-1 | ❌ NOT-IMPLEMENTED | Endpoint `/clientes/{id}/timeline` ausente; sem agregador cross-módulo. |
| AC-CLI-002-2 | ❌ NOT-IMPLEMENTED | Sem benchmark p95 <1.5s (endpoint inexistente). |
| AC-CLI-002-3 | ❌ NOT-IMPLEMENTED | `audit_trail.acessos_dados_cliente` inexistente — viola INV-013 (LGPD log de visualização) quando visão 360° subir. |
| AC-CLI-003-1 | ❌ NOT-IMPLEMENTED | Sem `POST /clientes/importar` nem preview CSV/XLSX. |
| AC-CLI-003-2 | ❌ NOT-IMPLEMENTED | Sem job batch de importação. |
| AC-CLI-004-1 | ❌ NOT-IMPLEMENTED | Sem endpoint `POST /{id}/bloquear` nem campo `bloqueado` no modelo. |
| AC-CLI-004-2 | ❌ NOT-IMPLEMENTED | AuthorizationProvider não recebe predicado `cliente_bloqueado_manual`. |
| AC-CLI-004-3 | ❌ NOT-IMPLEMENTED | `job_inadimplencia_alertas` inexistente. |
| AC-CLI-004-4 | ❌ NOT-IMPLEMENTED | Reações cross-módulo (os/orcamentos/agenda/omnichannel) ausentes. |
| AC-CLI-004-5 | ❌ NOT-IMPLEMENTED | Régua progressiva D+30/60/89 inexistente. |
| AC-CLI-004-6 | ❌ NOT-IMPLEMENTED | Reativação automática ausente. |
| AC-CLI-004-7 | ❌ NOT-IMPLEMENTED | `audit_trail.authz_decisions` com causation_id ausente. |
| AC-CLI-005-1 | ❌ NOT-IMPLEMENTED | Sem wizard de mesclagem; sem migração de histórico. |
| AC-CLI-005-2 | ❌ NOT-IMPLEMENTED | Sem soft-delete do perdedor. |
| INV-AUTHZ-001/INV-TENANT-001 | ✅ PASS | (não é AC do PRD, mas cobertos por `test_clientes_api.py` + `test_clientes_isolamento.py`) |

**Non-goals do PRD §5 — violações:** **nenhuma**. Diff implementa subset estrito do MVP-1, sem `equipamentos`, sem `cobranca`, sem `mailing`, sem `rating bureau`.

**Scope creep:** **nenhum** crítico. ADR-0017 (CNPJ alfanumérico) introduzida no VO sem US explícita — porém é requisito normativo (IN RFB 2.229/2024 vigência jul/2026, decisão Roldão 2026-05-18) e cobre AC-CLI-001-1 implicitamente. Concern menor: `nome_fantasia` foi adicionado ao modelo sem AC explícito pedindo, mas é campo natural de PJ (não-pedido ≠ proibido).

**Glossário:** termos do PRD ausentes do código por consequência da não-implementação (`Cliente.Bloqueado`, `régua progressiva`, `modo emergencial`, `RAT-03`). Não há divergência terminológica — há ausência. PT-BR coerente em todas as mensagens do serializer/views (sem jargão técnico vazado pra UX).

**Recomendação de ordem (menos custosa → mais custosa):**
1. **US-CLI-001 completar** (1h): adicionar campos `lgpd_versao_aceite`, `lgpd_canal_aceite`, `lgpd_aceito_em` no modelo + migration; serializer exigindo no POST (422 se ausente); response 409 estruturada `{cliente_existente_id, link}` no IntegrityError; publicar `Cliente.Criado` no bus (stub se bus ainda não existir — então criar `events.py` com função `publish()` no-op + TODO).
2. **US-CLI-005** (2h): wizard preview `/dedup/preview` + endpoint `/{id}/mesclar` com soft-delete LGPD-aware + migração de FKs (no Marco 1 só Cliente, então é trivial; FKs cross-módulo entram quando módulos surgirem).
3. **US-CLI-004 manual** (3h): campo `bloqueado` + `bloqueado_motivo` + `bloqueado_justificativa`; endpoints `/bloquear` + `/desbloquear`; predicado authz `cliente_bloqueado_manual` consultado por AuthorizationProvider.can("os.criar"); evento `Cliente.Bloqueado/Desbloqueado` publicado; **deixar US-CLI-004 automática (AC-3 a AC-7) como contrato de evento + job stub** porque dependem de `financeiro/contas-receber` que não existe — documentar dependência em `debitos-ritual.md`.
4. **US-CLI-002** (4h): endpoint `/timeline` retornando lista vazia/Cliente.Criado por enquanto (sem OS/certificados); tabela `audit_trail.acessos_dados_cliente` com middleware que loga ANTES de renderizar; teste p95 <1.5s sintético.
5. **US-CLI-003** (6h): importação CSV/XLSX async com Celery (procrastinate).

**Política aplicada:** auditor recomenda **NÃO mergear pra release MVP-1 enquanto US-CLI-001 não fechar verde 100%**. US-002..005 podem entrar em PRs subsequentes (Marcos 2-5 do Wave A clientes). Auto-avaliação do agente foi honesta — gap está documentado em `debitos-ritual.md` e plano de regularização compatível com as tasks pending #18, #19, #22, #25, #26.

---

### 2026-05-17 — Inicialização do doc
- **Tipo:** marco
- **Quem:** Claude Code (agente principal)
- **O que aconteceu:** Doc criado em lote conforme Família 5 prescrita pelo `documentos-do-projeto.md` v6.
- **Tenant afetado:** n/a
- **Resultado:** doc disponível
- **Ação tomada:** registrado no INDEX.yaml; ativação real começa com Foundation F-A e auditores rodando.
- **Lição:** rastreio começa quando agentes começam a tomar decisões reais sobre código.
- **Link:** primeira versão deste doc

---

## Como começa a popular (gatilhos)

| Gatilho | Quem registra |
|---------|----------------|
| Auditor Segurança devolve FAIL em PR | Auditor (no GitHub Action) ou Claude Code local |
| Auditor Qualidade devolve FAIL | idem |
| Auditor Produto devolve FAIL (pre-merge) | idem |
| Drill trimestral roda | Roldão (manual) |
| Incidente SEV-0/1 | RACI define quem registra |
| Roldão derruba veto de auditor | Claude Code (ao processar `APROVADO POR ROLDAO`) |
| Watchdog despertou pra incidente | Watchdog (V2 quando ativado) |
| Decisão autônoma do agente (ver `auditoria-decisoes-autonomas.md`) | Claude Code |

---

## Drill trimestral

A cada 3 meses, executar:
1. Query padrão: tenant T_X entre HH-HH — esperar ≤ 5 min de resultado consolidado
2. Validar que entradas dos 30 dias mais recentes estão completas
3. Verificar que entradas com PII passaram por anonimização
4. Confirmar que retenção configurada bate com `retencao-matriz.md`

Resultado do drill **vira entrada nova** neste doc.

---

## Operação V2 (com deploy)

- WORM B2 absorve linhas antigas (> 30 dias)
- Painel Grafana "Trilha auditoria" agrega + filtra por tenant
- Query rápida via índices em PG + cold storage em B2
- Drill anual: tentar restaurar linha de 18 meses atrás → ≤ 30 min

---

## Referências

- `governanca/RACI-incidente-ai.md`
- `governanca/auditoria-decisoes-autonomas.md`
- `governanca/metricas-operacao-agentes.md`
- `conformidade/comum/retencao-matriz.md`
- `seguranca-dados.md` §7
