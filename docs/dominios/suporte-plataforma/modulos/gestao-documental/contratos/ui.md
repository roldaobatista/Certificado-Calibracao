---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos UI — Módulo Gestão Documental

---

## Telas

### Tela 1: Biblioteca Central

**Propósito:** Listar e buscar todos os documentos do tenant.
**Persona principal:** Responsável Documental + Usuário Operacional.
**US:** `US-DOC-001`, `US-DOC-008`.
**Acessível por:** menu principal "Documentos".

**Elementos:**
- Barra de busca (full-text + filtros: entidade, tipo, status, data).
- Listagem com paginação (50 itens) + ordenação.
- Botão "+ Novo Documento".
- Filtros laterais: vigente / obsoleto / em revisão / vencido.
- Indicador visual de validade (verde / amarelo / vermelho).

**Estados:**
- Vazio: "Nenhum documento ainda. Faça o primeiro upload."
- Carregando: skeleton de 5 linhas.
- Erro: "Não foi possível carregar. Tente novamente."

**Acessibilidade:** WCAG AA, navegação por teclado, screen reader nas linhas.
**Mobile:** responsivo.

---

### Tela 2: Upload de Documento

**Propósito:** Subir arquivo + metadados.
**US:** `US-DOC-001`, `US-DOC-005`, `US-DOC-009`.
**Acessível por:** botão "+ Novo Documento" ou contexto de entidade ("anexar").

**Elementos:**
- Drag-and-drop ou seletor de arquivo (limite 50MB).
- Campos: título, tipo, entidade vinculada (autocompletar), tags, validade (opcional), política de retenção, requer aprovação (checkbox), ACL (avançado).
- Preview de PDF/imagem antes de salvar.
- Barra de progresso de upload.

**Estados:**
- Erro de tamanho: "Arquivo maior que 50MB. Reduza antes de enviar."
- Erro de tipo: "Formato não suportado: .xyz"
- Sucesso: redireciona pra detalhe do documento.

---

### Tela 3: Detalhe do Documento

**Propósito:** Ver todas as versões, metadados, trilha, ações.
**US:** `US-DOC-002`, `US-DOC-003`, `US-DOC-007`, `US-DOC-010`.

**Elementos:**
- Cabeçalho: título, status, entidade vinculada, validade.
- Aba "Versões": tabela v1..vN com autor, data, motivo, ações.
- Aba "Acessos": trilha de quem viu/baixou/editou.
- Aba "ACL": configurar permissões.
- Aba "Assinaturas": status de assinaturas pendentes/concluídas.
- Botões: "Substituir versão", "Compartilhar com cliente", "Solicitar assinatura", "Aprovar" (se em_revisao).

---

### Tela 4: Modelos de Documento

**Propósito:** Gerenciar templates reutilizáveis.
**US:** `US-DOC-006`.
**Acessível por:** menu "Documentos" → "Modelos".

**Elementos:**
- Lista de modelos + botão "+ Novo Modelo".
- Editor de variáveis (chave → tipo → label).

---

### Tela 5: Painel de Vencimentos

**Propósito:** Documentos vencendo nos próximos 90 dias.
**US:** `US-DOC-005`.

**Elementos:**
- Lista agrupada por janela (vencidos / 7d / 15d / 30d / 90d).
- Ação rápida: "Renovar" (abre upload de nova versão).

---

### Tela 6: Compartilhamento Externo (visualização do cliente)

**Propósito:** Cliente externo abre link e visualiza/assina.
**US:** `US-DOC-004`, `US-DOC-010`.

**Elementos:**
- Branding do tenant.
- Preview do documento.
- Botão "Baixar" (se permitido).
- Bloco de assinatura (se solicitada).

**Estados:**
- Link expirado: "Este link não é mais válido."
- Senha exigida: campo + botão "Acessar".

---

## Componentes reutilizáveis

Compartilhados em `../../../comum/contratos/ui.md`: autocompletar de entidade, picker de tags, indicador de status colorido.

## Como esta lista evolui

Tela nova → ligar a US-NNN. Mudança UX → bump CHANGELOG. Tela descontinuada → `@deprecated`.
