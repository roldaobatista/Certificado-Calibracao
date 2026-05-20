---
owner: corretora-seguros-saas (consultivo — não emite apólice)
revisado-em: 2026-05-20
status: stable
---

# Review corretora-seguros-saas — T-CLI-104

Veredito: **AJUSTAR** (3 absorvidos).

## C1 — Alerta P1 sem push real

ALTO risco se tenant externo; BAIXO em dogfooding. Apólices cyber
exigem "reasonable detection controls". Em sinistro pode disparar
exclusão "failure to maintain agreed security posture".

**Mitigação:** ADR cravando push real (PagerDuty/Slack) como
PRÉ-REQUISITO de 1º tenant externo pago. Sem tenant externo ≠
cobertura E&O acionável por terceiro.

## C2 — Threshold absoluto

**Obrigatório.** Breaker decorativo é pior que ausência — cria
falsa sensação de controle. Sugestão: `OR (falhas_absolutas ≥ 3)`.
Racional explícito: "regime de baixo tráfego MVP-1".

## C3 — Retenção 7d do contador

Sumário de transição (`disparado`/`normalizado`) precisa ir pra
cadeia F-A (25 anos). Detalhe operacional 7d OK, mas estado do
breaker é evidência de longo prazo (ANPD 6-18 meses, claim cyber
30-90 dias).

## Riscos cyber adicionais

- Exclusão "rogue insider" — breaker cego agrava.
- Franquia típica R$ 50-150k LGPD; sublimite multa 20-30%.
- E&O: ausência monitoramento real = "negligência grave".

## Limite OAB/SUSEP

Apólice real só corretora SUSEP licenciada emite (Lei 4.594/64).
Hoje review consultivo apenas.
