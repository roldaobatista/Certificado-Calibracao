---
id: R1
version: 1
status: active
owner: lgpd-security
rto: 4h
rpo: "0"
dispatcher: lgpd-security + product-governance
executor: operador de infra com permissão KMS
---

# R1 — Rotação de chave KMS comprometida

## Trigger

Executar quando houver alerta de chave exposta ou suspeita de uso indevido:

- commit contendo material sensível;
- acesso indevido ao KMS;
- SIEM apontando uso anômalo;
- assinatura normativa ou checkpoint gerado por identidade não autorizada.

## Impacto

Toda assinatura de pacote normativo e checkpoint de audit feita com a chave comprometida fica suspeita até análise. Certificados históricos não devem ser alterados; a recuperação trata confiança de verificação, nova assinatura e continuidade da cadeia.

## Papéis

- Dispatcher: `lgpd-security` e `product-governance`.
- Executor: operador de infra com permissão KMS.
- Revisores: `regulator`, `legal-counsel`, `senior-reviewer` quando houver impacto em pacote normativo, LGPD ou código crítico.
- Comunicação: `product-governance` coordena status interno e eventual comunicação externa com jurídico.

## Passos

1. Abrir incidente em `compliance/incidents/<YYYY-MM-DD>-kms-key-compromise.md`.
2. Congelar assinatura de novos pacotes normativos e checkpoints.
3. Desabilitar a chave comprometida no KMS; não apagar a chave durante investigação.
4. Girar secrets de `apps/api` que referenciem a chave.
5. Criar chave KMS nova com política least privilege e grants auditáveis.
6. Registrar metadados da chave nova no incidente, sem versionar segredo ou material privado.
7. Reassinar pacotes normativos vigentes usando a chave nova.
8. Atualizar sidecars de assinatura e `compliance/normative-packages/releases/manifest.yaml`.
9. Emitir novo checkpoint de audit log assinado pela chave nova.
10. Manter a chave antiga em modo apenas verificação enquanto certificados históricos precisarem ser validados.

## Validação

1. Rodar `pnpm check:all`.
2. Rodar teste específico do pacote normativo com `pnpm exec tsx --test packages/normative-rules/src/package.test.ts`.
3. Confirmar que `verifyApprovedNormativePackageRepository()` aceita o pacote reassinado.
4. Confirmar continuidade da hash-chain entre último checkpoint antigo e primeiro checkpoint novo.
5. Emitir certificado dogfood em staging e validar QR público.

## Evidência

Arquivar em `compliance/runbooks/executions/<YYYY-MM-DD>-r1-kms-key-rotation/`:

- `summary.md` com timeline, dispatcher, executor e decisão de retorno;
- logs de verificação do pacote normativo;
- hash do pacote antes/depois da reassinatura;
- identificador público da chave antiga e nova;
- saída de `pnpm check:all`;
- referência ao incidente e ao PR de reassinatura.

## Drill

- Frequência: trimestral.
- Ambiente: staging com KMS espelhado.
- Critério de sucesso: RTO de 4h respeitado, RPO 0, pacote vigente validado, QR dogfood válido e certificado histórico continuando verificável.

## Revisão

Revisar anualmente, após incidente real, após mudança de provider KMS ou após alteração no fluxo de assinatura normativa. Mudança substantiva exige ADR.
