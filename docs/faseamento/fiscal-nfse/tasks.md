---
owner: agente-ia
revisado-em: 2026-06-08
proximo-review: 2026-09-08
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: fiscal-nfse
tipo: tasks-faseamento
estado-ritual: ready-for-implement
relacionados:
  - docs/faseamento/fiscal-nfse/plan.md
  - docs/faseamento/fiscal-nfse/spec.md
---

# Tasks — frente `fiscal/NFS-e` (núcleo de emissão agnóstica)

> Deriva do `plan.md` (D-FIS-1..10 + INV-FIS-001..009). Ordem por dependência:
> 1a (domínio puro) → 1b (schema) → 2 (use cases + REST) → 3 (P7) → P8/P9. Cada task
> tem AC binário verificável. Path raiz própria `src/{domain,application,infrastructure}/fiscal/`.

## Fatia 1a — domínio puro (zero Django)

- **T-FIS-010** — VOs `InvoicePayload`/`InvoiceResult`/`InvoiceStatus`.
  - AC: `InvoiceStatus` enum {PENDING, AUTHORIZED, REJECTED, CANCELED}. `InvoicePayload`
    frozen com `tenant_id`, `issuer_taxid`, `customer_taxid`, `customer_name`,
    `service_description`, `service_code`, `amount: Decimal`, `issue_date`, `metadata: dict`.
    `InvoiceResult` frozen com `invoice_id`, `status`, `authorization_code|None`,
    `pdf_url|None`, `xml_bytes|None`, `rejection_reason|None`, `raw_response: dict`,
    `metadata: dict`. **Nenhum** atributo nomeado BR (`chave_acesso_44` etc.) — só em
    `metadata` (D-FIS-1). VO **não** valida formato BR.
- **T-FIS-011** — porta `FiscalProvider` (Protocol).
  - AC: métodos `emit_invoice(payload)->InvoiceResult`, `cancel_invoice(invoice_id,
    reason)->InvoiceResult`, `query_status(invoice_id)->InvoiceStatus`,
    `store_xml(invoice_id, xml)->StorageRef`, `supported_countries()->list[str]`,
    `health_check()->HealthStatus`. Sem conceito BR no contrato.
- **T-FIS-012** — `MockFiscalProvider` em `src/domain/fiscal/` (D-FIS-8).
  - AC: 4 modos determinísticos por hash do payload: `always_authorize` (→AUTHORIZED +
    `authorization_code`), `always_reject` (→REJECTED + `rejection_reason`),
    `pending_then_authorize` (1ª `emit`→PENDING; `query_status` subsequente→AUTHORIZED),
    `network_timeout` (levanta exceção de transporte). Sem I/O, sem SDK.
- **T-FIS-013** — entidade `NotaFiscalServico` + máquina de estados (D-FIS-3/4).
  - AC: transições válidas PENDING→AUTHORIZED|REJECTED; AUTHORIZED→CANCELED; REJECTED e
    CANCELED terminais. Transição inválida → erro de domínio. Cancelamento = nova
    transição (não recria). Snapshot probatório canonicalizado (ADR-0029) + hash
    versionado (ADR-0064). Testes cobrem cada aresta + UNHAPPY (transição proibida).
- **T-FIS-014** — função pura `documento_metrologico_obrigatorio_por_perfil` (D-FIS-5/6/7).
  - AC: assinatura `(perfil, tipo_servico, certificado|None, declaracao_id|None)`. Perfil
    A: exige `certificado_id` vinculado (RBC **ou** NAO_RBC — D-FIS-6); B/C: cert simples
    (não-RBC); B/C com cert `tipo_acreditacao==RBC` → `DocIncompativelComPerfilError`
    (AC-FIS-001-8); D: aceita `declaracao_id`. `tipo_servico="calibracao"` em todos os
    perfis (D-FIS-7). **Nunca** lê vigência do Tenant (INV-FIS-002). Função pura, sem I/O.
- **T-FIS-015** — repository Protocols + testes puros (Fakes).
  - AC: `NotaFiscalServicoRepository` Protocol (`salvar`/`obter`/`existe_chave`).
    ≥20 testes puros verdes; ruff/mypy limpos no módulo.

## Fatia 1b — schema (infra)

- **T-FIS-020** — model `nota_fiscal_servico` + migration RLS v2 + WORM Padrão B + grants.
  - AC: colunas tipadas (status, origem_id, versao, valor_centavos, perfil_no_evento,
    certificado_id/declaracao_id, snapshot_hash, customer_*); RLS v2 (`tenant_id` + policy);
    trigger WORM Padrão B respeitando D-FIS-4 (status mutável só pelas transições válidas;
    bloqueia DELETE/UPDATE de campos imutáveis). `migration-rls-check` exit 0.
- **T-FIS-021** — UNIQUE de negócio + seed authz.
  - AC: UNIQUE `(tenant_id, origem_id, versao)` (D-FIS-2). Seed `fiscal.emitir`/
    `fiscal.cancelar`/`fiscal.consultar`/`fiscal.retrieve` no authz. makemigrations --check limpo.
- **T-FIS-022** — mappers + repositories aninhados + `existe_chave`.
  - AC: mapper entidade↔model lossless; `existe_chave(tenant, origem_id, versao)` consulta
    a UNIQUE; repository implementa o Protocol da 1a.
- **T-FIS-023** — drill `validar_fiscal_nfse` + teste schema PG-real.
  - AC: drill ≥ checks de colunas/RLS/WORM/grants/UNIQUE 100% PG-real; teste RLS
    cross-tenant UNHAPPY (vê 0 linhas do outro tenant) + WORM (UPDATE imutável bloqueado).

## Fatia 2 — use cases + REST

- **T-FIS-030** — `emitir_nfse` (application puro + injeção de porta).
  - AC: carrega Cliente (customer_taxid/name) + Certificado (snapshot RBC, se exigido) +
    `amount` input → valida compatibilidade via T-FIS-014 (no use case, D-FIS-5) → chama
    `provider.emit_invoice` injetado → persiste `NotaFiscalServico` + evento cadeia WORM
    `Fiscal.NFSeEmitida` + outbox `fiscal.nfse_emitida` (D-FIS-9) + stub `store_xml`.
    Idempotência 2 camadas (D-FIS-2): Idempotency-Key (serviço central) + `existe_chave`
    (origem em PENDING → 409 retorna existente, sem 2ª chamada ao provider). `network_timeout`
    → nenhuma persistência + `falhar_chave` + erro 503/504 (D-FIS-3). Evento WORM só com
    `cliente_referencia_hash` (INV-FIS-009).
- **T-FIS-031** — `cancelar_nfse` + `consultar_status_nfse`.
  - AC cancelar: motivo ≥30ch (senão 422) + janela 24h (>24h → 422 PRAZO_EXPIRADO) +
    advisory lock `(tenant, nfse_id)` + transição AUTHORIZED→CANCELED + evento append-only
    `Fiscal.NFSeCancelada` + XML cancelamento canonicalizado. Cross-tenant → 404.
  - AC consultar: `query_status` resolve PENDING→AUTHORIZED|REJECTED (único caminho);
    consulta repetida no mesmo estado = no-op idempotente.
- **T-FIS-032** — `NotaFiscalServicoViewSet` REST.
  - AC: ações emitir/cancelar/consultar/retrieve; ACTION_MAP + `get_authz_action` (molde
    M8); `tenant_perfil_e` server-side (DRF, antes do use case); Idempotency-Key header;
    serializer **traduz `metadata` BR** no body (`chave_acesso_44`/`numero` — D-FIS-1);
    perfil nunca do payload (INV-FIS-001).
- **T-FIS-033** — testes API E2E.
  - AC: happy (mock always_authorize→201); perfil incompatível (B+cert RBC→403); perfil A
    + cert NAO_RBC → 201 (D-FIS-6); cross-tenant → 404/422 (INV-FIS-006); idempotência
    (mesmo Idempotency-Key 2× → mesmo nfse_id); dupla origem em PENDING → 409; PENDING→
    AUTHORIZED via consultar; network_timeout → 503 sem persistência. Todos PG-real verdes.

## Fatia 3 — P7

- **T-FIS-040** — INV-FIS-001..009 em `REGRAS-INEGOCIAVEIS.md` + `TestINV_FIS_*` (TST-004).
  - AC: 9 invariantes cravadas; 9 classes nomeadas `TestINV_FIS_00N` (PG-real/puro);
    sem ID duplicado.
- **T-FIS-041** — 3 hooks + casos `_test-runner`.
  - AC: `fiscal-perfil-server-side-check` (INV-FIS-001), `fiscal-provider-import-fronteira-check`
    (INV-FIS-003 — anti `plugnotas*`/`focus*`/`pybreaker` fora de infra/fiscal),
    `fiscal-anti-rbc-em-descricao` (INV-FIS-007). Hooks testados contra os arquivos REAIS
    (não bloqueiam código legítimo). Contagens sincronizadas (AGENTS/CLAUDE/README/STATUS-GERADO).
- **T-FIS-042** — `retencao-matriz.md` (FIS-J-02/03/04).
  - AC: citação corrigida (art. 173/174 + 195 §único CTN + ISS municipal); nota prudencial
    10a; linha NFS-e/XML zona B (ADR-0021).
- **T-FIS-043** — `matriz-feature-perfil.md`.
  - AC: linhas US-FIS por perfil (A RBC obrigatório / B-C-D doc × perfil / anti-RBC descrição
    / retenção 5a A-B-C, 5a D).

## P8/P9

- **T-FIS-050** — matriz-reconciliacao (molde M7, 8 seções) + emenda PRD + emenda ADR-0008.
  - AC: US↔AC↔INV↔ADR↔hook↔código + INV↔teste + GATEs + pendências; PRD §11/§7 emendado
    (predicate no use case; AC-FIS-001-9 sem `_basica`; borda perfil A+NAO_RBC); ADR-0008
    emendada (D-FIS-1/5 + 14 cláusulas); veredito pronto-para-P9.
- **T-FIS-051** — P9 auditores roteados (INV-RITUAL-003).
  - AC: seguranca + llm-correctness + produto + qualidade + idempotencia + observabilidade
    + **supplychain** (porta agnóstica/deps futuras) + **conformidade-lgpd** (PII tomador);
    cada achado MÉDIO+ resolvido na causa-raiz; INV-RITUAL-001 satisfeito.

**Próximo:** implement **Fatia 1a** (T-FIS-010..015) — domínio puro, sem dependência externa.
