---
owner: agente-ia
revisado-em: 2026-06-05
proximo-review: 2026-09-05
status: draft
diataxis: explanation
audiencia: [agente, advogado, tech-lead, consultor-rbc]
frente: fiscal-nfse
tipo: investigacao-regra-0
relacionados:
  - docs/adr/0008-fiscal-pluggable.md
  - docs/adr/0049-fiscal-ct-nfce-devolucao.md
  - docs/adr/0067-perfil-regulatorio-tenant.md
  - docs/arquitetura/anti-corrosion-layer.md
---

# T-FIS-000 — Investigação regra #0: frente fiscal/NFS-e

> **Por que esta frente agora (dependency-first):** terminado o bloco metrologia
> (M5–M9) + consolidação da base (porta REST M4 + observabilidade F-C2), o
> próximo passo Wave A foi escolhido por **sinal de ordem objetivo**, não
> preferência: **fiscal/NFS-e é o ÚNICO módulo Wave A com deadline externo DURO
> — 01/09/2026** (Padrão Nacional NFS-e, Resolução CGSN 189/2026; ADR-0008 §7
> "R-016 score 20"). ~13 semanas a partir de hoje. Além do deadline, destrava
> `contas-receber` + `caixa-tecnico` + (indireto) `billing-saas`.

## 1. Estado real investigado

- **Scaffolding fiscal: ZERO** — não há `src/domain/fiscal/`, `infrastructure/fiscal/`
  nem porta `FiscalProvider` no código. Greenfield. (ADR-0008 está ACEITA com a
  Protocol especificada, mas nenhuma linha implementada.)
- **Cliente (M1) fornece o tomador**: `Cliente.documento` (CNPJ/CPF normalizado,
  ADR-0017 alfanumérico) + `tipo_pessoa` + nome. É a fonte do `customer_taxid`.
- **Predicate `documento_metrologico_obrigatorio_por_perfil`: NÃO existe** — a
  emenda da ADR-0008 (matriz perfil A/B/C/D × NFS-e calibração) precisa dele.
  Reusa o helper `tenant_perfil_e` (SAN-PERFIL Sprint 2, já pronto) + leitura do
  `Certificado.tipo_acreditacao` (M8, já pronto).
- **Certificado (M8) fornece o vínculo metrológico**: perfil A exige
  `certificado_id` RBC vigente; B/C cert simples; D aceita declaração. M8 já
  persiste `tipo_acreditacao` (RBC/NAO_RBC) — o predicate consome.
- **Valor da nota (`amount`)**: viria de `orcamentos`/pricing — **que NÃO existe
  ainda**. Decisão de seam (anti-retrabalho): no NÚCLEO o `amount` é **input
  explícito do caller** (não calculado pelo fiscal). Quando `orcamentos` existir,
  ele passa a alimentar o valor — sem reescrever o fiscal.
- **Storage WORM B2 (`store_xml`)**: B2 pago não está provisionado (decisão
  `project_deploy_so_quando_roldao_quiser` + sem contratações externas). Stub de
  porta + diferido (GATE pré-produção).

## 2. Constraint de produto (memória) que molda o escopo

`project_sem_contratacoes_externas_ate_producao`: **zero gasto com terceiro pago**
enquanto em desenvolvimento. PlugNotas/Focus NFe são pagos por NFS-e. Logo:
- **CONSTRÓI agora:** a porta `FiscalProvider` (Protocol agnóstica ADR-0008 §1) +
  `MockFiscalProvider` (determinístico, 4 modos) + domínio + use case +
  persistência + REST + matriz perfil. Tudo testável sem 1 centavo gasto.
- **DIFERE (GATE pré-produção):** `PlugNotasProvider`/`FocusNFeProvider` reais,
  `store_xml` em B2, smoke test trimestral com sandbox real, cláusulas contratuais
  (advogado revisa minuta, mas só assina pré-produção), circuit breaker com
  fallback real.

Isto é **anti-retrabalho**, não corte de escopo: o adapter real pluga na MESMA
porta quando o contrato for assinado — espelha o padrão dos módulos metrologia
(porta + adapter + fail-closed) e da ADR-0008 §6 (CircuitBreaker wrapper).

## 3. NÚCLEO da frente (escopo startável agora)

Emissão de NFS-e de serviço (calibração/manutenção) via porta agnóstica, com a
trava metrológica por perfil. Em ordem de dependência:

1. **Porta `FiscalProvider`** (Protocol) + VOs `InvoicePayload`/`InvoiceResult`/
   `InvoiceStatus` (PENDING/AUTHORIZED/REJECTED/CANCELED) — `src/domain/fiscal/`.
2. **`MockFiscalProvider`** — 4 modos (always_authorize/always_reject/
   pending_then_authorize/network_timeout); determinístico por hash do payload.
3. **Domínio** `NotaFiscalServico` (entidade) + máquina de estados + canonicalização
   probatória do XML/JSON (reusa ADR-0029) + hash versionado (reusa ADR-0064).
4. **Predicate `documento_metrologico_obrigatorio_por_perfil(tenant, tipo_servico)`**
   — fail-closed perfil A sem cert RBC vigente (ADR-0008 emenda + ADR-0067).
5. **Use case `emitir_nfse`** — monta payload (Cliente + serviço + amount input +
   certificado_id quando exigido) → valida perfil → chama provider → persiste
   resultado + evento WORM + (stub) store_xml → idempotente (IDEMP-001).
6. **Use cases `cancelar_nfse` / `consultar_status_nfse`**.
7. **REST** `NotaFiscalServicoViewSet` (emitir/cancelar/consultar/retrieve) +
   authz (ações novas `fiscal.*` seedadas) + Idempotency-Key + perfil server-side.
8. **Retenção**: matriz Receita 5a + prudencial 10a (ADR-0008 §3) na
   `retencao-matriz.md`.

## 4. DIFERIDO (rastreado — não corta, adia)

- GATE-FIS-PLUGNOTAS-REAL / GATE-FIS-FOCUS-REAL (adapters reais + sandbox).
- GATE-FIS-B2-XML (store_xml em B2 Object Lock).
- GATE-FIS-SMOKE-TRIMESTRAL (cron GitHub Action — ADR-0008 §4).
- GATE-FIS-CONTRATO (cláusulas SLA/DPA — advogado revisa minuta agora; assina
  pré-produção — ADR-0008 §5).
- GATE-FIS-CIRCUIT-BREAKER (fallback real primary→fallback — ADR-0008 §6).
- Non-goal Wave A (ADR-0049): CT-e, NFC-e. Devolução = US própria depois.
- Non-goal: farma TOP-3 / dossiê BPF (ADR-0008 §Anvisa — decisão Roldão V2-V3).

## 5. Dependências (tudo PRONTO p/ o núcleo)

`clientes` (M1 ✅ documento/tipo_pessoa) · `certificados` (M8 ✅ tipo_acreditacao) ·
`tenant_perfil_e` (SAN-PERFIL ✅) · canonicalização ADR-0029 ✅ · hash ADR-0064 ✅ ·
idempotência F-C ✅ · authz ADR-0012 ✅ · observabilidade F-C2 ✅. `orcamentos`
(amount) e B2/contratos = diferidos com seam pronto.

## 6. Revisões da spec (P2) — a rotear (INV-RITUAL-003)

- **advogado-saas-regulado**: retenção fiscal (5a/10a), DPA com BaaS, LGPD do
  tomador no payload, cláusulas mínimas de contrato (minuta, não assinatura).
- **tech-lead-saas-regulado**: design da porta `FiscalProvider` (agnóstica
  país/fornecedor), idempotência da emissão, máquina de estados, seam do amount.
- **consultor-rbc-iso17025**: matriz perfil × documento metrológico (A exige RBC
  vigente), coerência com cl. 7.8 (certificado) + ADR-0067.

## 7. Veredito

Frente fiscal/NFS-e **ABERTA** — dependency-first justificada por deadline duro
01/09/2026. NÚCLEO 100% startável agora sem gasto externo (porta + mock +
domínio + use case + REST + perfil). Próximo: **P1 spec** (US-FIS-NNN / AC) →
P2 revisões (advogado + tech-lead + consultor-rbc) → P3 plan → tasks → implement
→ P9 auditores. Adapters reais + B2 + contratos = GATEs pré-produção rastreados.
