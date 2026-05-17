---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: garantia
dominio: operacao
---

# Contratos de UI — Módulo Garantia

> Telas + comportamento. Wireframe textual enquanto stack candidata (Django+HTMX / Flutter — ADR-0001).

---

## Telas

### Tela 1: Cadastro de Prazos de Garantia

**Propósito:** definir prazo por tipo de item.
**Persona:** P-GAR-03 Gerente.
**US:** `US-GAR-001`.
**Acessível por:** menu Operação → Garantia → Prazos.

**Elementos:**
- Lista de prazos vigentes (tipo, prazo_dias, vigente_de)
- Botão "Novo prazo" → modal (tipo, prazo_dias)
- Coluna "Histórico" → drill-down em versões anteriores

**Estados:** vazio (nenhum prazo) → CTA destacado; erro de validação inline.
**A11y:** WCAG AA (`INV-016`); navegação por teclado obrigatória.
**Mobile:** responsivo (uso raro).

---

### Tela 2: Abrir OS-filha em Garantia

**Propósito:** atendente abre OS-filha vinculada à OS-mãe.
**Persona:** P-GAR-01 Atendente.
**US:** `US-GAR-002`.
**Acessível por:** botão "Abrir em garantia" dentro da tela da OS-mãe; também por busca direta (número OS / cliente).

**Elementos:**
- Busca de OS-mãe (autocomplete por número, cliente, serial equipamento)
- Card "Status da garantia" — verde "DENTRO DO PRAZO" / vermelho "FORA DO PRAZO" / amarelo "PRAZO EXPIRA EM X DIAS"
- Tipo da garantia (radio): SERVIÇO / PEÇA / EQUIPAMENTO
- Campo motivo (obrigatório, ≥ 30 caracteres)
- Botão "Abrir OS em garantia" (desabilitado se fora do prazo, a menos que gerente aprove)

**Estados:** "fora do prazo" → exige aprovação de gerente em-tela; sucesso → redireciona pra OS-filha criada.

---

### Tela 3: Análise da Garantia (Laudo)

**Propósito:** técnico/metrologista registra decisão.
**Persona:** P-GAR-02 Técnico.
**US:** `US-GAR-003`.
**Acessível por:** OS-filha em garantia → aba "Análise".

**Elementos:**
- Resumo OS-mãe + OS-filha lado a lado
- Decisão (radio): PROCEDENTE / IMPROCEDENTE / PARCIAL
- Se PARCIAL → slider "parcela cobrável %" 0–100
- Causa raiz (select padronizado)
- Texto livre do laudo
- Upload de anexos (foto, vídeo, PDF)
- Botão "Assinar e fechar análise" — após assinar fica imutável (`INV-001`)

**Estados:** rascunho salvo automaticamente; após assinar não permite editar; toast confirma evento `Garantia.Analisada`.
**Mobile:** app do técnico permite preencher offline (sync ao voltar — herda padrão OS).

---

### Tela 4: Cobrança Bloqueada (visão Financeiro)

**Propósito:** financeiro vê a flag e pode pedir desbloqueio.
**Persona:** P-GAR-03 Gerente + financeiro (transversal).
**US:** `US-GAR-005`.
**Acessível por:** módulo Financeiro → tentativa de emitir NF em OS bloqueada.

**Elementos:**
- Banner vermelho "OS em garantia procedente — cobrança bloqueada"
- Botão "Solicitar desbloqueio" → modal com motivo + aprovação de gerente
- Histórico de tentativas e desbloqueios

---

### Tela 5: Garantia do Fornecedor

**Propósito:** comprador acompanha envio e retorno.
**Persona:** P-GAR-04 Comprador.
**US:** `US-GAR-006`.
**Acessível por:** menu Compras → Garantia-Fornecedor.

**Elementos:**
- Lista filtrável por status (ENVIADA, RETORNADA, EXPIRADA)
- Card por item: fornecedor, peça, nota remessa, prazo de retorno, dias até vencer
- Botão "Registrar retorno" → modal com valor ressarcido
- Alerta visual em itens com prazo vencido

---

### Tela 6: Dashboard de Reincidência

**Propósito:** gerente vê top reincidentes.
**Persona:** P-GAR-03 Gerente.
**US:** `US-GAR-007`.
**Acessível por:** menu Operação → Garantia → Reincidência.

**Elementos:**
- 4 abas: Cliente / Técnico / Peça-modelo / Equipamento-serial
- Tabela top 20 com qtd_procedentes_6m
- Drill-down → lista de OS-fonte
- Filtro por janela (3m, 6m, 12m)

---

## Componentes reutilizáveis

Cards de OS, busca autocompletar e modal de assinatura ficam em `../../../comum/contratos/ui.md`.

## Como evolui

Tela nova → adicionar + ligar a US-NNN. Mudança em UX → bump CHANGELOG.
