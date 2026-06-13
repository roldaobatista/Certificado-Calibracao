---
owner: Roldão
revisado-em: 2026-06-13
status: draft
modulo: colaboradores
dominio: rh-frota-qualidade
---

# Contrato UI — Colaboradores

## Telas MVP-1

### T-COL-01 — Lista de colaboradores
- **Quem vê:** Dono, Gerente, Qualidade (read).
- **Colunas:** Foto, Nome, Papéis (chips), Status (Ativo/Inativo), Vínculo, Comissão %, Ações.
- **Filtros:** Papel, Vínculo, Status, Habilidade.
- **Busca:** Nome ou CPF.
- **Vazio:** "Nenhum colaborador cadastrado. Adicione você mesmo como dono pra começar."
- **Ações:** Novo colaborador, Exportar (Excel/CSV).

### T-COL-02 — Cadastro / edição
- **Seções:** Dados pessoais, Vínculo, Papéis, Habilidades, Documentos, Comissão.
- **Validação CPF:** Formato + dígito verificador + dedup tenant (INV-024 espelhado) com mensagem: "Já existe colaborador com este CPF nesta empresa".
- **Papel "Signatário":** Habilita campo "Escopo de assinatura" (link para módulo responsabilidade-técnica). Sem escopo → botão "Salvar" bloqueado com tooltip "Signatário precisa de escopo declarado (regra ISO)".
- **Papel "Motorista UMC":** Habilita campo de CNH + categoria (B/C/D/E). Se CNH não for anexada, o botão "Salvar" **não bloqueia** — salva com `pendencia_cnh=true` e exibe aviso "CNH pendente: este colaborador não poderá ser alocado em OS de campo até regularização" (R-COL-1). O bloqueio de alocação acontece em frota/agenda, não no cadastro.
- **Habilidades:** Multi-select com sugestão do catálogo + livre. Cada habilidade tem nível.
- **Comissão padrão:** Slider 0-100% com 2 casas decimais. Mudança grava audit (INV-001).
- **Acessibilidade:** WCAG 2.1 AA (INV-016) — labels, foco visível, contraste 4.5:1, navegação teclado.

### T-COL-03 — Perfil próprio (self-service)
- **Quem vê:** Colaborador autenticado vendo só si mesmo.
- **Pode editar:** Telefone, e-mail, foto. NÃO PODE editar CPF, papéis, escopo, comissão.
- **Read-only:** Papéis, escopo signatário, comissão, habilidades.

### T-COL-04 — Desligamento
- **Acesso:** Dono apenas.
- **Campos:** Data desligamento, motivo (livre), aviso visível "Desligamento revoga todos os papéis automaticamente e o colaborador deixa de aparecer em novas Ordens de Serviço. O histórico fica preservado."
- **Confirmação dupla:** Modal "Tem certeza? Você está desligando [Nome]. Esta ação é registrada no histórico."

## Estados de erro (linguagem sem jargão)

| Erro técnico | Mensagem na tela |
|---|---|
| INV-024 violation | "Já existe colaborador com este CPF nesta empresa." |
| INV-003 violation | "Pra atribuir o papel de Signatário, o escopo de assinatura precisa estar declarado." |
| CNH ausente em motorista UMC (cadastro) | Aviso não-bloqueante: "CNH pendente: este colaborador não poderá ser alocado em OS de campo até regularização." (R-COL-1 — salva com pendência; não bloqueia cadastro) |
| Validação CPF | "Esse CPF não parece válido. Confira os números." |

## Componentes reutilizáveis

- `<ChipPapel papel="..." />` — exibe papel com cor padronizada.
- `<MatrizHabilidades colaborador=... />` — usado em T-COL-02 + relatório Operação.
- `<HistoricoAuditoria entidade="colaborador" id="..." />` — INV-001.

## Não-implementar MVP-1

Tela de holerite, ponto, férias, avaliação, vagas, organograma. → V2.
