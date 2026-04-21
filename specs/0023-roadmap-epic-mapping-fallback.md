# Spec 0023 — fallback de `epic-review-flag` via roadmap canônico

## Objetivo

Fechar a lacuna restante da ADR 0025: permitir que `CASCADE-008` continue agrupando correções por épico L0 mesmo quando o log de verificação registrar apenas referências L1, desde que o roadmap canônico já declare o vínculo entre requisito e épico.

## Escopo

- Exigir `epic_id` e `linked_requirements` em cada fatia de `compliance/roadmap/v1-v5.yaml`.
- Estender `pnpm roadmap-check` para validar essa metadata.
- Fazer `tools/verification-cascade.ts` carregar o mapa `REQ -> EPIC` do roadmap.
- Usar o mapa como fallback apenas quando o log não trouxer `L0/<EPIC-ID>` explícito.
- Atualizar a documentação operacional da fonte canônica do roadmap.

## Critérios de aceite

- `roadmap-check` falha quando qualquer fatia omite `epic_id`.
- `roadmap-check` falha quando qualquer fatia omite `linked_requirements`, ainda que a lista possa ser vazia.
- `checkVerificationCascade()` emite `CASCADE-008` para múltiplos REQs do mesmo épico quando os logs tiverem apenas `L1/...` e o roadmap fornecer o vínculo.
- Referências explícitas `L0/<EPIC-ID>` continuam tendo precedência sobre o fallback do roadmap.
- A leitura do roadmap na cascata é permissiva: YAML ausente ou inválido não gera falso positivo extra; apenas desabilita o fallback.

## Fora de escopo

- Inferir épicos automaticamente a partir de ADR, spec ou texto livre.
- Permitir que o mesmo REQ seja reconciliado automaticamente em múltiplos épicos de negócio.
- Substituir a futura bateria final de 30 certificados canônicos em PDF/A.
