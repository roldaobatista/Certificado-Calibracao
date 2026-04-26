# Finding — Validação PDF/A ainda depende de validador externo

## Status

Aberto, já documentado como limitação honesta.

## Contexto

O renderer determinístico gera PDFs com disclaimer fail-closed de que a conformidade PDF/A formal ainda depende de validação externa. Isso é correto como limitação, mas continua sendo um blocker real para produção regulada.

## Impacto

- Certificados emitidos podem não ser arquivisticamente conformes sem validação final.
- Auditoria externa pode rejeitar o processo de emissão.

## Correção recomendada

1. Integrar validador PDF/A no pipeline (ex: veraPDF, callas pdfaPilot, ou serviço externo contratado).
2. Bloquear publicação se o validador não aprovar.
3. Arquivar laudo de validação por lote/release no dossiê.

## Rastreamento

- Área: `apps/api/src/domain/emission/certificate-renderer.ts`, Gate 7
