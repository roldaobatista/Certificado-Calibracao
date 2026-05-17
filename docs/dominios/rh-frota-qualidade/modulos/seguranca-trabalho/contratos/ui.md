---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
modulo: seguranca-trabalho
---

# Contratos de UI — Módulo Segurança do Trabalho

> Telas + comportamento esperado. Wireframe textual enquanto stack final (Flutter + HTMX) não está finalizada (ADR-0001 candidata).

---

## Telas

### Tela 1: Painel SST (home do módulo)
**Propósito:** visão geral de alertas (EPIs / ASOs / treinamentos a vencer + acidentes recentes).
**Persona principal:** Gerente / Técnico SST.
**US:** `US-SST-003`, `US-SST-009`.
**Acessível por:** menu principal > Segurança do Trabalho.

**Elementos:**
- Cards: nº EPIs vencidos, ASOs vencidos, treinamentos vencidos, acidentes no mês.
- Lista paginada de alertas: vencido / ≤30d / ≤60d / ≤90d.
- Botão "Novo acidente / quase-acidente".
- Botão "Emitir Permissão de Trabalho".

**Estados:**
- Vazio: "Nenhum alerta — parabéns".
- Carregando: skeleton.
- Erro: "Não foi possível carregar — tentar de novo".

**WCAG:** AA (`INV-016`).
**Mobile:** responsivo.

---

### Tela 2: Cadastro de EPI
**Propósito:** CRUD de EPIs.
**US:** `US-SST-001`.

**Elementos:**
- Form: nome, nº CA, validade CA (date picker), fornecedor, categoria (dropdown), foto (upload).
- Indicador visual: CA válido / vencido.
- Lista de EPIs cadastrados com filtro por categoria + status.

**Validação:** CA obrigatório; data validade obrigatória.

---

### Tela 3: Entrega de EPI (web + mobile)
**Propósito:** registrar entrega ao colaborador com termo assinado.
**US:** `US-SST-002`.

**Elementos:**
- Seleção colaborador (autocomplete).
- Seleção EPI (filtra por CA válido).
- Quantidade, validade individual.
- Preview do termo gerado (PDF).
- Bloco de assinatura touch (mobile) ou código de confirmação por SMS/e-mail (web).

**Estados:**
- Bloqueio: "EPI com CA vencido não pode ser entregue".
- Sucesso: "Termo assinado salvo — link para download".

---

### Tela 4: ASO (lista + cadastro)
**Propósito:** registrar ASO de cada colaborador.
**US:** `US-SST-003`.

**Elementos:**
- Tabela por colaborador: tipo, data, validade, resultado, PDF.
- Form de novo ASO: tipo (dropdown), data, validade, médico, CRM, resultado (apto/inapto/apto-com-restrição), restrições (texto), upload PDF.

**LGPD:** marcado visualmente como "dado sensível — saúde".

---

### Tela 5: Permissão de Trabalho (PT)
**Propósito:** emitir PT vinculada a OS de risco.
**US:** `US-SST-006`.

**Elementos:**
- Seleção OS de risco.
- Tipo PT (altura / confinado / energizado / outro).
- Descrição serviço + medidas de controle.
- Validade até (default fim do turno).
- Bloco assinatura emitente + executante.

---

### Tela 6: APR (Análise Preliminar de Risco)
**Propósito:** preencher APR antes de iniciar OS de risco.
**US:** `US-SST-007`.

**Elementos:**
- Template selecionado conforme tipo de serviço.
- Lista de perguntas configuráveis (perigos, controles, EPIs aplicáveis).
- Assinatura do técnico.

---

### Tela 7: Checklist de segurança pré-OS (mobile)
**Propósito:** técnico preenche em campo antes de iniciar OS.
**US:** `US-SST-005`.

**Elementos:**
- Itens do template (sim/não/N/A).
- Campo de observação.
- Botão "Salvar e iniciar OS" (bloqueado se itens obrigatórios faltam).

**Mobile:** otimizado para uma mão; itens em ≤2 toques.

---

### Tela 8: Registro de acidente / quase-acidente
**Propósito:** registrar evento com evidências.
**US:** `US-SST-008`.

**Elementos:**
- Tipo (radio): acidente / quase-acidente / incidente ambiental.
- Data/hora, local, gravidade.
- Descrição (textarea longa).
- Colaboradores envolvidos (multi-select).
- Upload de fotos (múltiplas).
- Houve afastamento? + dias.
- Ação corretiva (texto + responsável + prazo).

**Imutabilidade:** após confirmação, só adendo é permitido.

---

### Tela 9: Relatório de Segurança
**Propósito:** consolidação por período.
**US:** `US-SST-009`.

**Elementos:**
- Filtro período (mês / trimestre / ano / customizado).
- Cards: TF, TG, nº acidentes, nº quase-acidentes, EPIs entregues, ASOs realizados.
- Botões de export: PDF, XLSX.

---

## Componentes reutilizáveis

- **AssinaturaTouch** — compartilhado com `colaboradores/` (termo geral) e `operacao/` (assinatura cliente em OS).
- **UploadEvidenciaFoto** — compartilhado com `qualidade/`, `operacao/`.

Componentes compartilhados em `../../../comum/contratos/ui.md`.

## Como esta lista evolui

- Tela nova → ligar a US-SST-NNN + bump CHANGELOG.
