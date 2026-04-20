---
description: Simula emissão de certificado (dry-run) por perfil A/B/C sem persistir nem assinar
---

Executa o pipeline de emissão contra o perfil `$ARGUMENTS` (`A`, `B` ou `C`) em modo dry-run.

Passos:

1. Carrega fixtures canônicos em `evals/snapshots/<perfil>/input.json`.
2. Chama `apps/api` em modo dry-run (sem persistência, sem assinatura real, sem QR).
3. Gera PDF em memória e compara byte-a-byte com snapshot de referência.
4. Reporta:
   - Diff de conteúdo (qualquer byte diferente = bloqueio).
   - Violações de §9 detectadas pelo `regulator`.
   - Incerteza/decisão do `metrology-calc`.
   - Normative package vigente.
5. Se tudo verde, marca execução em `compliance/validation-dossier/evidence/<timestamp>.json`.

Uso típico: antes de mudar template, engine ou norma, rodar dry para garantir que nada regrediu.

Ver `harness/05-guardrails.md` Gate 7 (full regression) e `harness/14-verification-cascade.md` L4.
