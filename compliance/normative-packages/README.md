# compliance/normative-packages/ — Pacotes normativos

**Owner:** `regulator`. Cada certificado grava o pacote normativo vigente no momento da emissão. Ver `harness/04-compliance-pipeline.md` Parte A.

## Estrutura esperada por pacote aprovado

```text
approved/<versao>/
├─ package.yaml
├─ package.sha256
├─ package.sig
└─ CHANGELOG.md
```

O verificador em `@afere/normative-rules` exige `package.sha256` e `package.sig`; pacote unsigned falha fechado. A assinatura real por KMS ainda é pendente e não deve armazenar chave privada neste repositório.
