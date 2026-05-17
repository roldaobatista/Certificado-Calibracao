---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/financeiro/README.md
---

# PRD — Módulo Custeio Real (Custos Reais por Serviço)

> Apuração de custo previsto vs real por OS, com margem por dimensão (OS, cliente, vendedor, técnico, serviço) e alerta de OS deficitária.

---

## 1. O que este módulo é

Módulo que **mostra onde a empresa ganha ou perde dinheiro de verdade**, por OS. Soma todos os custos diretos (mão de obra, deslocamento, hospedagem, alimentação, pedágio, peças, retrabalho, garantia, comissão), compara com o que foi orçado/previsto e calcula a margem real.

Não substitui `contas-pagar`/`contas-receber` (que registram movimentações financeiras brutas) nem `comissoes` (que calcula remuneração) — este **agrega** dados de várias fontes para uma visão de rentabilidade por OS/cliente/técnico/vendedor/serviço.

## 2. Por que este módulo existe

Linha 1599 de `docs/novas funcionalidades.txt`: "Sem custo real, o financeiro mostra receita, mas não mostra claramente onde a empresa ganha ou perde dinheiro."

Sem este módulo, o dono fatura R$100k/mês, vê lucro X no DRE, mas não sabe quais clientes/serviços/técnicos sustentam o lucro e quais drenam — decide no escuro.

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Custo previsto da OS (orçado)
- Custo real da OS (apurado pós-execução)
- Custo de mão de obra (hora-técnico × tempo aplicado)
- Custo de deslocamento (km × valor + combustível)
- Custo de hospedagem (recibos)
- Custo de alimentação (recibos)
- Custo de pedágio (recibos)
- Custo de peças (saída de estoque vinculada à OS)
- Custo de retrabalho (segunda execução da mesma OS sem cobrança)
- Custo de garantia (atendimento gratuito em garantia)
- Custo de comissão (devolvido pelo módulo `comissoes`)
- Margem real por OS (`receita_OS - custo_real_OS`)
- Margem real por cliente (agregação)
- Margem real por vendedor (agregação)
- Margem real por técnico (agregação)
- Margem real por tipo de serviço (agregação)
- Comparação previsto × realizado (variação % por categoria de custo)
- Alerta de OS deficitária (margem < 0 ou < threshold configurado)

## 5. Non-goals (o que NÃO está neste módulo)

- Apropriação de custos INDIRETOS / overhead (rateio de aluguel, energia, salário admin). Isso é contabilidade gerencial, fora do escopo desta versão.
- DRE / fluxo de caixa consolidado (fica no Financeiro de alto nível).
- Precificação automática (fica no módulo `Precificação Inteligente` — linha 1601).
- Folha de pagamento (fora).
- Cálculo do valor da comissão (isso é `comissoes`; aqui só CONSUMIMOS o custo já calculado).
- Decisão de aceitar/rejeitar OS deficitária — sistema só ALERTA; decisão é humana.

## 6. User Stories

### US-CUS-001: Apurar custo real de uma OS encerrada

**Como** sistema, **quero** consolidar todos os custos diretos de uma OS no fechamento, **para** que dono e gestores vejam margem real.

**Critérios de aceite:**
- **AC-CUS-001-1**: GIVEN OS com `status=encerrada`, WHEN evento `Operacao.OSEncerrada` chega, THEN módulo coleta: horas-técnico aplicadas (× hora-base), peças saídas do estoque, despesas reembolsáveis aprovadas (deslocamento/hospedagem/alimentação/pedágio), comissão calculada → grava `CustoRealOS`.
- **AC-CUS-001-2**: GIVEN custo real apurado, WHEN cálculo conclui, THEN dispara evento `CusteioReal.CustoApurado{os_id, custo_real, margem}`.
- **AC-CUS-001-3**: GIVEN OS reaberta (correção pós-encerramento), WHEN nova movimentação, THEN custo real é recalculado e versionado (histórico mantém versões).

**Invariantes:** `INV-TENANT-001` (custos isolados por tenant); apuração ATOMICA (custo real ou existe completo ou não existe).

**Dependências:**
- Bloqueado por: módulos `operacao/ordens-servico`, `estoque/saidas`, `financeiro/comissoes`, `financeiro/caixa-tecnico`.

---

### US-CUS-002: Comparar previsto × realizado por OS

**Como** dono ou gestor, **quero** ver lado a lado o que orçamos e o que de fato custou, **para** identificar onde estouramos.

**Critérios de aceite:**
- **AC-CUS-002-1**: GIVEN OS com orçamento prévio + custo real apurado, WHEN abro a tela da OS, THEN vejo tabela: categoria (mão de obra, peças, deslocamento, ...), previsto, realizado, variação R$, variação %.
- **AC-CUS-002-2**: GIVEN variação acima de X% (configurável), WHEN tela renderiza, THEN linha fica destacada em laranja/vermelho.

---

### US-CUS-003: Ver margem real agregada por cliente/técnico/vendedor/serviço

**Como** dono, **quero** rankings de margem real por dimensão, **para** decidir onde focar/cortar.

**Critérios de aceite:**
- **AC-CUS-003-1**: GIVEN período selecionado, WHEN abro relatório "Margem por Cliente", THEN vejo lista ordenada por margem (melhor → pior): cliente, receita período, custo real período, margem R$, margem %.
- **AC-CUS-003-2**: GIVEN mesmas premissas, idem para vendedor / técnico / tipo de serviço.
- **AC-CUS-003-3**: GIVEN cliente/técnico/etc com margem negativa, WHEN linha renderiza, THEN destacada em vermelho com flag "DEFICITÁRIO".

---

### US-CUS-004: Alerta de OS deficitária

**Como** gestor, **quero** ser alertado quando uma OS encerra com prejuízo, **para** investigar causa raiz.

**Critérios de aceite:**
- **AC-CUS-004-1**: GIVEN OS com `margem_real < 0` OU `margem_real_pct < threshold_alerta` (configurável por tenant), WHEN custo é apurado, THEN dispara notificação ao papel `gestor_operacional` + entra em fila de revisão.
- **AC-CUS-004-2**: GIVEN alerta enviado, WHEN gestor abre, THEN vê quebra de custos + comparação previsto×real + acesso à OS pra investigar.

---

### US-CUS-005: Registrar retrabalho como custo separado

**Como** sistema, **quero** identificar quando uma OS é re-executada sem cobrança adicional, **para** alocar esse esforço como custo de retrabalho.

**Critérios de aceite:**
- **AC-CUS-005-1**: GIVEN OS encerrada e reaberta sem nova cobrança, WHEN técnico aplica horas novas, THEN essas horas viram categoria `custo_retrabalho` (não `custo_mao_obra_normal`).
- **AC-CUS-005-2**: GIVEN visão por técnico, WHEN relatório carrega, THEN mostra coluna "% retrabalho" do técnico.

---

### US-CUS-006: Registrar garantia como custo separado

**Como** sistema, **quero** identificar atendimentos em garantia (gratuitos pro cliente), **para** alocar como `custo_garantia`.

**Critérios de aceite:**
- **AC-CUS-006-1**: GIVEN OS com flag `em_garantia=true` e `valor_cobrado=0`, WHEN custos são apurados, THEN tudo entra na categoria `custo_garantia`.
- **AC-CUS-006-2**: GIVEN relatório por tipo de serviço, WHEN carregado, THEN garantia aparece como linha separada (não polui margem do serviço pago).

---

### US-CUS-007: Configurar parâmetros de custeio por tenant

**Como** dono/admin, **quero** definir hora-base por técnico, custo/km de deslocamento, threshold de alerta deficitário, **para** que o cálculo reflita meu negócio.

**Critérios de aceite:**
- **AC-CUS-007-1**: GIVEN tela de configuração de custeio, WHEN admin edita hora-base de um técnico, THEN apuração de OSs FUTURAS usa novo valor; OSs já apuradas mantêm valor histórico.
- **AC-CUS-007-2**: GIVEN parâmetro alterado, WHEN salvo, THEN trilha de auditoria registra mudança (quem, quando, de→para).

---

## 7. Métricas de sucesso deste módulo

Ver `metricas.md`. Resumo:
- % OSs com custo real apurado em ≤24h após encerramento ≥ 95%
- % OSs deficitárias detectadas e revisadas ≤ 7 dias ≥ 90%
- Aderência (custo real apurado pelo sistema vs revisado manualmente) ≥ 95%

## 8. NFR

- **Performance:** apuração de uma OS em <2s; relatório agregado de 12 meses em <5s.
- **Disponibilidade:** apuração é eventual (consome eventos) — janela aceitável de até 1h.
- **Segurança:** dados de margem por técnico são sensíveis — RBAC restrito a gestor/dono.
- **Integridade:** apuração idempotente (re-execução produz mesmo resultado).

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo `US-CUS-NNN`.
- Categoria nova de custo → ADR (afeta modelo + integração com módulos fonte).
- Mudança em fórmula de margem → ADR + recálculo opcional do histórico.
