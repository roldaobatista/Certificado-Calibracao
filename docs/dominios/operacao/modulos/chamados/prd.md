---
owner: roldao
revisado-em: 2026-05-27
proximo-review: 2026-08-27
status: stable
modulo: chamados
dominio: operacao
diataxis: explanation
audiencia: agente
historico:
  - 2026-05-23 — versão inicial draft (porta de entrada Helpdesk)
  - 2026-05-27 — Onda 3 saneamento BATCH B2 — frontmatter canônico, perfil ADR-0067 declarado (SLA com coluna perfil_regulatorio), reescrita US-CH-001..009 em BDD GIVEN-WHEN-THEN, US-CH-009 nova (análise crítica de pedido cl. 7.1 — perfil A obriga; D dispensa), INV-AGENT-001 em US texto livre, vocabulário Wave A/Wave B, status STABLE.
relacionados:
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - docs/conformidade/comum/lgpd-rat.md
  - docs/dominios/operacao/modulos/os/prd.md
  - docs/dominios/operacao/modulos/agenda/prd.md
---

# PRD — Módulo Chamados (Helpdesk)

## 1. O que este módulo é

Porta de entrada de qualquer demanda do cliente: WhatsApp, telefone, portal, email. O chamado nasce, é triado em ≤ 30s, recebe SLA e ou (a) vira OS quando exige execução, ou (b) é fechado direto por orientação. **OP16 — Wave A** (faseamento operação dogfooding).

## 2. Por que este módulo existe

Dor #20 (atendente reabre WhatsApp 5x e perde contexto) + Dor #05 (cliente reclama que nunca sabe o status). Cobre JTBD-008 (triagem 30s), JTBD-016 (abrir em 1 min), JTBD-020 (não copiar info 3x), JTBD-086 (WhatsApp em 1 clique).

## 3. Personas

**Persona dominante:** P-OP-03 (atendente). Detalhes em `../personas.md` — P-OP-03 (atendente, primária), P-OP-04 (gerente — supervisão SLA), P-OP-05 (cliente final, autor do chamado).

## 4. Perfil regulatório (ADR-0067)

Este módulo é **transversal a todos os perfis A/B/C/D**, mas SLA + análise crítica de pedido (cl. 7.1) tem gating obrigatório por perfil (predicate `tenant_perfil_e([...])` lê `Tenant.perfil_regulatorio` no banco, NUNCA do payload):

| Feature | A — Acreditado RBC | B — Rastreável | C — Em preparação D→A | D — Comercial puro |
|---|---|---|---|---|
| **Chamado básico (US-CH-001..008)** | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |
| **SLA (tipo × urgência × perfil)** — perfil A tem SLA ANVISA mais pesado | ✅ OBRIGATÓRIO (SLA setorial ANVISA/CGCRE) | ✅ OBRIGATÓRIO (SLA padrão Aferê) | ✅ OBRIGATÓRIO (SLA padrão Aferê) | ✅ OBRIGATÓRIO (SLA padrão Aferê — sem peso ANVISA) |
| **Análise crítica de pedido cl. 7.1 (US-CH-009)** — predicates `cmc_cobre` + `procedimento_vigente_para` + `rt_competencia_cobre` + `padrao_disponivel` antes de criar OS de calibração | ✅ OBRIGATÓRIO (bloqueia conversão se algum predicate falhar) | 🟡 OBRIGATÓRIO_PARCIAL (warning ao gerente — não bloqueia) | 🟡 OBRIGATÓRIO_PARCIAL (warning ao gerente) | ⚪ OPCIONAL (não aplica — D não faz calibração regulada) |
| **Mascarar PII em UI + WhatsApp por LGPD** | ✅ OBRIGATÓRIO (ANPD + ANVISA) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |

Atualizar `docs/conformidade/comum/matriz-feature-perfil.md` antes de qualquer mudança.

## 5. Escopo Wave A

- CRUD de chamado com canal de origem rastreado
- Triagem rápida (tipo, urgência, equipamento, cliente) ≤ 30s
- Cálculo automático de SLA baseado em (tipo × urgência × perfil_regulatorio do tenant)
- Detecção de duplicados (cliente + equipamento + janela 7 dias) — sugere mesclar, **nunca mescla sozinho**
- Regra de distribuição sugere atendente/técnico (humano confirma)
- Escalonamento automático de SLA (75% do prazo → notifica; 100% → escala pra gerente)
- **Análise crítica de pedido (cl. 7.1)** antes de converter chamado em OS de calibração (perfil A obriga, D dispensa)
- Conversão em OS preservando histórico (chamado vira `os_origem`)
- Fechamento sem OS com razão obrigatória
- Integração WhatsApp (link "fale com a gente" — Solution 8.2)
- Audit log RAT-08

### Conversão (INV-CHM-RAST-001)

Chamado pode virar **(a) orçamento** (Wave B) **OR (b) OS direta**. A rastreabilidade tripla é preservada via `Orcamento.chamado_origem_id`, `OS.chamado_origem_id` e `OS.orcamento_origem_id`. Cliente não vê duplicidade — UI mostra "originado do chamado #N".

## 6. Não-objetivos Wave A

- **Integração OmniChannel (A-CH-001):** módulo `comunicacao-omnichannel` é Wave A e fornece porta `OmniChannelProvider` com 3 impls (WhatsApp Business API, Email SMTP, SMS). Chamados consome a porta, não implementa transporte aqui.
- Bot/IA respondendo o cliente sozinho (humano sempre na triagem)
- Mescla automática de duplicados (sempre humano decide)
- Pesquisa de satisfação dentro do chamado (vai pra Comercial NPS)
- Base de conhecimento integrada (Wave B)
- Roteamento por SLA financeiro / contrato premium (Wave B)
- Métricas avançadas estilo Zendesk (CSAT, FRT por agente) — Wave B

## 7. User Stories (BDD)

### US-CH-001 — Receber chamado via WhatsApp e triagem ≤ 30s

**Como** atendente (P-OP-03), **quero** receber chamado via WhatsApp (link) e triar em ≤ 30s, **para** não perder contexto.

- **AC-CH-001-1**: GIVEN cliente envia mensagem via link "fale com a gente" (WhatsApp Business API), WHEN servidor recebe, THEN cria `Chamado` em estado `aberto` + atribui ao atendente livre por round-robin + registra `canal_origem=whatsapp`.
- **AC-CH-001-2**: GIVEN chamado novo, WHEN atendente abre tela de triagem, THEN UI permite escolher `tipo` + `urgencia` + `equipamento` + `cliente` em ≤ 30s (atalhos teclado + defaults).
- **AC-CH-001-3 (anti prompt injection — INV-AGENT-001)**: GIVEN mensagem do cliente contém texto livre, WHEN servidor processa pra triagem automática ou LLM, THEN texto é tipado como `TextoLivreNaoConfiavel` antes de qualquer consumo (jamais expande variáveis ou instruções).
- **AC-CH-001-4 (LGPD)**: GIVEN chamado com número WhatsApp do cliente, WHEN UI renderiza lista, THEN número é mascarado conforme RAT-03 (`+55 (66) ****-1234`).

**Invariantes:** `INV-TENANT-001`, `INV-AGENT-001`, `RAT-03`.

---

### US-CH-002 — Detectar duplicado e sugerir mescla

**Como** atendente (P-OP-03), **quero** que sistema detecte duplicados (cliente + equipamento + janela 7 dias) e sugira mescla, **para** não abrir dois chamados pra mesma demanda.

- **AC-CH-002-1**: GIVEN chamado novo + existe outro chamado aberto com mesmo `cliente_id + equipamento_id` nos últimos 7 dias, WHEN servidor processa, THEN exibe banner "possível duplicado: chamado #N" + botão "mesclar".
- **AC-CH-002-2**: GIVEN atendente clica "mesclar", WHEN confirma, THEN mensagens do novo chamado migram pro antigo + novo chamado vira `fechado.motivo=mesclado`.
- **AC-CH-002-3**: GIVEN servidor detecta duplicado, WHEN salva, THEN NUNCA mescla automaticamente — sempre humano decide (INV-CH-MESCLA-001).

**Invariantes:** `INV-CH-MESCLA-001`.

---

### US-CH-003 — SLA calculado automaticamente por (tipo × urgência × perfil)

**Como** sistema, **quero** calcular SLA com base em (tipo, urgência, perfil_regulatorio), **para** garantir prazos compatíveis com regulação setorial.

- **AC-CH-003-1**: GIVEN chamado triado com `tipo` + `urgencia`, WHEN servidor calcula SLA, THEN consulta tabela `SLAConfig (tipo, urgencia, perfil_regulatorio) → prazo_horas`. Tabela tem coluna `perfil_regulatorio` indexada (predicate `tenant_perfil_e([Tenant.perfil_regulatorio])`).
- **AC-CH-003-2 (perfil A — ANVISA)**: GIVEN tenant em perfil A + chamado tipo `farma_critico`, WHEN SLA calculado, THEN prazo aplicado é o SLA-ANVISA setorial (mais agressivo que o padrão Aferê — ex: 4h vs 24h).
- **AC-CH-003-3 (perfil D)**: GIVEN tenant em perfil D, WHEN SLA calculado, THEN aplica SLA padrão Aferê sem peso ANVISA (linha `perfil_regulatorio=D` na tabela).
- **AC-CH-003-4 (read perfil — fecha L6)**: GIVEN servidor lê perfil pra escolha de SLA, WHEN executa, THEN lê `Tenant.perfil_regulatorio` do banco via `tenant_perfil_e([...])` — NUNCA do payload da request.

**Invariantes:** `INV-TENANT-PERFIL-002` (perfil lido do banco), `INV-CH-SLA-001`.

---

### US-CH-004 — Escalonamento automático de SLA

**Como** sistema, **quero** escalar chamados a 75% e 100% do SLA, **para** garantir cumprimento.

- **AC-CH-004-1**: GIVEN chamado com SLA configurado + `tempo_decorrido = 75% * prazo_sla`, WHEN job procrastinate roda, THEN dispara notificação push ao atendente responsável.
- **AC-CH-004-2**: GIVEN `tempo_decorrido = 100% * prazo_sla`, WHEN job processa, THEN escala pro gerente (P-OP-04) + dispara alerta visual no mapa de calor da fila.
- **AC-CH-004-3 (telemetria)**: GIVEN `tempo_triagem_ms` medido, WHEN chamado é triado, THEN registra em audit. Teste de carga Wave A com 100 atendentes simultâneos exige p95 ≤ 30s.

**Invariantes:** `IDEMP-001` (job procrastinate idempotente — ADR-0033).

---

### US-CH-005 — Converter chamado em OS preservando histórico

**Como** atendente (P-OP-03), **quero** converter chamado em OS preservando histórico, **para** rastrear origem.

- **AC-CH-005-1**: GIVEN chamado em estado `aguardando_conversao` + cliente confirmou, WHEN atendente clica "converter em OS", THEN cria `OS` (ADR-0023) com `OS.chamado_origem_id` setado + copia histórico de mensagens como `OS.notas_iniciais`.
- **AC-CH-005-2**: GIVEN OS criada, WHEN servidor persiste, THEN chamado vira `fechado.motivo=convertido_em_os` + publica `Chamado.ConvertidoEmOS` no bus.
- **AC-CH-005-3 (perfil A — gating cl. 7.1)**: GIVEN chamado contém item `tipo=CALIBRACAO` + tenant em perfil A, WHEN servidor tenta criar OS, THEN executa US-CH-009 (análise crítica) PRIMEIRO; se predicate falhar, bloqueia conversão com `412 ANALISE_CRITICA_BLOQUEADA`.

**Invariantes:** `INV-CHM-RAST-001`, `INV-OS-ANAL-001`.

---

### US-CH-006 — Fechar chamado sem OS

**Como** atendente (P-OP-03), **quero** fechar chamado sem OS quando o cliente foi atendido por orientação, **para** não inflar fila operacional.

- **AC-CH-006-1**: GIVEN chamado em estado `aberto`, WHEN atendente clica "fechar sem OS", THEN UI exige `razao_fechamento` (≥ 30 chars) + categoria (`orientado`, `desistencia`, `nao_se_aplica`, `duplicado`).
- **AC-CH-006-2**: GIVEN razão fornecida, WHEN salva, THEN chamado vira `fechado.motivo=sem_os` + emite `Chamado.FechadoSemOS`.

---

### US-CH-007 — Gerente vê fila SLA estourando em mapa de calor

**Como** gerente (P-OP-04), **quero** ver fila de chamados com SLA próximo de estourar em uma tela com mapa de calor, **para** intervir.

- **AC-CH-007-1**: GIVEN gerente abre painel SLA, WHEN UI renderiza, THEN mostra mapa de calor (verde < 50%, amarelo 50-75%, vermelho > 75%) + permite reatribuir chamado.

---

### US-CH-008 — Cliente recebe link WhatsApp pra acompanhar chamado

**Como** cliente (P-OP-05), **quero** receber link via WhatsApp para acompanhar status do meu chamado, **para** não ligar à base.

- **AC-CH-008-1**: GIVEN chamado criado + cliente tem `opt_in_whatsapp=true`, WHEN servidor publica `Chamado.Aberto`, THEN OmniChannel envia link `https://aferê.tenant.com.br/chamado/<token>` com token assinado HMAC 7 dias.
- **AC-CH-008-2**: GIVEN cliente clica link, WHEN abre portal, THEN vê status + ETA + histórico mensagens (sem dados internos).

---

### US-CH-009 — Análise crítica de pedido antes de criar OS (cl. 7.1 ISO 17025)

**Como** sistema, **quero** analisar criticamente o pedido antes de criar OS de calibração, **para** atender ISO 17025 cl. 7.1.4 + ADR-0024.

- **AC-CH-009-1 (perfil A obrigatório)**: GIVEN chamado convertido em OS contém item `tipo=CALIBRACAO` + tenant em perfil A (`tenant_perfil_e(['A'])`), WHEN servidor tenta criar OS, THEN executa predicate composto:
  - `cmc_cobre(equipamento.grandeza, faixa_solicitada, incerteza_objetivo)` (escopo CMC vigente — ADR-0066)
  - `procedimento_vigente_para(grandeza, faixa, metodo)` (procedimento aprovado vigente — ADR-0066)
  - `rt_competencia_cobre(rt_disponivel, grandeza, data_solicitada)` (ADR-0022 + ADR-0063)
  - `padrao_disponivel(grandeza, faixa, data_solicitada)`
  
  Se QUALQUER predicate falhar → bloqueia com `412 ANALISE_CRITICA_BLOQUEADA` + payload `{predicate_falhou, motivo, grandeza, faixa}`.
- **AC-CH-009-2 (perfil B/C — warning)**: GIVEN tenant em perfil B ou C + item de calibração, WHEN predicates avaliados, THEN ausência de cobertura emite warning ao gerente (banner amarelo) mas NÃO bloqueia conversão (permite trilha D→A em construção).
- **AC-CH-009-3 (perfil D — dispensa)**: GIVEN tenant em perfil D + item de calibração, WHEN servidor processa, THEN dispensa análise crítica (perfil D não emite certificado regulado; predicate retorna sucesso lazy).
- **AC-CH-009-4 (auditoria)**: GIVEN análise executada, WHEN bloqueia ou passa, THEN registra `AnaliseCriticaPedido` com `predicates_resultado JSONB` + snapshot canonicalizado (INV-DOC-CANON-001) + hash em audit (rastreabilidade ISO 17025 cl. 7.1.4 + 8.4).
- **AC-CH-009-5 (read perfil — fecha L6)**: GIVEN sistema avalia perfil pra gating, WHEN executa, THEN lê `Tenant.perfil_regulatorio` do banco via predicate canônico — NUNCA do payload.

**Invariantes:** `INV-OS-ANAL-001`, `INV-CAL-CMC-001`, `INV-CAL-VERSAO-001`, `INV-DOC-CANON-001`, `INV-TENANT-PERFIL-002`.

**Dependências:** ADR-0024, ADR-0066, ADR-0067, módulos `metrologia/escopos-cmc` + `metrologia/procedimentos-calibracao` (Wave A — predicate fail-open enquanto módulos não plugados).

---

## 8. Métricas

Ver `metricas.md`. Primárias (mínimo 2-3): tempo médio de triagem, % SLA cumprido, % chamados duplicados detectados, % chamados bloqueados por análise crítica (perfil A).

## 9. NFR

- **Triagem ≤ 30s p95 (A-CH-002):** `tempo_triagem_ms` é registrado em audit a cada triagem. Teste de carga obrigatório Wave A com 100 atendentes simultâneos. UI otimizada — atalhos teclado + valores default.
- WCAG 2.1 AA (INV-016)
- LGPD: número WhatsApp do cliente é dado pessoal — mascarar exibições conforme RAT-03

## 10. Dependências (ADRs)

ADR-0023 (OS com atividades — destino da conversão), ADR-0024 (regra de decisão ISO 17025), ADR-0033 (bus idempotência consumer — eventos `Chamado.Aberto`/`Chamado.ConvertidoEmOS`), ADR-0034 (saga compensação), ADR-0066 (predicates `cmc_cobre` + `procedimento_vigente_para`), ADR-0067 (perfil regulatório do tenant — SLA + análise crítica).

## 11. Glossário

Ver `glossario.md` + `docs/comum/glossario.md` + ADR-0037 (PT-EN canônico).

## 12. Como evolui

US nova → próximo `US-CH-NNN`. Feature nova com gating por perfil → atualizar `docs/conformidade/comum/matriz-feature-perfil.md` antes do merge.
