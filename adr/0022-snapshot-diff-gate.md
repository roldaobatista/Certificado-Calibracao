# ADR 0022 — Snapshot-diff canonico no Gate 7

Status: Aprovado

Data: 2026-04-20

## Contexto

P0-10 e o Gate 7 de `harness/05-guardrails.md` exigem diff byte-a-byte de certificados canonicos antes do merge em area critica. A primeira fatia de `tools/verification-cascade.ts` apenas sinalizava que snapshot-diff era obrigatorio, mas ainda nao existia um artefato versionado nem um gate executavel para validar baseline e current.

Sem esse contrato, a cascata L0-L5 informava o requisito, mas nao o aplicava.

## Decisao

Criar um dossie canonico em `compliance/validation-dossier/snapshots/` com:

- `manifest.yaml` como fonte de verdade de perfis obrigatorios, politica fail-closed e hashes aprovados;
- `baseline/` para o snapshot aprovado;
- `current/` para a saida atual a ser comparada;
- `README.md` descrevendo a governanca do baseline.

`tools/verification-cascade.ts` passa a validar:

- existencia de `compliance/verification-log/README.md`;
- manifesto YAML valido;
- perfis obrigatorios `A`, `B` e `C`;
- exigencia de aprovacao de `regulator` e `product-governance` para update de baseline;
- hash SHA-256 do baseline aprovado;
- igualdade byte-a-byte entre `baseline/` e `current/`.

Tambem adicionamos `pnpm snapshot-diff-check` ao pipeline root e um hook dedicado no pre-commit.

## Consequencias

O Gate 7 deixa de ser apenas planejado e passa a bloquear drift estrutural de snapshots no proprio repositório.

O dossie de compliance ganha um ponto canonico para evidencias de snapshot-diff, e `tools/compliance-structure-check.ts` passa a exigir essa arvore minima.

## Limitacao

Esta fatia usa snapshots dogfood em texto para exercitar o gate e estabilizar a governanca do baseline. A bateria de 30 certificados canonicos em PDF/A continua dependente do renderer real de emissao e fica registrada como trabalho pendente em `harness/STATUS.md`.
