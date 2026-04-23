# ADR 0061 — Renderer determinístico de certificado para Gate 7

## Status

Aceito

## Contexto

O Gate 7 já valida manifesto, hash e diff byte-a-byte, mas ainda opera sobre snapshots dogfood em texto. Isso deixa a cascata L4 em pé do ponto de vista estrutural, porém sem cobrir um artefato documental real do fluxo de emissão.

## Decisão

Adotar uma primeira camada de renderer determinístico de certificado para sustentar a bateria canônica do Gate 7:

1. Gerar PDFs determinísticos locais a partir de cenários canônicos da emissão.
2. Materializar 30 snapshots canônicos, distribuídos em 10 artefatos por perfil regulatório A/B/C.
3. Regenerar automaticamente `current/` antes do `snapshot-diff-check`.
4. Tratar a conformidade PDF/A formal como pendência explícita de validação externa, sem alegar que o renderer já fecha sozinho o requisito de arquivamento normativo.

## Consequências

### Positivas

- O Gate 7 passa a comparar uma peça documental real, em vez de snapshots textuais artificiais.
- A cascata L4 fica mais próxima do comportamento exigido pelo harness para área crítica de emissão.
- O catálogo canônico cria base reprodutível para evoluções futuras do renderer sem perder diff byte-a-byte.

### Limitações honestas

- O artefato é um PDF determinístico, mas a conformidade PDF/A formal ainda não está validada por ferramenta externa ou dossiê específico.
- O renderer continua focado em regressão canônica; não substitui sozinho a persistência oficial do binário emitido.
- Portal, WORM e assinatura criptográfica externa permanecem fora desta fatia.
