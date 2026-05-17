---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: projetos
dominio: operacao
---

# Personas — Módulo Gestão de Projetos

> Específicas. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## P-PRJ-01: Gerente de projeto

**Identidade:** responsável geral pelo projeto na empresa do tenant — pode ser dono em empresas pequenas, gerente operacional em médias.

**Goals:**
- Ter visão única do projeto (escopo, prazo, custo, risco)
- Disparar faturamento por etapa sem retrabalho manual
- Detectar atraso ou estouro de budget cedo

**Frustrations:**
- Hoje cola dados de OS no Excel à mão
- Aditivo "fica no WhatsApp" e some na hora de cobrar

**Jornada:** abre projeto → estrutura etapas → atribui responsáveis → acompanha Gantt → recebe alertas → atua → fecha projeto com aceite final.

**Devices:** web desktop primário; mobile read-only.
**Frequência:** diário.

---

## P-PRJ-02: Responsável técnico de etapa

**Identidade:** técnico sênior, engenheiro, líder de equipe — toca uma etapa específica (montagem mecânica, automação, comissionamento).

**Goals:**
- Ver claramente o que precisa entregar e até quando
- Registrar diário sem fricção
- Comunicar risco logo que aparece

**Frustrations:**
- "Esqueço de anotar e depois cliente cobra"
- Risco verbal não vira ação

**Devices:** web desktop + mobile (campo).
**Frequência:** diário.

---

## P-PRJ-03: Dono / Diretor

**Identidade:** dono ou diretor com visão de portfolio (vários projetos correndo).

**Goals:**
- Ver margem real (não só prevista)
- Identificar projeto entrando em prejuízo
- Aprovar aditivo grande

**Frustrations:**
- Hoje só descobre prejuízo no fechamento mensal
- Aditivo aprovado sem dado virou padrão

**Devices:** web desktop.
**Frequência:** semanal.

---

## P-PRJ-04: Cliente final (portal)

**Identidade:** representante do cliente do tenant — recebe visão filtrada do projeto.

**Goals:**
- Acompanhar progresso sem ligar
- Assinar aceite de etapa digitalmente
- Receber documentos do projeto

**Frustrations:**
- Hoje recebe planilha desatualizada por email

**Devices:** web (portal) + mobile (responsivo).
**Frequência:** semanal/ad-hoc.

---

## P-PRJ-05: Comprador / Estoquista (interação)

**Identidade:** quem compra materiais e baixa estoque vinculado ao projeto. Persona principal vive em outros módulos (Compras, Estoque) — aqui aparece apenas pelo vínculo.

**Goals:**
- Saber qual projeto absorve aquela compra
- Não baixar estoque sem rastrear o projeto

**Devices:** web desktop.
**Frequência:** diário.

---

## Convenções

Se persona aparece em ≥2 módulos com mesma responsabilidade, promover.
