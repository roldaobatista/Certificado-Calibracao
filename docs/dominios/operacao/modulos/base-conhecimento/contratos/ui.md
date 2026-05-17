---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: base-conhecimento
dominio: operacao
---

# Contratos UI — Base de Conhecimento

## Telas

### Tela 1: Lista de Artigos
**Propósito:** consultar e navegar a base.
**Persona:** P-BCN-03 (consumidor), P-BCN-01 (autor).
**US:** US-BCN-005, US-BCN-008, US-BCN-010.
**Acessível por:** menu lateral "Base de Conhecimento" + busca global.

**Elementos:**
- Barra de busca (full-text com auto-complete)
- Filtros laterais: equipamento, marca, modelo, tipo, norma, status, autor
- Lista de cards: título, snippet, categoria, autor, data, utilidade %, badge "desatualizado"
- Ordenação: relevância | mais útil | mais recente | mais visto

**Estados:**
- Vazio: "Nenhum artigo publicado ainda. Que tal criar o primeiro a partir de uma OS resolvida?"
- Carregando: skeleton de cards
- Erro: "Falha ao carregar. Tentar novamente."
- Sucesso: lista populada

**Acessibilidade:** WCAG AA, navegação teclado, foco visível em cards.
**Mobile:** responsivo; filtros viram bottom-sheet.

---

### Tela 2: Editor de Artigo (Autor)
**Propósito:** criar/editar artigo.
**Persona:** P-BCN-01.
**US:** US-BCN-001, US-BCN-006.

**Elementos:**
- Título (obrigatório), tipo (select), corpo (editor rich-text com markdown)
- Categoria: equipamento (autocomplete), marca, modelo, tipo serviço, normas (multi)
- Anexos (drag-drop: PDF, imagem, vídeo)
- Botões: salvar rascunho | submeter pra revisão | descartar
- Painel lateral: histórico de versões com botão "comparar"

**Estados:**
- Em rascunho: campos editáveis
- Em revisão: campos travados; aviso "aguardando aprovação"
- Rejeitado: banner com comentário do aprovador; campos liberados

---

### Tela 3: Fila de Aprovação
**Propósito:** aprovador técnico revisa pendentes.
**Persona:** P-BCN-02.
**US:** US-BCN-002.

**Elementos:**
- Lista de artigos em_revisao ordenados por antiguidade
- Cada item: título, autor, tipo, idade da submissão (com flag se > 7d)
- Click abre Tela 4 (Revisão).

---

### Tela 4: Revisão de Artigo
**Propósito:** aprovar/rejeitar artigo.
**Persona:** P-BCN-02.
**US:** US-BCN-002, US-BCN-006.

**Elementos:**
- Visualização do artigo
- Diff com versão anterior (quando atualização) lado-a-lado
- Botões: aprovar | rejeitar | pedir ajustes
- Campo comentário (obrigatório se rejeitar/ajustes)

---

### Tela 5: Painel de Sugestões (componente dentro de Chamado/OS)
**Propósito:** mostrar artigos sugeridos automaticamente.
**Persona:** P-BCN-03.
**US:** US-BCN-003, US-BCN-004.

**Elementos:**
- Painel lateral colapsável dentro de Chamado/OS
- Top 5 artigos por score
- Cada item: título, snippet, score visual, botões "abrir" / "marcar como aplicado"

**Estados:**
- Vazio: "Nenhuma sugestão. Buscar manualmente."
- Carregando: skeleton.

---

### Tela 6: Detalhe de Artigo
**Propósito:** ler artigo + interagir.
**Persona:** P-BCN-03.

**Elementos:**
- Conteúdo renderizado
- Anexos com preview
- Botões útil/não útil
- Campo comentário
- Metadados: autor, versão, aprovado por, normas relacionadas, última revisão

---

## Componentes reutilizáveis

Editor rich-text e player de vídeo são candidatos a `../../../comum/contratos/ui.md`.
