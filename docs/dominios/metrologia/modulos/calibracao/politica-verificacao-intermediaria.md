---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - ./prd.md
  - ./modelo-de-dominio.md
  - ../../../adr/0030-vigencia-temporal-canonica.md
---

# Política de Verificação Intermediária (VI) — esqueleto (novo Onda 7 — M4-CAL)

> Atende ISO/IEC 17025 cl. 6.4.10 + INV-CAL-VI-001. Esqueleto com IDs e responsabilidades; conteúdo técnico detalhado preenchido Wave A com `consultor-rbc-iso17025`.

---

## 1. Por que VI existe

Padrão calibrado externamente em janeiro com cert válido por 12 meses pode derivar antes do recálculo anual. Verificação intermediária (VI) entre as duas calibrações externas detecta deriva precoce + comprova estabilidade.

## 2. Regras (esqueleto)

| ID | Regra | Aplicabilidade | Frequência | Critério aceitação |
|---|---|---|---|---|
| VI-001 | VI mensal de pesos padrão classe E1 | Padrão E1 com uso frequente (≥10 calibrações/mês) | Mensal | Δ ≤ 1/3 da incerteza expandida do padrão |
| VI-002 | VI trimestral de pesos padrão classe E2 | Padrão E2 com uso frequente (≥5 calibrações/mês) | Trimestral | Δ ≤ 1/3 da incerteza expandida do padrão |
| VI-003 | VI semestral de padrões F1/F2 | Padrão F1/F2 (uso geral) | Semestral | Δ ≤ 1/2 da incerteza expandida do padrão |
| VI-004 | VI antes de cada calibração crítica de cliente farma | Padrão usado em cliente farma (regra de decisão BANDA_GUARDA_30 ADR-0024) | Por uso | Δ ≤ 1/4 da incerteza expandida |
| VI-005 | VI extraordinária após evento (queda, golpe, condição ambiental anormal) | Qualquer padrão | Por evento | Δ ≤ critério da classe |

## 3. Procedimento

VI segue procedimento documentado no módulo `procedimentos` (US-PROC-001). Cada VI executada:
1. Cria `VerificacaoIntermediaria` (entidade existente no modelo Calibração).
2. Registra resultado + condições + responsável.
3. Se reprovado: padrão fica INDISPONÍVEL + dispara NC (US-CAL-008 AC-2 + US-CER-008).
4. Se aprovado: padrão segue DISPONÍVEL + próxima VI agendada.

## 4. Invariante

- **INV-CAL-VI-001 (já em REGRAS):** padrão de uso frequente exige VI conforme classe + frequência cadastrada neste documento. VI reprovada bloqueia uso até nova VI APROVADA.

## 5. Como evolui

- Frequência ajustada por evidência (drift histórico do padrão).
- Critério de aceitação revisado por incidente (NC abre revisão da regra).
- ADR + revalidação software (cl. 7.11) se mudança afeta motor.
