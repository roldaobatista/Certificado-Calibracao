---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: orcamentos
dominio: comercial
diataxis: reference
---

# Contratos UI — Módulo Orçamentos

## Telas

### 1. Lista de orçamentos — `/orcamentos`
**Propósito:** vendedor/dono ver pipeline + filtrar por estado/cliente/responsável/valor.
**Persona:** P-ORC-01 Vendedor, P-ORC-04 Dono.
**Elementos:** filtros (estado, cliente, responsável, período, valor min/max), tabela com selo de estado colorido, ação rápida "enviar lembrete".
**Estados:** vazio ("nenhum orçamento — começar agora?"), com KPI no topo (total aberto / aprovado mês / expirando 7d).

### 2. Criação — `/orcamentos/novo`
**Propósito:** criar orçamento em < 5 min (US-ORC-001).
**Elementos:**
- Seleção de cliente (autocomplete da busca de clientes)
- Botão "usar template" (calibração padrão / manutenção / instalação / custom)
- Tabela de itens (escolher do catálogo → preço/alíquota auto)
- Campo desconto (% ou R$) com **preview de comissão impactada** ao lado
- Validade (default 15 dias, configurável)
- Condições de pagamento (texto + dropdown)
- Rodapé: total bruto / descontos / impostos / **total líquido** + comissão prevista
- Botões: "salvar rascunho", "enviar agora"

### 3. Detalhes do orçamento — `/orcamentos/{id}`
**Propósito:** ver versão ativa + histórico + tracking + ações.
**Elementos:** cabeçalho (cliente + estado + selo validade), abas (Itens, Histórico de versões, Tracking de leitura, Comentários), ações (editar/nova versão/enviar/cancelar/marcar aprovado manual).

### 4. Link público — `/o/{token}` (sem login)
**Propósito:** cliente final aprova em 1 clique (US-ORC-002).
**Elementos:**
- Cabeçalho com logo do tenant + nome do cliente
- Resumo visual (escopo + prazo + valor)
- Botão grande "**APROVAR**" + botão secundário "Pedir ajuste" (abre comentário)
- Link "baixar PDF"
- Checkbox LGPD aceite + texto explicativo
**Estados:** orçamento expirado (mensagem amigável), já aprovado (confirmação), revogado (mensagem).
**Mobile-first:** 75% dos acessos são mobile.

### 5. Comparação de versões — `/orcamentos/{id}/comparar?de=v1&para=v2` (Wave B)
**Propósito:** vendedor mostra cliente o que mudou.
**Elementos:** duas colunas lado a lado destacando alterações (verde adicionado / vermelho removido / amarelo alterado).

### 6. Templates — `/configuracoes/orcamentos/templates`
**Persona:** P-ORC-04 Dono.
**Elementos:** lista de templates + editor (nome, tipo, itens padrão, condições padrão, texto rodapé).

### 7. Configuração de limites — `/configuracoes/orcamentos/regras`
**Persona:** P-ORC-04 Dono.
**Elementos:** limite de desconto autônomo do vendedor, escalada de aprovação interna, validade padrão.

### 8. Aprovação interna — modal/inline em `/orcamentos/{id}` (Wave B)
**Propósito:** dono aprova orçamento com desconto > limite antes do envio.

## Componentes reutilizáveis

- `<ItemPicker>` (busca catálogo) — compartilhado com módulo OS.
- `<DescontoInput>` com preview de comissão — específico deste módulo.
- `<EstadoOrcamentoBadge>` colorido por estado.

## Acessibilidade

- WCAG AA mínimo.
- Link público (`/o/{token}`) **deve ser navegável só com teclado** (cliente externo pode ser leitor de tela).
- Botão "Aprovar" no link público: tamanho mínimo 44×44px (mobile), contraste AAA.

## Mobile

- Link público: mobile-first (responsivo).
- Criação: prioridade desktop (escolha de catálogo é lenta em mobile); mobile mostra "criar rápido a partir de template" simplificado.

## Como evolui

Tela nova → US-ORC-NNN + CHANGELOG.
