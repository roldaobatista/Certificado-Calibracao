# packages/normative-rules — Regras normativas

**Owner:** `regulator`. DOQ-CGCRE, NIT-DICLA, Portaria 157/2022, ILAC P10/G8, RTM.

**Regra dura:** library consumida **apenas** por `apps/api`. Violação bloqueada por lint (Gate 6).

## Pacote normativo assinado

Primeira fatia de P0-2 implementada em `src/package.ts`:

- hash canônico SHA-256 de `package.yaml`;
- assinatura/verificação Ed25519 sobre o payload canônico;
- `verifySignedNormativePackage` falha fechado quando `package.sha256`, `package.sig` ou chave pública estão ausentes;
- `loadSignedNormativePackageFromDirectory(dir, publicKeyPem)` valida um diretório `package.yaml` + `package.sha256` + `package.sig`.

O KMS real ainda entra em uma fatia posterior. Os testes usam chave Ed25519 efêmera para provar o contrato criptográfico sem armazenar chave privada no repositório.
