---
owner: roldao
revisado_em: 2026-05-19
proximo_review: 2026-08-19
status: proposta
diataxis: explanation
audiencia: agente
decisao_requer: Roldão + CODEOWNERS (REGRAS-INEGOCIAVEIS.md é path anti-bypass D5)
relacionados:
  - .specify/memory/constitution.md
  - REGRAS-INEGOCIAVEIS.md
  - .claude/hooks/context-budget.sh
  - docs/faseamento/F-A/tasks.md
---

# ADR-0020 — Orçamento de `REGRAS-INEGOCIAVEIS.md` vs crescimento de IDs

## Contexto

Reconciliação F-A (T-FA-08 / AC-FA-009-3) detectou: `REGRAS-INEGOCIAVEIS.md`
está **acima do orçamento** — 192 linhas / ~13.783 tokens estimados
(`wc -c`/4). A Constituição §3 fixa teto **≤120 linhas**; o hook
`context-budget.sh` (gate vinculante — a Constituição diz "hooks contam
tokens, não linhas") usa **12.000 tokens** e já **avisa** (exit 0 —
warning, não bloqueio).

Causa real: o arquivo cresce **legitimamente** com novos `INV-` (cada
módulo de Wave A acrescenta invariantes). O teto de 120 linhas da
Constituição foi escrito antes de o catálogo de IDs existir; o próprio
hook já reconheceu isso elevando o budget para 12.000.

Mexer em `REGRAS-INEGOCIAVEIS.md` é alteração de **doc canônico
não-negociável** (D5 — path anti-bypass, exige aprovação CODEOWNERS) e
mudança de teto exige **ADR formal** (Constituição §"Mudança aqui
exige"). Por isso esta decisão **não pode** ser tomada unilateralmente
pelo agente — é encaminhada aqui.

## Decisão (proposta — pendente Roldão/CODEOWNERS)

**Opção A (recomendada): compactar mantendo a tabela de IDs.**
`REGRAS-INEGOCIAVEIS.md` mantém **apenas** a tabela canônica
`ID | regra (1 linha) | hook/teste | severidade | impacto`. Toda
justificativa longa, exemplo e narrativa migra para docs já citados por
ID (Constituição Regra mestre 2: "outros docs citam IDs, não duplicam" —
o inverso também vale: REGRAS não duplica a narrativa que vive nos docs
de conformidade/ADRs). Alvo: ≤120 linhas / ≤12.000 tokens com folga
para crescimento de IDs de Wave A. Zero perda semântica (IDs e hooks
permanecem; narrativa fica no doc temático).

**Opção B: ajustar o teto formalmente.** Reconhecer que o catálogo de
invariantes cresce com o produto e elevar o teto na Constituição (ex.:
"tabela de IDs sem teto de linha; cada linha ≤ 2 linhas; narrativa
proibida no arquivo") + alinhar `context-budget.sh`. Mantém status quo
do conteúdo; muda a régua.

**Recomendação:** **Opção A** — preserva o princípio "conciso vence
completo" (Constituição §3) e a função do arquivo (índice executável de
regras travadas em hook), sem inflar a régua a cada wave. Opção B só
adia o problema (o arquivo volta a crescer).

## Não-objetivos

- NÃO remover nenhum `INV-`/`SEC-`/`TST-`/`INV-TENANT-`/`INV-AUTHZ-`
  (são fonte única — só some via ADR próprio).
- NÃO enfraquecer hook algum.
- NÃO bloquear o fechamento de **código/segurança** de F-A: este é
  débito de **governança documental**, não de invariante de produto —
  rastreado, não varrido (ver `F-A/tasks.md` T-FA-08).

## Consequência

Até decisão: T-FA-08 fica **encaminhado** (não "aceito como ok"). O
hook continua avisando (sinal honesto, não silenciado). F-A pode fechar
P5 (auditores) pois nenhum invariante de produto/segurança está em
falta; a compactação executa após aprovação CODEOWNERS, antes de
declarar a **Foundation inteira** concluída.
