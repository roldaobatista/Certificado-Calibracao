---
owner: agente-ia
revisado-em: 2026-06-08
proximo-review: 2026-09-08
status: draft
diataxis: reference
audiencia: [agente, auditor, advogado, tech-lead, consultor-rbc]
frente: fiscal-nfse
tipo: spec-faseamento
relacionados:
  - docs/faseamento/fiscal-nfse/T-FIS-000-investigacao.md
  - docs/dominios/financeiro/modulos/fiscal/prd.md
  - docs/adr/0008-fiscal-pluggable.md
  - docs/adr/0049-fiscal-ct-nfce-devolucao.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0029-canonicalizacao-texto-probatorio.md
  - docs/adr/0064-rotacao-hmac-kms.md
  - docs/conformidade/comum/retencao-matriz.md
  - docs/conformidade/comum/matriz-feature-perfil.md
---

# Spec de faseamento — frente `fiscal/NFS-e` (núcleo de emissão agnóstica)

> **Escopo:** núcleo lógico da emissão de NFS-e de serviço (calibração/manutenção)
> via **porta agnóstica `FiscalProvider`** (ADR-0008 §1) + `MockFiscalProvider`
> determinístico, com a **trava metrológica por perfil** (`documento_metrologico_
> obrigatorio_por_perfil`, emenda ADR-0008 + ADR-0067), entidade `NotaFiscalServico`
> com máquina de estados, canonicalização probatória (ADR-0029) e hash versionado
> (ADR-0064), use cases emitir/cancelar/consultar, REST e retenção fiscal. Adapters
> reais (PlugNotas/Focus), `store_xml` em B2, A3/OCSP real, contingência, CC-e,
> inutilização, devolução e cutover ficam **DIFERIDOS** (GATE-FIS-* pré-produção) —
> espelha o recorte porta+mock+domínio dos módulos metrologia. Base:
> `T-FIS-000-investigacao.md` (regra #0; greenfield confirmado).

## 1. Por que agora (dependency-first)

Único módulo Wave A com **deadline externo DURO — 01/09/2026** (Padrão Nacional
NFS-e, Resolução CGSN 189/2026; ADR-0008 §Contexto, R-016 score 20). ~12 semanas a
partir de hoje. Sem fiscal, o tenant não fatura serviço (receita zero). Destrava
`financeiro/contas-receber` + `caixa-tecnico` + (indireto) `billing-saas`.

## 2. Seam pronto (NÃO reconstruir — T-FIS-000 §1/§5)

| Peça | Onde | Uso na frente |
|------|------|---------------|
| `Cliente.documento` (CNPJ/CPF normalizado ADR-0017) + `tipo_pessoa` + nome | M1 `clientes` ✅ | fonte do `customer_taxid`/`customer_name` do payload |
| `Certificado.tipo_acreditacao` (RBC/NAO_RBC) | M8 `certificados` ✅ | vínculo metrológico consumido pelo predicate de perfil |
| `tenant_perfil_e(perfis)` + ContextVar `perfil_tenant_context` | SAN-PERFIL Sprint 2 ✅ | base do predicate (lê tenant, NUNCA payload — defesa L6) |
| Canonicalização probatória ADR-0029 + hash versionado ADR-0064 | M3/M4 ✅ | snapshot imutável do payload/resultado da NFS-e |
| Idempotência (IDEMP-001) + authz ACTION_MAP (ADR-0012) + observabilidade F-C2 | F-C ✅ | molde de ViewSet/use case (reusar, zero padrão novo) |
| Path infra aninhado (ADR-0072) — `src/{domain,infrastructure}/fiscal/` | molde metrologia ✅ | (fiscal é raiz própria, não sob `metrologia/`; mesmo padrão de camadas) |

## 3. Escopo — US do PRD cobertas (núcleo)

| US do PRD | O que entra AGORA | O que difere |
|-----------|-------------------|--------------|
| **US-FIS-001** emitir NFS-e a partir de Cert/OS | use case `emitir_nfse` via `MockFiscalProvider`; predicate `documento_metrologico_obrigatorio_por_perfil` (A=cert RBC vigente / B=cert simples / C=cert+flag / D=declaração) fail-closed; AC-1 (happy mock), AC-4 (cross-tenant INV-TENANT-001), AC-5 (idempotência), AC-8 (perfil incompatível 403), AC-9 (perfil D declaração); evento WORM `Fiscal.NFSeEmitida` + `perfil_no_evento` | AC-2 cert A3 vencido / AC-3 BaaS down→contingência / AC-6 OCSP revoked / AC-7 município sem cobertura — todos exigem A3/OCSP/BaaS reais (diferidos) |
| **US-FIS-003** cancelar NFS-e <24h | use case `cancelar_nfse` (motivo ≥30ch + janela 24h) via `MockFiscalProvider.cancel_invoice`; AC-1 (happy), AC-2 (prazo expirado 422), AC-3 (cross-tenant 404) | janela/regras reais por município (adapter real) |
| **US-FIS-001 (consulta)** resolver PENDING | use case `consultar_status_nfse` via `query_status` (mock `pending_then_authorize`) | polling/webhook real do BaaS |
| **US-FIS-007** `Fiscal.NFSeEmitida` → ContasReceber | **publica o evento WORM agora** (seam) — payload `{nfse_id, cliente_referencia_hash, certificado_id_OR_declaracao_id, tipo_servico, valor_centavos, perfil_no_evento}` | o **consumer** `financeiro/contas-receber` não existe ainda → criação do título = frente própria depois (seam pronto) |

`amount` (valor) = **input explícito do caller** no núcleo (não calculado). Quando
`orcamentos`/pricing existir, alimenta o valor sem reescrever o fiscal (T-FIS-000 §1).

## 4. Non-goals desta frente (diferidos — declarados; rastreados GATE-FIS-*)

- **Adapters reais** `PlugNotasProvider`/`FocusNFeProvider` + sandbox E2E
  (GATE-FIS-PLUGNOTAS-REAL / GATE-FIS-FOCUS-REAL) — pagos, `project_sem_contratacoes_
  externas_ate_producao`.
- **`store_xml` em B2 Object Lock** (GATE-FIS-B2-XML) — stub de porta agora.
- **Smoke trimestral** sandbox (GATE-FIS-SMOKE-TRIMESTRAL — ADR-0008 §4).
- **Cláusulas SLA/DPA do contrato BaaS** (GATE-FIS-CONTRATO — advogado revisa a
  minuta AGORA na P2; assinatura só pré-produção — ADR-0008 §5).
- **Circuit breaker primary→fallback** (GATE-FIS-CIRCUIT-BREAKER — ADR-0008 §6).
- **A3/OCSP real do tenant** (US-FIS-001 AC-2/6 + predicate `documento_a3_
  obrigatorio_por_perfil`) — depende de `seguranca/certificados-digitais` (ADR-0048/0046).
- **Contingência** US-FIS-002 / **CC-e** US-FIS-004 / **inutilização** US-FIS-005
  (Wave B) / **devolução** US-FIS-009 / **ajuste extemporâneo** US-FIS-010 / **tabelas
  fiscais** US-FIS-008 / **export contador** US-FIS-006 (V2) / **cutover drill**
  US-FIS-CUT-001 (manual pré-01/09).
- **Aferê NÃO calcula imposto** (non-goal permanente PRD §6) — campos exibidos, valor
  é input. **CT-e / NFC-e** (ADR-0049 Wave B). **Farma TOP-3 / dossiê BPF** (V2-V3).

## 5. Invariantes (a cravar em REGRAS — família INV-FIS-*; numeração no /plan)

Núcleo:
- **INV-FIS-PERFIL-001** — emissão de NFS-e `tipo_servico=calibracao` exige documento
  metrológico **compatível com `Tenant.perfil_regulatorio`** (predicate
  `documento_metrologico_obrigatorio_por_perfil`), lido via ContextVar **server-side
  NUNCA do payload**; perfil A sem cert RBC vigente → 422/403 fail-closed (defesa
  anti-fraude L6). Formaliza INV-INT-001 do PRD para a porta de emissão.
- **INV-FIS-PROVIDER-001** — domínio/use case nunca importam SDK de fornecedor; toda
  emissão passa pela porta `FiscalProvider` (Protocol). `import plugnotas*`/`focus*`
  só em `infrastructure/fiscal/adapters/` (hook de fronteira).
- **INV-FIS-WORM-001** — `NotaFiscalServico` emitida + evento `Fiscal.NFSeEmitida` são
  append-only (WORM Padrão B); cancelamento é **nova transição registrada**, não
  UPDATE destrutivo; XML/JSON probatório canonicalizado (ADR-0029) + hash (ADR-0064).
- **INV-FIS-IDEMP-001** — `emitir_nfse` é idempotente por `Idempotency-Key`
  (= `causation_id`); 2 POSTs em 24h → mesmo `nfse_id` (IDEMP-001 / AC-FIS-001-5).
- **INV-FIS-TENANT-001** — payload referenciando cliente/cert de outro tenant →
  bloqueio hard anti-oracle (reusa INV-TENANT-001; AC-FIS-001-4).
- **Reusadas:** INV-INT-001 (matriz perfil), INV-FIS-CR-001 (evento dispara título —
  consumer diferido), INV-007/008 (audit + contingência — contingência diferida),
  INV-TENANT-001..004, INV-TENANT-PERFIL-001/003/004, INV-HMAC-001..005,
  INV-DOC-CANON-001, INV-ANON-001..004 (PII do tomador no payload).

## 6. Fatias propostas (refinar no /plan — ordem por dependência)

- **Fatia 1a** — domínio puro: VOs `InvoicePayload`/`InvoiceResult`/`InvoiceStatus`
  (PENDING/AUTHORIZED/REJECTED/CANCELED) + porta `FiscalProvider` (Protocol) +
  `MockFiscalProvider` (4 modos determinísticos por hash do payload) + entidade
  `NotaFiscalServico` + máquina de estados + transições WORM + canonicalização/hash.
  Zero Django.
- **Fatia 1b** — schema: migrations RLS v2 + WORM Padrão B (triggers anti-mutação) +
  grants + seed authz (`fiscal.*`) + UNIQUE idempotência (`Idempotency-Key`) +
  mappers/repositories aninhados + drill `validar_fiscal_nfse`.
- **Fatia 2** — predicate + use cases + REST: `documento_metrologico_obrigatorio_por_
  perfil` (server-side, fail-closed, timeout 50ms) + `emitir_nfse` (monta payload do
  Cliente + serviço + amount input + certificado_id/declaracao_id quando exigido →
  valida perfil → chama provider → persiste + evento WORM + stub `store_xml`) +
  `cancelar_nfse` + `consultar_status_nfse` + `NotaFiscalServicoViewSet`
  (emitir/cancelar/consultar/retrieve) + ACTION_MAP authz + Idempotency-Key + perfil
  server-side.
- **Fatia 3 (P7)** — família INV-FIS-* em REGRAS + `TestINV_FIS_*` nomeadas (TST-004) +
  hooks (`fiscal-perfil-server-side-check`, `fiscal-provider-import-fronteira-check`,
  `fiscal-worm-cancelamento-check`) + retenção-matriz (linha NFS-e/XML — Receita 5a +
  prudencial 10a, ADR-0008 §3) + matriz-feature-perfil (linhas US-FIS por perfil).
- **P8/P9** — matriz-reconciliacao (molde M7) + emenda PRD (marcar AC núcleo vs
  diferido) + auditores roteados (INV-RITUAL-003: + **auditor-supplychain** pela porta
  agnóstica e + **auditor-conformidade-lgpd** pelo PII do tomador).

## 7. Decisões / questões para os revisores (P2 — INV-RITUAL-003)

- **advogado-saas-regulado:** retenção fiscal (Receita 5a legal + 10a prudencial —
  ADR-0008 §3); PII do tomador no payload/evento (`cliente_referencia_hash` vs dado
  claro; LGPD base legal "obrigação fiscal"); cláusulas mínimas do contrato BaaS
  (escrever a **minuta** agora; assinatura só pré-produção). Confirmar que o núcleo
  sem adapter real **não cria obrigação contratual** nesta janela.
- **tech-lead-saas-regulado:** design da porta `FiscalProvider` agnóstica de
  país/fornecedor (não vazar conceito BR no Protocol); idempotência da emissão
  (chave = `causation_id`); máquina de estados (PENDING→AUTHORIZED/REJECTED;
  AUTHORIZED→CANCELED); seam do `amount`; onde mora o circuit breaker (wrapper
  diferido) sem acoplar o núcleo.
- **consultor-rbc-iso17025:** matriz perfil × documento metrológico (A exige RBC
  vigente na **data de emissão** — coerência com cl. 7.8 + ADR-0067 + INV-CER-CGCRE-
  VIG-001 do M8); perfil D `declaracao_calibracao_basica` aceitável sem ritual 17025;
  o fiscal **lê** o vínculo metrológico, não emite documento metrológico.
- **Fronteira com o M8 (rbc/tech-lead):** o predicate de perfil deve **reconsultar** a
  vigência da acreditação (M9 populou `Tenant.acreditacao_vigencia_fim`) ou confiar no
  `Certificado.tipo_acreditacao` já snapshotado pelo M8? (provável: confia no snapshot
  do certificado RBC vigente — o M8 já rebaixou RBC→não-RBC se a acreditação estava
  vencida na emissão; o fiscal só exige o vínculo).

**Próximo:** revisões `advogado` + `tech-lead` + `consultor-rbc` (P2) → incorporar →
`plan` (P3, crava numeração INV-FIS + decide ADRs/emendas + tasks T-FIS-NNN) →
`/tasks` → implement Fatia 1a.
