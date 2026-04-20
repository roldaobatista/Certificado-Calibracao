# ADR 0004 — Governança do pacote normativo

## Status

Aprovado para bootstrap técnico em 2026-04-20.

## Contexto

O Aferê precisa emitir certificados registrando a versão exata do pacote normativo usado na data da emissão. O pacote precisa ser reprodutível, assinado, indexado historicamente e validável por código antes de qualquer consumo pelo backend.

`harness/04-compliance-pipeline.md` exige:

- pacote versionado em `compliance/normative-packages/approved/<versao>/`;
- hash publicado;
- assinatura;
- manifest histórico;
- nenhuma chave privada versionada;
- falha fechada para pacote ausente, unsigned ou divergente.

## Decisão

1. O pacote normativo usa versionamento semântico no campo `version` de `package.yaml`.
2. Cada pacote aprovado possui estes sidecars obrigatórios:
   - `package.yaml`
   - `package.sha256`
   - `package.sig`
   - `package.public-key.pem`
   - `package.signature.yaml`
   - `CHANGELOG.md`
3. `releases/manifest.yaml` é o índice histórico obrigatório e aponta apenas para caminhos sob `compliance/normative-packages/approved/`.
4. `@afere/normative-rules` valida manifest, versão, data efetiva, hash, assinatura Ed25519 e `key_id` antes de aceitar o pacote.
5. O baseline `2026-04-20-baseline-v0.1.0` pode usar chave Ed25519 bootstrap offline porque a infraestrutura KMS ainda não está provisionada. A chave privada não é versionada.
6. A próxima mudança de pacote normativo precisa migrar a assinatura para KMS real ou registrar uma exceção explícita em ADR.
7. Mudança normativa publicada inicia análise em até 5 dias úteis e atualização em até 60 dias quando aplicável, seguindo o PRD §16.4.

## Comitê Revisor

- `regulator`: owner do conteúdo normativo e do pacote.
- `product-governance`: gate de release e histórico em `compliance/**`.
- `metrology-auditor`: pré-auditoria ISO/IEC 17025 e Cgcre.
- `legal-counsel`: risco jurídico, LGPD e claims regulatórios.
- `senior-reviewer`: revisão de código crítico em `packages/normative-rules/**`.

## Watchlist Normativa

- ABNT NBR ISO/IEC 17025:2017.
- Portaria Inmetro nº 157/2022.
- Portaria Inmetro nº 289/2021.
- Portaria Inmetro nº 248/2008 e 350/2012 como referência fora do escopo direto do MVP.
- DOQ-CGCRE-008 e DOQ-CGCRE-028.
- NIT-DICLA-021, NIT-DICLA-030 e NIT-DICLA-038.
- ILAC P10, P14, G8 e G24.

## Consequências

- Pacote normativo passa a ser um artefato auditável, não um dado implícito de código.
- Reemissão histórica pode reaplicar o pacote antigo por versão e hash.
- CI pode bloquear drift entre manifest e pacote aprovado.
- KMS permanece um blocker técnico antes de considerar P0-2 concluído.
