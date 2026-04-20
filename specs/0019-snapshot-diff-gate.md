# Spec 0019 — Snapshot-diff canonico no Gate 7

## Objetivo

Fechar a lacuna de P0-10 em que a cascata L0-L5 marcava snapshot-diff como obrigatorio, mas ainda nao validava artefatos canonicos nem bloqueava divergencia byte-a-byte.

## Escopo

- Tornar `tools/verification-cascade.ts` responsavel por validar `compliance/validation-dossier/snapshots/manifest.yaml`.
- Exigir perfis canonicos `A`, `B` e `C`, com hash SHA-256 aprovado por baseline.
- Bloquear baseline ausente, snapshot atual ausente, manifesto invalido e diff entre `baseline/` e `current/`.
- Versionar os snapshots dogfood iniciais em `compliance/validation-dossier/snapshots/`.
- Adicionar gate dedicado no pre-commit e script raiz `pnpm snapshot-diff-check`.
- Ampliar `tools/compliance-structure-check.ts` para tratar `snapshots/` como artefato canonico do dossie.

## Criterios de aceite

- O teste falha quando `manifest.yaml` nao existe.
- O teste falha quando um snapshot em `current/` diverge do `baseline/`.
- O teste passa quando os 3 perfis canonicos batem com o hash aprovado.
- `pnpm snapshot-diff-check` roda o gate estrutural no root.
- O pre-commit executa o gate quando o delta toca snapshots, ferramenta, spec, ADR ou status.

## Fora de escopo

- Nao gera PDF/A real nem renderiza certificados finais.
- Nao abre issues automaticamente no GitHub.
- Nao substitui a futura bateria de 30 certificados canonicos prevista para o renderer de emissao.
