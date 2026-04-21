# Harness Dashboard

> Gerado por `pnpm harness-dashboard:write`. Não editar manualmente.

## Status por Prioridade

| Prioridade | Total | Em implementação | Implementado | Proposto/Não iniciado | Rejeitado |
|------------|-------|------------------|--------------|------------------------|-----------|
| P0 | 13 | 12 | 1 | 0 | 0 |
| P1 | 4 | 4 | 0 | 0 | 0 |
| P2 | 4 | 4 | 0 | 0 | 0 |

## Cobertura PRD §13

- 22/22 mapeados
- 11/22 validados por teste ativo
- 0/22 sem requisito mapeado

## Gates em check:all

- `typecheck`
- `test:tools`
- `test:ac`
- `test:regulatory`
- `copy-lint:check`
- `test:sync-simulator`
- `worm-check`
- `governance-gate`
- `escalation-check`
- `external-auditors-gate`
- `roadmap-check`
- `sync-simulator-check`
- `cloud-agents-policy-check`
- `compliance-structure-check`
- `agent-frontmatter-check`
- `slash-commands-check`
- `harness-design-tier3-check`
- `harness-dashboard:check`
- `runbook-check`
- `snapshot-diff-check`
- `redundancy-check`
- `budget:check`
- `tsx tools/validation-dossier.ts check --quiet`
- `sync:agents:check`
- `check:drift`

## Itens Abertos

- P0-1 (P0): Backend apps/api como peça de 1ª classe + agente backend-api — [~] Em implementação (scaffold Fastify + tRPC + Prisma + Docker Compose; /healthz + /trpc/health.ping verdes; lógica de domínio pendente para fatias V1+)
- P0-2 (P0): Pipeline de normative package assinado e versionado — [~] Em implementação (@afere/normative-rules valida pacote normativo com hash canônico SHA-256, assinatura Ed25519, sidecars de chave pública/metadados e releases/manifest.yaml; baseline 2026-04-20-baseline-v0.1.0 aprovado por bootstrap offline; KMS real ainda pendente)
- P0-3 (P0): Dossiê formal de validação contínua — [~] Em implementação (requirements.yaml, traceability-matrix.yaml, coverage-report.md e tools/validation-dossier.ts; 22/22 critérios do PRD §13 mapeados, 11/22 validados por teste ativo, demais seguem validation_status: planned)
- P0-4 (P0): Hard gates de multitenancy e trilha imutável — [~] Em implementação (Gates 1, 2, 3, 4, 5 e 6 funcionais em primeiras fatias; Gate 7 agora valida manifesto/hashes de snapshot-diff para perfis A/B/C, gera drafts automáticos de issue para CASCADE-003 no required-gates e mantém flake gate estrutural, enquanto a bateria final de 30 certificados canonicos em PDF/A ainda depende do renderer de emissao; Gate 5 cobre RLS, RBAC depende de auth real em apps/api)
- P0-5 (P0): Copy-lint regulatório — [~] Em implementação (packages/copy-lint funcional com 8 regras, CLI, hook PreCommit fail-closed, slash /claim-check; finding de 4 claims proibidos em PRD.md fechado por correção de copy + tools/copy-lint-prd.test.ts; pnpm copy-lint:check varre o repo em check:all; claim-set completo segue draft até revisão jurídica humana)
- P0-6 (P0): Agente product-governance + CODEOWNERS — [~] Em implementação (.github/CODEOWNERS, template de PR e pnpm governance-gate funcionais; pre-commit aciona o gate no delta; branch protection configurado em main exigindo required-gates; CODEOWNERS usa owner GitHub real e metadados agent-owners para papéis regulatórios; review obrigatório por CODEOWNERS depende de segundo colaborador/time GitHub real)
- P0-8 (P0): Matriz de escalonamento e rito de desempate — [~] Em implementação (tools/escalation-check.ts valida registro/template/ADR, bloqueia escalations abertas e entrou em check:all; tiebreaker designado na ADR 0009)
- P0-9 (P0): Runbooks de recuperação (KMS, hash-chain, WORM, normative package) — [~] Em implementação (compliance/runbooks/ contém R1-R4, calendário de drills e área de evidência; pnpm runbook-check valida estrutura e entra em pnpm check:all; drills reais de staging ainda pendentes)
- P0-10 (P0): Cascata de verificação L0→L5 + propagação bidirecional — [~] Em implementação (tools/verification-cascade.ts planeja L4 por delta, exige full regression e snapshot-diff em área crítica, valida 3 pareceres L5 por release, checa manifesto/hashes em compliance/validation-dossier/snapshots/, exige compliance/verification-log/_template.yaml, gera drafts determinísticos de issue para CASCADE-003, CASCADE-007 e CASCADE-008 em compliance/verification-log/issues/, usa fallback REQ -> EPIC do roadmap canônico quando o log trouxer apenas L1 e o workflow required-gates reconcilia criação/reabertura/fechamento das issues gerenciadas; a bateria final de 30 certificados em PDF/A segue pendente)
- P0-11 (P0): Redundância, loops e auto-consistência (property tests, flake gate, dupla checagem) — [~] Em implementação (evals/property-config.yaml declara N por criticidade, seeds canônicos e trace_path; pnpm redundancy-check:trace gera JSONL por seed em compliance/validation-dossier/evidence/property-traces/; pnpm redundancy-check valida traces, flake gate e precedentes regulatórios; self-consistency real e branch protection seguem pendentes)
- P0-12 (P0): 3 agentes auditores externos substituem humanos contratados (metrology-auditor, legal-counsel, senior-reviewer) — [~] Em implementação (tools/external-auditors-gate.ts valida agentes, paths de escrita, templates, casos-limite e pareceres L5 por release; entrou em check:all e pre-commit)
- P0-13 (P0): Operação dual Claude Code + Codex CLI com AGENTS.md canônico — [~] Em implementação (.claude/ + .codex/ espelhados; git hooks canônicos via .githooks/ + tools/install-hooks.sh; tools/install-mcp.sh; tools/sync-agents.ts gera .codex/agents/*.toml a partir de .claude/agents/*.md; pnpm check:all valida sync + drift)
- P1-1 (P1): Simulador determinístico de sync/conflito + fila de revisão humana — [~] Em implementação (evals/sync-simulator executa C1-C8 com 100 seeds determinísticos e o caos do PRD §13.20 com 1.000 OS em 5 dispositivos; tools/sync-simulator-check.ts valida cenários, seeds, propriedades e reports; entrou em check:all e pre-commit)
- P1-2 (P1): Política de Tier 3 com provenance/attestation (SLSA/sigstore) — [~] Em implementação (compliance/cloud-agents/policy.yaml vira fonte executável; tools/cloud-agents-policy-check.ts valida allowlist/blocklist, SLSA/Sigstore/GitHub Attestations e bloqueio fail-closed para branch cloud-agent/* sem attestation)
- P1-3 (P1): Diretório /compliance/ canônico — [~] Em implementação (árvore canônica criada no bootstrap; tools/compliance-structure-check.ts valida 56 artefatos e 13 referências no README, incluindo validation-dossier/snapshots/, verification-log/_template.yaml, verification-log/issues/ e roadmap/transversal-tracks.yaml; pnpm compliance-structure-check entrou em check:all e pre-commit; conteúdo semântico segue nos gates especializados)
- P1-4 (P1): Roadmap em fatias verticais V1–V5 — [~] Em implementação (compliance/roadmap/v1-v5.yaml virou fonte operacional; compliance/roadmap/transversal-tracks.yaml materializa as exclusões transversais; tools/roadmap-check.ts valida ordem V1-V5, dependências, gates de saída, metadata epic_id/linked_requirements, integridade dos REQ-IDs contra requirements.yaml, cobertura explícita dos REQ-PRD-* por fatia ou exclusão canônica e mapeamento obrigatório das exclusões para trilhas transversais com comandos reais do package.json; entrou em check:all e pre-commit)
- P2-1 (P2): Nomenclatura de agentes (frontmatter padrão) — [~] Em implementação (schema_version: 1 nos 13 agentes; tools/agent-frontmatter-check.ts valida nome canônico, role, model, tools, owner_paths, blocked_write_paths e handoff_targets; gate entrou em check:all e pre-commit)
- P2-2 (P2): Slash-commands regulatórios (/spec-norm-diff, /ac-evidence, /claim-check, /tenant-fuzz, /emit-cert-dry) — [~] Em implementação (.claude/commands/ contém os 5 comandos canônicos; tools/slash-commands-check.ts valida frontmatter, owner, risco, seções e bloco executável; gate entrou em check:all e pre-commit)
- P2-3 (P2): Dashboard de observabilidade do harness — [~] Em implementação (compliance/harness-dashboard.md gerado por tools/harness-dashboard.ts; resume P0/P1/P2, cobertura PRD §13 e gates do check:all; gate entrou em check:all e pre-commit)
- P2-4 (P2): Reescrever texto do Tier 3 no HARNESS_DESIGN.md raiz — [~] Em implementação (HARNESS_DESIGN.md §2.1 restringe Tier 3 a tarefas low-risk aprovadas pela política P1-2, com attestation verificável, revisão humana e product-governance; tools/harness-design-tier3-check.ts bloqueia regressão para backlog overnight sem qualificação)
