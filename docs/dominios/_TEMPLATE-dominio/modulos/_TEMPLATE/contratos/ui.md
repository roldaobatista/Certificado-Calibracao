---
owner: roldao
revisado_em: 2026-05-16
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo [NOME] (TEMPLATE)

> Telas do módulo + comportamento esperado. Wireframe simples ou descrição textual basta enquanto stack não está decidida.

---

## Telas

### Tela 1: [Nome da tela]

**Propósito:** [1 linha — o que esta tela permite fazer]
**Persona principal:** [referenciar `../personas.md`]
**US relacionadas:** `US-[MOD]-NNN`, `US-[MOD]-MMM`
**Acessível por:** [menu / busca / link direto / após ação X]

**Elementos:**
- [Campo / botão / lista / etc.] — comportamento

**Estados:**
- Vazio (nenhum dado): [o que mostrar]
- Carregando: [skeleton / spinner]
- Erro: [mensagem em PT]
- Sucesso: [feedback ao usuário]

**Acessibilidade (WCAG):**
- Nível mínimo: AA (a confirmar em ADR)
- Navegação por teclado: obrigatória
- Screen reader: textos alt obrigatórios

**Mobile:** [responsivo / app nativo / PWA — ver ADR-0003]

---

### Tela 2: ...

(mesmo formato)

---

## Componentes reutilizáveis

Componentes compartilhados com outros módulos ficam em `../../../comum/contratos/ui.md`.

## Como esta lista evolui

- Tela nova → adicionar + ligar a US-NNN.
- Mudança em UX → bump CHANGELOG seção "Modificado".
- Tela descontinuada → marcar `@deprecated` + janela de migração.
