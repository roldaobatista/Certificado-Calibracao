---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: clientes
dominio: comercial
diataxis: reference
---

# Contratos UI — Módulo Clientes

## Telas

### 1. Lista de clientes — `/clientes`
**Propósito:** encontrar cliente rápido + filtrar por segmento/rating/status.
**Persona principal:** P-CLI-01 Atendente, P-CLI-02 Vendedor.
**US:** US-CLI-002, US-CLI-004.
**Elementos:** busca fuzzy (nome/CPF/CNPJ/telefone), filtros (segmento, rating, status, bloqueio, última OS), tabela paginada, ações em massa (segmentar/exportar).
**Estados:** vazio ("nenhum cliente cadastrado — começar pelo Importar?"), carregando (skeleton), erro (mensagem PT).

### 2. Cadastro novo — `/clientes/novo`
**Propósito:** criar cliente PF ou PJ em < 1 min (US-CLI-001).
**Elementos:** toggle PF/PJ, campos mínimos (documento, nome/razão, telefone, e-mail), checkbox aceite LGPD obrigatório, botão "salvar e criar OS" + "salvar e voltar".
**Validações inline:** CPF/CNPJ via algoritmo; duplicidade ao perder foco do documento.

### 3. Visão 360° — `/clientes/{id}`
**Propósito:** ver tudo do cliente em uma tela (BIG-07).
**Elementos:** cabeçalho com selos (rating, status, bloqueio, limite usado), abas (Resumo, OS, Certificados, Financeiro, Contatos, NPS, Anexos, Timeline), botões de ação (nova OS, novo orçamento, enviar WhatsApp, bloquear).
**Estados:** carregando (skeleton por aba), 360° sem dados ("cliente novo — sem histórico").
**Performance:** carregar aba ativa primeiro; demais lazy.

### 4. Edição do cliente — `/clientes/{id}/editar`
**Propósito:** atualizar dados cadastrais.
**Elementos:** mesmos campos do cadastro + abas para endereços e contatos múltiplos (PJ).
**Auditoria:** mostra "alterado por X em Y" em cada campo (LGPD art. 18).

### 5. Importação 1-clique — `/clientes/importar`
**Propósito:** subir CSV/XLSX em lote (Foundation F-C).
**Elementos:** upload, preview 10 linhas, mapeamento de colunas (auto-sugerido), botão "executar", relatório final (criados/atualizados/rejeitados + download de erros).

### 6. Wizard de dedup — `/clientes/dedup`
**Propósito:** mesclar dois cadastros duplicados (US-CLI-005).
**Elementos:** lista de duplicatas detectadas (filtro: mesmo documento, telefone similar, e-mail igual), tela lado a lado campo a campo com escolha do valor a manter, confirmação com aviso ("histórico migra para o vencedor — perdedor é arquivado").

### 7. Configuração de segmentos — `/configuracoes/segmentos`
**Propósito:** dono define tags + cores + regras de segmentação automática.
**Persona:** P-CLI-03 Dono.

### 8. Bloqueio comercial — modal dentro de `/clientes/{id}`
**Propósito:** marcar bloqueado/desbloqueado com motivo + justificativa.
**Persona:** P-CLI-04 Financeiro, P-CLI-03 Dono.

## Componentes reutilizáveis

- `<DocumentoInput>` (CPF/CNPJ com validação + máscara — CNPJ aceita alfanumérico `[A-Z0-9]{12}[0-9]{2}` a partir de jul/2026, ver ADR-0017; input normaliza pra maiúsculas antes de validar) — promover pra `../../../comum/contratos/ui.md` se reaparecer.
- `<TimelineCliente>` (lista cronológica filtrável).

## Acessibilidade

- WCAG AA mínimo (a confirmar em ADR).
- Navegação teclado obrigatória em busca + cadastro.

## Mobile

- Lista + visão 360° responsivas (consulta).
- Cadastro completo: prioridade desktop; mobile faz cadastro mínimo (PF + nome + telefone) + completar depois.

## Como evolui

Tela nova → US-CLI-NNN + bump CHANGELOG.
