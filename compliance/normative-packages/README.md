# compliance/normative-packages/ — Pacotes normativos

**Owner:** `regulator`. Cada certificado grava o pacote normativo vigente no momento da emissão. Ver `harness/04-compliance-pipeline.md` Parte A.

## Estrutura esperada por pacote aprovado

```text
approved/<versao>/
├─ package.yaml
├─ package.sha256
├─ package.sig
├─ package.public-key.pem
├─ package.signature.yaml
└─ CHANGELOG.md
```

O índice histórico vive em:

```text
releases/manifest.yaml
```

O verificador em `@afere/normative-rules` exige `package.sha256`, `package.sig`, `package.public-key.pem` e `package.signature.yaml`; pacote unsigned ou sem chave pública falha fechado. `pnpm test:tools` valida o baseline aprovado contra `releases/manifest.yaml`.

## Baseline atual

- `approved/2026-04-20-baseline-v0.1.0/`
- Hash publicado: `b8a3f72a16bb9e7e70f4d52f084b384f830d2af3c0a7ad80f6ef3225d7aaa531`
- Chave: `bootstrap-ed25519-2026-04-20-v1`

A assinatura por KMS agora possui trilha canônica de tooling via `pnpm normative-package:kms-sign -- --dir <approved/...> --key-id <arn|alias> --region <aws-region> --signer <label>`, escrevendo `package.sha256`, `package.sig`, `package.public-key.pem` e `package.signature.yaml` no formato esperado pelo verificador. A ativação em produção continua pendente de infraestrutura/credenciais reais; este baseline segue com chave Ed25519 bootstrap offline, com apenas chave pública e metadados versionados.
