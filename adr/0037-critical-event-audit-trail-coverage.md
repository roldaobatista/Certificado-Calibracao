# ADR 0037 — Cobertura obrigatória de eventos críticos na trilha imutável

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0034-prd-13-06-critical-event-audit-trail.md`, `PRD.md` §13.6 e §7.10

## Contexto

O PRD exige não apenas que a trilha seja imutável, mas também que os eventos críticos do ciclo apareçam nela. O pacote `@afere/audit-log` já verificava integridade append-only via hash-chain, porém ainda não demonstrava que um fluxo completo de calibração, revisão, assinatura, emissão e eventual reemissão estava semanticamente coberto.

## Decisão

1. `@afere/audit-log` passa a exportar `verifyCriticalEventAuditTrail()`.
2. A função combina dois eixos:
   - verificação estrutural da hash-chain;
   - cobertura semântica dos eventos críticos obrigatórios.
3. O conjunto mínimo obrigatório passa a ser:
   - `calibration.executed`;
   - `technical_review.completed`;
   - `certificate.signed`;
   - `certificate.emitted`.
4. Quando `requireReissue` estiver ativo, `certificate.reissued` passa a ser obrigatório.
5. A decisão é fail-closed: hash-chain inválida ou evento crítico ausente torna a trilha inválida.

## Consequências

- O PRD §13.6 deixa de depender apenas do checksum da trilha e passa a provar cobertura mínima do fluxo.
- `apps/api` ganha um contrato futuro simples para validar a trilha de uma OS ou certificado antes de exportar evidência de auditoria.
- A reemissão pode ser coberta no mesmo mecanismo, sem duplicar verificador.

## Limitações honestas

- Esta ADR não modela todos os campos de metadata de cada evento; identidade, timestamp e dispositivo ficam para o requisito §13.4.
- A semântica atual depende de nomes de ação canônicos em payloads, não de schema completo do backend.
- O pacote ainda não lê eventos persistidos do banco nem gera export formal para auditor externo.
