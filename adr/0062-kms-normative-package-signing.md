# ADR 0062 — Signer AWS KMS para pacote normativo

## Status

Aceito

## Contexto

O baseline normativo atual é seguro para bootstrap e verificação, mas ainda depende de assinatura offline fora da infraestrutura remota controlada. O próximo passo natural é oferecer uma trilha oficial de assinatura em KMS sem quebrar a compatibilidade com o baseline já publicado.

## Decisão

Adotar signer opcional via AWS KMS para o pacote normativo:

1. Preservar o contrato atual de verificação baseado em hash SHA-256, assinatura, chave pública e metadata versionada.
2. Acrescentar metadata opcional de provider KMS em `package.signature.yaml`.
3. Exigir, no signer remoto, chave assimétrica `SIGN_VERIFY` com key spec Ed25519 e algoritmo `ED25519_SHA_512`.
4. Expor uma CLI canônica para escrever os sidecars do pacote aprovado sem versionar material privado.
5. Manter o baseline bootstrap offline compatível até a ativação da infraestrutura real.

## Consequências

### Positivas

- O repositório passa a ter caminho de assinatura compatível com KMS real sem armazenar chave privada.
- O pipeline normativo fica mais próximo do desenho de P0-2 e do runbook de rotação de chave.
- O baseline atual não precisa ser refeito para aceitar metadata nova.

### Limitações honestas

- A existência do signer não provisiona IAM, grants, alias nem credenciais reais.
- O fluxo continua local/operacional até haver infraestrutura e decisão humana para ativação.
- O manifest histórico ainda depende de processo humano para promover o pacote assinado a baseline aprovado.
