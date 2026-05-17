---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo Despesas

> Telas do módulo. Wireframe textual até stack decidida.

---

## Tela 1: Lançar despesa

**Propósito:** registrar nova despesa com comprovante.
**Persona principal:** Colaborador solicitante (`../personas.md`).
**US relacionadas:** `US-DSP-001`, `US-DSP-004`.
**Acessível por:** botão "Nova despesa" na home do app mobile + menu Financeiro → Despesas → Nova.

**Elementos:**
- Campo data (default hoje).
- Campo valor (R$).
- Selector categoria (lista de `CategoriaDespesa` ativas do tenant).
- Campo descrição (texto livre, 240 chars).
- Botão "Anexar comprovante" (câmera + galeria + arquivo).
- Selector opcional OS (autocomplete pelas OS abertas do colaborador).
- Selector opcional viagem.
- Selector opcional centro de custo.
- Checkbox "Compensar adiantamento existente" (visível se houver adiantamento aberto no caixa do técnico).
- Botão "Salvar rascunho" + "Enviar para aprovação".

**Estados:**
- Vazio: formulário em branco com data preenchida.
- Carregando upload do comprovante: barra de progresso.
- Erro upload: mensagem "Não foi possível anexar. Tente outra foto."
- Validação: bloqueia envio sem comprovante.
- Sucesso: toast "Despesa enviada para aprovação. Você será avisado."

**Acessibilidade:** WCAG AA; navegação por teclado obrigatória; labels nos campos.

**Mobile:** prioritário (técnico/vendedor em campo). Câmera direta.

---

## Tela 2: Lista de despesas

**Propósito:** consultar despesas com filtros.
**Persona:** Colaborador, aprovador ou financeiro.
**US:** `US-DSP-005`.

**Elementos:**
- Filtros: período, status, categoria, colaborador (somente para aprovador/financeiro), OS, centro de custo.
- Colunas: data, valor, categoria, vínculo (OS/viagem/técnico), status, aprovador atual.
- Ações por linha: "Ver detalhes", "Aprovar/Rejeitar" (se papel permite), "Cancelar" (se rascunho).
- Botão "Exportar CSV/PDF".

**Estados:**
- Vazio: "Você não tem despesas no período selecionado."
- Carregando: skeleton.
- Erro: mensagem PT com botão "Tentar de novo".

---

## Tela 3: Detalhe da despesa

**Propósito:** revisar despesa, ver comprovante, histórico de aprovação.
**US:** `US-DSP-002`, `US-DSP-005`.

**Elementos:**
- Cabeçalho com status colorido.
- Bloco "Dados": data, valor, categoria, descrição, vínculos.
- Visualizador do comprovante (zoom + download).
- Timeline de aprovações: quem, quando, decisão, motivo.
- Botões "Aprovar" / "Rejeitar com motivo" (se aprovador dentro da alçada).
- Botão "Compensar com adiantamento" / "Gerar reembolso" (se financeiro).

---

## Tela 4: Fila de aprovação

**Propósito:** aprovador vê despesas que esperam decisão dele.
**Persona:** Aprovador.
**US:** `US-DSP-002`.

**Elementos:**
- Lista filtrada por "aguardando minha aprovação".
- Resumo no topo: total pendente, total em valor.
- Ações em lote: aprovar selecionadas (se todas dentro da alçada).

---

## Componentes reutilizáveis

- Visualizador de comprovante → também usado em `contas-pagar/`.
- Selector de OS → componente comum.

Ver `../../../comum/contratos/ui.md`.

## Como esta lista evolui

- Tela nova → ligar a `US-DSP-NNN`.
- Mudança UX → bump CHANGELOG.
- Tela `@deprecated` → janela de migração.
