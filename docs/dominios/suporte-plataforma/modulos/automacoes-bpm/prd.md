---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/suporte-plataforma/README.md
  - docs/adr/0005-engine-automacoes.md
  - docs/adr/0006-feature-flags.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
---

# PRD — Módulo Automações & BPM

> Camada de UI e governança do motor decisório do Aferê. O backend de execução (engine de automações) é decisão de ADR-0005; este módulo entrega o **editor visual**, o **catálogo de eventos/condições/ações pré-aprovadas**, o **painel de pendências de aprovação** e a **observabilidade** dos fluxos.

---

## 1. O que este módulo é

Centro de configuração e operação de **fluxos de trabalho (BPM)**, **regras automáticas por evento** e **alertas** transversais ao ERP. Permite que empresas-tenant desenhem aprovações por alçada, automatizem geração de tarefas/OS recorrentes/cobranças, configurem escalonamento por SLA e centralizem envio de notificações (e-mail, WhatsApp, SMS) sem código.

Faz a ponte entre o motor decisório (ADR-0005) e os módulos de negócio (CRM, Financeiro, Orçamentos, Chamados, OS, Calibração, Contratos, Estoque, Fiscal, Frota) via catálogo de eventos publicados (ver `../../../comum/integracoes-inter-modulos.md`).

## 2. Por que este módulo existe

Sem este módulo, cada regra de aprovação ou alerta vira código fixo dentro do seu módulo de origem — gerando duplicação, regras conflitantes entre empresas-tenant e impossibilidade de auditar quem aprovou o quê e quando. O módulo resolve a dor de **flexibilidade por tenant** (cada empresa tem políticas diferentes de alçada) e a dor de **rastreabilidade de decisão** (quem aprovou, em que etapa, com qual SLA, sob qual condição).

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Editor visual de fluxos (etapas, transições, condições, alçadas).
- Editor de regras automáticas por evento (gatilho + condição + ação).
- Catálogo de **eventos publicados** disponíveis (origem: módulos de negócio).
- Catálogo de **condições pré-aprovadas** (por valor, cliente, tipo de serviço, risco, unidade, segmento).
- Catálogo de **ações pré-aprovadas** (enviar e-mail/WhatsApp/SMS, gerar tarefa, gerar OS recorrente, gerar cobrança, bloquear transição, escalonar).
- Aprovação em múltiplos níveis com alçada por valor / categoria / tenant.
- Delegação de aprovação e substituto temporário (período de ausência).
- Painel de pendências de aprovação (por aprovador, por etapa, por SLA estourado).
- Configuração de **SLA por etapa** e regras de **escalonamento automático**.
- Configuração e operação de **alertas** (vencimento, SLA, estoque mínimo, financeiro, fiscal, contrato, calibração, manutenção de frota).
- **Logs de execução** de cada fluxo/regra (entrada, condição avaliada, ação executada, resultado).
- **Reprocessamento de falhas** (re-disparar ação que falhou, com diff de payload).
- Histórico imutável de fluxo (quem aprovou, quando, qual versão da regra estava ativa).
- Versionamento de fluxos/regras (mudança gera nova versão; instâncias em execução continuam na versão antiga).

## 5. Non-goals (o que NÃO está neste módulo)

- **Não** executa as ações — só configura e observa. A execução fica no motor decisório (ADR-0005).
- **Não** substitui regras de negócio intrínsecas ao domínio (ex: cálculo de incerteza de medição em Calibração continua no módulo de Calibração; este módulo só dispara o aviso de "incerteza fora do range").
- **Não** é orquestrador de microserviços (ex: Camunda/Temporal). É um BPM de aprovações de negócio, não de transações distribuídas.
- **Não** decide alçadas por si — quem cadastra a alçada é o tenant.
- **Não** cuida do canal de envio (gateway WhatsApp, SMTP, gateway SMS) — só dispara para o módulo de Integrações Externas.
- **Não** é módulo de Gestão de Projetos (Gantt, marcos, BOM) — esse é módulo separado.

## 6. User Stories

### US-BPM-001: Criar fluxo de aprovação de orçamento com desconto alto

**Como** gestor comercial, **quero** desenhar visualmente um fluxo "orçamento com desconto > 15% precisa aprovação de gerente; > 30% precisa diretoria", **para** evitar regra fixa no código e adaptar conforme alçada da minha empresa.

**Critérios de aceite:**
- **AC-BPM-001-1**: GIVEN editor visual aberto, WHEN arrastar etapa "Aprovação Gerente" e definir condição `desconto > 15%`, THEN salvar gera versão nova do fluxo sem afetar instâncias em execução.
- **AC-BPM-001-2**: GIVEN fluxo publicado, WHEN orçamento com 20% de desconto é submetido, THEN sistema cria pendência para grupo "Gerentes Comerciais" e envia notificação.
- **AC-BPM-001-3**: GIVEN aprovação concedida, WHEN aprovador clica "Aprovar", THEN evento `BPM.AprovacaoConcedida` é publicado, orçamento muda de status, log imutável registra (quem, quando, IP, versão do fluxo, condição que disparou).

**Non-goals desta story:** lógica de cálculo do desconto (fica em Orçamentos); envio do PDF do orçamento ao cliente (fica em CRM).

**Invariantes relacionadas:** `INV-NNN` (auditoria imutável), `INV-TENANT-NNN` (fluxo só acessível ao tenant dono).

**Dependências:**
- Bloqueia: US-BPM-002, US-BPM-003.
- Bloqueado por: ADR-0005 (engine), ADR-0007 (camada de domínio).

---

### US-BPM-002: Configurar alerta de calibração vencendo

**Como** responsável técnico de laboratório, **quero** receber alerta 30 dias antes do vencimento de cada certificado de calibração emitido para meus clientes, **para** acionar contato comercial e renovar o serviço.

**Critérios de aceite:**
- **AC-BPM-002-1**: GIVEN catálogo de eventos do módulo Calibração inclui `Calibracao.CertificadoEmitido`, WHEN cadastrar alerta tipo "vencimento" com offset -30 dias, THEN sistema agenda envio para `data_vencimento - 30d`.
- **AC-BPM-002-2**: GIVEN data alvo atingida, WHEN alerta dispara, THEN sistema envia e-mail + WhatsApp ao contato comercial vinculado ao cliente e gera tarefa em CRM.
- **AC-BPM-002-3**: GIVEN falha de envio (gateway WhatsApp fora), WHEN reprocessamento manual ou automático, THEN log mostra diff de tentativas e horário de cada uma.

**Non-goals:** envio físico via gateway (Integrações Externas); geração do orçamento de renovação (Orçamentos).

**Invariantes:** `INV-NNN` (log de execução obrigatório).

---

### US-BPM-003: Delegar aprovação durante férias

**Como** aprovador, **quero** cadastrar substituto temporário para o período X-Y, **para** que pendências cheguem nele e SLA não seja estourado.

**Critérios de aceite:**
- **AC-BPM-003-1**: GIVEN cadastro de delegação ativo, WHEN nova pendência chega ao aprovador titular durante o período, THEN sistema roteia automaticamente ao substituto e registra delegação no log.
- **AC-BPM-003-2**: GIVEN delegação expirada, WHEN nova pendência chega, THEN volta a rotear ao titular.

**Non-goals:** integração com agenda corporativa (fica em Agenda); aprovação por substituto sem cadastro de delegação (não permitido).

---

### US-BPM-004: Reprocessar regra que falhou

**Como** operador de suporte, **quero** ver lista de execuções falhadas e re-disparar individualmente ou em lote, **para** corrigir efeito de gateway temporariamente indisponível.

**Critérios de aceite:**
- **AC-BPM-004-1**: GIVEN tela "Execuções", WHEN filtrar por status "FALHA", THEN lista paginada com motivo do erro + payload original.
- **AC-BPM-004-2**: GIVEN execução selecionada, WHEN clicar "Reprocessar", THEN sistema cria nova tentativa preservando payload original e regista link entre tentativa nova e original.

---

### US-BPM-005: Painel consolidado de pendências por aprovador

**Como** aprovador, **quero** ver todas as minhas pendências (de qualquer fluxo) em um painel único com SLA restante, **para** priorizar e não estourar prazo.

**Critérios de aceite:**
- **AC-BPM-005-1**: GIVEN painel aberto, WHEN logado, THEN lista filtrada por mim com ordenação por SLA crescente; cor indica risco (verde > 50% restante, amarelo 20-50%, vermelho < 20%).
- **AC-BPM-005-2**: GIVEN SLA estourado, WHEN evento de escalonamento configurado, THEN sistema notifica gestor (ou nível superior na alçada) e mantém pendência ativa para o aprovador.

---

### US-BPM-006: Geração automática de OS recorrente

**Como** gestor de contratos, **quero** que contratos com cláusula de "manutenção mensal" gerem OS automaticamente todo dia 1º, **para** não depender de operador lembrar.

**Critérios de aceite:**
- **AC-BPM-006-1**: GIVEN regra cadastrada com gatilho temporal "todo dia 1º", WHEN data atingida, THEN sistema chama serviço do módulo OS via comando `criarOS` com dados do contrato.
- **AC-BPM-006-2**: GIVEN OS criada, WHEN evento `OS.Criada` retorna, THEN log de execução registra ID da OS gerada.

---

### US-BPM-007: Catálogo de eventos disponíveis

**Como** configurador de regras, **quero** ver lista pesquisável de todos os eventos que cada módulo publica, com schema do payload, **para** desenhar regras sem ter que perguntar ao agente técnico o que existe.

**Critérios de aceite:**
- **AC-BPM-007-1**: GIVEN catálogo aberto, WHEN filtrar por módulo "Calibração", THEN lista de eventos com nome, descrição em PT-BR, payload exemplo, frequência típica.
- **AC-BPM-007-2**: GIVEN evento descontinuado (`@deprecated`), WHEN apresentar na lista, THEN marcação visual + data de remoção planejada.

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- % de aprovações dentro do SLA configurado = ≥ 95%.
- Taxa de falhas de execução reprocessadas com sucesso = ≥ 90%.
- Tempo médio entre criação de fluxo no editor e primeira execução em produção = ≤ 1 dia (sem código).

## 8. NFR

- **Performance:** avaliação de condição < 100ms p95; render de painel de pendências < 500ms p95.
- **Disponibilidade:** alinhada ao motor (ADR-0005). SLO específico em `metricas.md`.
- **Segurança:** alçadas e delegações respeitam RBAC + tenant isolation (`INV-TENANT-NNN`); log imutável de aprovações (`INV-NNN`).
- **Acessibilidade:** WCAG AA mínimo (a confirmar em ADR de UX).

## 9. Glossário

Ver `glossario.md` deste módulo.

## 10. Como este PRD evolui

- US nova → próximo ID `US-BPM-NNN`.
- Mudança em catálogo de eventos → bump CHANGELOG + comunicação cross-módulos.
- Quebra de contrato de regra publicada → ADR + janela de migração.
