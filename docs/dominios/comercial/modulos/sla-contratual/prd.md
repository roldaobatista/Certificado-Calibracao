---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/comercial/README.md
  - docs/dominios/comercial/modulos/contratos/prd.md
  - docs/dominios/operacao/modulos/chamados/prd.md
---

# PRD — Módulo SLA Contratual

> Gestão de acordos de nível de serviço (SLA) **comerciais**, definidos em contrato com o cliente. Distinto de SLO técnico (observabilidade de infra) e de SLA operacional de chamados internos.

---

## 1. O que este módulo é

Módulo que permite definir, monitorar, alertar e reportar **SLAs contratuais** — promessas formais de tempo de resposta, tempo de solução, disponibilidade e qualidade pactuadas em contrato com cada cliente. Calcula penalidade/bonificação automaticamente e gera evidência de cumprimento.

Atende a empresa contratada (técnico, gerente de contas, financeiro) e o cliente final (relatório SLA periódico).

## 2. Por que este módulo existe (problema a resolver)

Em contratos recorrentes (manutenção, calibração programada, assistência técnica), o SLA é parte central da negociação. Hoje o controle é manual (planilha, e-mail), o que causa: descumprimento não detectado, penalidade não cobrada/aplicada, bonificação não reconhecida, cliente questionando sem evidência. Risco financeiro e reputacional direto.

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Definição de SLA por contrato, por cliente, por tipo de serviço, por criticidade.
- Calendário de atendimento (horário comercial, 24/7, feriados, escalas).
- Cálculo de tempo de resposta (TR) e tempo de solução (TS).
- Penalidade por descumprimento (regra parametrizável).
- Bonificação por desempenho (regra parametrizável).
- Pausa justificada de SLA (aguardando cliente, peça em trânsito, etc.).
- Alerta preventivo antes do estouro.
- Escalonamento automático por nível (técnico → gerente → diretoria).
- Relatório SLA periódico para o cliente.
- Evidência de cumprimento (anexa logs, fotos, OS, chamados).

## 5. Non-goals (o que NÃO está neste módulo)

- **NÃO** define SLO técnico de infra/software (latência, uptime do app) — isso é `docs/operacao/observabilidade.md`.
- **NÃO** define SLA interno de chamados de TI/suporte de uso do sistema — isso é `dominios/operacao/modulos/chamados/`.
- **NÃO** redige cláusula contratual jurídica (faz o cálculo conforme cláusula já redigida em `contratos/`).
- **NÃO** emite nota de débito/crédito da penalidade/bonificação (gera **evento** consumido pelo Financeiro).
- **NÃO** substitui módulo de contratos (depende dele para SLAs serem vinculados).

## 6. User Stories

### US-SLA-001: Cadastrar perfil de SLA reutilizável

**Como** gerente comercial, **quero** cadastrar perfis de SLA reutilizáveis (ex: "Ouro 24/7", "Prata 8x5", "Básico 8x5"), **para** aplicar o mesmo perfil em vários contratos sem retrabalho.

**Critérios de aceite:**
- **AC-SLA-001-1**: GIVEN usuário com papel "comercial", WHEN cria perfil com TR=2h, TS=8h, calendário 24/7, penalidade=2% do mensal por hora estourada, THEN perfil fica disponível para vincular em contratos.
- **AC-SLA-001-2**: GIVEN perfil já vinculado a contrato ativo, WHEN tenta editar, THEN sistema exige criar nova versão (perfis vinculados são imutáveis quanto a regras críticas).
- **AC-SLA-001-3**: GIVEN perfil rascunho, WHEN tenta vincular a contrato sem cláusula equivalente, THEN sistema avisa divergência e exige confirmação.

**Non-goals:** não cria contrato — só perfil.

**Invariantes relacionadas:** `INV-TENANT-001` (isolamento tenant).

**Dependências:**
- Bloqueado por: módulo `contratos/` (cláusulas mestre).

---

### US-SLA-002: Cronometrar SLA de chamado/OS em tempo real

**Como** atendente, **quero** ver na tela do chamado/OS o tempo restante de TR e TS, **para** priorizar atendimento sem estourar SLA.

**Critérios de aceite:**
- **AC-SLA-002-1**: GIVEN chamado aberto vinculado a contrato com SLA "Ouro 24/7", WHEN abro chamado, THEN sistema mostra cronômetro decrescente de TR e TS com cor (verde > 50%, amarelo 50–20%, vermelho < 20%).
- **AC-SLA-002-2**: GIVEN calendário 8x5 fora do horário comercial, WHEN tempo passa fora do horário, THEN cronômetro pausa automático e retoma na abertura do próximo expediente.
- **AC-SLA-002-3**: GIVEN feriado nacional/municipal cadastrado, WHEN data atual = feriado, THEN cronômetro respeita calendário.

**Invariantes:** `INV-TENANT-001`.

**Dependências:** bloqueado por `dominios/operacao/modulos/chamados/`, `dominios/operacao/modulos/ordens-servico/`.

---

### US-SLA-003: Pausar SLA com justificativa

**Como** atendente, **quero** pausar o SLA quando o atendimento depende do cliente (peça em trânsito, cliente fora), **para** não ser penalizado por causa alheia.

**Critérios de aceite:**
- **AC-SLA-003-1**: GIVEN chamado em andamento, WHEN clico "Pausar SLA" e seleciono motivo de uma lista controlada + descrição obrigatória + anexo (opcional), THEN cronômetro pausa e registro fica em trilha imutável.
- **AC-SLA-003-2**: GIVEN SLA pausado, WHEN cliente responde / peça chega, THEN sistema notifica atendente e exige despausar manualmente (não despausa sozinho).
- **AC-SLA-003-3**: GIVEN motivo de pausa não está na lista permitida pelo contrato, WHEN tenta pausar, THEN sistema bloqueia.

**Invariantes:** trilha imutável da pausa (cita política WORM).

---

### US-SLA-004: Alertar preventivamente antes de estouro

**Como** gerente de operações, **quero** receber alerta quando SLA atinge 80% do tempo, **para** intervir antes do descumprimento.

**Critérios de aceite:**
- **AC-SLA-004-1**: GIVEN SLA com TR=2h, WHEN cronômetro atinge 1h36min consumidos, THEN sistema dispara notificação ao responsável (canal configurável: e-mail, push, comunicação omnichannel).
- **AC-SLA-004-2**: GIVEN alerta enviado, WHEN ninguém atua em 15 min, THEN dispara escalonamento (US-SLA-005).

---

### US-SLA-005: Escalonar automaticamente quando SLA está em risco

**Como** diretor, **quero** ser notificado quando um SLA crítico está prestes a estourar e ninguém agiu, **para** acionar contingência.

**Critérios de aceite:**
- **AC-SLA-005-1**: GIVEN nível 1 sem ação em X min, WHEN dispara escalonamento, THEN nível 2 é notificado (gerente).
- **AC-SLA-005-2**: GIVEN nível 2 sem ação em Y min, WHEN dispara, THEN nível 3 (diretoria) é notificado.
- **AC-SLA-005-3**: GIVEN escalonamento atingiu nível máximo, WHEN SLA estoura, THEN evento `SLA.Estourou` é publicado para Financeiro calcular penalidade.

---

### US-SLA-006: Calcular penalidade/bonificação automaticamente

**Como** financeiro, **quero** que o sistema calcule a penalidade/bonificação por SLA automaticamente, **para** aplicar em fatura ou nota sem cálculo manual.

**Critérios de aceite:**
- **AC-SLA-006-1**: GIVEN SLA estourado em N horas, WHEN regra = "2% do mensal por hora", THEN sistema calcula valor e publica evento `SLA.PenalidadeCalculada` para Financeiro.
- **AC-SLA-006-2**: GIVEN SLA cumprido 100% no mês com bonificação configurada, WHEN ciclo fecha, THEN evento `SLA.BonificacaoCalculada` é emitido.
- **AC-SLA-006-3**: GIVEN regra de teto/piso configurada (ex: penalidade máxima 20% do mensal), WHEN cálculo ultrapassa, THEN aplica o teto.

---

### US-SLA-007: Gerar relatório SLA para cliente

**Como** gerente de contas, **quero** gerar relatório mensal de SLA do cliente, **para** enviar como evidência contratual.

**Critérios de aceite:**
- **AC-SLA-007-1**: GIVEN período (mês), WHEN clico "Gerar relatório SLA", THEN sistema produz PDF com: chamados/OS no período, TR/TS de cada, % de cumprimento, eventos de pausa, penalidades/bonificações, observações.
- **AC-SLA-007-2**: GIVEN relatório gerado, WHEN clico "Enviar ao cliente", THEN dispara envio via módulo de Comunicação Omnichannel (e-mail/WhatsApp conforme preferência cadastrada).
- **AC-SLA-007-3**: GIVEN relatório emitido, WHEN tento alterar, THEN sistema bloqueia (relatório é imutável após emissão).

**Invariantes:** WORM no relatório emitido.

---

### US-SLA-008: Anexar evidência de cumprimento

**Como** técnico, **quero** anexar foto/log/assinatura do cliente como evidência do atendimento, **para** comprovar cumprimento de SLA em caso de questionamento.

**Critérios de aceite:**
- **AC-SLA-008-1**: GIVEN OS encerrada vinculada a SLA, WHEN técnico anexa foto + assinatura cliente, THEN evidências ficam vinculadas ao registro SLA.
- **AC-SLA-008-2**: GIVEN evidência anexada, WHEN consulta relatório SLA, THEN evidências aparecem como hyperlink/QR code para verificação.

---

## 7. Métricas de sucesso deste módulo

Ver `metricas.md`. Resumo:
- % SLAs cumpridos no período ≥ 95%
- Tempo médio de detecção de risco de estouro ≤ 30min antes
- 100% das penalidades/bonificações aplicadas via evento (zero manual)

## 8. NFR

- **Performance:** cronômetro em tela atualiza < 1s.
- **Disponibilidade:** SLO 99.9% — perda de cronômetro = risco direto de descumprimento.
- **Segurança:** trilha imutável de pausas e ajustes (`SEC-*` WORM).
- **Multi-tenant:** `INV-TENANT-001` em toda query.

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID livre `US-SLA-NNN`.
- US deprecada → marcar `@deprecated` + ADR.
- Mudança em AC implementado → ADR + novo teste.
