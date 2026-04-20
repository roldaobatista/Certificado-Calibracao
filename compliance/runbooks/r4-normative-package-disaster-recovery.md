---
id: R4
version: 1
status: active
owner: regulator
rto: 1h
rpo: "0"
dispatcher: regulator + product-governance
executor: backend-api
---

# R4 — Disaster recovery de pacote normativo

## Trigger

Executar quando o backend ou o verificador de pacote normativo falhar fechado:

- pacote ausente em `compliance/normative-packages/approved/`;
- `package.sha256` divergente;
- assinatura inválida;
- `releases/manifest.yaml` aponta para pacote inexistente;
- `apps/api` falha no boot por pacote normativo inválido.

## Impacto

Emissão regulada fica indisponível até recuperar pacote normativo verificável. Certificados históricos não devem ser rerenderizados com pacote diferente do registrado em sua emissão.

## Papéis

- Dispatcher: `regulator` e `product-governance`.
- Executor: `backend-api`.
- Apoio: operador de infra para storage imutável; `lgpd-security` para chave de assinatura; `metrology-auditor` para revisão do conteúdo restaurado.

## Passos

1. Confirmar erro de boot ou verificação e manter emissão fail-closed.
2. Identificar versão e hash esperados em `compliance/normative-packages/releases/manifest.yaml`.
3. Tentar restauração do storage WORM primário.
4. Baixar pacote, sidecars e manifest.
5. Validar hash e assinatura localmente.
6. Se primário falhar, recuperar de backup secundário frio ou offline.
7. Se primário e secundário falharem, recompilar pacote a partir do draft aprovado e ADR vigente.
8. Validar que pacote recompilado tem conteúdo canônico idêntico ao hash esperado.
9. Reassinar somente se o incidente também exigir R1.
10. Restaurar diretório aprovado e manifest.
11. Subir `apps/api` em staging e depois produção conforme rito de release.

## Validação

1. Rodar `pnpm exec tsx --test packages/normative-rules/src/package.test.ts`.
2. Rodar `pnpm check:all`.
3. Confirmar que `verifyApprovedNormativePackageRepository()` valida o manifest restaurado.
4. Emitir certificado dogfood e verificar QR.
5. Verificar rerender de certificado histórico usando a versão normativa original.

## Evidência

Arquivar em `compliance/runbooks/executions/<YYYY-MM-DD>-r4-normative-package-disaster-recovery/`:

- `summary.md` com versão normativa, hash esperado, hash restaurado e decisão de retorno;
- logs de verificação do pacote;
- fonte usada para restauração;
- PR que restaurou artefatos;
- parecer de `regulator` e `metrology-auditor` quando houver recompilação.

## Drill

- Frequência: semestral.
- Ambiente: staging.
- Cenário: corromper pacote normativo de staging, restaurar a partir do storage imutável e validar emissão dogfood.
- Critério de sucesso: RTO de 1h respeitado e RPO 0.

## Revisão

Revisar após mudança no pacote normativo, alteração em `packages/normative-rules/**`, troca de estratégia de assinatura ou incidente real. Mudança substantiva exige ADR.
