# 0033 — Bloqueio fail-closed para elegibilidade de padrão metrológico

## Contexto

O PRD §13.2 exige bloqueio de emissão quando o padrão metrológico estiver vencido, sem certificado válido ou fora da faixa aplicável. O mesmo documento detalha que:

- padrão sem certificado anexado bloqueia aprovação final;
- padrão fora da faixa bloqueia o ensaio específico;
- a validação automática deve considerar vigência, faixa e rastreabilidade antes da emissão.

O pacote `@afere/normative-rules` já contém a regra textual `RULE-STANDARD-TRACEABILITY-DOCUMENTED`, mas faltava uma API executável mínima para transformar esse requisito em decisão determinística e testável.

## Escopo

- Adicionar em `packages/normative-rules` uma regra executável para elegibilidade de padrão.
- Bloquear certificado ausente, certificado vencido e ensaio fora da faixa declarada.
- Falhar fechado para datas ou faixa insuficientes para validação.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-02-standard-eligibility-block.test.ts`.
- Promover `REQ-PRD-13-02-STANDARD-ELIGIBILITY-BLOCK` para `validated` se a evidência ficar verde.

## Fora de escopo

- Consultar documentos anexos reais ou OCR de certificados.
- Validar cadeia completa ILAC MRA/INM por perfil regulatório.
- Integrar com fluxo real de OS ou tela de seleção de padrões em `apps/api`.

## Critérios de aceite

- Padrão com certificado ausente bloqueia a elegibilidade.
- Padrão com validade anterior à data do ensaio bloqueia a elegibilidade.
- Padrão fora da faixa aplicável ao ponto de ensaio bloqueia a elegibilidade.
- Entrada sem dados mínimos de faixa ou data falha fechado.
- O teste de aceite falha se a API não for exportada por `packages/normative-rules/src/index.ts`.

## Evidência

- `pnpm exec tsx --test packages/normative-rules/src/standard-eligibility.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-02-standard-eligibility-block.test.ts`
- `pnpm check:all`
