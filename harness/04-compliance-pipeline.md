# 04 — Pipeline de compliance (normative package + validation dossier)

> **P0-2 + P0-3**: transforma "evals" em dossiê de validação auditável e em versionamento formal do pacote normativo.

## Parte A — Normative package versionado e assinado

### Estrutura
```
compliance/normative-packages/
├─ drafts/
│  └─ 2026-04-19-doq-cgcre-028-v5.yaml
├─ approved/
│  └─ 2026-04-10-baseline-v1.0.0/
│     ├─ package.yaml            # conteúdo consolidado
│     ├─ package.sig             # assinatura KMS
│     ├─ package.sha256          # hash publicado
│     ├─ package.public-key.pem  # chave pública usada para validação
│     ├─ package.signature.yaml  # algoritmo, key_id, signer, signed_at
│     └─ CHANGELOG.md
└─ releases/
   └─ manifest.yaml              # índice histórico de todos os packages assinados
```

### Fluxo obrigatório

1. **Draft** — `regulator` cria `drafts/<YYYY-MM-DD>-<slug>.yaml` com mudanças propostas e referência à norma-fonte (DOQ/NIT/Portaria/ILAC).
2. **Diff semântico** — slash-command `/spec-norm-diff <draft>` gera:
   - Diff contra o pacote vigente.
   - Impacto em cada regra de §9 do PRD.
   - Lista de testes em `evals/regulatory/` potencialmente afetados.
3. **Revisão humana** — PR template dedicado exige **2 aprovadores** (sendo 1 fora do time de engenharia).
4. **Assinatura** — merge gera build que assina o pacote com chave em KMS e publica `package.sha256` em `releases/manifest.yaml`.
5. **Consumo** — `apps/api` só carrega pacotes assinados. Tentativa de consumo de *unsigned* = erro fatal no boot.
6. **Gravação por certificado** — cada certificado emitido persiste `normative_package.version`, `normative_package.hash`, `normative_package.effective_date`.

### Reprodutibilidade histórica
- Rerender de certificado antigo **reaplica o pacote da época** (não o atual). Isso é *invariant*; teste de regressão em `evals/ac/`.

### Implementação bootstrap

- `packages/normative-rules/src/package.ts` calcula hash canônico SHA-256 do pacote e verifica assinatura Ed25519.
- `loadSignedNormativePackageFromDirectory()` consome `package.yaml`, `package.sha256` e `package.sig`.
- `loadApprovedNormativePackageFromDirectory()` consome também `package.public-key.pem` e `package.signature.yaml`.
- `verifyApprovedNormativePackageRepository()` valida `releases/manifest.yaml` contra todos os pacotes aprovados apontados no índice.
- Pacote sem hash, assinatura, chave pública ou metadados de assinatura falha fechado.
- O baseline `2026-04-20-baseline-v0.1.0` está publicado em `compliance/normative-packages/approved/` e validado por `pnpm test:tools`.
- KMS real entra na próxima fatia; nenhuma chave privada é versionada. O baseline atual usa chave Ed25519 bootstrap offline.

---

## Parte B — Validation dossier

### Estrutura
```
compliance/validation-dossier/
├─ requirements.yaml             # fonte única de requisitos
├─ traceability-matrix.yaml      # gerada por CI
├─ evidence/
│  └─ REQ-§9.3-BLOCK-PADRAO-VENCIDO/
│     └─ 2026-04-19T14-22-00Z/
│        ├─ test-output.log
│        ├─ certificate-attempt.pdf
│        ├─ db-state.sha256
│        └─ summary.md
├─ revalidation-triggers.md
└─ coverage-report.md            # gerado por merge
```

### `requirements.yaml` (schema)

```yaml
- id: REQ-§9.3-BLOCK-PADRAO-VENCIDO
  source:
    doc: PRD.md
    section: "§9"
  description: Padrão com certificado vencido bloqueia emissão
  linked_specs: [specs/0007-wizard-emissao.md]
  linked_tests: [evals/regulatory/padrao-vencido.spec.ts]
  evidence_path: compliance/validation-dossier/evidence/REQ-§9.3-BLOCK-PADRAO-VENCIDO/
  owner: regulator
  criticality: blocker
  critical_paths: [packages/normative-rules/**]
```

Implementação bootstrap:

- `pnpm validation-dossier:write` gera `traceability-matrix.yaml` e `coverage-report.md`.
- `pnpm validation-dossier:check` valida schema, links para specs/testes e divergência manual da matriz.
- `tsx tools/validation-dossier.ts critical-tests <paths...>` retorna os testes de regressão para REQs `blocker`/`high` quando uma área crítica muda.

### Regras de gate

1. **Cobertura**: todo requisito do PRD §13 tem entrada em `requirements.yaml` + ao menos 1 teste ligado. CI falha se cobertura cair.
2. **Traceability matrix** é gerada automaticamente a cada merge e commitada. Divergência humana = CI quebra.
3. **Evidence archiving**: `qa-acceptance` tem responsabilidade dupla — rodar testes **e** persistir artefato assinado por execução.
4. **Revalidation triggers bidirecionais** — política em `revalidation-triggers.md` define quando uma mudança força revalidação. Ver `14-verification-cascade.md` para a regra de propagação completa (L0↔L5). Resumo:

   **Para baixo (correção em nível acima re-audita abaixo):**
   - Alteração em `packages/engine-uncertainty/**` → revalidar todos os REQs de incerteza.
   - Novo pacote normativo aprovado → revalidar REQs ligados às normas modificadas.
   - Mudança em template A/B/C → revalidar REQs de template.
   - L0 épico corrigido → toda story L1 derivada é re-auditada.
   - L1 spec corrigida → plano L2 e código L3 ligados são re-revistos.

   **Para cima (correção em código revela defeito estrutural):**
   - 3 correções consecutivas no mesmo REQ que alteraram AC → `spec-review-flag` reabre L1.
   - Múltiplos L1 do mesmo épico com correções do mesmo tipo → reabrir L0.
   - Correção que muda política → PR em `compliance/` + ADR.

5. **PR blocker**: alteração em `packages/engine-uncertainty/**` ou `packages/normative-rules/**` sem matriz atualizada = CI falha.
6. **Full regression em área crítica** (ver `14-verification-cascade.md` L4): mudança em `apps/api/src/domain/emission/**`, `apps/api/src/domain/audit/**`, `packages/engine-uncertainty/**`, `packages/normative-rules/**` ou `packages/audit-log/**` → CI roda 100% dos REQs da área, não só os do diff.

## ADR obrigatório

`adr/0004-normative-package-governance.md` documenta:
- Política de versionamento (semver do pacote).
- SLA de atualização após publicação de nova norma.
- Composição do comitê revisor.
- Watchlist de normas acompanhadas.
