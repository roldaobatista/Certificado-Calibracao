# ADR 0039 — Reemissão controlada validada por sequência auditável

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0036-prd-13-16-controlled-reissue.md`, `PRD.md` §13.16 e `compliance/roadmap/v1-v5.yaml` V4

## Contexto

A reemissão controlada não depende apenas da existência de um novo certificado: o PRD exige dupla aprovação, versionamento explícito, preservação do vínculo com o certificado anterior e notificação ao cliente. Como ainda não existe backend real de reissue, a melhor evidência executável imediata é validar a sequência mínima desses eventos na hash-chain imutável.

## Decisão

1. `@afere/audit-log` passa a exportar `verifyControlledReissueAuditTrail()`.
2. A função exige a seguinte sequência mínima:
   - ao menos dois eventos `certificate.reissue.approved` com `actorId` distintos;
   - um evento `certificate.reissued` com `previousCertificateHash`, `previousRevision` e `newRevision`;
   - um evento `certificate.reissue.notified` após a reemissão.
3. `previousCertificateHash` deve ser um SHA-256 hexadecimal de 64 caracteres.
4. `previousRevision` e `newRevision` seguem o padrão `R<number>` e `newRevision` deve avançar exatamente uma unidade.
5. A decisão é fail-closed: hash-chain inválida, aprovação insuficiente, revisão inválida ou notificação ausente/fora de ordem tornam a trilha inválida.

## Consequências

- O PRD §13.16 ganha uma evidência automatizada antes mesmo da implementação completa do backend de reemissão.
- O contrato deixa explícita a ordem mínima dos eventos regulatórios esperados para uma reemissão.
- O backend futuro pode reutilizar a mesma validação como pré-condição antes de liberar o artefato reemitido.

## Limitações honestas

- A ADR não dispara notificação real ao cliente; apenas exige evidência auditável de que ela ocorreu.
- Não há validação de justificativa textual, política de aprovação por papel ou antifraude.
- A regra opera sobre payloads já materializados da trilha e não em persistência transacional real.
