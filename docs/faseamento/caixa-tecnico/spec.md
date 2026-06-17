---
owner: agente-ia
revisado-em: 2026-06-17
proximo-review: 2026-09-17
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: caixa-tecnico
tipo: spec
proximo-passo: P3 — plan/tasks (revisão P2 tech-lead + advogado LGPD CONCLUÍDA — ver §8)
relacionados:
  - docs/faseamento/caixa-tecnico/T-CT-000-investigacao.md
  - docs/dominios/financeiro/modulos/caixa-tecnico/prd.md
  - docs/dominios/financeiro/modulos/caixa-tecnico/modelo-de-dominio.md
  - docs/dominios/operacao/modulos/app-tecnico/prd.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0050-gateway-pagamento.md
  - docs/adr/0064-rotacao-hmac-anual-kms.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0021-anonimizacao-retencao.md
---

# Spec — frente `caixa-tecnico` (P1, derivada do PRD + T-CT-000; P2 incorporada)

> Frente nível 5 (financeiro). **Controle financeiro individual do técnico de campo**:
> adiantamentos (solicitação→aprovação→entrega), despesas (foto-comprovante OBRIGATÓRIA,
> offline-first, GPS opt-in LGPD), validação pelo financeiro (despesa validada IMUTÁVEL),
> prestação de contas mensal (saldo adiantado × gasto). **Transversal A/B/C/D** — sem gating
> regulatório (só retenção de PII de GPS). Molde técnico = `contas-receber` (par/vizinho
> financeiro, FECHADO) + ritual `agenda`. **Wave A robusto** (técnicos = evangelizadores — PRD §2).

## 1. O que é — e o que NÃO é (fronteiras)

**É:** o caixa que individualiza dinheiro por técnico de campo. Cada técnico tem um **`CaixaTecnico`**
(saldo derivado = adiantamentos entregues − despesas validadas); registra **`Adiantamento`** (com
aprovação/alçada), **`Despesa`** (foto obrigatória content-addressed, GPS opcional, vínculo OS),
o financeiro **valida** por swipe (despesa validada vira **imutável WORM**), e o técnico **fecha a
prestação** do período (saldo + direção). Provê endpoints **idempotentes offline-first** para o app.

**Não é (fronteiras — D-CT):**
- **Não executa o reembolso** — prestação com `direcao=tenant-deve` **REGISTRA o saldo** (estado
  consultável) e **PUBLICA** `caixa_tecnico.prestacao.fechada` (fail-open lazy, G4/Roldão). A
  execução (PIX/transferência) é de **`contas-pagar`** (par N5 ausente), que ao nascer faz **backfill
  por query** das prestações `tenant-deve` não-reembolsadas + consome o evento. **Sem reembolso manual
  no caixa-tecnico.** GATE-CT-CONTAS-PAGAR.
- **Não executa a devolução** — `direcao=tecnico-deve` em Wave A **só REGISTRA o saldo devedor**;
  a execução (dinheiro/PIX/desconto-folha) é **Wave B**. GATE-CT-DEVOLUCAO-EXEC (G5/Roldão).
- **Não é o app mobile** — Flutter offline-first DIFERIDO (ADR-0009). O backend **só provê** os
  endpoints idempotentes (`Idempotency-Key` + `client_offline_id` + foto content-addressed). Sem fila
  local nem UI.
- **Não faz OCR do recibo** nem lê cartão corporativo (Pluggy) — Wave B (GATE-CT-OCR).
- **Não é a fonte do consentimento GPS de RH** — apenas LÊ o opt-in/oposição server-side (NUNCA do
  payload). O **aviso ao titular** (transparência) mora no onboarding/termo de admissão de RH, não no
  código (ADV-CT-06). A base legal e a LIA são preocupação LGPD transversal (D-CT-6).
- **Não é o custeio da OS** — `despesa.validada` é **publicada**; o consumo (margem por OS) é Wave B
  (a despesa só grava `os_id` denormalizado quando vinculada; não segue cancelamento da OS — D-CT-11).
- **Não calcula adicional/folha** — adiantamento via folha e desconto em folha = non-goal.
- **Anti-duplicata de foto = bit-idêntica, NÃO anti-fraude semântica** — re-fotografar a tela ou crop
  de 1px muda o hash e passa (limite conhecido; non-goal Wave A — TL-honestidade).

## 2. Recorte núcleo Wave A vs diferido (por US)

| US | Núcleo Wave A | Diferido (GATE/Wave B) |
|----|---------------|------------------------|
| US-CT-001 solicitar adiantamento | `Adiantamento` solicitado→aprovado→entregue; alçada por `Politica`; meio pix/transf/dinheiro; recusa c/ motivo | liberação PIX automática (GATE-CT-PIX / ADR-0050) — Wave A manual |
| US-CT-002 lançar despesa c/ foto | foto OBRIGATÓRIA content-addressed (412 `FOTO_OBRIGATORIA`); categoria enum; vínculo OS opcional; km×tarifa | OCR (GATE-CT-OCR); cartão corporativo (Pluggy) |
| US-CT-002 (offline) | `Idempotency-Key`+`client_offline_id` UUID4 (IDEMP-001); `POST /sync/despesas-lote` (`foto_base64`, per-item 207, LWW) | fila local do app Flutter (ADR-0009) |
| US-CT-002 (GPS LGPD) | opt-in server-side; NULL→coleta off (despesa segue); revogação para coleta não a despesa; retenção própria curta + crypto-shredding | termo de admissão RH + LIA assinada (GATE-CT-GPS-LGPD-OAB) |
| US-CT-003 despesa no custeio da OS | grava `os_id` denormalizado; valida OS existe via query (seam OS) | painel de custeio/margem (Wave B) |
| US-CT-004 validar 50 despesas <10min | fila `pendente`; swipe valida/rejeita; `validada` publica `despesa.validada` | UI rica de swipe (frente de telas) |
| US-CT-005 foto bloqueada + validada imutável | trigger PG `caixa_tecnico_despesa_anti_mutacao` (`WHEN status='validada'`) + block-delete (fiscal); estorno = nova despesa | — |
| US-CT-006 fechar prestação ≤5min | saldo + lista validada + 1 toque (advisory lock); publica `prestacao.fechada`; bloqueia novas despesas no período; **PDF leve WeasyPrint** | PDF rico (Wave B); execução reembolso/devolução |
| US-CT-007 rejeição + reanexar | `rejeitada` c/ motivo≥30; reanexar foto melhor → volta `pendente`; audit do ciclo | — |

## 3. Decisões cravadas (D-CT-1..13) — P2 incorporada

- **D-CT-1 — Path FLAT espelhando `contas-receber` (vizinho financeiro). ✅ CONFIRMADO (TL-CT-09).**
  `src/domain/caixa_tecnico/` + `src/application/caixa_tecnico/` + `src/infrastructure/caixa_tecnico/`
  (`app_label="caixa_tecnico"`). Financeiro é flat (`contas_receber`, `fiscal`); a `agenda` aninhou só
  porque espelhava `os`. Consistência local > global; aninhar exigiria mover CR+fiscal+billing junto.
- **D-CT-2 — `CaixaTecnico` raiz por técnico; 4 agregados; saldo DERIVADO on-read. ✅ APROVADO (TL-CT-10).**
  `CaixaTecnico` (1 por `(tenant, tecnico)`), `Adiantamento`, `Despesa`, `PrestacaoContas` raízes;
  `Politica` por tenant. `saldo_atual` = projeção calculada (Σ adiantamentos entregues − Σ despesas
  validadas), **não** campo mutável (evita drift; volume baixo). Leitura em snapshot único; **fechamento
  da prestação sob `pg_advisory_xact_lock` por `(tenant, tecnico)`** (molde CR) — evita 2 prestações
  concorrentes congelarem saldos divergentes. INV-CT-SALDO-001.
- **D-CT-3 — `Despesa` máquina de estados + imutabilidade WORM. ✅ CONFIRMADO (TL-CT-05).**
  `pendente→validada`, `pendente→rejeitada`, `rejeitada→pendente` (reapresentação US-CT-007),
  `pendente→cancelada` (técnico, antes de validar). **Validada = imutável**: trigger PG
  `caixa_tecnico_despesa_anti_mutacao` (`BEFORE UPDATE OR DELETE ... WHEN (OLD.status='validada')`,
  molde `orcamentos/0003_triggers_worm.py`) — **não dispara** na reapresentação `rejeitada→pendente`
  (UPDATE legítimo; teste obrigatório). **block-delete SEMPRE** (toda despesa é documento fiscal,
  retenção Receita 5a — molde `contas_receber titulo_receber_block_delete`); cancelar = `estado=cancelada`,
  nunca DELETE físico. Correção de validada = nova `Despesa(tipo=estorno)` referenciando a original.
  INV-CT-IMUT-001. **[Correção do PRD — ação P3]:** AC-CT-005-3 diz "trigger ON `caixa_tecnico`"; o
  sujeito imutável é a **DESPESA** — trigger vai na tabela `despesa`.
- **D-CT-4 — Foto-comprovante OBRIGATÓRIA: validar→EXIF-strip→HMAC-tenant→content-address (TL-CT-01/02,
  ADV-CT-03/04).** Sem foto → `412 FOTO_OBRIGATORIA` (`foto_hash` NOT NULL + domínio `__post_init__`).
  Pipeline (molde `equipamentos/services_foto_storage.py`, **NÃO** `AnexoStoragePort` que é PDF):
  (1) valida **JPG/PNG** + MIME allowlist + ≤5MB; (2) **EXIF strip** obrigatório via Pillow; (3)
  `foto_hash = HMAC-SHA256(bytes_pós-strip, chave_do_tenant)` (ADR-0064 — **não** SHA-256 global: o
  crypto-shredding da chave do tenant cobre o hash, impede correlação cross-tenant); (4) content-address
  por-tenant (`tenant/<hmac[:2]>/<hmac>`). **Fronteiras:** storage é idempotente por hash (replay não
  re-grava — `if not exists`); a **anti-fraude vive SÓ na constraint** `UNIQUE (tenant_id, foto_hash)
  WHERE status NOT IN ('rejeitada','cancelada')` (escopada por tenant — fotos idênticas em tenants
  diferentes coexistem; teste cross-tenant obrigatório). **EXIF nunca vira canal de GPS** — o GPS vem
  SÓ do opt-in estruturado (D-CT-6); a foto é sempre stripada (TL-CT-14). Storage **filesystem LOCAL**
  (G3/Roldão — B2 = GATE pré-prod). Aviso de UI "fotografe só o comprovante, evite pessoas/documentos
  ao fundo" (ADV-CT-03, molde AC-APP-006-5). INV-CT-FOTO-001, INV-CT-FOTO-DEDUP-001.
- **D-CT-5 — Idempotência offline dupla-camada (IDEMP-001 / ADR-0033). +batch (TL-CT-06).** REST single:
  `_aplicar_idempotencia` + header `Idempotency-Key` (UUID4) com `payload_fingerprint` incluindo
  `client_offline_id` (molde `agenda/views.py`). **Batch** `POST /v1/caixa-tecnico/sync/despesas-lote`
  (`foto_base64`): **limite ≤20 itens/lote** + tamanho total (413 se exceder); **atomicidade per-item**
  (resposta estilo 207 — 1 foto ruim não trava o sync inteiro); dedup **por item** via `UNIQUE
  (tenant_id, client_offline_id)` na tabela `despesa` (o `Idempotency-Key` do header é do lote, não do
  item). LWW por `(client_event_ts, device_id)`. 2ª camada = content-addressing da foto. Consumers
  `@consumer_idempotente` (fan-out). INV-CT-IDEMP-001.
- **D-CT-6 — GPS opt-in server-side (LGPD): base legítimo-interesse + retenção própria curta (ADV-CT-01/02/05/06).**
  **Base legal: art. 7º IX (legítimo interesse, com LIA da DPIA-02 §6) + art. 7º V (apoio do vínculo).**
  O opt-in/oposição server-side é **salvaguarda de transparência/controle** (art. 8º §5º / art. 18 §2º),
  **NÃO** a base legal autônoma (consentimento de empregado é frágil — assimetria, art. 8º §1º). Fonte do
  opt-in: server-side, **NUNCA do payload**; NULL → coleta GPS **off** com `403 GPS_CONSENTIMENTO_AUSENTE`
  **mas a despesa segue** (não bloqueia). Revogação/oposição para a coleta, não a despesa (AC-CT-002-6).
  **Retenção do GPS própria e curta: fechamento da prestação + 90 dias (máx. 6–12 meses), NÃO 5a**
  (minimização art. 6º III) — foto+valor seguem 5a fiscais; GPS purgado antes via crypto-shredding
  seletivo (`ReferenciaPIIAnonimizavel`). Base/retenção **IDÊNTICAS** ao app-tecnico (INV-LGPD-CONSENT-001
  compartilhada). Transparência: GPS da despesa exposto no canal "Meus dados (LGPD)" (reuso US-ACS-012).
  **G1/GATE-CT-GPS-MIGRATION — ✅ decidido (TL-CT-04/ADV-CT-06):** `colaboradores` FECHADO não é tocado.
  O registro do opt-in nasce como entidade **`ConsentimentoGpsColaborador`** (colaborador-scoped, **não**
  despesa-scoped; INSERT-com-vigência, RLS v2) e é exposto por **`ConsentimentoGpsPort`**, desenhada para
  **promoção a `shared` via ADR curta** — app-tecnico (N6) consome **a porta**, nunca a tabela (evita
  registro duplicado/divergente — R2). **IA nunca grava opt-in — só fluxo de RH/colaborador.**
- **D-CT-7 — `Adiantamento` máquina de estados + alçada.** `solicitado→aprovado→entregue`;
  `solicitado→recusado` (motivo obrigatório); `solicitado→cancelado` (técnico, antes de aprovar).
  **Entregue NÃO cancela** (vira ajuste na prestação / devolução — `AdiantamentoNaoCancelavel` 422).
  Alçada `Politica.alcada_aprovacao` (valor→papel) server-side. Liberação real do PIX **manual Wave A**
  (automática Wave B — ADR-0050). INV-CT-ADIAN-001.
- **D-CT-8 — Prestação: fecha + registra + publica (fail-open lazy, G4/G5; sem porta — TL-CT-08).** Fecha
  período: `total_adiantado` (entregues) − `total_despesas_validadas` = `saldo_final` + `direcao
  ∈ {tecnico-deve, tenant-deve, quitado}`. **Imutável WORM** (campos congelados pós-fecha; molde CR).
  Publica `caixa_tecnico.prestacao.fechada` **dentro do `atomic`** (outbox). **Bloqueia novas despesas
  no período fechado** (`PERIODO_PRESTACAO_FECHADO` 422). NFR p95 ≤5min (JTBD-062). **PDF leve via
  WeasyPrint** (G6 resolvido — TL-CT-03): dado estruturado é a fonte WORM, PDF é projeção on-demand
  (regenerável, não persistido como fonte). **Sem `AReembolsarPort`** (porta-stub que só publica é
  cerimônia): a prestação `tenant-deve` fica como **estado consultável** + evento publicado; contas-pagar,
  ao nascer, faz **backfill por query** (rede de segurança — dinheiro do técnico não pode sumir no outbox).
  INV-CT-PRESTACAO-001.
- **D-CT-9 — `Politica` por tenant + km automático + limite não-bloqueante.** `limite_por_categoria`,
  `alcada_aprovacao`, `tarifa_km`, `exige_gps`, `prazo_prestacao_dias` (default 30). Despesa de
  `deslocamento`: valor = `km_percorridos × tarifa_km` (server-side). Despesa acima do limite **NÃO
  bloqueia** — lança com flag `acima_limite=true` (financeiro vê na fila; emergência legítima existe).
- **D-CT-10 — Multi-tenancy RLS v2 + WORM + perfil só no evento. ✅ (TL-CT-12/13).** Todas as tabelas
  RLS v2 (ENABLE+FORCE+4 policies `app.tenant_ids`/`app.active_tenant_id`, molde
  `contas_receber/0002_rls_policies.py`). `Despesa` validada imutável + block-delete (D-CT-3);
  `PrestacaoContas` WORM. Perfil já é **auto-injetado no envelope** por `publicar_evento` — módulo é
  transversal A/B/C/D e **não gateia feature por perfil**, então **nenhuma coluna `perfil_no_evento`**
  nas tabelas. Trilha de auditoria via evento canônico WORM do bus; tabela `EventoAuditoriaCaixa` própria
  **só se** o GPS sensível não puder ir no payload geral (decidir no P3).
- **D-CT-11 — Eventos canônicos `caixa_tecnico.*` (G7).** Registrar `ACOES_CAIXA_TECNICO` em
  `src/infrastructure/audit/acoes_canonicas.py` (frozenset **+ união em `ACOES_CANONICAS`** — senão
  `assert_acao_canonica` faz todo publish falhar, TL-CT-11): `caixa_tecnico.adiantamento.solicitado`/
  `.aprovado`/`.entregue`/`.recusado`/`.cancelado`, `caixa_tecnico.despesa.lancada`/`.validada`/
  `.rejeitada`, `caixa_tecnico.prestacao.fechada`. **Lê OS** via query (valida `os_id` no lançamento);
  **não consome** `os.*` em Wave A (vínculo on-write; reduz acoplamento). Despesa **não segue cancelamento
  da OS** (non-goal explícito — rastro histórico). Re-avaliar consumo de `colaborador.desligado` no P3.
- **D-CT-12 — `esta_referenciado` (FK guard cross-módulo).** Técnico com caixa aberto / despesas /
  adiantamentos / prestação **não é hard-deletado**: implementa `ColaboradorReferenciadoPort.esta_referenciado`
  (molde D-AGE-12). INV-CT-REF-001.
- **D-CT-13 — GATE-CT-GPS-LGPD-OAB (bloqueante de PRODUÇÃO, molde GATE-AGE-JORNADA-TRABALHISTA — ADV-CT-09).**
  Antes do deploy com técnico real (PF): (a) **LIA assinada** por advogado OAB; (b) **termo de admissão /
  aviso de privacidade do colaborador** com cláusula de geolocalização; (c) **DPIA-02 aprovada**. Minutas
  escritas agora (sem custo); assinatura dispara só pré-produção ([[project_sem_contratacoes_externas_ate_producao]]).

## 4. Modelo (domínio puro)

- **enums:** `CategoriaDespesa`(combustivel|alimentacao|pedagio|hospedagem|peca|deslocamento),
  `TipoDespesa`(normal|estorno), `EstadoDespesa`(pendente|validada|rejeitada|cancelada),
  `EstadoAdiantamento`(solicitado|aprovado|entregue|recusado|cancelado),
  `MeioEntrega`(pix|transferencia|dinheiro), `DirecaoPrestacao`(tecnico-deve|tenant-deve|quitado).
- **entities (`frozen+slots`):** `CaixaTecnico` (raiz por técnico), `Adiantamento`, `Despesa` (raiz),
  `PrestacaoContas` (WORM), `Politica` (por tenant), `ConsentimentoGpsColaborador` (opt-in GPS
  colaborador-scoped, INSERT-com-vigência — D-CT-6).
- **value_objects:** reusa `Dinheiro` (`src/domain/shared/value_objects.py`); `Periodo(de, ate)`
  (imutável, valida `de<ate`); `Coordenada(lat, lng)` (opcional, validada); `ResultadoSaldo(total_adiantado,
  total_despesas, saldo_final, direcao)` (puro). `ReferenciaPIIAnonimizavel` p/ GPS (crypto-shredding).
- **regras puras:** `calcular_saldo(adiantamentos, despesas) -> ResultadoSaldo` (determinístico);
  `valor_deslocamento(km, tarifa) -> Dinheiro`; `transicoes_despesa.py` / `transicoes_adiantamento.py`
  (`_TRANSICOES: Mapping[Estado, frozenset]` + `validar_transicao`).
- **portas.py (Protocols):** `FotoComprovanteStoragePort` (validar+strip+HMAC-tenant+content-address —
  molde `services_foto_storage`, **não** `AnexoStoragePort`/PDF — G2/TL-CT-01), `OSReferenciaPort` (valida
  `os_id` existe/pertence ao tenant — seam OS), `ConsentimentoGpsPort` (opt-in vigente por
  `(tenant, colaborador, na_data)`, server-side, promovível a `shared` — D-CT-6), `ColaboradorCaixaPort`
  (papel `TECNICO`, dados mínimos). **Sem `AReembolsarPort`** (TL-CT-08 — reembolso = evento + backfill).
- **erros.py:** `FotoComprovanteObrigatoria`(412), `DespesaValidadaImutavel`(409),
  `FotoDuplicada`(409), `GpsConsentimentoAusente`(403, não bloqueia despesa),
  `AdiantamentoNaoCancelavel`(422), `PeriodoPrestacaoFechado`(422), `TransicaoInvalida`(422).

## 5. Invariantes candidatas (P7 crava em REGRAS + hook)

| INV candidata | Enforcement |
|---------------|-------------|
| INV-CT-FOTO-001 | despesa sem foto = `412 FOTO_OBRIGATORIA` (`foto_hash` NOT NULL + domínio `__post_init__`); teste happy/unhappy |
| INV-CT-FOTO-DEDUP-001 | `UNIQUE (tenant_id, foto_hash) WHERE status NOT IN ('rejeitada','cancelada')`; `foto_hash = HMAC-tenant(bytes pós-EXIF-strip)` (ADR-0064); mesma foto 2x = 409; **fotos idênticas cross-tenant coexistem** (teste); anti-fraude na constraint, idempotência no storage |
| INV-CT-IMUT-001 | trigger PG `caixa_tecnico_despesa_anti_mutacao` (`WHEN OLD.status='validada'`) + **block-delete sempre** (fiscal 5a); reapresentação `rejeitada→pendente` NÃO dispara (teste); estorno = nova despesa; hook `audit-immutability-check.sh`; drill anti-mutação |
| INV-CT-ADIAN-001 | transições válidas (`validar_transicao`); **entregue não cancela** (422); alçada server-side; teste de cada transição proibida |
| INV-CT-PRESTACAO-001 | `PrestacaoContas` WORM (campos congelados); saldo = Σ adiantamentos entregues − Σ despesas validadas; fechamento sob advisory lock; período fechado bloqueia nova despesa (422); teste imutabilidade + concorrência |
| INV-CT-SALDO-001 | `saldo_atual` derivado on-read (não campo mutável); teste consistência soma após N operações |
| INV-CT-IDEMP-001 | despesa offline dedup por `client_offline_id`+`Idempotency-Key` (REST) + `UNIQUE(tenant_id, client_offline_id)` (batch per-item) + content-addressing foto; consumer fan-out idempotente; teste replay parcial de lote |
| INV-LGPD-CONSENT-001 | consentimento GPS **server-side** (opt-in vigente NOT NULL), oposição append-only; GPS **nunca do payload nem do EXIF** (foto sempre stripada); base **art. 7º IX + V**; retenção própria curta + crypto-shredding; teste payload-spoof + EXIF-spoof rejeitados |
| INV-CT-REF-001 | técnico com caixa/despesa/adiantamento/prestação não é hard-deletado (`esta_referenciado`); teste guard |
| INV-008 (audit) | trilha via evento canônico WORM (bus); audit completo (foto, timestamp, GPS opcional, actor) |
| INV-TENANT-* / INV-BUS-001 (herdadas) | RLS v2 FORCE em todas as tabelas; consumers idempotentes (fan-out); perfil auto-injetado no envelope |

## 6. Portas, eventos e seams

**Publica (bus, dentro do `atomic`):** `caixa_tecnico.adiantamento.solicitado`/`.aprovado`/`.entregue`/
`.recusado`/`.cancelado`, `caixa_tecnico.despesa.lancada`/`.validada`/`.rejeitada`,
`caixa_tecnico.prestacao.fechada` (consumido por **contas-pagar** quando existir — fail-open lazy +
backfill por query).
**Consome (bus):** nenhum obrigatório em Wave A (vínculo OS validado on-write). Re-avaliar
`colaborador.desligado` (cancelar caixa) no P3.
**Lê via DB/porta:** `OSReferenciaPort.existe_os(os_id, tenant_id)` (seam OS, on-write);
`ConsentimentoGpsPort.opt_in_vigente(tenant, colaborador, na_data)` (server-side).
**Implementa para `colaboradores`:** `ColaboradorReferenciadoPort.esta_referenciado` (D-CT-12).

## 7. Non-goals Wave A

OCR de recibo; cartão corporativo (Pluggy); reembolso PIX instantâneo (ADR-0050) e execução do
pagamento; execução da devolução técnico-deve (Wave B); múltiplas moedas / viagem internacional;
adiantamento via folha; desconto em folha; app Flutter offline (ADR-0009 — só endpoints idempotentes);
custeio/margem real da OS (Wave B — `despesa.validada` só é publicada); despesa não segue cancelamento da
OS; anti-fraude de foto **semântica** (só bit-idêntica). GATEs: CT-CONTAS-PAGAR, CT-DEVOLUCAO-EXEC,
CT-PIX, CT-OCR, CT-B2, CT-GPS-LGPD-OAB.

## 8. Estado da revisão P2 (CONCLUÍDA) + ações P3

- ✅ **`tech-lead-saas-regulado` — APROVA COM CORREÇÕES** (incorporadas): TL-CT-01/02 foto = molde
  `services_foto_storage` + HMAC-tenant pós-strip + fronteira storage/constraint (D-CT-4); TL-CT-03 G6
  PDF via WeasyPrint, fatia leve (D-CT-8); TL-CT-04 G1 GPS `ConsentimentoGpsColaborador` + porta
  promovível a shared (D-CT-6); TL-CT-05 trigger na `despesa` + block-delete (D-CT-3); TL-CT-06 batch
  limite+per-item+UNIQUE client_offline_id (D-CT-5); TL-CT-08 sem porta de reembolso, evento + backfill
  (D-CT-8); TL-CT-09 path flat (D-CT-1); TL-CT-10 saldo derivado + advisory lock (D-CT-2); TL-CT-11 união
  `ACOES_CANONICAS` (D-CT-11); TL-CT-12/13 sem coluna de perfil/auditoria redundante (D-CT-10); TL-CT-14
  EXIF não é canal de GPS (D-CT-4/6). **Limite de honestidade (escalado):** sync offline de fotos grandes
  é net-new sem molde — teste de carga com falha de rede antes do 1º tenant pago; anti-duplicata é
  bit-idêntica (non-goal §7).
- ✅ **`advogado-saas-regulado` — minuta APROVA COM CORREÇÕES** (incorporadas): ADV-CT-01 base **art. 7º
  IX (legítimo interesse+LIA) + V apoio**, opt-in = salvaguarda não base (D-CT-6); ADV-CT-02 retenção GPS
  própria curta (fechamento+90d, máx 6–12m), desacoplada da foto 5a (D-CT-6); ADV-CT-03 aviso de UI + PII
  de terceiros na foto (D-CT-4); ADV-CT-04 `foto_hash` HMAC-tenant (D-CT-4); ADV-CT-05 transparência canal
  "Meus dados" (D-CT-6); ADV-CT-06 fronteira consentimento colaborador-scoped + aviso em RH (D-CT-6/§1);
  ADV-CT-09 GATE-CT-GPS-LGPD-OAB (D-CT-13). **Divergência sanada (ADV-CT-08):** base legal unificada com
  app-tecnico/RAT-13/T-CT-000 (V+IX) — INV-LGPD-CONSENT-001 compartilhada agora coerente nos dois lados.

**GATEs resolvidos em P0 (produto — Roldão 2026-06-17):** G3/CT-B2 = **LOCAL**; G4/CT-CONTAS-PAGAR =
**fail-open lazy**; G5/CT-DEVOLUCAO-EXEC = **só registra saldo**.
**GATEs resolvidos em P2 (tech-lead):** G1/CT-GPS-MIGRATION, G2/CT-STORAGE-PORT, G6/CT-PDF, D-CT-1/CT-PATH.

**Ações P3 (antes/durante plan/tasks):**
1. Corrigir PRD `caixa-tecnico/prd.md`: AC-CT-005-3 (trigger na `despesa`, não na raiz); AC-CT-002-5 (base
   legal V → **V+IX**); AC-CT-002-7 (retenção GPS **própria curta**, não 5a).
2. ADR curta para promover `ConsentimentoGpsPort`/entidade a `shared` (consumida por caixa-tecnico +
   app-tecnico) — ou registrar a porta como promovível e diferir a ADR ao nascer o app-tecnico.
3. Registrar **GATE-CT-GPS-LGPD-OAB** em `gates-wave-a-consolidado.md` (bloqueante de produção).
4. `retencao-matriz.md`: linha própria do GPS da despesa **só no GATE-LGPD-RAT-CONSOLIDACAO** (respeitar
   congelamento R17 — agora só o apontador-PII na spec).
5. Ordem de fatias (TL-CT-15): 1a domínio puro → 1b schema PG (RLS + triggers + UNIQUEs) → 2 use cases/REST
   (+ advisory lock, `/sync` batch) → 3a adapters reais (foto/GPS/OS/esta_referenciado) → 3b eventos/fan-out
   → 3c PDF WeasyPrint → P8 matriz → P9 auditores Família 5.

**Próximo:** P3 — plan/tasks. **Ritual obrigatório** (Spec Kit) — ver [[feedback_ritual_orquestrador]].
