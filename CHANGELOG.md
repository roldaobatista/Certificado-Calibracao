# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog 1.1.0](https://keepachangelog.com/pt-BR/1.1.0/) e este projeto segue [Versionamento Semântico](https://semver.org/lang/pt-BR/) (a confirmar em ADR-0001).

> **Audiência principal: Roldão (dono não-técnico).** Cada entrada deve estar em PT-BR claro, descrevendo o efeito visível pro usuário, NÃO o detalhe técnico. Quando aplicável, citar ID rastreável (`US-`, `T-`, `INV-`, `ADR-`).

---

## [Não publicado]

### Adicionado
- **Módulo de Orçamentos (2026-06-15):** o sistema agora cria orçamentos comerciais, calcula preços/impostos/comissão, envia link de aprovação por WhatsApp/e-mail (o cliente aprova em 1 clique, sem login), faz a análise crítica de calibração exigida pela ISO 17025 conforme o tipo de laboratório, e converte o orçamento aprovado em Ordem de Serviço automaticamente. Inclui **modelos de orçamento reutilizáveis** (com trava do selo de acreditação RBC só para laboratórios acreditados). O cliente nunca enxerga margem/custo. *(US-ORC-001/002/004/005/007/008/009; T-ORC-039 fecha o módulo; as telas ficam para etapa futura.)*
- Estrutura inicial de documentação (2026-05-16): pastas + arquivos de fundação + 15 cabeçalhos de Discovery prontos pra preencher na Rodada 0.

### Modificado
- (nada ainda)

### Corrigido
- (nada ainda)

### Removido
- (nada ainda)

### Segurança
- (nada ainda)

---

<!-- Quando primeira versão for liberada, mover [Não publicado] pra [0.1.0] - YYYY-MM-DD -->
