---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/novas funcionalidades.txt
  - docs/dominios/dados/README.md
---

# PRD — Módulo BI, Indicadores e Inteligência Gerencial

> Fonte de funcionalidades: `docs/novas funcionalidades.txt` linhas 880-923 (Módulo 22).
> **Status no roadmap: Wave B / V2.** MVP-1 não entrega este módulo completo, apenas KPIs fixos por módulo.

---

## 1. O que este módulo é

Camada de leitura agregada do Aferê. Junta dados de **todos os módulos operacionais** (Financeiro, OS, CRM, Estoque, Frota, Qualidade, Laboratório, e-mail) e entrega: dashboards por área, indicadores chave, relatórios customizáveis, projeções (fluxo de caixa, manutenção preditiva), e canais de distribuição (envio agendado, link público).

Resolve a dor do dono que hoje "abre 3 sistemas + pede planilha pro contador" para entender como o negócio vai.

## 2. Por que este módulo existe (problema a resolver)

- Empresas pequenas/médias de assistência técnica + laboratório **não enxergam o todo** — vivem por sintoma (caixa baixo, técnico ocioso, recalibração esquecida).
- Ferramentas externas (Power BI, Tableau) são caras, exigem técnico, e o dado segue fragmentado.
- Dor mapeada em `docs/discovery/dores-mapeadas.md` (a referenciar ID exato quando criada): "não consigo ver o negócio inteiro num lugar só".

## 3. Personas

Ver `personas.md` deste módulo + `../../personas.md` (domínio) + `docs/comum/personas.md`. Principais:
- **P1 Dono** — consumidor de resumo executivo.
- **P2 Gerente** — operacional ao vivo.
- **Analista** (específica) — constrói relatórios.
- **Cliente externo** (Wave B+) — dashboard público restrito.

## 4. Escopo (o que ESTÁ neste módulo)

Lista derivada **direto** das funcionalidades da seção 22 do `novas funcionalidades.txt`:

- Dashboards por área (financeiro, comercial, operacional, estoque, qualidade, frota, laboratório).
- Indicadores financeiros (faturamento, margem, custo).
- Indicadores comerciais (pipeline, taxa de conversão).
- Indicadores operacionais (SLA, tempo médio de atendimento).
- Indicadores de estoque (giro, ruptura).
- Indicadores de qualidade.
- Indicadores de frota.
- Indicadores de laboratório.
- Fluxo de caixa projetado.
- DRE (Demonstração de Resultado).
- Inadimplência.
- Receita por cliente.
- Receita por serviço.
- Receita por técnico.
- Receita por vendedor.
- Produtividade técnica.
- Taxa de conversão comercial.
- SLA.
- Tempo médio de atendimento.
- Churn (perda de clientes).
- Segmentação de clientes.
- Sugestões comerciais (cross/up-sell baseado em histórico).
- Manutenção preditiva baseada em histórico.
- Relatórios customizados (builder visual).
- Link público de dashboard.
- Envio agendado de relatórios (e-mail).

## 5. Non-goals (o que NÃO está neste módulo)

- **Não é ferramenta de exploração estatística avançada** (sem regressão / ML pesado fora de manutenção preditiva simples).
- **Não substitui contador/contabilidade legal** — DRE aqui é gerencial, não contábil oficial.
- **Não entrega data lake / warehouse externo** — exportação para ferramenta externa (Power BI) é via export CSV / API REST, não conexão direta ao banco operacional.
- **Não cria políticas de retenção próprias** — usa as do `conformidade/comum/retencao-matriz.md`.
- **Não é canal de notificação push** — usa o módulo Notificações para envio agendado.
- **MVP-1 não entrega** — só Wave B+.

## 6. User Stories

### US-BI-001: Dashboard executivo do dono
**Como** dono (P1), **quero** abrir o sistema e ver em 1 tela faturamento do mês, contas a receber, inadimplência e OS em andamento, **para** decidir o dia sem pedir relatório a ninguém.

**Critérios de aceite:**
- **AC-BI-001-1:** GIVEN dono logado, WHEN abre home, THEN vê 4 cards: faturamento mês corrente, receber 30 dias, inadimplência (R$ e %), OS abertas.
- **AC-BI-001-2:** GIVEN dado atualizado < 15 min, WHEN abre dashboard, THEN cada card mostra timestamp da última atualização.
- **AC-BI-001-3:** GIVEN dono clica num card, WHEN drill-down, THEN abre lista detalhada (clientes em atraso, OS por técnico, etc.) filtrada por tenant.

**Invariantes:** `INV-TENANT-001..004` (toda query filtrada por tenant), `INV-001` (audit trail das consultas sensíveis).

---

### US-BI-002: Dashboards por área operacional
**Como** gerente (P2), **quero** dashboards separados para financeiro, comercial, OS, estoque, qualidade, frota e laboratório, **para** acompanhar o setor de que sou responsável.

**Critérios de aceite:**
- **AC-BI-002-1:** GIVEN papel `gerente_operacional`, WHEN navega para "BI > Operacional", THEN vê SLA, tempo médio atendimento, fila por técnico.
- **AC-BI-002-2:** GIVEN papel sem permissão financeira, WHEN tenta abrir "BI > Financeiro", THEN bloqueado (403) + log de tentativa.

**Invariantes:** RBAC por papel; `INV-TENANT-001`.

---

### US-BI-003: Fluxo de caixa projetado
**Como** dono, **quero** ver projeção de caixa para próximos 30/60/90 dias **considerando** contas a receber, contas a pagar agendadas e recorrências, **para** antecipar aperto e decidir investimento.

**Critérios de aceite:**
- **AC-BI-003-1:** GIVEN base de contas a pagar e a receber atualizada, WHEN solicita projeção 30 dias, THEN retorna saldo dia-a-dia + alerta visual quando saldo cruzar zero.
- **AC-BI-003-2:** GIVEN alteração em conta a receber/pagar, WHEN salva, THEN projeção recalcula em ≤ 1 min.

---

### US-BI-004: DRE gerencial
**Como** dono, **quero** ver DRE simplificado por período (mês / trimestre / ano) **com** receita, custo direto, despesa operacional, lucro bruto e líquido, **para** entender saúde do negócio sem esperar contador.

**Critérios de aceite:**
- **AC-BI-004-1:** GIVEN classificação de plano de contas configurada, WHEN escolhe período, THEN exibe DRE com linhas agrupadas e percentuais.
- **AC-BI-004-2:** AVISO obrigatório em rodapé: "Visão gerencial. Não substitui demonstrativo contábil oficial."

---

### US-BI-005: Inadimplência e ação
**Como** dono/gerente, **quero** lista de clientes inadimplentes ordenada por valor + dias em atraso, **para** disparar cobrança.

**Critérios de aceite:**
- **AC-BI-005-1:** GIVEN parcelas vencidas há > 0 dias, WHEN abre relatório, THEN lista com colunas: cliente, valor total atraso, dias, último contato.
- **AC-BI-005-2:** GIVEN cliente selecionado, WHEN clica "Cobrar", THEN dispara fluxo do módulo Cobranças (sem duplicar regra).

---

### US-BI-006: Receita por dimensão
**Como** dono, **quero** ver receita agrupada por cliente / serviço / técnico / vendedor com ranking, **para** identificar onde concentrar esforço comercial.

**Critérios de aceite:**
- **AC-BI-006-1:** GIVEN período selecionado, WHEN escolhe dimensão (cliente/serviço/técnico/vendedor), THEN exibe top N com valor + % participação.
- **AC-BI-006-2:** GIVEN cliente único representa > 30% da receita, WHEN gera relatório, THEN alerta visual de concentração de risco.

---

### US-BI-007: Produtividade técnica
**Como** gerente, **quero** ver produtividade por técnico (OS concluídas, tempo médio, NPS quando houver), **para** distribuir trabalho com justiça e identificar treinamento.

**Critérios de aceite:**
- **AC-BI-007-1:** GIVEN OS com técnico atribuído, WHEN gera indicador, THEN mostra OS/dia, tempo médio por tipo de OS, taxa de retrabalho.

---

### US-BI-008: Taxa de conversão comercial
**Como** dono/gerente comercial, **quero** funil comercial com taxa de conversão por etapa (lead → orçamento → aprovado → faturado), **para** identificar onde perco venda.

**Critérios de aceite:**
- **AC-BI-008-1:** GIVEN funil configurado no CRM, WHEN abre indicador, THEN visualiza tx conversão entre cada etapa.

---

### US-BI-009: SLA e tempo médio de atendimento
**Como** gerente, **quero** SLA por tipo de chamado/OS e tempo médio de atendimento, **para** cumprir contrato de cliente exigente.

**Critérios de aceite:**
- **AC-BI-009-1:** GIVEN SLA configurado por contrato/cliente, WHEN OS aberta, THEN indicador exibe % de SLA cumprido no período.
- **AC-BI-009-2:** GIVEN OS prestes a violar SLA, WHEN abre dashboard, THEN destaque visual + opção de notificar responsável.

---

### US-BI-010: Churn de clientes
**Como** dono, **quero** identificar clientes que pararam de comprar / renovar contrato, **para** ação de retenção.

**Critérios de aceite:**
- **AC-BI-010-1:** GIVEN janela de inatividade configurável (90/180/365 dias), WHEN cliente não fatura no período, THEN entra no relatório de churn.

---

### US-BI-011: Segmentação de clientes
**Como** dono, **quero** segmentar clientes por porte / frequência / ticket médio / mix de serviços, **para** ação comercial dirigida.

**Critérios de aceite:**
- **AC-BI-011-1:** GIVEN critérios de segmentação selecionados, WHEN aplica, THEN gera lista exportável para CRM/campanhas.

---

### US-BI-012: Sugestões comerciais (cross/up-sell)
**Como** vendedor, **quero** receber sugestões de produtos/serviços para oferecer ao cliente baseado em **histórico do próprio cliente** e clientes similares, **para** aumentar ticket.

**Critérios de aceite:**
- **AC-BI-012-1:** GIVEN cliente com histórico de compras, WHEN abre ficha do cliente, THEN exibe até 3 sugestões + justificativa simples ("clientes parecidos compraram X").

**Non-goals:** sem ML caro; lógica simples de regras + estatística básica.

---

### US-BI-013: Manutenção preditiva (baseada em histórico)
**Como** gerente operacional / laboratório, **quero** ver alertas de equipamentos com tendência de falha **baseado em histórico** (intervalo médio entre falhas, vencimento de calibração), **para** propor manutenção preventiva ao cliente.

**Critérios de aceite:**
- **AC-BI-013-1:** GIVEN equipamento com ≥ 3 ocorrências de manutenção, WHEN intervalo médio se aproxima, THEN alerta "manutenção sugerida em X dias".

**Non-goals:** sem ML/IA pesada; estatística simples sobre histórico do próprio equipamento + da família.

---

### US-BI-014: Relatórios customizados
**Como** analista (P3), **quero** construir relatório escolhendo métrica + filtros + agrupamento sem chamar suporte, **para** atender pedido pontual de diretoria.

**Critérios de aceite:**
- **AC-BI-014-1:** GIVEN analista logado, WHEN abre builder, THEN escolhe entre lista de métricas pré-aprovadas + filtros + agrupamentos.
- **AC-BI-014-2:** GIVEN relatório salvo, WHEN reabre depois, THEN reusa configuração.
- **AC-BI-014-3:** GIVEN dado fora do escopo de permissão do analista, WHEN tenta selecionar, THEN métrica fica indisponível na lista (não só erro pós-clique).

**Invariantes:** `INV-TENANT-*`, RBAC.

---

### US-BI-015: Envio agendado de relatórios
**Como** dono / analista, **quero** agendar envio de relatório por e-mail (diário / semanal / mensal) para lista de destinatários, **para** não esquecer de gerar.

**Critérios de aceite:**
- **AC-BI-015-1:** GIVEN relatório salvo + agendamento configurado, WHEN data/hora chega, THEN sistema gera relatório + envia e-mail com PDF e/ou link.
- **AC-BI-015-2:** GIVEN destinatário externo (não usuário do tenant), WHEN inclui no agendamento, THEN avisa risco LGPD + exige confirmação.

**Invariantes:** `SEC-*` (proteção em trânsito do anexo), `INV-TENANT-*`.

---

### US-BI-016: Link público de dashboard
**Como** dono / analista, **quero** gerar link público de um dashboard específico **com** opções de proteção (senha, expiração, dados agregados-somente), **para** compartilhar com cliente externo sem dar acesso ao sistema.

**Critérios de aceite:**
- **AC-BI-016-1:** GIVEN dashboard escolhido, WHEN clica "Compartilhar link público", THEN obriga definir: senha (sim/não), expiração, escopo de dados (agregado / filtrado por cliente específico).
- **AC-BI-016-2:** GIVEN link público gerado, WHEN dados do dashboard envolverem outro tenant, THEN bloqueado.
- **AC-BI-016-3:** GIVEN link expirado, WHEN acessado, THEN página de "link expirado" sem vazar dado.

**Invariantes:** `INV-TENANT-001..004` (nenhum link vaza dado entre tenants), `SEC-*`, LGPD.

**Non-goals desta story:** sem analytics de visitas no link (V3+).

---

### US-BI-017: Dashboard customizado por tenant + default global

**Como** tenant, **quero** salvar dashboard próprio, **para** customizar sem afetar outros tenants (G-BI-2).

**Critérios de aceite:**
- **AC-BI-017-1**: tenant clica "Salvar como meu dashboard" → grava em `DashboardCustom(tenant_id, user_id, layout_json)`.
- **AC-BI-017-2**: admin Aferê (US-BI-018) publica `DashboardDefault(escopo=global)` que tenant herda se não tem custom; tenant pode "duplicar como meu" e editar.

### US-BI-018: Admin Aferê publica default global

- **AC-BI-018-1**: admin com `perfil=admin_afere` publica dashboard global; tenants veem automaticamente.

### US-BI-019: Dashboard MRR/ARR alimentado por CDC desde dia 1 (G-BI-1)

**Como** dono Aferê, **quero** ver MRR/ARR/churn em ≤5min de defasagem desde o dia 1 (`INV-BI-MRR-001`), **para** acompanhar receita do próprio SaaS.

**Critérios de aceite:**
- **AC-BI-019-1**: `MeterUsoEvent` + `BillingSaas.UsoMedido` + `BillingSaas.FaturaPaga` + `BillingSaas.PlanoCriado` alimentam dashboard MRR/ARR **via outbox transacional** (Fase 0 ADR-0011 — sem Debezium); refresh ≤5min p95.
- **AC-BI-019-2**: dashboard separa **MRR por componente** (base / faixas / addons / uso variável / desconto) — visibilidade do mix de receita.
- **AC-BI-019-3**: churn separado voluntário × involuntário (US-BIL-014 motivo_churn).
- **AC-BI-019-4**: Debezium **Fase 2b** alimenta outros datasets (OS, equipamentos, certificados) — não bloqueia MRR/ARR no dia 1.

**Invariantes:** `INV-BI-MRR-001`, `INV-001`.

### US-BI-020: RBAC papel × dashboard (G-BI-3)

**Como** sistema, **quero** matriz papel→dashboard via `AuthorizationProvider.can()`, **para** não usar `if user.groups.filter()` espalhado.

**Critérios de aceite:**
- **AC-BI-020-1** (refina US-BI-002): GIVEN usuário tenta abrir dashboard X, WHEN view consulta `AuthorizationProvider.can(action="dashboard.ver", resource={"dashboard_id": X})`, THEN decisão centralizada (ADR-0012).
- **AC-BI-020-2**: matriz papel × dashboard configurável por tenant (admin tenant define quem vê o quê).

### US-BI-021: Export CSV PII exige role + audit (G-BI-4)

**Como** sistema, **quero** que export ad-hoc CSV com >100 linhas contendo PII exija `role=BI_EXPORT_PII` + audit, **para** mitigar exfiltração.

**Critérios de aceite:**
- **AC-BI-021-1**: GIVEN export CSV solicita >100 linhas E colunas incluem campo da denylist PII (cpf/email/telefone), WHEN usuário tenta, THEN sistema exige perfil `BI_EXPORT_PII`; sem perfil → bloqueia + log tentativa.
- **AC-BI-021-2**: export aprovado grava `audit_trail.bi_export_pii(usuario, dashboard, filtros, linhas, hash_arquivo)`.
- **AC-BI-021-3**: tipo de defasagem alinhada ADR-0011 (G-BI-5): operacional ≤5min via outbox, gerencial 1h (MV), executivo 1d (batch ETL).

## 7. Métricas de sucesso deste módulo

Ver `metricas.md`. Resumo:
- **% de donos que abrem dashboard executivo ≥ 4 vezes/semana** = ≥ 70% (lag).
- **Tempo de carregamento p95 do dashboard executivo** ≤ 2s.
- **Relatórios customizados criados / cliente / mês** ≥ 1 (uso real do builder).

## 8. NFR (Requisitos Não-Funcionais)

- **Performance:** dashboards executivos p95 ≤ 2s. Builder de relatório p95 ≤ 5s para datasets ≤ 100k linhas.
- **Disponibilidade:** SLO 99,5% (módulo não-crítico operacional).
- **Segurança:** SEC-* aplicáveis; link público respeita LGPD; RBAC por métrica.
- **Acessibilidade:** WCAG AA. Daltonismo: paleta acessível por padrão.
- **Atualização de dados:** dashboard executivo ≤ 15 min de defasagem; operacional ao vivo ≤ 1 min.

## 9. Glossário

Ver `glossario.md` deste módulo.

## 10. Como este PRD evolui

- US nova → próximo ID `US-BI-NNN` livre.
- US deprecada → marcar `@deprecated` + ADR.
- Mudança em AC já implementado → ADR + novo teste.
