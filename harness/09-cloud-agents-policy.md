# 09 — Política de Tier 3 (cloud agents)

> **P1-2**: restringe uso de cloud agents em domínio LGPD/regulado.

## Racional

O Tier 3 (Claude Code Web, Copilot Coding Agent, Jules) roda em VMs de terceiros. Em produto que lida com dados de laboratório, clientes corporativos, assinaturas eletrônicas e trilha auditável, expor paths sensíveis a esses agentes é inaceitável sem política dura.

## Allowlist — cloud agent PODE tocar

- `apps/web/ui/components/**` — componentes puros de UI, sem lógica de domínio.
- `apps/portal/ui/**` — mesma regra.
- `docs/**`
- `evals/fixtures/synthetic/**` — fixtures sintéticas (não reais).
- `tests/unit/**` quando limitado a utilitários sem acesso a schemas regulatórios.

## Blocklist — cloud agent NUNCA toca

- `apps/api/**`
- `apps/android/**`
- `packages/engine-uncertainty/**`
- `packages/normative-rules/**`
- `packages/db/**`
- `packages/audit-log/**`
- `compliance/**`
- `specs/**` quando ligadas a emissão, audit ou normativo
- `.claude/agents/**`
- `infra/**`
- Qualquer seed ou fixture com dados reais

## Enforcement

### Pre-receive hook no Git server
Rejeita push de branch rotulada como `cloud-agent/*` se tocar path bloqueado.

### Hook de PR
PR com label `cloud-agent` exige:
- Diff apenas em allowlist.
- Review humano + aprovação de `product-governance`.
- Fixture scanner: bloqueio se qualquer arquivo contiver CPF, CNPJ, e-mail, telefone ou nome reconhecido de cliente.

### Provenance obrigatória (attestation forte)

**Regra**: cloud agent só consegue abrir PR se o commit trouxer *attestation* verificável de sua origem. User-agent e metadata de commit são **sinal fraco** e não servem como gate.

Mecanismos aceitos:
- **SLSA Build Level 2+** com provenance gerado pela plataforma do cloud agent (GitHub Actions, Vertex AI, etc.) e publicado no registro de attestation.
- **Sigstore (cosign)** — assinatura de commit/artefato verificável contra identidade OIDC do agente.
- **GitHub Artifact Attestations** — quando disponível na plataforma que executou o agente.

**Enforcement**:
1. CI roda `cosign verify-blob` ou `gh attestation verify` no head commit do PR.
2. Attestation ausente ou inválida → PR é **rejeitado automaticamente** (não apenas rotulado).
3. Attestation válida → label `cloud-agent` aplicada e gates extras (allowlist, fixture scanner) entram em ação.
4. Fallback explícito: se nenhum mecanismo de attestation estiver disponível para a plataforma usada, cloud agent é proibido por essa plataforma até que esteja.

**Registro**: cada attestation verificada é arquivada em `compliance/cloud-agents-log.md` com hash + issuer + timestamp. Verificação falha gera entrada em `compliance/incidents/` com investigação obrigatória.

## Sanitização de fixtures

Cloud agent só opera com fixtures sintéticas geradas por `evals/fixtures/synthetic/generate.ts`:
- CPF/CNPJ: gerados com dígitos verificadores válidos mas sem correspondência real (prefixo 000.000.000-XX convencionado).
- Nomes: pool controlado com prefixo `TEST_`.
- E-mails: domínio `@example.kalibrium.test`.

Scanner em CI bloqueia qualquer padrão que não seja sintético.

## Auditoria

Todo PR com label `cloud-agent`:
- Vira entrada em `compliance/cloud-agents-log.md` com data, agente, paths tocados, veredito.
- Reviewed pelo `product-governance` quinzenalmente em batch.

## O que NÃO está em debate

- Cloud agent **nunca** roda com credencial de produção.
- Cloud agent **nunca** acessa banco real.
- Cloud agent **nunca** modifica CI/CD, hooks ou política de segurança.

## Revisão da política

Esta política é versionada em `compliance/cloud-agents-policy.md`. Alteração exige:
- PR em `compliance/`.
- Aprovação de `product-governance` + `lgpd-security`.
- ADR em `adr/` explicando motivação e impacto.
