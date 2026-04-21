# ADR 0036 — Elegibilidade fail-closed de padrão metrológico

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0033-prd-13-02-standard-eligibility-block.md`, `PRD.md` §13.2, §7.8 e §8.6

## Contexto

O PRD exige bloqueio duro quando o padrão estiver vencido, sem certificado válido ou fora da faixa aplicável. O pacote normativo baseline já descrevia a rastreabilidade documental, mas faltava uma regra executável pequena o suficiente para impedir que a seleção do padrão prosseguisse sem esses mínimos.

## Decisão

1. `@afere/normative-rules` passa a exportar `evaluateStandardEligibility()`.
2. A função avalia, no mínimo:
   - presença de certificado válido;
   - vigência do certificado na data do ensaio;
   - faixa aplicável ao ponto de medição.
3. A função falha fechado para dados mínimos ausentes ou inválidos:
   - data do ensaio inválida;
   - validade do certificado ausente quando o certificado existe;
   - faixa aplicável ausente ou inválida;
   - valor do ponto de medição ausente ou inválido.

## Consequências

- O PRD §13.2 deixa de depender apenas de texto e passa a ter decisão executável.
- `apps/api` ganha um contrato futuro único para bloquear seleção de padrão antes da emissão.
- A validação não tenta ser "tolerante"; na falta de dados mínimos, bloqueia.

## Limitações honestas

- Esta ADR não lê anexos reais de certificado nem prova cadeia ILAC MRA/INM ponta a ponta.
- A faixa aplicável continua sendo recebida como intervalo numérico simples, sem modelagem por instrumento ou ponto multiparamétrico.
- A integração com a OS real e com o fluxo de emissão continua pendente em `apps/api`.
