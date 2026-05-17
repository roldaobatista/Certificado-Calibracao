---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: garantia
dominio: operacao
---

# Personas — Módulo Garantia

> Personas específicas. Personas transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## P-GAR-01: Atendente que recebe reclamação

**Identidade:** atendente comercial / SAC, primeiro contato com cliente reclamando.

**Goals:**
- Abrir OS em garantia em ≤ 2 min sem precisar perguntar prazo
- Saber na hora se a OS-mãe ainda está dentro do prazo
- Evitar prometer garantia que não existe

**Frustrations:**
- Hoje precisa abrir 3 telas pra descobrir prazo da garantia
- Cliente cobra "se está na garantia" e ela não sabe responder

**Jornada:** recebe ligação → busca OS-mãe / venda → sistema mostra "dentro do prazo" → abre OS-filha em garantia → cliente sai informado.

**Devices:** web desktop.
**Frequência:** diário.

---

## P-GAR-02: Técnico/metrologista que analisa procedência

**Identidade:** quem foi ao campo ou bancada e decide se garantia procede.

**Goals:**
- Registrar laudo (procedente / improcedente / parcial) com motivo claro
- Não ter que digitar duas vezes (laudo OS + análise garantia)
- Documentar causa raiz pra reduzir reincidência

**Frustrations:**
- Pressão do cliente que "não quer pagar"
- Falta de histórico da peça/equipamento na hora da análise

**Jornada:** abre OS no app → executa → marca análise → escreve laudo → fecha OS → garantia recalcula custo e cobrança.

**Devices:** mobile (campo) + web (bancada).
**Frequência:** diário.

---

## P-GAR-03: Gerente operacional

**Identidade:** dono / gerente que paga a conta do retrabalho.

**Goals:**
- Ver custo de garantia / mês separado do custo normal
- Identificar técnico, peça e cliente reincidentes
- Aprovar desbloqueio manual de cobrança quando for o caso

**Frustrations:**
- Hoje "garantia" some na rotina e ninguém mede
- Cliente que abusa de garantia passa despercebido

**Jornada:** abre dashboard semanal → vê top reincidentes → toma ação (mudar fornecedor, treinar técnico, conversar com cliente).

**Devices:** web desktop.
**Frequência:** semanal.

---

## P-GAR-04: Comprador (garantia do fornecedor)

**Identidade:** quem fala com fornecedor pra obter ressarcimento de peça que falhou.

**Goals:**
- Não esquecer prazo de devolução ao fornecedor
- Documentar nota de remessa e retorno
- Saber valor recuperado / valor perdido

**Frustrations:**
- Fornecedor "enrola" no retorno
- Peça enviada e esquecida = prejuízo

**Devices:** web desktop.
**Frequência:** semanal.

---

## Convenções

Se persona aparece em ≥2 módulos com mesma responsabilidade, promover. Hook valida não-duplicação.
