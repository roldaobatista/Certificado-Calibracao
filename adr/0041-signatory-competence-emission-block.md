# ADR 0041 — Assinatura bloqueada por competência vencida ou incompatível

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0038-prd-13-09-signatory-competence-block.md`, `PRD.md` §13.9

## Contexto

O backend precisa de uma regra explícita para responder se um signatário pode ou não assinar um instrumento. Sem isso, a decisão fica implícita ou distribuída em pontos futuros do sistema.

## Decisão

1. `apps/api/src/domain/competencies` passa a exportar `evaluateSignatoryCompetence()`.
2. A decisão considera:
   - `instrumentType` alvo;
   - instante da assinatura;
   - competências registradas do signatário.
3. Só é permitido assinar quando existir competência com mesmo tipo de instrumento e janela de vigência contendo o instante da assinatura.
4. O contrato falha fechado para dados mínimos ausentes ou registros de competência inválidos.

## Consequências

- O PRD §13.9 ganha evidência executável antes da implementação completa do fluxo de emissão.
- O backend futuro pode usar a mesma função como gate antes de `certificate.signed`.
- Competência deixa de ser uma inferência implícita do payload.
