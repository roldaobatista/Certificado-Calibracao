---
owner: Roldão
revisado-em: 2026-05-22
status: draft
modulo: clientes
dominio: comercial
diataxis: reference
audiencia: agente
---

# Débitos técnicos — Módulo Clientes

> Lista formal de **gaps de domínio** identificados após entrega Marco 1 (2026-05-20) que não bloquearam fechamento mas precisam virar tarefa rastreável em Wave A. Origem: Onda 4 saneamento — Auditor 3.

## Como ler

| Coluna | Significado |
|---|---|
| **ID** | `T-CLI-SAN-NN` (saneamento) — chave estável para rastrear até commit. |
| **Severidade** | CRÍTICO / ALTO / MÉDIO / BAIXO conforme INV-RITUAL-001. CRÍTICO/ALTO bloqueia abertura de Wave A do módulo dependente. |
| **Janela** | Wave A / Wave B / V2 — quando entra em pauta. |
| **Critério de fechamento** | O que precisa estar verde para considerar resolvido. |

---

## T-CLI-SAN-01 — `EventoTimeline` materializada (não filtro LIKE)

- **Severidade:** ALTO
- **Janela:** Wave A (US-CLI-002 visão 360°)
- **Origem:** Onda 4 A1-CLI + Marco 1 GATE-CLI-2 (`EventoTimeline` consumers).
- **Problema:** Marco 1 entregou a visão 360° via consulta filtrada `WHERE cliente_id = ? AND tipo IN (...)` em tabelas de origem (`os_eventos`, `certificados_eventos`, `nf_eventos`). Em tenant com cliente "histórico" (>500 eventos), p95 estoura SLA 1.5s (medido 3.2s em ambiente local com 800 eventos sintéticos).
- **Decisão:** materializar `EventoTimeline` como tabela própria no schema do tenant (entidade nova em `modelo-de-dominio.md`); alimentação via consumers de eventos publicados pelos módulos origem; índice composto `(tenant_id, cliente_id, ocorrido_em DESC)`.
- **Critério de fechamento:**
  - Tabela `evento_timeline_cliente` criada com índice composto.
  - Consumers idempotentes para `OS.Concluida`, `Certificado.Emitido`, `NotaFiscal.Emitida`, `NPS.Respondido`, `ContatoCliente.Registrado`, `Cliente.Bloqueado`.
  - p95 visão 360° < 1.5s em tenant com 10.000 clientes × 500 eventos cada (medido em ambiente dogfooding Balanças Solution).
  - Backfill executado nos tenants existentes (job `backfill_evento_timeline`).

## T-CLI-SAN-02 — Régua D+30/60/89 — PRD detalhado dos 8 GATEs CLI

- **Severidade:** ALTO
- **Janela:** Wave A (US-CLI-004 + módulo `comunicacao-omnichannel` + `contas-receber`)
- **Origem:** Onda 4 A4-CLI + GATE-CLI-3..8 rastreados em AGENTS.md §12 + INV-048/INV-CLI-BLOQ-001.
- **Problema:** Marco 1 deixou política de bloqueio automático **desligada por default** (`Tenant.bloqueio_automatico_inadimplencia_habilitado=False`) com justificativa "módulo `comunicacao-omnichannel` ainda não entrega régua D+30/60/89 — CDC art. 6º III/IV exige comunicação prévia escalonada". Sem detalhar a régua, Wave A vai improvisar.
- **Decisão (consolidada em PRD da régua, a ser linkado quando Wave A criar):**

### 2.1 Canal preferido + fallback

| Tentativa | Canal preferido | Fallback se indisponível |
|---|---|---|
| D+30 (notificação amigável) | WhatsApp (Cliente.consentimento_whatsapp=True) | E-mail (Cliente.email principal) |
| D+60 (notificação formal) | E-mail | SMS (telefone principal Contato.principal=True) |
| D+89 (última chamada) | Ligação manual registrada em audit | E-mail + SMS combinados |

"Indisponível" = canal sem consentimento ativo OU API com falha persistente (>3 retries em 24h). Sem nenhum canal disponível → marca `Cliente.regua_inalcancavel=True` + alerta P2 ao gerente operacional; **bloqueio automático D+90 NÃO ocorre** sem régua completa registrada (INV-CLI-BLOQ-001).

### 2.2 Reset de prazo

| Evento | Comportamento |
|---|---|
| Pagamento parcial (>0% do valor devido) | **Não reseta** — régua continua, mas `valor_em_aberto` atualiza. Se pagamento < 50% do título mais antigo vencido, continua para D+60/89. |
| Acordo de parcelamento aceito + 1ª parcela paga | **Reseta** — `dias_vencido` zera; régua reinicia a partir do próximo vencimento. |
| Carnê (parcelamento aceito sem 1ª parcela ainda paga) | **Reseta parcial** — régua passa a considerar a próxima parcela do carnê como "novo D+0"; parcelas anteriores quitam-se na ordem da emissão. |
| Renegociação (novo título substitui anterior) | **Reseta** — título anterior `BAIXADO_POR_RENEGOCIACAO`; novo título tem `D+0` novo. |

### 2.3 Fonte da hora

- `dias_vencido` calculado a partir de **data de vencimento ORIGINAL** do título (não data emissão; não data de inserção no sistema; não data de última atualização). Independe de timezone do usuário — usa `tenant.timezone` para definir corte de "dia".
- Job `job_inadimplencia_alertas` roda **02:00 BRT** (ADR-0015 fluxo 4); reabre a janela todo dia (idempotência via `IDEMP-001`).

### 2.4 Idempotência

- **1 mensagem por título × por canal × por dia.** Re-execução do job no mesmo dia não duplica notificação. Chave idempotência: `hash(tenant_id, titulo_id, canal, data_envio_yyyymmdd)`.
- Mudança de canal (fallback ativado) cria nova chave (D+30 WhatsApp falha → e-mail no mesmo dia conta como nova tentativa, com `tentativa_n=2` no payload).

### 2.5 SLA p95 visão 360°

- Tenants com ≤10.000 clientes: p95 < 1.5s (medido em prod com tracing OTel).
- Tenants com 10.000 < clientes ≤ 50.000: degradação aceita até p95 3.0s.
- Tenants > 50.000 clientes: requer mitigação dedicada (paginação cursor + materialização incremental — fora MVP).

- **Critério de fechamento:**
  - PRD detalhado escrito em `docs/dominios/operacao/modulos/comunicacao-omnichannel/regua-cobranca.md` (Wave A criará).
  - Consumer `ContasReceber.TituloVencido` implementado com idempotência.
  - Teste E2E: 100 títulos × 4 tenants distintos × 30 dias simulados → 0 mensagens duplicadas, 0 bloqueio sem régua completa.
  - INV-CLI-BLOQ-001 validado por hook + teste de regressão.

## T-CLI-SAN-03 — Reset de papel `cadastro_avancado` no AuthorizationProvider

- **Severidade:** ALTO (depende de C3-CLI sucessao + A2-CLI reativação)
- **Janela:** Wave A
- **Origem:** Onda 4 A2-CLI + C3-CLI.
- **Problema:** Sucessão societária e cadastro pós-anonimização exigem papel novo `cadastro_avancado` (papel mais restrito que `atendente_comercial`). `AuthorizationProvider` Marco 1 não tem esse papel.
- **Critério de fechamento:**
  - Papel `cadastro_avancado` registrado em `docs/comum/papeis.md`.
  - `AuthorizationProvider.can("cliente.criar_pos_anonimizacao", ...)` e `.can("cliente.registrar_sucessao", ...)` autorizam apenas papel `cadastro_avancado` + `dono_tenant`.
  - Teste unitário cobrindo atendente comum sendo rejeitado.

## T-CLI-SAN-04 — `LimiteCredito` ainda como VO no agregado Cliente

- **Severidade:** MÉDIO
- **Janela:** Wave A
- **Origem:** Onda 4 M3-CLI + glossário §"Limite de crédito".
- **Problema:** `LimiteCredito{valor, moeda}` está declarado em `modelo-de-dominio.md` como VO mas sem regras de uso (uso atual, recálculo após pagamento, override por gerente). Marco 1 não usou.
- **Status formal:** **Wave A**. Implementação: VO + 3 ACs (consulta, override, bloqueio de OS quando excede).
- **Critério de fechamento:** VO + suite de testes + 2 ACs em PRD US-CLI-NNN (Wave A criará).

## T-CLI-SAN-05 — `Segmento` postergado para Wave B (CRM)

- **Severidade:** MÉDIO
- **Janela:** Wave B
- **Origem:** Onda 4 M3-CLI.
- **Problema:** `Segmento` declarado em `modelo-de-dominio.md` + glossário. Marco 1 não implementou (Foundation F-C não bloqueou). Domínio real de Segmento é CRM (Wave B módulo `crm/segmentacao`).
- **Status formal:** **Wave B**. No PRD do CRM, Segmento vira agregado próprio; Cliente só carrega `segmento_ids` (array de FK).
- **Critério de fechamento:** entidade movida para `docs/dominios/comercial/modulos/crm/modelo-de-dominio.md` quando módulo CRM nascer; campo `segmento_ids` em Cliente fica como FK opcional.

## T-CLI-SAN-06 — Bloqueio comercial → finalidade `AcessoDadosCliente`

- **Severidade:** MÉDIO
- **Janela:** Wave A
- **Origem:** Onda 4 M4-CLI.
- **Problema:** Cliente `BLOQUEADO_COMERCIAL` (por inadimplência ou manual) ainda permite consulta para finalidade COMERCIAL/MARKETING — viola LGPD art. 6º III (necessidade) já que não há vínculo comercial ativo.
- **Decisão:** AC em US-CLI-002: "Cliente `BLOQUEADO_COMERCIAL` aceita consulta com `finalidade=COBRANCA` ou `finalidade=JURIDICO`; nega com 403 + texto canônico se `finalidade ∈ {COMERCIAL, MARKETING}`."
- **Critério de fechamento:** AC adicionada em PRD + teste de regressão + hook `lgpd-policy-unica.sh` cobre a regra.

## T-CLI-SAN-07 — `lead_id_origem` no payload `Cliente.Criado`

- **Severidade:** MÉDIO
- **Janela:** Wave B (entrega quando CRM/leads nascer)
- **Origem:** Onda 4 M5-CLI.
- **Problema:** Lead→cliente é fluxo CRM Wave B. Quando lead converte em cliente, `Cliente.Criado` precisa carregar `lead_id_origem` para o BI conseguir medir conversão por canal/campanha.
- **Critério de fechamento:** Catálogo de eventos (Onda 1) adiciona campo `lead_id_origem: UUID NULL` em `Cliente.Criado.payload`; CRM/leads publica `Lead.Convertido` que dispara criação via API com esse campo.

## T-CLI-SAN-08 — `aceite_lgpd_ip_hash` CHECK constraint

- **Severidade:** BAIXO
- **Janela:** Wave A migration
- **Origem:** Onda 4 B1-CLI.
- **Problema:** `Cliente.aceite_lgpd_ip_hash` aceita qualquer string. Deve ter `CHECK (length(aceite_lgpd_ip_hash) = 64 AND aceite_lgpd_ip_hash ~ '^[a-f0-9]+$')` — SHA-256 hex válido.
- **Critério de fechamento:** CHECK constraint na próxima migration do módulo + teste.

## T-CLI-SAN-09 — `cpf_responsavel_legal` DV (PJ)

- **Severidade:** BAIXO
- **Janela:** Wave A migration
- **Origem:** Onda 4 B2-CLI.
- **Problema:** PJ tem campo opcional `cpf_responsavel_legal` (sócio administrador, RT do cliente). Marco 1 valida formato (11 dígitos) mas **não valida DV** (Módulo 11).
- **Critério de fechamento:** VO `CPF` em `value_objects.py` reutilizado; teste com 1000 CPFs sintéticos passa.

## T-CLI-SAN-10 — Drift `modelo-de-dominio.md` status `draft`

- **Severidade:** BAIXO
- **Janela:** Onda 4 (esta) — fechado ao publicar este doc
- **Origem:** Onda 4 B3-CLI.
- **Problema:** `modelo-de-dominio.md` ainda em status `draft` + `revisado-em: 2026-05-17` — defasado vs Marco 1 entregue.
- **Resolução:** atualizar frontmatter para `status: stable` + `revisado-em: 2026-05-22` (feito nesta Onda 4).

---

## Resumo por janela

| Janela | Itens |
|---|---|
| Wave A | T-CLI-SAN-01, 02, 03, 04, 06, 08, 09 |
| Wave B | T-CLI-SAN-05, 07 |
| Onda 4 (fechado) | T-CLI-SAN-10 |

## Como evolui

Débito novo → adicionar entrada com próximo ID `T-CLI-SAN-NN` + severidade + janela + critério de fechamento. Débito fechado → marcar com data de fechamento + commit/PR de referência (manter na lista para histórico, não deletar).
