---
owner: roldao
revisado_em: 2026-05-19
proximo_review: 2026-08-19
status: stable
diataxis: reference
audiencia: agente
fase: Foundation F-A
tipo: matriz-reconciliacao-spec-codigo
relacionados:
  - docs/faseamento/F-A/spec.md
  - docs/faseamento/F-A/plan.md
---

# Foundation F-A — Reconciliação spec ↔ código (P3)

> **Pra quê:** mede cada AC da `spec.md` (já corrigida pós-review dos 3
> subagentes) contra o **código real**. Coluna **Estado**: `OK`
> (código satisfaz — base de evidência citada), `GAP` (diverge → vira
> `T-FA-NNN`, conserto causa-raiz em P4), `TRACK` (gate Wave A rastreado,
> NÃO bloqueia fechar F-A — Constituição §4).
>
> **Base de evidência do `OK`** (não é suposição — Constituição
> "verificar antes de afirmar"): (a) F-A saneamento **rodada 2** = zero
> CRÍTICO/ALTO sobre código real (`auditorias/F-A-CONSOLIDADO-rodada-
> 2.md`); (b) review tech-lead 2026-05-19 declarou **SÓLIDOS** os
> pilares hash chain/RLS/fail-loud sobre o código atual; (c) leituras
> diretas do código nesta sessão (services.py, connection.py,
> rls_templates.py, middleware.py, models, migrations). Onde nada disso
> cobre → `GAP` ou verificação explícita em P4.

---

## Matriz

| AC | Estado | Evidência / ação |
|----|--------|------------------|
| AC-FA-001-1..2 | OK | docker-compose + settings; rodada 2 |
| AC-FA-001-3 | OK | `config/urls.py:15,22` `healthz` existe |
| AC-FA-001-4 | OK | `config/settings/test.py` LocMem, sem Redis |
| AC-FA-002-1..4 | OK | models tenant/usuario/audit/feature_flag; rodada 2 |
| AC-FA-002-5 | OK | `makemigrations --check` limpo + migrate from-scratch verde (verificado nesta sessão); tech-lead validou grafo de deps |
| AC-FA-003-1 | OK | `TenantMiddleware` resolve lista de `UsuarioPerfilTenant`, valida ativo, 401/403 fail-loud (leitura direta) |
| AC-FA-003-2 | OK | roles NOBYPASSRLS+NOSUPERUSER (`01-roles.sh`; rodada 2) |
| AC-FA-003-3 | OK | `rls_templates.py` fonte única + builders dedicados auditoria/authz (pattern modo_sistema/pré-tenant) — tech-lead confirmou no código |
| AC-FA-003-4..5 | OK | FORCE RLS + hook `migration-rls-check` (rodada 2 + hooks verdes) |
| AC-FA-004-1..4 | OK | `connection.py` 3 contextos + reset GUC no pool; tech-lead "fail-loud sólido" |
| AC-FA-005-1 | OK | `calcular_hash`+`canonicalizar` único, datetime naive fail-loud |
| AC-FA-005-2 | OK | advisory lock classe por-tabela + chave derivada do filtro + `sequencia` |
| **AC-FA-005-2b** | **GAP** | **T-FA-01**: invariante "1 cadeia/classe-lock por transação" não declarado em código nem coberto por caso de drill intra-request multi-cadeia |
| AC-FA-005-3 | OK | trigger `auditoria_anti_*` + hook `audit-immutability-check` |
| AC-FA-005-4 | OK | `verificar_integridade_cadeia` recomputa no recalculado (Q-02) — tech-lead confirmou |
| AC-FA-005-5 | OK | export stub (NG-FA-4) |
| **AC-FA-005-6** | **GAP** | **T-FA-02**: marco de corte "início de cadeia autoritativa" gravado na trilha — NÃO implementado |
| **AC-FA-005-7** | **GAP** | **T-FA-03**: `AcessoDadosCliente` tem trigger anti-mutation (`audit/0005`) mas falta **teste F-A dedicado** provando rejeição UPDATE/DELETE (hoje só exercitado indiretamente em testes clientes) |
| AC-FA-006-1..3 | OK | `hashear_pii_com_salt_tenant`/`verificar_pii_hash` (rodada 2 FA-A1) |
| **AC-FA-006-3b** | **GAP** | **T-FA-04**: `ChavePIIIndisponivel` só faz `raise` — falta gerar evento próprio na cadeia sistema (accountability art. 6 X) |
| AC-FA-006-4 | OK | `sanitizar_payload_audit` existe (capacidade; obrigatoriedade = Wave A, conforme spec rebaixada) |
| **AC-FA-006-5** | **GAP** | **T-FA-05**: crypto-shredding por tenant + amarração ciclo-de-vida-chave↔retenção não documentado/forçado; spec declara, código não tem o procedimento |
| AC-FA-007-1..4 | OK | 15 hooks, `_test-runner` 118/118 verde (verificado nesta sessão) |
| AC-FA-008-1 | OK | suíte verde + `--cov-fail-under=80` (rodada 2: ~85%) |
| AC-FA-008-2 | OK | fuzzing concorrente cross-tenant zero vazamento (rodada 2) |
| AC-FA-008-3 | OK | `validar_f_a` robusto FA-A5 (injeção+detecção+anti-falso-verde+exit code) |
| AC-FA-008-4 | OK | benchmark p99<200ms multi-tenant (rodada 2) |
| AC-FA-008-5 | OK | restore PG cronometrado < 30min (rodada 2 evidência) |
| **AC-FA-008-6** | **GAP** | **T-FA-06**: nenhum smoke verifica que `test_afere` tem matriz roles/grants = produção → fuzzing AC-FA-008-2 pode ser falso-verde (tech-lead P-A4) |
| **AC-FA-008-7** | **TRACK** | GATE-2 Wave A: verificação periódica + evidência persistida (stub agendado em F-A) |
| AC-FA-009-1 | OK | `django-convencoes.md` `status: stable` |
| **AC-FA-009-2** | **GAP** | **T-FA-07**: `isolamento-multi-tenant.md` existe mas `status: draft` — falta evidência da implementação real + promover a `stable` |
| **AC-FA-009-3** | **GAP** | **T-FA-08**: `REGRAS-INEGOCIAVEIS.md` = 192 linhas > teto 120 (Constituição §3) — débito real declarado |

### Gates Wave A rastreados (TRACK — não bloqueiam F-A)

| Gate | Item | Onde rastrear |
|------|------|---------------|
| GATE-1 | export B2/WORM operacional | foundation-waves + retenção-matriz |
| GATE-2 | verificação periódica c/ evidência (AC-FA-008-7) | foundation-waves |
| GATE-3 | carimbo de tempo fonte confiável (NTP) | foundation-waves |
| GATE-4 | política formal ciclo-de-vida chave PII ↔ retenção | retenção-matriz |
| GATE-5 | hash chain de `AcessoDadosCliente` (se ANPD/CGCRE exigir) | foundation-waves |

> **[P3-verify] B-2:** `docs/conformidade/comum/retencao-matriz.md`
> **existe** porém `status: draft`. Como AC-FA-006-5/GATE-4 a tratam
> como **gate rastreado de Wave A** (não entregável de F-A), `draft`
> aqui **não bloqueia** o fechamento de F-A — mas fica registrado:
> promover a `stable` é parte de GATE-4. Não é citação vazia (doc
> existe); é citação para doc ainda não-estável, aceitável p/ gate
> futuro.

---

## Tarefas de conserto (P4) — causa-raiz, sem mascaramento

| T-FA | AC | Conserto (raiz) | Bloqueia fechar F-A? |
|------|----|-----------------|----------------------|
| **T-FA-01** | AC-FA-005-2b | Declarar invariante no `audit/services.py` (docstring + guarda se viável) + caso no `validar_f_a`: dentro de UMA transação registrar 2 cadeias → ou proibido com erro claro, ou locks em ordem determinística; provar ausência de deadlock no drill | **Sim** (corretude concorrência) |
| **T-FA-02** | AC-FA-005-6 | Migration/serviço que grava 1 elo "marco de início de cadeia autoritativa" (maior `sequencia` no instante) na própria trilha encadeada; verificação reconhece a fronteira | **Sim** (evidência CGCRE) |
| **T-FA-03** | AC-FA-005-7 | Teste F-A dedicado: trigger PG rejeita UPDATE/DELETE em `acessos_dados_cliente` (a barreira real, sem hash chain) | **Sim** (prova da decisão consciente) |
| **T-FA-04** | AC-FA-006-3b | `verificar_pii_hash` (ou wrapper de resposta-titular) emite evento `registrar_em_cadeia` cadeia sistema ao levantar `ChavePIIIndisponivel` em contexto de resposta (sem valor cru) | **Sim** (accountability LGPD) |
| **T-FA-05** | AC-FA-006-5 | Documentar+forçar: crypto-shredding por tenant como caminho de eliminação; amarrar `PII_HASH_KEYS_RETIRED`↔retenção (não aposentar antes do prazo) — procedimento + nota em isolamento/retenção | **Sim** (LGPD art. 18 VI) |
| **T-FA-06** | AC-FA-008-6 | Smoke (drill `validar_f_a` ganha critério): `verificar_objetos_seguranca` rodando contra `test_afere` confirma roles/grants = produção; reprova se divergir | **Sim** (anti falso-verde) |
| **T-FA-07** | AC-FA-009-2 | Preencher `isolamento-multi-tenant.md` com evidência real (2 camadas + fail-loud + roles + hash chain) → `status: stable` | **Sim** (entregável F-A) |
| **T-FA-08** | AC-FA-009-3 | `REGRAS-INEGOCIAVEIS.md` ≤ 120 linhas: mover detalhe não-crítico p/ docs citados por ID **OU** ADR formal ajustando o teto (decisão Roldão/CODEOWNERS — constitution muda só via ADR) | **Sim** (Constituição §3) |

GATE-1..5 = **TRACK** (rastreado, não T-FA; F-A fecha sem eles —
dogfooding-only). 8 tarefas de conserto P4. Nenhuma reabre arquitetura
nem joga código fora — todas aditivas/causa-raiz.

> **Próximo (P4):** executar T-FA-01..08 (causa-raiz), commits atômicos,
> suíte verde + hooks + `validar_f_a` + makemigrations limpo; então P5
> (3 auditores Família 5, loop até zero crítico/alto). Só então F-A
> fecha e P6 (F-B) começa.
