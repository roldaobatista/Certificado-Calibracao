# Spec 0084 — Assinatura KMS do pacote normativo

## Contexto

O pacote normativo aprovado já possui hash canônico, assinatura Ed25519 bootstrap offline, chave pública versionada e manifesto histórico. A principal lacuna restante de P0-2 é a assinatura remota em KMS real, para que novos pacotes normativos não dependam de chave privada fora da infraestrutura controlada.

Sem esta fatia, o repositório consegue verificar pacotes aprovados, mas ainda não oferece um caminho nativo para assinar um novo pacote com KMS real e materializar os sidecars esperados pelo pipeline.

## Escopo

- Adicionar em `@afere/normative-rules` um signer opcional usando AWS KMS para pacotes normativos.
- Exportar artefatos prontos para `package.sha256`, `package.sig`, `package.public-key.pem` e `package.signature.yaml`.
- Validar, no signer KMS, key usage, key spec e algoritmo compatíveis com assinatura Ed25519.
- Criar CLI canônica para assinar um diretório de pacote normativo já preparado com `package.yaml`.
- Registrar no metadata de assinatura quando o pacote foi assinado por KMS.

## Fora de escopo

- Provisionar de fato a chave KMS, grants, IAM, alias ou política de produção.
- Armazenar credenciais AWS, tokens, secrets ou material privado no repositório.
- Reassinar automaticamente o baseline já aprovado sem decisão humana.
- Integrar o signer KMS ao CI remoto com credenciais reais.

## Critérios de aceite

- `packages/normative-rules/src/kms-signing.ts` assina um pacote normativo via AWS KMS e retorna sidecars completos.
- A implementação falha fechada quando a chave não é `SIGN_VERIFY`, não é Ed25519 ou não anuncia `ED25519_SHA_512`.
- `package.signature.yaml` passa a aceitar metadata de provider KMS sem quebrar o baseline bootstrap offline.
- `tools/normative-package-kms-sign.ts` assina um diretório com `package.yaml` e escreve os sidecars no formato canônico.
- Os testes cobrem o caminho feliz, key spec incompatível e key usage incompatível sem depender de AWS real.

## Evidência

- `pnpm exec tsx --test packages/normative-rules/src/package.test.ts packages/normative-rules/src/kms-signing.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
