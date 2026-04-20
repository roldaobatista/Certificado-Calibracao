# 01 — Princípios não-negociáveis do harness

> Espelham os princípios do produto (PRD §2.3) aplicados ao processo de construção.

## Os 6 princípios

### 1. Conformidade por arquitetura vale para o harness também
Se o produto bloqueia emissão fora da norma (PRD §9), o harness bloqueia merge fora da política. Regras automatizáveis viram hook/CI, não recomendação em CLAUDE.md.

### 2. Spec-as-source, não spec-first descartável
Cada módulo (§7.x do PRD) tem arquivo em `specs/` com 6 elementos: outcomes, scope, constraints, prior decisions, task breakdown, verification. Agentes leem a spec antes de editar. Código que diverge da spec é bug de spec **ou** de código — nunca "código venceu".

### 3. Estado fora do processo
Sessões de agente são efêmeras. A verdade vive em Git + Postgres + artefatos versionados (specs, ADRs, dossiê de validação, pacote normativo). Nenhuma decisão relevante mora em memória de conversa.

### 4. Budgets são feature de produto
Caps de custo por task / usuário / tenant ficam no harness, não no billing mensal. Circuit breakers em loops e *tool errors* impedem runaway.

### 5. Context rot é inimigo
`/compact` manual aos 50%, `/clear` entre tasks, *rewind > correct*. Não deixar sessão passar de ~300–400k tokens em trabalho sensível. Subagentes isolam exploração para preservar contexto do orquestrador.

### 6. "Done" = AC verde + evidência arquivada
Não é opinião de revisor. Cada critério de aceite do PRD §13 tem ID estável, teste executável e evidência persistida em `/compliance/validation-dossier/`.

## Consequências operacionais

- Nenhum princípio acima é "soft". Violação em PR = CI falha.
- Agente `product-governance` (ver `07-governance-gate.md`) audita cumprimento por release.
- Revisão humana só entra onde automação não cobre — não como substituta de gate automático.
