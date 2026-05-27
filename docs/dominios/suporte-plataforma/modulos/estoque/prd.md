---
owner: roldao
revisado-em: 2026-05-27
proximo-review: 2026-08-27
status: stable
modulo: estoque
dominio: suporte-plataforma
diataxis: explanation
audiencia: agente
relacionados:
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0030-vigencia-temporal-canonica.md
  - docs/adr/0031-soft-delete-tres-padroes.md
  - docs/adr/0032-fk-cross-modulo-anonimizacao.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0034-saga-compensacao-cross-modulo.md
  - docs/adr/0051-propagacao-adr0023-modulos-wave-a.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - docs/faseamento-foundation-waves.md
  - docs/faseamento-modulos.md
  - REGRAS-INEGOCIAVEIS.md
historico:
  - 2026-05-27 — saneamento Onda 3 Batch B4 pré-Wave A: **escopo movido Wave B → Wave A** (alinha com AGENTS §12 + `faseamento-modulos.md` linha 60 + `faseamento-foundation-waves.md` §5 lista 18 módulos Wave A); CRÍTICO L1#8 corrigido (lote vencido em veículo/cliente revalidado por job diário `bloquear_lote_vencido` — não só em consumo); VO `LoteEstoqueVigente` com `JanelaVigencia` (ADR-0030); soft-delete em 3 padrões (ADR-0031 — lote estado-máquina, movimento estado-máquina, configuração armazém `deletado_em`); AC binários GIVEN-WHEN-THEN com ID `AC-EST-NNN-N`; declara perfil ADR-0067; persona inline; deps ADR completas; matriz feature × perfil; métricas inline; status `draft` → `stable`.
---

# PRD — Módulo Estoque multi-local

## 1. O que este módulo é

Controle de saldo físico de peças/padrões em **múltiplos locais** (central, veículos, técnicos em campo, com cliente). Suporta **lote**, **validade** (via VO `JanelaVigencia` — ADR-0030), **número de série** e **transferência 2-etapas** com aceite + foto obrigatória (BIG-12, JTBD-104). Mantém **kardex** (linha do tempo de movimentos append-only) e suporta inventário. **Wave A** (decisão Roldão 17/05 — `faseamento-modulos.md` v8 linha 60: "Promovido (era Wave B implícita): OS sem peça = retrabalho"; `faseamento-foundation-waves.md` §5 lista 18 módulos Wave A incluindo `estoque`).

## 2. Por que existe

- BIG-12 (estoque rastreável é diferencial real — selo INMETRO rastreável).
- JTBD-098..109 (6 jobs): "saber onde está cada peça", "transferir com aceite", "alertar mínimo", "bloquear vencido", etc.
- Dor: "técnico levou peça e sumiu"; "peça vencida em calibração" (CRÍTICO L1#8 saneamento — lote em veículo/cliente fica fora do radar até consumo); inventário físico demora 8h.
- **OS sem peça = retrabalho = quebra promessa "1 visita resolve"** — justifica promoção para Wave A.

## 3. Personas (inline)

- **P-SUP-01 Almoxarife** — cadastra locais, faz entradas/saídas, dispara inventário; opera majoritariamente em desktop.
- **P-OP-01 Técnico de campo** — recebe transferência pra veículo, anexa foto do lacre, recusa se divergente; opera em smartphone (Flutter Wave A app-tecnico) offline-first.
- **P-SUP-02 Metrologista / RT** — confere que padrão metrológico tem validade vigente antes de usar em calibração (consumido por `metrologia/calibracao` via predicate `padrao_disponivel`).
- **P-COM-02 Atendente / Vendedor** — reserva peça pra OS na abertura (US-EST-005).

Detalhe operacional em `personas.md` deste módulo.

## 4. Escopo (Wave A — o que ESTÁ)

- Cadastro de locais de estoque (central + N veículos + N técnicos + cliente como local — soft-delete padrão C `deletado_em` ADR-0031).
- Saldo por (item, local, lote, NS).
- Movimentos append-only: entrada / saída / transferência / ajuste de inventário (padrão A estado-máquina ADR-0031 — `movimento.estado ∈ {emitido, em_transito, aceito, recusado, ajustado}`).
- Transferência 2-etapas: emissão → trânsito → aceite com foto obrigatória.
- **Bloqueio de consumo de lote vencido** (AC-EST-002-2).
- **Job diário `bloquear_lote_vencido`** revalida lotes em qualquer local incluindo veículo/cliente (US-EST-007 — fecha CRÍTICO L1#8 saneamento 2026-05-27).
- Reservas para OS (consumida por `operacao/os` via `atividade_id` — ADR-0051).
- Alerta de estoque mínimo (por item por local).
- Inventário com tela de conferência.
- Kardex por item ou por local.
- Custo médio ponderado (CMP) recalculado em cada entrada.

## 5. Non-goals (Wave A)

- NÃO emite NF de entrada (pertence ao `financeiro/notas-entrada` — Wave B).
- NÃO cota com fornecedor (pertence ao `comercial/fornecedores` — Wave B).
- NÃO cadastra catálogo (pertence ao `suporte-plataforma/catalogo` — Wave A, bloqueante).
- NÃO faz logística de transporte detalhada (roteirização multi-paradas — Wave B).
- NÃO controla custo por moeda estrangeira / NÃO suporta multi-moeda (Wave B).

## 6. Perfil regulatório (ADR-0067)

Este módulo é **transversal** — todos os perfis usam estoque. Mas algumas features se acoplam ao perfil regulatório:

| Comportamento | A — Acreditado RBC | B — Rastreável | C — Em preparação | D — Comercial puro |
|---|---|---|---|---|
| **Bloqueio de uso de padrão metrológico vencido em calibração** (predicate `padrao_disponivel` consultado por `metrologia/calibracao`) | ✅ OBRIGATÓRIO (fail-closed — calibração rejeita) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ⚪ OPCIONAL (modo warning) |
| **Job diário `bloquear_lote_vencido` revalida todos os locais (inclui veículo/cliente)** | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO |
| **Snapshot `perfil_no_evento` em `MovimentoEstoque` audit** (ADR-0067 §3) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ⚪ OPCIONAL |
| **Foto do lacre na transferência 2-etapas** | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | 🟢 OPCIONAL_RECOMENDADO |
| **Retenção do kardex** (cross-ref matriz retenção ADR-0067) | 25a | 25a | 25a | 5a (Receita) |

Predicate canônico: `tenant_perfil_e([...])` invocado por `metrologia/calibracao` ao chamar `padrao_disponivel`. Fail-closed: se perfil indeterminado, sistema **bloqueia uso de padrão sem vigência verificada**.

## 7. User Stories

### US-EST-001 — Cadastrar local e ver saldo

**Como** almoxarife, **quero** cadastrar locais e ver saldo, **para** saber onde está cada peça em < 30s.

- **AC-EST-001-1**: GIVEN almoxarife cadastrou "Central" + "Veículo João", WHEN abre lista de saldos, THEN vê saldo por (item, local) em < 1s (p95).
- **AC-EST-001-2**: GIVEN almoxarife marca local como desativado (padrão C ADR-0031 — `deletado_em`), WHEN salva, THEN local some da UI mas saldos históricos do kardex permanecem visíveis (audit imutável).

### US-EST-002 — Entrada de peça com lote e validade (VO `JanelaVigencia`)

**Como** almoxarife, **quero** dar entrada com lote + validade, **para** rastrear origem e bloquear consumo vencido.

- **AC-EST-002-1**: GIVEN almoxarife informa entrada com `lote=L123` + `vigencia_inicio=now()` + `vigencia_fim=2027-01-01`, WHEN salva, THEN sistema cria `LoteEstoqueVigente(lote, vigencia_inicio, vigencia_fim, revogado_em=NULL, motivo_revogacao=NULL)` conforme ADR-0030 + cria `MovimentoEstoque` append-only (padrão A estado-máquina ADR-0031) + saldo do local sobe.
- **AC-EST-002-2**: GIVEN tentativa de consumo de lote com `vigencia_fim < now()` OR `revogado_em IS NOT NULL`, WHEN consumidor (OS, calibração) solicita, THEN sistema bloqueia com mensagem PT "lote vencido em DD/MM/AAAA — local <Veículo João>" + emite `Estoque.ConsumoBloqueadoLoteVencido` audit.
- **AC-EST-002-3**: GIVEN almoxarife tenta editar `LoteEstoqueVigente.vigencia_fim` após movimentação ter consumido o lote, WHEN salva, THEN sistema rejeita "lote já movimentado — para revogar antecipadamente use 'revogar lote' com motivo" (INV-VIG-003).

### US-EST-003 — Transferência 2-etapas com foto

**Como** almoxarife, **quero** transferir peça pro veículo do técnico com aceite, **para** rastrear (BIG-12 JTBD-104).

- **AC-EST-003-1**: GIVEN almoxarife cria transferência (origem=Central, destino=Veículo João, qtd=2), WHEN confirma emissão, THEN saldo origem cai 2, saldo "em trânsito" sobe 2, `MovimentoEstoque.estado="em_transito"` (padrão A ADR-0031).
- **AC-EST-003-2**: GIVEN transferência em trânsito, WHEN técnico aceita no Flutter + anexa foto do lacre (≤ 5MB, comprimida server-side), THEN saldo destino sobe 2, "em trânsito" zera, `MovimentoEstoque.estado="aceito"` + foto salva em storage `ReferenciaPIIAnonimizavel` (ADR-0032 — técnico que aceita é PII).
- **AC-EST-003-3**: GIVEN tentativa de aceite sem foto, WHEN técnico submete, THEN sistema rejeita "foto do lacre obrigatória" (perfil A/B/C OBRIGATÓRIO; perfil D RECOMENDADO — matriz §6).
- **AC-EST-003-4**: GIVEN técnico recusa transferência, WHEN submete motivo, THEN saldo retorna pra origem, `MovimentoEstoque.estado="recusado"`, motivo registrado, evento `Estoque.TransferenciaRecusada` emitido.
- **AC-EST-003-5**: GIVEN sync mobile offline (ADR-0027 — LWW por atividade), WHEN técnico aceita offline e reconecta, THEN merge respeita ordem temporal e idempotência consumer (ADR-0033 — `idempotency_key=movimento_id+estado`).

### US-EST-004 — Inventário físico

**Como** almoxarife, **quero** rodar inventário e ajustar diferenças, **para** alinhar sistema ↔ físico.

- **AC-EST-004-1**: GIVEN almoxarife inicia inventário do local Central, WHEN registra contagem por item, THEN sistema mostra diferença (sistema − físico) + cria `MovimentoEstoque` `estado="ajustado"` com `motivo` obrigatório (≥10 chars) + `responsavel_id` + foto da assinatura do almoxarife (audit forte).
- **AC-EST-004-2**: GIVEN tentativa de ajuste com motivo < 10 chars, WHEN salva, THEN sistema rejeita (CHECK constraint análoga a INV-VIG-002).

### US-EST-005 — Reserva para OS (via `atividade_id` — ADR-0051)

**Como** atendente, **quero** reservar peça pra atividade da OS, **para** garantir disponibilidade.

- **AC-EST-005-1**: GIVEN saldo do item=5 no local "Veículo João", atendente reserva 2 pra `atividade_id=ATV-789`, WHEN salva, THEN saldo disponível=3, reservado=2 (FK `Reserva.atividade_id` — ADR-0051 §3).
- **AC-EST-005-2**: GIVEN atividade `ATV-789` concluída (evento `AtividadeDaOS.Concluida` consumido), WHEN consumer roda, THEN reservas viram `MovimentoEstoque.estado="aceito"` saída (idempotência ADR-0033 — `idempotency_key=atividade_id+reserva_id`).
- **AC-EST-005-3**: GIVEN atividade cancelada (US-OS-008), WHEN evento `AtividadeDaOS.Cancelada` chega, THEN reservas são liberadas + saldo disponível volta ao valor anterior (saga compensação ADR-0034).

### US-EST-006 — Alerta de mínimo

**Como** almoxarife, **quero** configurar mínimo por item, **para** receber alerta antes de zerar.

- **AC-EST-006-1**: GIVEN configuração `minimo=10` para item X no local Central, saldo cai pra 9, WHEN movimento é gravado, THEN sistema dispara notificação (canal: dashboard + email do almoxarife) + evento `Estoque.AlertaMinimo` (ADR-0033 — idempotência por `(item_id, local_id, dia)`).

### US-EST-007 — Job diário revalida lotes vencidos em **todos os locais** (CRÍTICO L1#8 — saneamento 2026-05-27)

**Como** sistema, **quero** job diário que percorre todos os lotes em todos os locais (inclui veículos e clientes) e revoga os vencidos, **para** lote vencido em veículo não ser descoberto só na hora do consumo em campo.

- **AC-EST-007-1**: GIVEN job `bloquear_lote_vencido` agendado diariamente (procrastinate cron 02:00 UTC), WHEN roda, THEN percorre `LoteEstoqueVigente` em **todos os locais** (não apenas Central) e para cada `vigencia_fim < now()` AND `revogado_em IS NULL` aplica `revogado_em=now()` + `motivo_revogacao="vencido_job_diario_YYYY-MM-DD"`.
- **AC-EST-007-2**: GIVEN lote revogado pelo job, WHEN consumer (OS, calibração) tenta consumir, THEN bloqueio é aplicado IMEDIATAMENTE (não espera consumo trazer a checagem — fecha CRÍTICO L1#8).
- **AC-EST-007-3**: GIVEN job revoga lote em Veículo, WHEN almoxarife abre dashboard, THEN vê notificação "lote L123 do Veículo João venceu hoje — coletar pra descarte ou reentrada com novo lote".
- **AC-EST-007-4**: GIVEN job falha (rede, banco), WHEN retry esgotado, THEN entra em `dead_letter_events` (ADR-0033) + alerta SEV-2 ao operacional.
- **AC-EST-007-5**: GIVEN tenant `perfil ∈ {A, B, C}`, WHEN job roda, THEN evento `Estoque.LoteRevogadoPorVencimento` grava `perfil_no_evento` snapshot (ADR-0067 §3) — defesa CGCRE retroativa que sistema bloqueou padrão vencido.
- **INV:** INV-EST-LOTE-VIGENTE-001 (lote vencido em qualquer local não pode ser consumido), ADR-0030, ADR-0033.

### US-EST-008 — Predicate `padrao_disponivel(tenant_id, grandeza, faixa, prazo)` consumido por análise crítica cl. 7.1 (US-ORC-009 + M4)

**Como** sistema, **quero** predicate canônico que responde se existe pelo menos 1 padrão metrológico vigente para uma grandeza/faixa no prazo informado, **para** análise crítica de pedido e abertura de OS de calibração.

- **AC-EST-008-1**: GIVEN consulta `padrao_disponivel(tenant_id, grandeza="massa", faixa="0-5kg", prazo=now()+7d)`, WHEN executa, THEN consulta `LoteEstoqueVigente` JOIN catálogo onde `categoria="padrao_metrologico"` AND `grandeza=$1` AND `faixa_cobre($2)` AND `JanelaVigencia.contem(prazo)` e retorna boolean.
- **AC-EST-008-2**: GIVEN nenhum padrão vigente encontrado, WHEN predicate retorna `False`, THEN consumidor (orçamento US-ORC-009, calibração M4) reprova/avisa conforme matriz perfil.
- **AC-EST-008-3**: GIVEN sistema indeterminado (catálogo de padrões ainda não plugado — ADR-0066 fail-open lazy), WHEN predicate retorna `unknown`, THEN consumidor segue com warning (perfil B/C) ou bloqueia (perfil A).

## 8. Métricas (inline)

**Primárias:**
- **Lotes vencidos consumidos por engano: 0** (mensal) — métrica binária; um único = SEV-1 obrigatório investigar.
- **Tempo médio de transferência aceita (emissão → aceite): p50 < 30 min** (excluindo período offline do técnico).
- **Taxa de inventário ajustado / inventários: < 5%** (qualidade da gestão física).

Detalhe em `metricas.md`.

## 9. NFR

- **Performance:** kardex p95 ≤ 1,5s; lista saldos ≤ 1s; predicate `padrao_disponivel` p95 ≤ 200ms.
- **Foto do lacre:** ≤ 5MB, compressão server-side, storage cifrado (`ReferenciaPIIAnonimizavel` — ADR-0032).
- **Job diário:** `bloquear_lote_vencido` executa em ≤ 5min para 100k lotes; idempotente (re-execução no mesmo dia é no-op).
- **Segurança:** foto fica em storage com acesso autenticado (INV-TENANT-001).
- **Append-only:** `MovimentoEstoque` é WORM via trigger PG anti-UPDATE/DELETE (mesmo padrão de `auditoria` da F-A).

## 10. Glossário

- **VO `LoteEstoqueVigente`** — value object `(lote: str, vigencia_inicio, vigencia_fim, revogado_em, motivo_revogacao)` conforme ADR-0030. Fonte canônica de vigência de lote.
- **Local de estoque** — entidade `Local(id, tipo ∈ {central, veiculo, tecnico, cliente}, nome, deletado_em)` com soft-delete padrão C (ADR-0031).
- **`MovimentoEstoque`** — entidade WORM com estado-máquina (padrão A ADR-0031): `emitido → em_transito → {aceito | recusado}` ou `entrada → aceito` ou `ajustado` (inventário).
- **Predicate `padrao_disponivel`** — função canônica consultada por análise crítica cl. 7.1 (US-ORC-009) e configuração de calibração M4.
- **Job `bloquear_lote_vencido`** — procrastinate cron diário que revalida vigência de lotes em todos os locais (fecha CRÍTICO L1#8).

Demais termos em `glossario.md`.

## 11. Matriz feature × perfil

Ver `docs/conformidade/comum/matriz-feature-perfil.md` linhas "Job diário bloquear_lote_vencido", "Foto do lacre transferência", "Snapshot RT competência por grandeza" (predicate `padrao_disponivel` é consumido por estes).

## 12. Como este PRD evolui

- US nova → próximo `US-EST-NNN` livre.
- Mudança em AC já implementado → ADR + novo teste.
- Mudança da matriz feature × perfil → editar `matriz-feature-perfil.md` + hook `feature-perfil-matriz-validator.sh` revalida.
