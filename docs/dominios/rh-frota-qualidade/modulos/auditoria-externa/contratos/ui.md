---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md
---

# Contratos de UI — Módulo Auditoria Externa

> Telas web + mobile (registro de apontamento em tempo real). Wireframe textual.

---

## Telas

### Tela 1: Painel de Prontidão
**Propósito:** semáforo por norma ativa — visão de 30s para o diretor.
**Persona principal:** Diretor + RQ.
**US relacionadas:** `US-AUD-013`.
**Acessível por:** menu principal "Auditorias" → primeira aba.

**Elementos:**
- Cards por norma (ISO 17025, ISO 9001, etc.): semáforo verde/amarelo/vermelho, % conformidade, qtd NCs abertas, próxima auditoria.
- Top-3 ações prioritárias (se qualquer norma vermelha).
- Botão "Ver detalhe" por card → navega pra matriz de conformidade.

**Estados:**
- Vazio (nenhuma norma cadastrada): "Cadastre uma norma para começar."
- Carregando: skeleton de 3 cards.
- Erro: "Falha ao calcular prontidão. Tentando novamente..."

**Acessibilidade:** AA. Semáforo NUNCA só por cor — sempre texto "Pronto / Atenção / Crítico" junto.
**Mobile:** responsivo.

---

### Tela 2: Lista de Auditorias
**Propósito:** ver todas auditorias passadas/atuais/futuras.
**US:** `US-AUD-001`, `US-AUD-008`.

**Elementos:**
- Tabela: data, norma, organismo, status, NCs abertas, ações.
- Filtros: status, norma, ano.
- Botão "Nova auditoria".

---

### Tela 3: Detalhe da Auditoria
**Propósito:** centro de comando da auditoria.
**US:** `US-AUD-001`–`US-AUD-007`, `US-AUD-009`.

**Elementos:**
- Header: norma, organismo, datas, escopo, responsável geral, status.
- Abas: Checklist | Apontamentos | Planos de Ação | Drills | Relatório.
- Indicadores topo: % checklist completo, qtd NCs (por tipo), próximo prazo pendente.

---

### Tela 4: Checklist (aba)
**Propósito:** lista de requisitos com status e ações.
**US:** `US-AUD-002`–`US-AUD-005`.

**Elementos:**
- Tabela: cláusula, descrição (resumida), responsável, prazo, status, ação.
- Filtros: status, responsável, criticidade, atrasados.
- Ação por linha: "Anexar evidência" | "Marcar não aplicável" | "Reatribuir".
- Barra de progresso global.

**Estados:**
- Linha em vermelho: prazo vencido.
- Linha em amarelo: prazo ≤3 dias.

---

### Tela 5: Anexar Evidência
**Propósito:** vincular documento/registro a requisito.
**US:** `US-AUD-004`.

**Elementos:**
- Tipo (arquivo/link doc controlado/registro do sistema).
- Upload OU seletor de doc controlado (busca por título) OU referência (ex: nº calibração).
- Campo observação.
- Botão "Anexar".

---

### Tela 6: Registrar Apontamento (mobile + web)
**Propósito:** capturar NC/observação em tempo real durante auditoria.
**US:** `US-AUD-006`.

**Elementos:**
- Tipo (NC maior / NC menor / Observação / Oportunidade).
- Requisito vinculado (busca rápida por cláusula).
- Descrição (texto).
- Evidência apresentada (seletor de evidência já anexada).
- Foto opcional (mobile: câmera).
- Botão "Registrar".

---

### Tela 7: Plano de Ação
**Propósito:** detalhe de plano com causa raiz + ação corretiva.
**US:** `US-AUD-007`.

**Elementos:**
- Apontamento vinculado (read-only).
- Bloco causa raiz: método (5-porquês obrigatório se NC maior — wizard com 5 campos), causa primária.
- Bloco ação corretiva: descrição, responsável, prazo.
- Bloco ação preventiva (opcional).
- Lista de evidências de fechamento + botão "Anexar".
- Botão "Solicitar aprovação" (vai pra RQ).

**Estados:**
- 5-porquês incompleto + NC maior: bloqueia salvar.

---

### Tela 8: Matriz de Conformidade
**Propósito:** visão cláusula × status, tempo real.
**US:** `US-AUD-010`.

**Elementos:**
- Tabela: cláusula | requisito | status (atendido/parcial/não atendido/não avaliado) | última evidência | responsável.
- Filtros: status, criticidade.
- Botão "Aprofundar" por linha → mostra evidências e histórico.

---

### Tela 9: Documentos Exigidos
**Propósito:** lista do que cada norma pede.
**US:** `US-AUD-011`.

**Elementos:**
- Tabela: norma, cláusula, doc exigido, doc controlado vinculado, vencimento, status, responsável.
- Alerta visual: vencidos em vermelho, próximos a vencer em amarelo.

---

### Tela 10: Drill (Simulação)
**Propósito:** rodar e revisar drill.
**US:** `US-AUD-012`.

**Elementos:**
- Botão "Criar drill" (escolhe auditor: pessoa ou agente Família 5).
- Lista de drills (data, auditor, qtd gaps).
- Detalhe do drill: gap report + comparação com auditoria real.

---

### Tela 11: Relatório Final
**Propósito:** gerar e baixar PDF.
**US:** `US-AUD-009`.

**Elementos:**
- Preview do PDF.
- Botão "Gerar/Atualizar".
- Botão "Baixar PDF".

---

### Tela 12: Histórico de Auditorias
**Propósito:** série temporal de todas auditorias passadas.
**US:** `US-AUD-008`.

**Elementos:**
- Linha do tempo + gráfico de evolução (qtd NC maior/menor por auditoria).
- Tabela detalhada.

---

## Componentes reutilizáveis

- Componente "Semáforo de prontidão" — usado em painel, lista de normas.
- Componente "Card de NC" — usado em painel, plano de ação, histórico.
- Componente "Upload de evidência" — reutilizável com módulo Qualidade.
- Compartilhados em `../../../comum/contratos/ui.md`.

## Como esta lista evolui

- Tela nova → adicionar + ligar US-NNN.
- Mudança UX → bump CHANGELOG.
- Tela `@deprecated` → janela de migração.
