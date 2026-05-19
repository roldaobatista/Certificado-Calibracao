---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
tipo: consolidado-auditoria-F-B
rodada: 1
---

# F-B — Consolidado da auditoria (rodada 1)

> Mesmo loop da F-A (auditar→corrigir→reauditar até zero CRÍTICO/ALTO).
> 3 lentes sobre o código REAL: segurança (`auditor-seguranca`),
> arquitetura (`tech-lead-saas-regulado`), qualidade (`auditor-qualidade`).
> **Tema central:** a F-B foi escrita contra o contrato PRÉ-FA-C1; o
> saneamento da F-A mudou contratos que a F-B consome e ela não foi
> religada → regressões diretas.

## Veredito rodada 1

| Lente | Veredito |
|---|---|
| Segurança | **FAIL** (4 FAIL + 3 CONCERN) |
| Arquitetura | **REJEITA** (4 CRÍTICO + 4 ALTO + 5 MÉDIO + 4 BAIXO) |
| Qualidade | **FAIL** (3 CRÍTICO + 3 ALTO + 3 MÉDIO + 2 BAIXO) |

Convergência massiva. Esperado em rodada 1 (descoberta).

## Débitos CRÍTICOS (bloqueiam fechamento F-B)

| ID | Débito | Origem |
|---|---|---|
| **FB-C1** | Hash chain do `authz_decisions` regrediu pré-FA-C1: cadeia GLOBAL ordenada por `timestamp` (colide em µs sob concorrência → bifurca), `select_for_update().first()` que NÃO trava INSERT concorrente, sem coluna `sequencia`, **algoritmo de hash divergente** do `audit/hash_chain` (duas trilhas com hashes incompatíveis), reimplementação duplicada de canonicalização/hash | seg+arq+qual |
| **FB-C2** | `@public` seta `_authz_public` mas `RequireAuthz` lê `authz_public` (atributo divergente) → toda view DRF `@public` é NEGADA; válvula legítima do INV-AUTHZ-001 inexistente; `@public` em CBV DRF nem propaga | seg+arq+qual |
| **FB-C3** | RLS `authz_decisions` usa `current_setting('app.usuario_id')=''` como proxy de "sistema"; FA-C1 cravou `app.modo_sistema='1'` como sinal canônico único → worker tenant sem usuário vê decisões pré-tenant de outros (vazamento) | seg+arq |
| **FB-C4** | Drill `validar_f_b` falso-verde (mesma classe FA-A5): passa com banco virgem, valida cadeia global por timestamp sem segregar tenant, NÃO recomputa sha256 (cadeia toda `hash="x"` passaria), checa runner por substring não exit code, sem guarda anti-falso-verde | arq+qual |
| **FB-C5** | INV-AUTHZ-002 sem prova criptográfica real: testes só caminho feliz (encadeamento), nenhum recomputa `sha256(hash_anterior+payload)` nem testa detecção de adulteração | qual |

## Débitos ALTOS

| ID | Débito |
|---|---|
| **FB-A1** | `_decidir` roda predicates ABAC globais ignorando `action` (predicate de `cliente.*` roda em `os.criar`) |
| **FB-A2** | `transaction.atomic()` aninhado só no `_gravar_audit` não garante atomicidade can()+audit fora de request HTTP (Celery) — INV-AUTHZ-002 exige mesma transação |
| **FB-A3** | `select_for_update()` documentado como mitigação de race mas NÃO mitiga (lock de linha existente não barra INSERT) — concern de segurança "mitigado" só no papel |
| **FB-A4** | `MfaRequiredMiddleware._tem_perfil_sensivel` não filtra `valido_ate` (divergente do provider `_resolver_perfis_vigentes`) |
| **FB-A5** | `ip_hash` declarado obrigatório no INV-AUTHZ-002, nunca preenchido (100% vazio) → resposta ANPD "de qual origem" impossível |
| **FB-A6** | Testes MFA usam stub `_FakeUserMFAOff`, nunca exercitam `django-otp.is_verified()` real (mock que mascara integração) |
| **FB-A7** | Nenhum teste de `RequireAuthz.has_permission` (a materialização do INV-AUTHZ-001 na borda DRF) — só via `provider.can()` |

## Débitos MÉDIO/BAIXO (anotados — tratar no loop ou Wave A)

- M: cache `can()` sem invalidação por evento (privilégio stale até 5min); seed `0003` DISABLE RLS/DROP POLICY (padrão criticado em SANEA-04); fuzzing 500 é loop paramétrico não fuzzing + contadores misturados; `pytest.raises` largo; helper `models_q_valido_ate_ok` duplicado; `purpose` string livre sem catálogo.
- B: provider não herda a porta (duck-typing sem teste de contrato); `Meta.ordering=["-timestamp"]` perigoso dado FB-C1; drill sem smoke test; `default_auto_field` inócuo.

## Regressões F-A→F-B confirmadas

1. FB-C1 — hash chain global/timestamp + algoritmo divergente (FA-C1 cravou por-tenant + sequência + `audit/hash_chain`).
2. FB-C3 — `usuario_id=''` vs sinal canônico `app.modo_sistema='1'` (FA-C1).
3. FB-A3 — race "mitigado" com `select_for_update`; FA-C1 usa `pg_advisory_xact_lock` por-tenant.
4. FB-C4 — drill repete falso-verde FA-A5 já saneado em `validar_f_a`.
5. M5 — seed authz DISABLE RLS/DROP, padrão que SANEA-04 criticou.
6. policies authz inline na migration fora do `rls_templates.py` (fonte única F-A).

## Plano do loop (ordem de conserto — causa-raiz)

1. **FB-C1 + FB-A2 + FB-A3** (núcleo): `AuthzDecision` ganha `sequencia`;
   extrair de `audit/services.py` um helper de cadeia compartilhado
   (`registrar_em_cadeia`) reusando `canonicalizar` + `calcular_hash` +
   advisory lock por-tenant + `_obter_hash_anterior`; authz delega.
   **Toca o núcleo F-A saneado → design + review tech-lead obrigatório.**
2. **FB-C3** — policy authz lê `app.modo_sistema='1'`; mover pro
   `rls_templates.py` (fonte única).
3. **FB-C2** — unificar atributo `authz_public` + mixin pra CBV DRF +
   hook `authz-check.sh` reconhecer o nome.
4. **FB-C4 + FB-C5** — drill robusto (recomputa hash, por-tenant, guarda
   anti-falso-verde, exit code) + teste de detecção de adulteração.
5. **FB-A1/A4/A5/A6/A7** — binding predicate→action; MFA filtra
   `valido_ate`; popular `ip_hash`; teste django-otp real; teste
   `RequireAuthz`.
6. MÉDIO/BAIXO conforme couber.
Depois: **reauditar F-B rodada 2** (3 lentes). Loop até zero CRÍTICO/ALTO.
