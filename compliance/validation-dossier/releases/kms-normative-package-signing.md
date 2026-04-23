# Signer KMS do pacote normativo

## Escopo

- Signer opcional via AWS KMS para pacotes normativos.
- Metadata de assinatura compatível com provider `aws-kms`.
- CLI canônica para gerar sidecars do pacote aprovado sem chave privada no repositório.

## Evidências executadas

- `pnpm exec tsx --test packages/normative-rules/src/package.test.ts packages/normative-rules/src/kms-signing.test.ts`
- `pnpm --filter @afere/normative-rules typecheck`

## Limitações honestas

- O signer não provisiona a chave KMS, grants ou credenciais.
- O baseline aprovado atual continua bootstrap offline até decisão humana e infraestrutura real.
- A integração do signer com CI remoto e rotação real de chaves permanece dependente de ambiente AWS configurado.
