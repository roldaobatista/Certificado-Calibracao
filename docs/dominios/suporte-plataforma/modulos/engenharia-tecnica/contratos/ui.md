---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo Engenharia Técnica

> Telas do módulo. Stack final em ADR-0001.

---

## Telas

### Tela 1: Lista de Projetos Técnicos

**Propósito:** ver projetos do tenant, filtrar, criar novo.
**Persona principal:** Engenheiro Projetista.
**US:** `US-ENG-001`.
**Acessível por:** menu "Engenharia > Projetos".

**Elementos:**
- Tabela: código, título, cliente, categoria, revisão corrente, status, atualizado em.
- Filtros: status, cliente, categoria, data, autor.
- Busca por código/título.
- Botão "Novo projeto".

**Estados:** vazio (tenant sem projetos) com CTA; loading skeleton; erro com retry.

**Acessibilidade:** WCAG AA; navegação por teclado; sort por coluna acessível.
**Mobile:** leitura otimizada; criação é desktop.

---

### Tela 2: Detalhe do Projeto Técnico

**Propósito:** ver/editar revisão corrente; navegar histórico de revisões; ver entidades vinculadas.
**Persona principal:** Engenheiro Projetista; consumido também por Auditor.
**US:** `US-ENG-001`, `US-ENG-002`, `US-ENG-008`.

**Elementos:**
- Cabeçalho: código, título, cliente, revisão corrente (letra + status).
- Tabs: Desenhos | BOM | Memorial | Especificações | Cálculos | Anexos | Histórico | Vinculações.
- Lateral direita: timeline de revisões (A, B, C…) com diff entre adjacentes.
- Botões: "Nova revisão", "Submeter para aprovação", "Editar metadados".

**Estados:** revisão aprovada → modo leitura (com aviso "imutável; crie nova revisão pra editar"); rascunho → modo edição; em aprovação → leitura + status "aguardando aprovador X".

---

### Tela 3: Upload de Anexo

**Propósito:** subir arquivo CAD/PDF/imagem com classificação.
**Persona:** Engenheiro Projetista.
**US:** `US-ENG-001`.

**Elementos:**
- Drop-zone com progress bar.
- Campos: categoria (desenho|diagrama|esquema|memorial|cálculo|datasheet|outro), título, observação.
- Limite por arquivo: 100MB (configurável por tenant).

**Estados:** uploading, sucesso (toast + linha na lista), erro (rede / tamanho / formato).

---

### Tela 4: Editor de BOM

**Propósito:** adicionar/editar linhas de BOM.
**Persona:** Engenheiro Projetista.
**US:** `US-ENG-005`.

**Elementos:**
- Tabela editável: posição, componente (busca biblioteca OU ad-hoc), descrição, quantidade, unidade, ref desenho, observação.
- Botão "Adicionar linha"; reordenar drag-and-drop.
- Validação inline (posição duplicada bloqueia salvar).
- Botão "Importar de revisão anterior" (copia BOM como ponto de partida).

---

### Tela 5: Memorial Descritivo (formulário estruturado)

**Persona:** Engenheiro Projetista.
**US:** `US-ENG-006`.

**Elementos:**
- Seções: Escopo, Premissas, Soluções Adotadas, Normas Aplicáveis (lista), Considerações Finais.
- Editor rich text leve (negrito, itálico, lista, link, imagem inline).
- Botão "Gerar PDF" — usa template do tenant.

---

### Tela 6: Biblioteca de Componentes

**Persona:** Engenheiro Projetista.
**US:** `US-ENG-004`.

**Elementos:**
- Tabela: fabricante, modelo, descrição, categoria, datasheet, projetos onde é usado (contagem clicável).
- Filtros: categoria, fabricante.
- Botão "Novo componente" com validação anti-duplicidade (alerta antes de salvar se (fabricante, modelo) já existe).

---

### Tela 7: Diff de Revisões

**Persona:** Engenheiro Responsável (aprovador).
**US:** `US-ENG-007`.

**Elementos:**
- Seletor: revisão A vs B.
- Painéis lado-a-lado: campos estruturados (diff textual), anexos (add/del), BOM (linhas add/del/qty change), memorial (diff).

---

### Tela 8: Painel de Aprovação Técnica

**Persona:** Engenheiro Responsável.
**US:** `US-ENG-002`.

**Elementos:**
- Lista de revisões em status "em_aprovacao" para este aprovador.
- Para cada: ver revisão, ver diff, aprovar (com tipo de assinatura: interna ou ICP), rejeitar (com motivo obrigatório).
- Pode estar integrado ao painel BPM (se tenant usa workflow BPM).

---

### Tela 9: Vinculações (OS / Orçamento / Equipamento / Contrato)

**Persona:** Engenheiro / Técnico.
**US:** `US-ENG-003`.

**Elementos:**
- Lista bidirecional: "este projeto é usado por" + "este projeto referencia".
- Permite vincular OS, orçamento, equipamento, contrato.

---

### Tela 10: Histórico de Alterações

**Persona:** Auditor.
**US:** `US-ENG-008`.

**Elementos:**
- Timeline cronológica: ação, autor, timestamp, motivo, link para diff/revisão.

---

## Componentes reutilizáveis

`<UploadArquivo>`, `<BuscaComponenteBiblioteca>`, `<AssinaturaTecnica>` — promover para `../../../comum/contratos/ui.md` quando reutilizados.

## Como esta lista evolui

- Tela nova → linkar US.
- Mudança UX → bump CHANGELOG.
- Descontinuação → `@deprecated` + janela.
