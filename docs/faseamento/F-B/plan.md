---
owner: roldao
revisado_em: 2026-05-19
proximo_review: 2026-08-19
status: stable
diataxis: explanation
audiencia: agente
fase: Foundation F-B
tipo: plano-arquitetural
revisores: [tech-lead-saas-regulado, advogado-saas-regulado]
relacionados:
  - docs/faseamento/F-B/spec.md
  - docs/faseamento/F-A/spec.md
  - docs/adr/0012-autorizacao-unificada.md
---

# Foundation F-B — Plano arquitetural

> Ponte `spec.md` → `tasks.md`. F-B é a camada de autorização SOBRE
> F-A fechada. Parte do código já foi reconciliado a esta spec nas
> frentes desta sessão (FB-C1+C3/FB-C2/FB-C4+C5) — o plano valida a
> abordagem e expõe risco dos ALTOs ainda abertos (FB-A1/A4/A5/A6)
> antes da matriz P8. `status: draft` até review tech-lead + advogado.

## Princípio

Não reescrever o que o ritual desta sessão já consertou (cadeia authz,
válvula pública, drill). Focar a revisão em: (a) os ALTOs abertos, (b)
fidelidade spec↔código pós-reconciliação, (c) o que F-A fechada agora
garante e F-B consome.

## US-FB-001/002/003 — porta + adapter + cadeia (RECONCILIADO)

`src/domain/authz/provider.py` (Protocol puro) + `infrastructure/authz/
django_provider.py` (adapter). `_gravar_audit` delega a
`registrar_em_cadeia` (helper único de F-A — classe de lock
`_ADVISORY_LOCK_CLASSE_AUTHZ`). Cadeia por-tenant; pré-tenant
POR-USUÁRIO via `run_in_user_context` + policy builder único
(`policies_authz_decisions` em `rls_templates.py`, sinal canônico
`modo_sistema='1'`). `_normalizar_para_hash` fonte única hash+persist.
**Risco:** baixo — revisado por tech-lead em FB-C1 (4 bloqueantes
absorvidos) + Família 5 F-A confirmou o helper sólido. **Onde:**
`django_provider.py`, `models.py`, `migrations/0001..0005`.

## US-FB-005 — RequireAuthz + válvula pública (RECONCILIADO)

`is_public(view,request)` fonte única (FB-C2) reconhece `@public`,
`PublicEndpoint`, função embrulhada, handler do método. Hook
`authz-check.sh` reconhece a marca canônica (+5 casos no runner →
118/118). Teste `test_authz_require_authz.py` cobre a matriz.
**Risco:** baixo. **Onde:** `permissions.py`, `decorators.py`.

## US-FB-006 — RBAC + ABAC binding (ALTO ABERTO FB-A1)

Hoje `_decidir` roda **todos** os predicates ABAC registrados
ignorando a `action` (predicate de `cliente.*` roda em `os.criar`) →
nega indevido. **Conserto proposto:** registry de predicates passa a
ser indexado por `action`/prefixo de recurso; `_decidir` só avalia
predicates **vinculados** à action corrente. Não muda RBAC. **Onde:**
`django_provider._decidir` + `predicates.py` (registry). **Ponto P-FB1
ao tech-lead.**

## US-FB-007 — MFA TOTP (ALTOS ABERTOS FB-A4, FB-A6)

`MfaRequiredMiddleware` barra perfil sensível sem TOTP. FB-A4: a
checagem de perfil sensível **não filtra `valido_ate`** (diverge de
`_resolver_perfis_vigentes`) → pode barrar por perfil expirado ou
divergir. **Conserto:** reusar o **helper único de vigência**
(`models_q_valido_ate_ok`) também no middleware MFA. FB-A6: testes MFA
usam stub `_FakeUserMFAOff` — nunca exercitam `django-otp
is_verified()` real (mock que mascara integração — viola TST-003).
**Conserto:** teste com device TOTP real do `django-otp` (verificado e
não-verificado). **Onde:** `authz/middleware.py`, `tests/test_authz_
mfa.py`. **Ponto P-FB2 ao tech-lead.**

## US-FB-008 — ip_hash (ALTO ABERTO FB-A5)

`authz_decisions.ip_hash` declarado obrigatório no INV-AUTHZ-002,
hoje **100% vazio**. **Conserto:** `RequireAuthz`/decorator extrai IP
do request, calcula SHA-256 (sem IP cru), propaga via parâmetro a
`can()` → `_gravar_audit` persiste. Chamada sem request (task) →
`ip_hash` vazio documentado (não-violação). **Risco:** baixo, mas toca
assinatura de `can()` (porta) — **Ponto P-FB3 ao tech-lead** (assinatura
da porta vs passar IP por contexto) + **ponto P-FB-A1 ao advogado**
(minimização: hash de IP é dado pessoal pseudonimizado — base/retentção).

## US-FB-009 — drill + cripto (RECONCILIADO)

`validar_f_b` robusto (FB-C4+C5): por-tenant + pré-tenant por-usuário,
injeção+detecção, anti-falso-verde, exit code, critério cobertura.
`verificar_integridade_cadeia_authz` recomputa sha256.
`test_adulteracao_no_meio` (Q-02). **Falta** confirmar AC-FB-009-5
(teste que prova `can()` retorna só após commit do audit) — verificar
em P8 (pode ser GAP). **Onde:** `management/commands/validar_f_b.py`,
`tests/test_authz_*`.

## Pontos para os revisores (bloqueante até resposta)

### tech-lead-saas-regulado
- **P-FB1**: binding predicate→action — registry indexado por action/
  prefixo é a abstração certa, ou o predicate deve declarar seu escopo
  e `_decidir` filtra? Risco de "predicate sem binding" virar
  permissivo silencioso (deve ser deny/erro explícito).
- **P-FB2**: MFA reusar `models_q_valido_ate_ok` no middleware — fonte
  única de vigência (sem 3ª cópia da regra `valido_ate`)? `django-otp`
  device real em teste é a forma correta de matar o stub FB-A6?
- **P-FB3**: `ip_hash` — passar como parâmetro novo de `can()` (muda a
  porta `AuthorizationProvider` no domínio) OU resolver via contexto
  (request) sem tocar a assinatura? Qual preserva melhor o domínio
  puro (NG-FB-1)?
- **P-FB4**: AC-FB-009-5 (`can()` só retorna após commit do audit) —
  como F-A fechou a fronteira transacional (xact-lock até COMMIT do
  request sob ATOMIC_REQUESTS), esse teste ainda é necessário/possível
  em F-B ou já está garantido por construção? Não criar teste teatral.

### advogado-saas-regulado
- **P-FB-A1**: `ip_hash` (SHA-256 do IP) na trilha de decisão —
  pseudonimização adequada (art. 13 §4)? Precisa de base legal/
  finalidade explícita no `purpose` e amarração à matriz de retenção
  (igual GATE-4 do PII hash)? IP é dado pessoal — minimização art. 6
  III.
- **P-FB-A2**: `authz_decisions` campos obrigatórios INV-AUTHZ-002
  (timestamp, user, tenant, action, resource_summary, purpose,
  decision, reason, perfis_aplicados, escopo_avaliado, ip_hash) —
  algum risco de PII bruta em `resource_summary`/`escopo_avaliado`
  (devem passar pelo `_normalizar_para_hash`/redator)? A trilha de
  decisão authz responde à mesma pergunta ANPD que a de auditoria?

> Revisar a abordagem (não reimplementar). Veredito por ponto:
> APROVA / APROVA COM CORREÇÃO / REJEITA + bloqueantes numerados.

---

## Correções absorvidas — review tech-lead + advogado (2026-05-19)

Veredito: ambos **APROVA COM CORREÇÕES**. Disposição: `[SPEC]` corrige
a spec agora; `[T-FB/P8]` vira tarefa de conserto; `[GATE-WaveA]`
rastreado (não bloqueia F-B dogfooding); `[P8-verify]` confere em P8.

### Tech-lead
- **BLOQ-1 (P-FB1) `[SPEC]`**: AC-FB-006-2 crava 2 bordas binárias:
  (a) predicate registrado **sem escopo declarado → erro em
  import-time** (não runtime, não permissivo global); (b) action **sem
  predicate aplicável → ABAC neutro (segue RBAC), NÃO deny**. Sem isso
  o conserto do FB-A1 vira fail-closed indevido.
- **BLOQ-2 (P-FB2/FB-A4) `[SPEC]`+`[T-FB/P8]`**: são **3** cópias da
  regra de vigência (middleware:153, django_provider:406 duplicada,
  _tem_perfil_sensivel que ignora `valido_ate` por completo). Conserto =
  **definição ÚNICA** da janela completa (`valido_de` E `valido_ate`)
  em módulo sem ciclo de import (ex.: `usuario/vigencia.py`), consumida
  por `_resolver_perfis_vigentes` + `_tem_perfil_sensivel` + middleware.
  T-FB próprio para a função duplicada. AC-FB-007-3 = "reusa a janela
  completa", não "filtra valido_ate".
- **BLOQ-3 (P-FB3) `[SPEC]`**: assinatura de `can()` **NÃO muda** em
  F-B (estabilidade do Protocol = NG-FB-1). `ip_hash` via **contextvar**
  (irmão de `usuario_id_context`), lido em `_gravar_audit`; entra
  **tanto** em `_payload_para_hash` **quanto** na coluna (senão
  `verificar_integridade_cadeia_authz` não o cobre → campo adulterável).
- **BLOQ-4 (P-FB4) `[SPEC]`**: AC-FB-009-5 + §3 item 4 reformulados —
  garantia é **atomicidade decisão↔audit / rollback-junto**, NÃO
  "commit antes do retorno" (FALSO sob ATOMIC_REQUESTS: savepoint).
  Teste = rollback-órfão (transação→can()→rollback→nova transação
  verifica ausência da linha). Não criar teste teatral.
- **MÉDIO-1 `[SPEC §3.1]`**: declarar risco aceito do TTL de cache de
  perfil (perfil expira, autoriza até `CACHE_TTL_SECS`) — espelha o
  rigor de F-A §3.1; gate Wave A liga invalidação event-driven
  (INV-INT-008).
- **MÉDIO-2/BAIXO-1 `[GATE]`+`[P8-verify]`**: redator PII em
  `resource_summary`/`escopo_avaliado` (ver advogado C-A2) vira gate;
  P8 confirma que `validar_f_b` enumera todas as partições
  (`tenant_id` distinct ∪ `usuario_id` distinct onde tenant NULL) —
  senão prova cripto é falso-verde por omissão.

### Advogado (LGPD) — `authz_decisions` é registro LGPD = mesmo rigor de F-A
- **C-A1.1 (P-FB-A1) `[SPEC]`+`[T-FB/P8]`**: `ip_hash` = **HMAC-SHA256
  com chave fora do banco** (não SHA-256 cru — IPv4 quebra por força
  bruta; cru não sustenta "pseudonimizado" art. 13 §4). Reusar família
  de chave do PII hash F-A.
- **C-A1.2 `[GATE-WaveA]`**: finalidade do `ip_hash` no RAT
  (segurança/rastreabilidade — art. 7 IX/II), não presumida.
- **C-A1.3 / BLOQ-jur-1 `[GATE-WaveA]`**: **GATE-FB-2** — retenção de
  `authz_decisions` + `ip_hash` na matriz tríplice (Receita/ISO/LGPD).
  Trilha imutável **sem prazo de descarte = violação art. 15/16**.
  `ip_hash` pode expirar antes do resto da linha (minimização).
- **C-A2.1 / BLOQ-jur-2 (P-FB-A2) `[SPEC]`+`[T-FB/P8]`**: `resource`
  sem PII tem que ser **imposto por código**, não docstring.
  `_normalizar_para_hash` **NÃO é redator** (só serializa). Conserto:
  `resource` aceita **allowlist de chaves** (`recurso_tipo`,
  `recurso_id`, `escopo`, flags) e **rejeita** chave de campo livre
  (fail-loud, simétrico ao rigor de tipo não-serializável). PII por
  **referência (id)**, nunca por valor (minimização art. 6 III).
- **C-A2.2 `[SPEC]`**: `escopo_avaliado` idem; nota na spec que
  `INV-AUTHZ-002` deve vedar PII por valor (texto da invariante em
  REGRAS muda via ADR/CODEOWNERS — flag, não editar REGRAS aqui).
- **BLOQ-jur-3 `[SPEC §3]`**: declarar conflito art. 18 (eliminação)
  × trilha imutável: `authz_decisions` conservada sob **art. 16 II /
  art. 37** (obrigação legal/registro de operação); não elimináveis
  por pedido de titular dentro do prazo de retenção; `ip_hash` pode
  expirar antes. Espelha a decisão de F-A (B-4 / crypto-shredding).

**Convergência:** a trilha authz tem o MESMO regime LGPD da auditoria
F-A — replicar (não inventar): mesma matriz de retenção, mesmo RAT,
mesma exceção de apagamento art. 16, mesma família de chave (HMAC).

**Limite honesto (escalado, não fechado por review):** ausência de
deadlock na cadeia authz sob concorrência real + integração
`django-otp`/`OTPMiddleware`/sessão real → drill `validar_f_b` +
pentest ASVS L2 antes do 1º tenant pago (consistente com §3.2/GATEs).

Pós-correções → `plan.md` `status: stable`. Próximo: P8 (matriz +
conserto T-FB).
