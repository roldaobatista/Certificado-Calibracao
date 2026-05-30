---
owner: roldao
revisado-em: 2026-05-29
proximo_review: 2026-08-29
status: aceito
aceito-em: 2026-05-29
diataxis: explanation
audiencia: agente
tipo: adr
---

# ADR-0073 — Validação de cobertura metrológica (`cmc_cobre` / `procedimento_vigente_para`) no use case, não no permission layer DRF

## Contexto

Revisão do tech-lead ao `/plan` do M6 `metrologia/escopos-cmc` (2026-05-29, NC
TL-C-01 CRÍTICO) revelou que o "drop-in" assumido pela ADR-0066 para tornar o
predicate `cmc_cobre` real **não é viável como predicate-na-permissão**:

- `cmc_cobre` está registrado como predicate ABAC (`calibracao/apps.py:55-59`) e é
  avaliado por `DjangoAuthorizationProvider._decidir` (`django_provider.py:310-318`)
  durante `RequireAuthz.has_permission` (`permissions.py:43-83`).
- `get_authz_resource(request)` (`permissions.py:93-97`) recebe **apenas `request`**
  e roda **antes** do corpo da view `configurar` carregar a Calibracao persistida.
  Logo não há de onde derivar `grandeza`/`faixa`/`data` **server-side** no momento
  em que o predicate é avaliado, sem uma query adicional dentro do permission layer.
- O molde M3 (`ordens_servico/views.py:220`) monta o resource a partir de
  `request.data`/`query_params` — **do payload** — o que é proibido para dado
  metrológico (SEG-CAL-10: faixa não pode vir do cliente).
- Além disso, a validação anti-PII (`django_provider.py:69-89`) só não-recursa
  dentro da chave `escopo`; grandeza/faixa no topo do resource levantam `ValueError`
  (NC TL-C-02).

O mesmo problema atinge `procedimento_vigente_para` (módulo irmão
`procedimentos-calibracao`). Resolver uma vez evita que cada módulo decida
diferente.

## Decisão

1. **A validação de cobertura metrológica (`cmc_cobre`, `procedimento_vigente_para`
   e futuras regras de barreira metrológica) é avaliada DENTRO do use case**
   (`configurar_calibracao`, `aprovar_revisao`, etc.), por **chamada explícita à
   porta** do módulo (`escopos_cmc.query_service.cobre(...)` /
   `procedimentos.query_service.vigente_para(...)`), retornando erro de domínio
   mapeado a **412** (`EscopoNaoCobreFaixa` / `ProcedimentoVigenteAusente`).
2. **O permission layer DRF (`RequireAuthz` + predicates ABAC) fica restrito a
   RBAC/perfil/segregação de funções** — regras que dependem só de IDs e do
   contexto da request (ex.: `pode_aprovar_revisao_2a_conferencia`, que é REAL e
   opera sobre IDs sem DB). Regras de NEGÓCIO METROLÓGICO que exigem estado
   persistido (escopo vigente, procedimento vigente) saem do permission layer.
3. **Os predicates STUB `cmc_cobre` / `procedimento_vigente_para` em
   `predicates_calibracao.py` são DEPRECADOS** quando a porta no use case entrar.
   Mantidos como no-op documentado durante a transição (não removidos no mesmo
   commit que adiciona a porta — evita quebrar o registro em `apps.py` sem migração
   coordenada). O bloco drop-in comentado (`:170-178`) é removido (substituído pela
   chamada no use case).
4. **A porta é exposta como função de módulo sem estado** em
   `query_service.py` (molde M5 `padroes/query_service.py`), **fail-CLOSED**, com
   filtro `tenant_id` explícito além da RLS — NÃO singleton stateful (resolve
   também NC TL-C-04 / §9 Q do dossiê).

## Non-goals desta ADR

- NÃO altera o contrato lógico de cobertura (faixa/CMC/vigência) — só ONDE é
  avaliado.
- NÃO remove o ABAC para RBAC/perfil/segregação — esses continuam no permission layer.
- NÃO entrega os módulos `escopos-cmc`/`procedimentos` (escopo do M6 e do irmão).

## Consequências

**Positivas:**
- A regra de negócio metrológica vive na camada de negócio (use case), não no
  permission layer DRF — clean architecture (ADR-0007). O use case tem acesso ao
  estado persistido (Calibracao já carregada), elimina a dependência do timing/shape
  do resource e do contorno anti-PII.
- Padrão único para os dois módulos fail-open lazy da ADR-0066 (`cmc_cobre` e
  `procedimento_vigente_para`) — não divergem.
- Mensagem de erro (412 com CMC oficial / procedimento) é construída no domínio,
  onde há o contexto completo.

**Negativas (aceitas):**
- Diverge do padrão M3 (que pôs algumas regras como predicates ABAC). Aceito: M3
  não tinha regra que exigisse estado persistido carregado pós-permissão.
- Os predicates STUB ficam órfãos temporariamente (no-op) até remoção coordenada —
  débito de limpeza rastreado.

## Dependências

- **Refina:** ADR-0066 (que declarou o fail-open lazy assumindo predicate-na-permissão).
- **Habilita:** GATE-CAL-CMC-PREDICATE (M6) + GATE-CAL-PROC-VIGENTE-PREDICATE
  (`procedimentos-calibracao`).
- **Depende de:** ADR-0007 (camada de domínio), ADR-0012 (AuthorizationProvider).

## Status

ACEITO em 2026-05-29 como conserto da NC TL-C-01 (CRÍTICO) da revisão tech-lead do
plan M6 `escopos-cmc`. Análogo a como a revisão tech-lead do M5 gerou ADR-0072.
Reconciliação em `docs/faseamento/M6-escopos-cmc/reviews-consolidado.md`.
