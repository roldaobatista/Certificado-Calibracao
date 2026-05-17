---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/rh-frota-qualidade/README.md
  - docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md
  - docs/dominios/rh-frota-qualidade/modulos/qualidade/prd.md
  - docs/governanca/README.md
---

# PRD — Módulo Auditoria Externa e Preparação para Certificações

> Módulo para planejar, preparar e conduzir auditorias **externas** (CGCRE/ISO 17025, ISO 9001, auditorias de cliente, auditorias regulatórias). Diferente de auditoria **interna** (que vive em `docs/governanca/` e cobre auditores Família 5 da plataforma).

---

## 1. O que este módulo é

Sistema que organiza a empresa para receber auditorias externas com previsibilidade: planeja a auditoria, monta checklist por norma, distribui evidências a responsáveis, controla prazos de envio, registra apontamentos do auditor, gera plano de ação e mantém histórico. Inclui simulação ("drill") interna pra testar prontidão antes da auditoria real, e painel de prontidão que mostra ao gestor se a empresa está "pronta hoje" pra ser auditada.

## 2. Por que este módulo existe (problema a resolver)

Empresas que mantêm certificações ISO/IEC 17025, ISO 9001 e similares perdem semanas em cada ciclo de auditoria correndo atrás de evidência espalhada em pastas e emails. Cliente cancelar contrato porque auditoria saiu com não-conformidades graves é risco real. Sem módulo dedicado: planilhas paralelas, evidência desatualizada, responsável esquecido, e o gestor descobre que não estava pronto na véspera. Para o cliente piloto (Balanças Solution) o risco direto é perder a credencial RBC — equivale a perder o negócio.

## 3. Personas

Ver `personas.md` deste módulo + transversais em `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Planejamento da auditoria externa (escopo, norma, organismo auditor, datas, equipe envolvida).
- Checklist por norma (templates pré-carregados: ISO/IEC 17025, ISO 9001, ANVISA, INMETRO, cliente customizado).
- Evidências por requisito (upload + link a documento controlado).
- Responsável por evidência (1 dono claro por requisito).
- Prazo de envio (com lembrete automático).
- Pendências de auditoria (o que falta antes da auditoria real).
- Registro de apontamentos do auditor durante a auditoria (não-conformidades maior/menor, observações, oportunidades de melhoria).
- Plano de ação para cada apontamento (responsável, prazo, evidência de fechamento).
- Histórico de auditorias (todas auditorias passadas com resultado e seguimento).
- Relatório final (do auditor e da empresa).
- Matriz de conformidade (% requisitos atendidos por norma, em tempo real).
- Controle de documentos exigidos (lista de docs que a norma pede, vencidos/válidos).
- Simulação de auditoria (drill interno — auditor interno ou Família 5 simula auditor externo).
- Painel de prontidão para certificação (semáforo verde/amarelo/vermelho por norma).

## 5. Non-goals (o que NÃO está neste módulo)

- **Auditoria interna recorrente** dos processos da plataforma — fica em `docs/governanca/` (auditores Família 5: Segurança, Qualidade, Produto).
- **Geração do certificado RBC** — fica em módulo Calibração (ver `docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md`).
- **Substituir o organismo certificador** — este módulo prepara a empresa, mas o certificado é emitido pelo CGCRE/INMETRO/organismo de terceira parte.
- **Auditoria fiscal/contábil** — não está no escopo (esse fluxo é do módulo Financeiro/Contabilidade).
- **Auditoria de fornecedor** feita pela empresa em terceiros — escopo de outro módulo (Compras/Suprimentos) se houver.

## 6. User Stories

### US-AUD-001: Planejar uma auditoria externa

**Como** responsável da qualidade, **quero** registrar uma auditoria externa programada (norma, organismo, datas, escopo, equipe), **para** organizar o que precisa ser feito antes.

**Critérios de aceite:**
- **AC-AUD-001-1**: GIVEN responsável da qualidade autenticado, WHEN cria uma auditoria, THEN salva norma + organismo + data início/fim + escopo + responsável geral + status (planejada).
- **AC-AUD-001-2**: GIVEN auditoria criada, WHEN sistema carrega template de checklist da norma, THEN copia todos requisitos pré-cadastrados pra essa auditoria.

**Invariantes:** `INV-TENANT-001`.

**Dependências:**
- Bloqueado por: cadastro de templates de norma (US-AUD-002 ou seed inicial).

---

### US-AUD-002: Carregar checklist por norma

**Como** sistema, **quero** ter templates de checklist por norma (ISO 17025, ISO 9001, etc.), **para** que o responsável não tenha que digitar do zero a cada auditoria.

**Critérios de aceite:**
- **AC-AUD-002-1**: GIVEN responsável seleciona norma "ISO/IEC 17025:2017", WHEN cria auditoria, THEN sistema carrega todos requisitos da norma (cláusulas 4-8) com descrição em PT-BR.
- **AC-AUD-002-2**: GIVEN responsável quer adicionar requisito customizado (ex: exigência de cliente), WHEN edita o checklist, THEN permite incluir requisito ad-hoc com origem "customizado".

**Dependências:** seed inicial das normas (curado por especialista — consultor RBC/agente).

---

### US-AUD-003: Atribuir responsável e prazo por evidência

**Como** responsável da qualidade, **quero** designar quem produz cada evidência e até quando, **para** que ninguém esqueça.

**Critérios de aceite:**
- **AC-AUD-003-1**: GIVEN checklist carregado, WHEN responsável atribui pessoa X ao requisito Y com prazo Z, THEN pessoa X recebe notificação + tarefa.
- **AC-AUD-003-2**: GIVEN prazo se aproxima (3 dias antes), WHEN responsável ainda não anexou evidência, THEN sistema dispara lembrete.

---

### US-AUD-004: Anexar evidências por requisito

**Como** responsável da evidência, **quero** anexar documentos/registros que comprovam atendimento ao requisito, **para** que a auditoria tenha o que examinar.

**Critérios de aceite:**
- **AC-AUD-004-1**: GIVEN requisito atribuído a mim, WHEN anexo arquivo ou link a documento controlado, THEN evidência fica vinculada ao requisito com timestamp + autor + versão.
- **AC-AUD-004-2**: GIVEN documento controlado foi atualizado, WHEN evidência aponta pra versão antiga, THEN sistema sinaliza "evidência desatualizada".

**Invariantes:** evidência imutável após auditoria fechada (`INV-NNN`).

---

### US-AUD-005: Acompanhar pendências antes da auditoria

**Como** responsável da qualidade, **quero** painel de pendências (% checklist completo, evidências faltantes, atrasadas), **para** saber se vou estar pronto na data.

**Critérios de aceite:**
- **AC-AUD-005-1**: GIVEN auditoria planejada, WHEN abro painel, THEN vejo % completo, lista de pendências por responsável, prazos atrasados em vermelho.
- **AC-AUD-005-2**: GIVEN ≤7 dias para auditoria e <90% completo, WHEN sistema avalia, THEN dispara alerta P1 ao responsável geral + diretoria.

---

### US-AUD-006: Registrar apontamentos do auditor durante a auditoria

**Como** responsável da qualidade, **quero** registrar em tempo real (no app/web) o que o auditor apontou (não-conformidades maior/menor, observações, oportunidades), **para** ter base do plano de ação.

**Critérios de aceite:**
- **AC-AUD-006-1**: GIVEN auditoria em andamento, WHEN registro apontamento, THEN salva tipo (NC maior|NC menor|observação|oportunidade) + descrição + requisito vinculado + evidência apresentada + foto opcional.
- **AC-AUD-006-2**: GIVEN apontamento registrado, WHEN auditoria fecha, THEN gera lista consolidada exportável.

---

### US-AUD-007: Plano de ação para cada apontamento

**Como** responsável de processo, **quero** criar plano de ação para cada não-conformidade (causa raiz, ação corretiva, responsável, prazo, evidência de fechamento), **para** que o organismo verifique no follow-up.

**Critérios de aceite:**
- **AC-AUD-007-1**: GIVEN apontamento de NC registrado, WHEN crio plano, THEN registra análise de causa raiz (método 5-porquês obrigatório p/ NC maior), ação corretiva, responsável, prazo.
- **AC-AUD-007-2**: GIVEN plano com prazo vencido sem evidência de fechamento, WHEN sistema avalia, THEN alerta P0 (NC maior) ou P1 (NC menor).
- **AC-AUD-007-3**: GIVEN evidência de fechamento anexada, WHEN responsável da qualidade aprova, THEN NC é marcada como "fechada" com data e quem aprovou.

---

### US-AUD-008: Histórico de auditorias

**Como** responsável da qualidade, **quero** consultar todas auditorias passadas (ano, norma, organismo, apontamentos, status atual do plano), **para** mostrar evolução ao auditor da próxima ronda.

**Critérios de aceite:**
- **AC-AUD-008-1**: GIVEN >0 auditorias passadas, WHEN abro histórico, THEN listo ordenado por data com indicadores (qtd NC maior, menor, % fechadas).
- **AC-AUD-008-2**: GIVEN seleciono auditoria passada, WHEN abro detalhe, THEN vejo checklist, apontamentos, planos de ação e fechamentos.

---

### US-AUD-009: Relatório final da auditoria

**Como** responsável da qualidade, **quero** gerar relatório final (PDF) com escopo, checklist, apontamentos, planos de ação, **para** entregar à diretoria e arquivar.

**Critérios de aceite:**
- **AC-AUD-009-1**: GIVEN auditoria com status "concluída", WHEN gero relatório, THEN PDF com cabeçalho da norma + cronograma + apontamentos + planos + anexos.

---

### US-AUD-010: Matriz de conformidade

**Como** responsável da qualidade, **quero** ver matriz % de conformidade por norma (em tempo real, baseada em evidências válidas), **para** saber onde estamos sem esperar a auditoria.

**Critérios de aceite:**
- **AC-AUD-010-1**: GIVEN dados das auditorias e evidências válidas, WHEN abro matriz, THEN mostra cláusula/requisito → status (atendido|parcial|não atendido|não avaliado) com cor.
- **AC-AUD-010-2**: GIVEN clico em requisito, WHEN aprofundo, THEN vejo última evidência, validade, responsável.

---

### US-AUD-011: Controle de documentos exigidos

**Como** responsável da qualidade, **quero** lista dos documentos que cada norma exige (procedimentos, instruções, registros) com status (vigente/vencido/em revisão), **para** garantir que não há documento desatualizado quando auditor pedir.

**Critérios de aceite:**
- **AC-AUD-011-1**: GIVEN norma cadastrada, WHEN abro lista de docs exigidos, THEN vejo status de cada um e responsável.
- **AC-AUD-011-2**: GIVEN documento vencido, WHEN sistema avalia, THEN alerta amarelo no painel de prontidão + notifica responsável.

---

### US-AUD-012: Simulação de auditoria (drill)

**Como** responsável da qualidade, **quero** rodar uma simulação interna (auditor interno ou agente Família 5) usando checklist da norma, **para** descobrir lacunas antes do auditor externo.

**Critérios de aceite:**
- **AC-AUD-012-1**: GIVEN auditoria planejada, WHEN crio drill, THEN sistema cria cópia do checklist marcada como "simulação" e atribui ao auditor interno/agente.
- **AC-AUD-012-2**: GIVEN drill concluído, WHEN comparo com checklist real, THEN gera "gap report" com requisitos em risco.

**Dependências:** integração com auditores Família 5 (`docs/governanca/catalogo-auditores.md`).

---

### US-AUD-013: Painel de prontidão para certificação

**Como** diretor/Roldão, **quero** painel único (semáforo) que diz se a empresa está pronta hoje para receber qualquer auditoria mapeada, **para** decidir se aceito visita surpresa do cliente.

**Critérios de aceite:**
- **AC-AUD-013-1**: GIVEN normas ativas (ISO 17025, ISO 9001, etc.), WHEN abro painel, THEN vejo card por norma: % conformidade, qtd NCs abertas, docs vencidos, próxima auditoria agendada.
- **AC-AUD-013-2**: GIVEN qualquer norma com semáforo vermelho, WHEN sistema avalia, THEN exibe top-3 ações prioritárias.

---

## 7. Métricas de sucesso deste módulo

Ver `metricas.md`. Resumo:
- % auditorias externas concluídas sem NC maior = ≥80%
- Tempo médio fechamento de NC menor = ≤30 dias
- % docs exigidos vigentes = 100%

## 8. NFR (Requisitos Não-Funcionais)

- **Performance:** painel de prontidão carrega em ≤2s.
- **Disponibilidade:** SLO ver `../../../operacao/observabilidade.md`.
- **Segurança:** SEC-NNN (controle de acesso — só perfis com permissão veem apontamentos confidenciais).
- **Acessibilidade:** WCAG 2.1 AA.
- **Retenção:** registros de auditoria ≥ 8 anos (ISO 17025 cláusula 8.4 + LGPD); ver `../../../conformidade/comum/retencao-matriz.md`.

## 9. Glossário

Ver `glossario.md` deste módulo.

## 10. Como este PRD evolui

- US nova → próximo ID livre (`US-AUD-NNN`).
- US deprecada → `@deprecated` + ADR.
- Mudança em AC já implementado → ADR + novo teste.
