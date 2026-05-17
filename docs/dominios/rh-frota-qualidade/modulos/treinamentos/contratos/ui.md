---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
modulo: treinamentos
---

# Contratos de UI — Módulo Treinamentos e Certificações Internas

> Telas + comportamento. Wireframe textual enquanto ADR-0001 não está finalizada.

---

## Telas

### Tela 1: Painel Treinamentos
**Propósito:** visão geral (próximos eventos, certificados vencendo, lacunas de trilha).
**Persona principal:** Gerente RH / Qualidade.
**US:** `US-TRE-006`, `US-TRE-008`.

**Elementos:**
- Cards: nº eventos próximos 30d, certificados vencendo 30/60/90d, colaboradores com trilha incompleta.
- Lista resumida de alertas com link para detalhe.
- Botões "Novo treinamento", "Programar evento".

---

### Tela 2: Catálogo de Treinamentos
**Propósito:** CRUD do catálogo.
**US:** `US-TRE-001`.

**Elementos:**
- Tabela: nome, categoria, sub-categoria, carga horária, validade padrão, status.
- Form de novo: nome, categoria (dropdown), sub-categoria, carga horária, validade padrão (meses), descrição.

---

### Tela 3: Programação de Evento (turma)
**Propósito:** criar evento a partir de treinamento.
**US:** `US-TRE-002`.

**Elementos:**
- Seleção treinamento (autocomplete catálogo).
- Data início/fim, local.
- Facilitador (interno colaborador OU externo texto+CPF/CNPJ).
- Participantes (multi-select colaboradores).
- Material anexo (upload múltiplo).

---

### Tela 4: Execução de Evento (presença + nota)
**Propósito:** registrar presença e nota dos participantes.
**Persona:** Facilitador.
**US:** `US-TRE-003`.

**Elementos:**
- Lista participantes com checkbox presença + campo nota (se prova).
- Botão "Concluir evento" (libera emissão de certificados).

---

### Tela 5: Emissão de Certificados (em lote)
**Propósito:** emitir certificados após evento concluído.
**US:** `US-TRE-004`.

**Elementos:**
- Lista aprovados; checkbox por participante.
- Preview PDF do certificado.
- Botão "Emitir selecionados".

---

### Tela 6: Trilhas de Capacitação
**Propósito:** configurar trilha por escopo.
**US:** `US-TRE-005`.

**Elementos:**
- Seletor escopo (função / cargo / equipamento / norma).
- Lista treinamentos da trilha + flag obrigatório/opcional.
- Botão "Nova versão" (versionamento — colaboradores antigos ficam na versão anterior até renovação).

---

### Tela 7: Matriz de Competência
**Propósito:** visão consolidada colaboradores × habilidades.
**US:** `US-TRE-006`.

**Elementos:**
- Tabela colaboradores (linha) × habilidades (colunas).
- Célula colorida: verde (válido) / amarelo (a vencer ≤30d) / vermelho (vencido) / cinza (inexistente).
- Filtros: função, departamento, equipamento, norma.
- Botões export PDF e XLSX.

**Estados:**
- Vazio: "Cadastre trilhas para visualizar".
- Carregando: skeleton.

---

### Tela 8: Histórico de Capacitação do Colaborador
**Propósito:** linha do tempo de um colaborador.
**US:** `US-TRE-009`.

**Elementos:**
- Cabeçalho com dados colaborador.
- Timeline cronológica.
- Filtro status (válido / vencido / todos).
- Botão export "Currículo interno".

---

### Tela 9: Bypass de Bloqueio
**Propósito:** liberação excepcional.
**US:** `US-TRE-007` (AC-3).

**Elementos:**
- Form: colaborador, escopo, justificativa (obrigatória, mínimo 50 chars), data validade (≤30 dias).
- Aprovador (gerente Qualidade) recebe notificação.
- Banner vermelho: "Esta ação fica registrada em audit; auditor CGCRE pode questionar".

---

### Tela 10: Reciclagem Programada
**Propósito:** auto-programar reciclagem antes do vencimento.
**US:** `US-TRE-010`.

**Elementos:**
- Lista certificados vencendo + sugestão de evento de reciclagem (auto-populado com turma anterior).
- Botão "Confirmar programação".

---

## Componentes reutilizáveis

- **MatrizColorida** — usado também em `qualidade/` (matriz de não-conformidade × cliente).
- **TimelineCronologica** — usado em `colaboradores/`.
- **AssinaturaTouch** — compartilhado com SST.

Componentes em `../../../comum/contratos/ui.md`.

## Acessibilidade

- WCAG 2.1 AA (`INV-016`).
- Matriz colorida tem alternativa textual + ícone (não depender só de cor).

## Como esta lista evolui

- Tela nova → ligar a US-TRE-NNN + bump CHANGELOG.
