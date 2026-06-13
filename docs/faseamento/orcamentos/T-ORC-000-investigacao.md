---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
diataxis: explanation
audiencia: [agente, auditor]
frente: orcamentos
tipo: investigacao-p0
relacionados:
  - docs/faseamento/plano-dependencia-sistema.md
  - docs/dominios/comercial/modulos/orcamentos/prd.md
  - docs/dominios/comercial/modulos/orcamentos/modelo-de-dominio.md
  - docs/adr/0034-saga-compensacao-cross-modulo.md
  - docs/adr/0051-propagacao-adr0023-modulos-wave-a.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
---

# T-ORC-000 — Investigação regra #0 — frente `orcamentos` (#5 da cadeia, 1ª ponta de receita)

> **Pra quê:** ler o estado REAL (código + docs + decisões) antes de escrever spec.
> Molde: `docs/faseamento/colaboradores/T-COL-000-investigacao.md`.
> Ordem cravada (`plano-dependencia-sistema.md` §7): #1 config ✅ → #2 pps ✅ →
> #3 precificacao ✅ → #4 colaboradores ✅ (2026-06-13) → **#5 orcamentos**.
> Fonte: 3 subagentes Explore (seams · análise-crítica+saga · INVs/ADRs/LGPD+Família 0), 2026-06-13.

## 1. Estado real do código — GREENFIELD do módulo, mas a OUTRA ponta já existe

- **Zero código de orçamento comercial:** não há `src/{domain/comercial,application/comercial,infrastructure}/orcamentos/`.
  Os hits de grep `orcamento` são de OUTRA coisa (incerteza metrológica `OrcamentoIncerteza` no M4; o consumer da OS).
- **A ponta consumidora JÁ ESTÁ PRONTA (aguardando o emissor):**
  - Consumer `Orcamento.Aprovado` → `src/infrastructure/ordens_servico/consumers/orcamento.py:153`
    (`@consumer_idempotente(consumer_id="os.consumer.orcamento_aprovado")`, ADR-0033).
  - Use case `abrir_os_via_orcamento` → `src/application/operacao/os/abrir_os_via_orcamento.py:125`
    (cria 1 OS + N AtividadeSnapshot, 1 por item, estado PENDENTE).
  - **Contrato do envelope conhecido** (`consumers/orcamento.py:74-104`): `payload{orcamento_id,
    tenant_id, cliente_id, cliente_referencia_hash, cliente_key_id, equipamento_id,
    equipamento_recebimento_id?, analise_critica_id?, analise_critica_snapshot_hash,
    regra_decisao_acordada, valor_total, abertura_at, criada_por_user_id?, itens[{tipo,
    sequencia, valor_unitario, requer_recebimento}]}`. **O emissor (orcamentos) deve produzir EXATAMENTE este envelope.**
- **Eventos no catálogo v8** (`integracoes-inter-modulos.md:241-249`): `Orcamento.Aprovado/Convertido/
  Enviado/Recusado/Expirado/Lido` JÁ catalogados (consumer OS/crm/portal). **AUSENTES:**
  `Orcamento.AnaliseCriticaReprovada`/`ComRessalva` (criar — P7). `Orcamento.LinkAberto` = Wave B.
  Sem `ACOES_ORCAMENTOS` em `acoes_canonicas.py` (criar).

## 2. Seams prontos (consumir, não recriar)

| Peça | Onde | Uso pela frente |
|------|------|-----------------|
| Motor `calcular_precos(CalcularPrecosInput, *, repos, custo_provider, resolver_preco_fn, aliquota_imposto_fn)` POR CESTA | `application/precificacao/calculo.py:66` | orçamento chama server-side (molde `precificacao/views.py:539`); `cliente_id`→`VinculoTabelaPrecoCliente`→`tabela_id` |
| **`PrecoResolvido`** (carimbo probatório: item_id, item_versao_n, linha_tabela_id, tabela_id, preco, data_referencia, origem_preco, composicao) | `domain/produtos_pecas_servicos/entities.py:161` | **FONTE do snapshot de preço — NÃO criar VO `Preco` novo (D-ORC-1)** |
| VO `Preco` (só `valor: Decimal>0`, BRL escala 2) | `domain/produtos_pecas_servicos/value_objects.py:20` | NÃO é o `Preco(valor_centavos,moeda,vigencia,fonte)` do PRD — reconciliar PRD (usar PrecoResolvido) |
| Consumer `Orcamento.Aprovado` + `abrir_os_via_orcamento` | `ordens_servico/consumers/orcamento.py` + `application/operacao/os/abrir_os_via_orcamento.py` | orçamento PUBLICA o envelope; OS já cria. `AtividadeSnapshot.origem_item_id` **NÃO existe** (rastreio por `sequencia`) — D-ORC tech-lead |
| `ReferenciaPIIAnonimizavel` (uuid_atual?, hash HMAC, key_id) + molde FK cliente da OS (`ordens_servico/models.py:37`) | `domain/shared/value_objects.py:258` | cliente do orçamento: par `(cliente_atual_id SET_NULL, cliente_referencia_hash, cliente_key_id)` (ADR-0032) |
| `ImpostoRepository.listar(tenant_id, ...)` | `domain/configuracoes_sistema/repository.py:30` | alíquota fiscal SIMULADA (D-PRC-10; non-goal fiscal exato) |
| `tenant_perfil_e(perfis) -> (bool, reason)` fail-closed + ContextVar `perfil_tenant_context` | `infrastructure/authz/perfil_tenant_helper.py` | gating US-ORC-009 perfil-aware (molde fiscal/certificados) |
| REST: idempotência 2 camadas + ACTION_MAP + `publicar_evento(outbox=True)` + perfil server-side | `precificacao/_views_suporte.py` + `audit/event_helpers.py` | REST da frente nasce no molde |
| Bus: `@consumer_idempotente` + `dead_letter_events` (após 5 retries) | `bus/consumer_base.py` + `audit/models.py:444` | idempotência/replay; saga-manager (reabrir) ver §4 |
| WeasyPrint (HTML→PDF) | `equipamentos/services_etiqueta.py:33` | molde do PDF de orçamento (DIFERIDO — GATE-ORC-PDF) |

## 3. Análise crítica cl. 7.1 ISO 17025 (US-ORC-009) — CHAMAR PORTAS, não predicates NO-OP

- **Mudança de arquitetura (ADR-0073):** `cmc_cobre` e `procedimento_vigente_para` em
  `calibracao/predicates_calibracao.py` viraram **NO-OP** `(True,"")` — a validação real migrou
  para dentro dos use cases de calibração, via portas `escopos_cmc.query_service.cobre` e
  `procedimentos_calibracao.query_service.cobre_procedimento`. **A análise crítica do orçamento
  deve chamar essas PORTAS diretamente** (não os predicates ABAC NO-OP).
- **Os 4 predicates/checagens:**
  - `cmc_cobre(tenant, grandeza, faixa)` → porta `escopos_cmc.query_service.cobre` (M6 real).
  - `procedimento_vigente_para(tenant, grandeza, equipamento)` → porta `procedimentos.query_service` (M7 real; sem `equipamento` na assinatura atual).
  - `rt_competencia_cobre(resource{tenant,executor_user_id,grandeza,data})` → **REAL** (consulta DB), `ordens_servico/predicates_os.py:67`.
  - `padrao_disponivel(tenant, grandeza, faixa, prazo)` → **INEXISTENTE** → GATE-ORC-PADRAO (stub fail-open, porta `metrologia/padroes`).
- **Perfil-aware (ADR-0067 / matriz feature×perfil):** `tenant_perfil_e(["A","B","C"])` gate;
  A = **fail-closed** (qualquer reprovação → 422 + `Orcamento.AnaliseCriticaReprovada` WORM);
  B = **fail-open lazy** (unknown → aprova com ressalva `Orcamento.AnaliseCriticaComRessalva`);
  C = parcial/warning; D = **desabilitado** (não roda predicates). Default fail-closed se perfil indeterminado.
- Evento de análise crítica leva `perfil_no_evento` snapshot (ADR-0067 §3), `itens_avaliados[]` com veredito por checagem.

## 4. Saga / compensação (ADR-0034) — orçamento é o Passo 1 da Saga 1

- **Existe:** `dead_letter_events` (`audit/models.py:444`, após 5 retries, INV-BUS-002), idempotência
  consumer (`@consumer_idempotente`). Compensação por EVENTO (`OS.Cancelada`), não DELETE (INV-SAGA-002).
- **NÃO existe:** tabela saga `comercial_saga_orcamento_os`; o consumer/watchdog que lê `dead_letter`
  e devolve o orçamento a `aprovado_pendente_os` (US-ORC-002 AC-3). **Recorte:** Wave A entrega o estado
  `aprovado_pendente_os` no modelo + o orçamento NÃO vira `convertido` até confirmar criação da OS
  (idempotência + estado), mas o saga-manager completo (auto-reabertura via DLQ) é **GATE-ORC-SAGA-DLQ**.

## 5. Recorte núcleo Wave A proposto (startável HOJE)

**NÚCLEO (backend):**
1. Agregado `Orcamento` (máquina de estados Padrão A: rascunho→enviado→aprovado→recusado/expirado/
   cancelado→convertido + `aprovado_pendente_os`) + `ItemOrcamento` (com `tipo_atividade_alvo` enum —
   ADR-0051) + `Template` (Padrão C). Cliente via `ReferenciaPIIAnonimizavel`.
2. **Snapshot de preço = `PrecoResolvido` carimbado por item** (INV-026 — não retroage; D-ORC-1).
   Cálculo via `calcular_precos` server-side (preço+desconto+imposto+comissão prevista).
3. Criar/editar/enviar(gera token+estado) orçamento (US-ORC-001) + templates (US-ORC-005, com gate
   selo RBC por perfil).
4. **Aprovar (US-ORC-002):** transição + **análise crítica cl. 7.1 perfil-aware (US-ORC-009)** via portas
   + idempotência (`idempotency_key=orcamento_id`) + publica `Orcamento.Aprovado` (envelope §1 exato, outbox)
   → consumer OS já cria a OS (US-ORC-007).
5. Bloquear cancelamento de convertido (US-ORC-008, 409).
6. Endpoint público de **aprovação 1-clique** (POST `/v1/public/orcamentos/{token}/aprovar`, sem auth,
   token=autorização, rate-limit, registra ip_hash+user_agent+aceite WORM) — **a LÓGICA/endpoint** entra;
   a TELA HTML pública é frente de telas.

**DIFERIDO (GATE-ORC-*):** PDF de orçamento (GATE-ORC-PDF, WeasyPrint molde) · TELA pública e telas internas
(frente de telas, WCAG INV-016) · versionamento V1/V2/V3 (US-ORC-003 Wave B) · tracking de leitura
(US-ORC-006 Wave B, `Orcamento.LinkAberto`) · aprovação escalada por desconto>X% (US-ORC-004 parte 2, Wave B —
alçadas já existem em precificacao) · assinatura eletrônica (Wave B) · saga-manager DLQ→reabrir
(GATE-ORC-SAGA-DLQ) · US-ORC-010 cobrança gateway (consumer é de `contas-receber`, futuro) ·
`padrao_disponivel` (GATE-ORC-PADRAO) · `origem_item_id` na OS (GATE-ORC-ORIGEM-ITEM se tech-lead diferir).

## 6. Decisões abertas (classificadas por dono)

**PRODUTO — Roldão (batch única no P2, com recomendação):**
- D-aberta-1: **No MVP-1 (dogfooding), o cliente aprova pelo LINK PÚBLICO** (precisa do endpoint público +
  PDF agora) **ou o vendedor marca aprovação internamente** (link público/PDF ficam p/ frente de telas)?
  *Recomendação: entregar a LÓGICA de aprovação (interna via API + endpoint público de 1-clique) AGORA,
  mas DIFERIR PDF e a TELA HTML pública à frente de telas (o cliente aprova via API/integração; a página
  bonita vem depois).* — confirma o que o cliente vê no MVP.

**TÉCNICA/ARQUITETURA — subagentes (P2 tech-lead + advogado):**
- VO `Preco` do PRD: reconciliar para `PrecoResolvido` (não criar VO novo) + emendar PRD/modelo (D-ORC-1).
- `AtividadeSnapshot.origem_item_id`: adicionar campo na OS (migration aditiva) vs rastrear por `sequencia`
  (zero-retrofit). Recomendação: por `sequencia` no MVP + GATE-ORC-ORIGEM-ITEM (campo aditivo quando precisar).
- Análise crítica: chamar portas `escopos_cmc`/`procedimentos`/`padroes` query_service direto no use case
  (ADR-0073), com fail-open lazy onde a porta não existir (padrao_disponivel).
- Saga: profundidade do recorte (estado `aprovado_pendente_os` + idempotência agora; saga-manager DLQ diferido).
- Path: domínio `comercial` aninha → `src/domain/comercial/orcamentos/` + infra flat `src/infrastructure/orcamentos/`
  (molde clientes — confirmar; NÃO seguir precificacao flat, que era módulo solto).
- advogado: apontador-PII (nome_aprovador/email_aprovador/ip_hash/user_agent — RAT-11 cobre; congelado);
  base legal aprovação pública (art.7º V + consentimento checkbox); cliente via ReferenciaPIIAnonimizavel.

## 7. AUSÊNCIAS mapeadas — destino

> RAT/DPIA/retenção/zonas CONGELADOS até GATE-LGPD-RAT-CONSOLIDACAO — só rastrear, não escrever.

| Ausência | Destino |
|----------|---------|
| Família `INV-ORC-*` (PRECO-001, CL71-001, + INV-ORC-EXP-001 já em invariantes-futuras) | criar em REGRAS (P7) |
| Eventos `Orcamento.AnaliseCriticaReprovada`/`ComRessalva` no catálogo + `ACOES_ORCAMENTOS` | P7 |
| INV-026/INV-001 texto normativo no mestre (referência fantasma) | apontar P8 (não bloqueia — operacional via discovery) |
| RAT linha aprovação digital · retenção orçamento · DPIA tela pública | **GATE-LGPD-RAT-CONSOLIDACAO** (congelado) |
| ADR imutabilidade template PDF pós-aprovação; colisão ref "RAT-06" em exports.md | P8 (quando PDF sair do GATE) |
| `comercial_saga_orcamento_os` saga-manager completo | GATE-ORC-SAGA-DLQ |

## 8. Próximos passos do ritual

P1 spec (recorte §5 sobre PRD; reconciliar VO Preco→PrecoResolvido) → P2 revisões `tech-lead` + `advogado`
+ batch Roldão (D-aberta-1) → P3 plan/tasks (fatias 1a domínio / 1b schema+RLS / 2 use cases+REST+análise
crítica+evento / 3 P7) → P4..P7 implementação → P8 emendas → P9 auditores roteados (perfil/saga/idempotência/
lgpd OBRIGATÓRIO — PII cliente + endpoint público) com 2ª passada escopada + adversarial (INV-RITUAL-001).
