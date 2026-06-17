---
owner: roldao
revisado-em: 2026-06-17
proximo-review: 2026-09-17
status: stable
modulo: caixa-tecnico
dominio: financeiro
diataxis: explanation
audiencia: agente
historico:
  - 2026-05-17 — versão inicial draft (caixa do técnico Wave A robusto)
  - 2026-05-27 — Onda 3 saneamento BATCH B2 — frontmatter canônico completo (owner lowercase + hífen + diataxis + audiencia + proximo-review), perfil ADR-0067 declarado, US-CT-001..007 reescritas em BDD GIVEN-WHEN-THEN, AC LGPD GPS opcional matriz base legal (idêntico app-tecnico), AC trigger PG `caixa_tecnico_anti_mutacao` (US-CT-005), AC IDEMP-001 client_offline_id (US-CT-002), Glossário §11, vocabulário Wave A/Wave B, status STABLE.
  - 2026-06-17 — correções P2 da spec (revisão tech-lead + advogado LGPD): AC-CT-005-3 trigger na tabela `despesa` (não na raiz) + block-delete fiscal [TL-CT-05]; AC-CT-002-5 base legal GPS = art. 7º IX (legítimo interesse + LIA) + V de apoio, não consentimento [ADV-CT-01]; AC-CT-002-7 retenção GPS própria curta (fechamento+90d) desacoplada dos 5a fiscais [ADV-CT-02]. Detalhe: `docs/faseamento/caixa-tecnico/reviews-consolidado.md`.
relacionados:
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0050-gateway-pagamento.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - docs/conformidade/comum/lgpd-rat.md
  - docs/conformidade/comum/retencao-matriz.md
  - docs/dominios/operacao/modulos/app-tecnico/prd.md
---

# PRD — Caixa do Técnico

## 1. O que é

Controle financeiro individual de cada técnico de campo: adiantamentos recebidos, despesas executadas, fotos de recibo, prestação de contas mensal. Vinculado a OS quando aplicável.

## 2. Por que existe

BIG-08 (frota + UMC + caixa). Hoje em tenants reais: técnico recebe R$ 500 em dinheiro, anota recibos em papel, no fim do mês entrega pasta amassada → financeiro perde 4-8h pra conciliar. JTBD-060/061/062/064. **Wave A robusto** (não simplificado) — decisão estratégica pra ganhar técnicos como evangelizadores.

## 3. Personas

**Persona dominante:** P-OP-01 (técnico de campo). Detalhes em `personas.md` + `../personas.md` — P-OP-01 (técnico de campo, primária), P-FIN-01 (financeiro — valida e fecha mês), P-FIN-02 (dono — vê total adiantado).

## 4. Perfil regulatório (ADR-0067)

Módulo é **transversal a A/B/C/D** (toda empresa com técnico de campo tem caixa). Sem gating de regulação específico, mas retenção de PII GPS varia por perfil:

| Feature | A — Acreditado RBC | B — Rastreável | C — Em preparação D→A | D — Comercial puro |
|---|---|---|---|---|
| **Caixa do técnico básico (US-CT-001..007)** | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |
| **GPS opcional na despesa** — opt-in server-side `Colaborador.consente_gps_em` (idêntico app-tecnico US-APP-003) | ⚪ OPCIONAL | ⚪ OPCIONAL | ⚪ OPCIONAL | ⚪ OPCIONAL |
| **Retenção GPS da despesa** | 5 anos + crypto-shredding | 5 anos + crypto-shredding | 5 anos + crypto-shredding | 5 anos + crypto-shredding |
| **Despesa imutável após validação (trigger PG `caixa_tecnico_anti_mutacao`)** | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |

Predicate canônico: `tenant_perfil_e([...])` lê `Tenant.perfil_regulatorio` no banco — NUNCA do payload.

## 5. Escopo Wave A

- Solicitação de adiantamento via app (técnico → aprovação financeiro/dono)
- Lançamento de despesa via app com foto-comprovante obrigatória
- Vincular despesa a OS (opcional, recomendado)
- Categorização (combustível, alimentação, pedágio, hospedagem, peça, deslocamento)
- Reembolso de km automático (km × tarifa configurada pelo tenant)
- Prestação de contas em ≤ 5 min (JTBD-062): saldo aberto + lista validada + 1 toque fecha mês
- Validação financeiro: 1 swipe valida/rejeita com motivo
- Audit completo (foto + GPS opcional + timestamp)
- Política do tenant: limites por categoria, alçada de aprovação
- **Despesa validada = imutável** (trigger PG `caixa_tecnico_anti_mutacao` análogo `auditoria_anti_*`)

## 6. Não-objetivos Wave A

- OCR automático do recibo (Wave B)
- Integração com gateway de cartão corporativo (Wave B — depende Pluggy)
- Reembolso via PIX instantâneo (Wave B — depende ADR-0050)
- Múltiplas moedas / técnico em viagem internacional
- Adiantamento via folha de pagamento

<!-- prd-ux-states: skip -- caixa-tecnico Wave A entrega BACKEND (endpoints idempotentes offline-first + validacao de foto/prestacao + triggers WORM); a captura de foto, o swipe de validacao e a fila por-tela sao da FRENTE DE TELAS (app Flutter diferido ADR-0009 + telas web — spec §1/§2), nao desta frente. Estados de API nao-felizes JA estao especificados nas US-CT e na spec §4 erros.py (412 FotoComprovanteObrigatoria, 409 DespesaValidadaImutavel/FotoDuplicada, 403 GpsConsentimentoAusente, 422 AdiantamentoNaoCancelavel/PeriodoPrestacaoFechado/TransicaoInvalida). Debito da secao por-tela rastreado em GATE-CT-PRD-UX-STATES no catalogo central (espelha GATE-AGE-PRD-UX-STATES). -->

## 7. User Stories (BDD)

### US-CT-001 — Técnico solicita adiantamento

**Como** técnico (P-OP-01), **quero** solicitar adiantamento via app, **para** não usar dinheiro pessoal em viagem longa.

- **AC-CT-001-1**: GIVEN técnico abre tela de adiantamento, WHEN preenche `valor` + `justificativa` (≥ 30 chars) + `os_id` (opcional) + `viagem_id` (opcional), THEN cria `Adiantamento` em estado `pendente_aprovacao` + envia notificação push pro dono/financeiro.
- **AC-CT-001-2**: GIVEN dono aprova em 1 toque (P-FIN-02), WHEN confirma, THEN adiantamento vira `aprovado` + financeiro libera PIX/transferência (manual Wave A; automático Wave B via ADR-0050).
- **AC-CT-001-3**: GIVEN dono recusa, WHEN salva, THEN adiantamento vira `recusado` + `motivo` obrigatório + notifica técnico.

**Invariantes:** `INV-TENANT-001`, `INV-CT-ADIAN-001`.

---

### US-CT-002 — Técnico lança despesa com foto

**Como** técnico (P-OP-01), **quero** tirar foto do recibo + escolher categoria + valor, **para** registrar despesa sem perder comprovante.

- **AC-CT-002-1 (foto obrigatória)**: GIVEN técnico lança despesa, WHEN salva sem foto-comprovante, THEN bloqueia com `412 FOTO_OBRIGATORIA` (INV-008 análogo a INV-007 NF-e contingência).
- **AC-CT-002-2 (offline-first)**: GIVEN técnico sem sinal, WHEN lança despesa, THEN salva localmente em `OperacaoSyncPendente` + sincroniza quando sinal retorna.
- **AC-CT-002-3 (IDEMP-001 — ADR-0033)**: GIVEN despesa enviada com `client_offline_id` UUID4 + `Idempotency-Key`, WHEN servidor processa, THEN replay retorna mesmo registro (não duplica). ADR-0033 IDEMP-001 obrigatório.
- **AC-CT-002-4 (categorização)**: GIVEN técnico salva, WHEN escolhe categoria, THEN enum: `combustivel`, `alimentacao`, `pedagio`, `hospedagem`, `peca`, `deslocamento`. INV-AGENT-001: enum tipado, jamais texto livre.
- **AC-CT-002-5 (LGPD GPS opcional)**: GIVEN opt-in de GPS vigente do colaborador (server-side, `ConsentimentoGpsColaborador` NOT NULL) + política do tenant, WHEN salva despesa, THEN captura GPS pra evidenciar local. Base legal: **legítimo interesse (art. 7º IX) com LIA (DPIA-02) + execução de contrato (art. 7º V de apoio)** — o opt-in/oposição é salvaguarda de transparência/controle (art. 8º §5º / art. 18 §2º), **NÃO** a base autônoma (consentimento de empregado é frágil pela assimetria, art. 8º §1º) (RAT-13). GPS NUNCA é lido do payload **nem do EXIF da foto** (sempre stripada) — sempre do opt-in server-side (idêntico app-tecnico US-APP-003; INV-LGPD-CONSENT-001 compartilhada). [corrigido P2/ADV-CT-01]
- **AC-CT-002-6 (revogação consentimento)**: GIVEN técnico revogou consentimento (`consente_gps_em.revogado_em IS NOT NULL`), WHEN tenta lançar despesa com GPS, THEN servidor bloqueia coleta GPS + permite lançamento sem GPS (não bloqueia despesa).
- **AC-CT-002-7 (retenção — minimização art. 6º III)**: GIVEN despesa salva com GPS, WHEN o período de retenção **próprio do GPS** expira (**fechamento da prestação + 90 dias; máx. 6–12 meses** — NÃO os 5a fiscais; GPS não é dado fiscal), THEN job purga GPS via crypto-shredding; **foto + valor preservados pelos 5a fiscais** (auditoria Receita). Retenção do GPS desacoplada da foto/valor. [corrigido P2/ADV-CT-02]

**Invariantes:** `INV-CT-FOTO-001` (foto obrigatória), `IDEMP-001`, `INV-LGPD-CONSENT-001` (consentimento server-side).

---

### US-CT-003 — Despesa vinculada a OS aparece no custeio

**Como** dono (P-FIN-02), **quero** ver despesa vinculada à OS no custeio dela, **para** medir margem real.

- **AC-CT-003-1**: GIVEN despesa com `os_id` setado, WHEN dono abre painel da OS, THEN despesa aparece em "Custos diretos" (rastreabilidade pra Wave B comissão sobre margem).

---

### US-CT-004 — Financeiro valida 50 despesas em < 10 min

**Como** financeiro (P-FIN-01), **quero** validar 50 despesas do mês em < 10 min (1 swipe cada), **para** fechar mês rápido.

- **AC-CT-004-1**: GIVEN financeiro abre fila, WHEN despesa em `pendente_validacao`, THEN UI mostra foto-comprovante + valor + categoria + botões swipe (verde valida, vermelho recusa com motivo).
- **AC-CT-004-2**: GIVEN financeiro valida, WHEN swipe verde, THEN despesa vira `validada` + publica `Despesa.Validada` + bloqueia mutação (US-CT-005).

---

### US-CT-005 — Despesa sem foto bloqueada + despesa validada imutável

**Como** sistema, **quero** bloquear despesa sem foto + impedir mutação após validação, **para** ter trilha probatória.

- **AC-CT-005-1**: GIVEN tentativa de lançamento sem foto, WHEN salva, THEN bloqueia com `412 FOTO_OBRIGATORIA` (idem AC-CT-002-1).
- **AC-CT-005-2 (trigger PG `caixa_tecnico_anti_mutacao`)**: GIVEN despesa em estado `validada`, WHEN qualquer UPDATE/DELETE direto no banco tenta mutar, THEN trigger PG `caixa_tecnico_anti_mutacao` (análogo ao trigger `auditoria_anti_*` de Foundation F-A) bloqueia com erro `cannot modify validated expense` + audit. Correção exige nova despesa estornadora (`tipo=estorno`).
- **AC-CT-005-3 (migration)**: GIVEN a tabela **`despesa`** é criada (o sujeito imutável é a DESPESA validada, não a raiz `CaixaTecnico`), WHEN migration roda, THEN inclui na mesma migration: `CREATE TRIGGER caixa_tecnico_despesa_anti_mutacao BEFORE UPDATE OR DELETE ON despesa FOR EACH ROW WHEN (OLD.status='validada') EXECUTE FUNCTION ...` **+ block-delete sempre** (toda despesa é documento fiscal, retenção Receita 5a — nunca DELETE físico; cancelar = `status=cancelada`). Reapresentação `rejeitada→pendente` **NÃO** dispara (só `WHEN status='validada'`). Hook `audit-immutability-check.sh` valida. [corrigido P2/TL-CT-05]

**Invariantes:** `INV-CT-IMUT-001` (despesa validada imutável — análogo INV-001 audit).

---

### US-CT-006 — Técnico fecha prestação de contas em ≤ 5 min

**Como** técnico (P-OP-01), **quero** fechar prestação de contas em ≤ 5 min, **para** não consumir tempo de campo.

- **AC-CT-006-1**: GIVEN técnico abre prestação, WHEN UI carrega, THEN mostra saldo aberto + lista despesas + adiantamentos vinculados + cálculo `saldo_a_receber_ou_devolver`.
- **AC-CT-006-2**: GIVEN técnico revisa, WHEN clica "fechar", THEN sistema gera relatório PDF + publica `PrestacaoContas.Fechada` + bloqueia novas despesas no período.
- **AC-CT-006-3 (NFR)**: GIVEN telemetria, WHEN técnico fecha, THEN tempo total p95 ≤ 5 min (JTBD-062).

---

### US-CT-007 — Rejeição com motivo + reanexar foto

**Como** financeiro (P-FIN-01), **quero** recusar despesa com motivo, **para** dar feedback ao técnico.

- **AC-CT-007-1**: GIVEN financeiro recusa despesa, WHEN preenche motivo (≥ 30 chars), THEN despesa vira `rejeitada` + notifica técnico.
- **AC-CT-007-2**: GIVEN técnico reanexa foto melhor, WHEN reenvia, THEN despesa volta pra `pendente_validacao` + audit registra ciclo de reapresentação.

---

## 8. Métricas

Ver `metricas.md`. Primárias (mínimo 2-3):
- Tempo médio prestação de contas ≤ 5 min p95
- % despesas validadas no 1º envio
- Total adiantado vs prestado (compensação)

## 9. NFR

- App offline-first: técnico em campo sem 4G consegue lançar; sincroniza ao voltar conectividade.
- Foto comprimida + armazenamento (S3/B2) — não inflar app.
- Prestação ≤ 5 min p95 (medido em telemetria).
- GPS opcional (com consentimento server-side — LGPD), pra evidenciar local da despesa.
- WCAG 2.1 AA (INV-016).

## 10. Invariantes consolidadas

- **INV-CT-FOTO-001:** despesa sem foto-comprovante = não aceita (regra inegociável; análoga a NF-e em contingência).
- **INV-CT-IMUT-001:** despesa validada não pode ser editada (só nova despesa estornadora); enforcement via trigger PG `caixa_tecnico_anti_mutacao` + hook `audit-immutability-check.sh`.
- **INV-008:** audit completo (foto, timestamp, GPS opcional, actor).
- **IDEMP-001:** despesa enviada offline com `client_offline_id` UUID4 + `Idempotency-Key` é deduplicada (ADR-0033).
- **INV-LGPD-CONSENT-001:** consentimento GPS server-side (NOT NULL) + revogação append-only.

## 11. Glossário

Ver `glossario.md` deste módulo + `docs/comum/glossario.md` + ADR-0037 (PT-EN canônico).

Termos centrais:
- **Adiantamento** — valor antecipado ao técnico pra cobrir despesas previstas de viagem.
- **Despesa** — gasto efetivo do técnico (com foto-comprovante obrigatória).
- **Prestação de contas** — fechamento mensal/por viagem: adiantamentos vs despesas vs saldo.
- **Caixa do técnico** — saldo aberto individualizado por técnico.

## 12. Dependências (ADRs e módulos)

- ADR-0023 (OS com atividades — despesa pode vincular atividade)
- ADR-0033 (bus idempotência consumer — IDEMP-001 obrigatório)
- ADR-0050 (gateway pagamento — Wave B reembolso PIX)
- ADR-0067 (perfil regulatório)
- Módulos: Operação (cadastro de técnico + OS), Financeiro (contas a pagar), Armazenamento (B2/S3)

## 13. Como evolui

US nova → próximo `US-CT-NNN`. Mudança em fluxo de validação → ADR. Feature nova com gating por perfil → atualizar `docs/conformidade/comum/matriz-feature-perfil.md`.

## 14. Integração com OS

Despesa vinculada a OS aparece em:
- Painel da OS (custos diretos)
- Custeio da OS (Wave B — habilita comissão sobre margem)
- Relatório "OSs deficitárias" (Wave B)
