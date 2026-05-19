# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Fase/Marco/US.

**Fase:** **FOUNDATION F-A + F-B FECHADA via ritual Spec Kit**
(2026-05-19). Próximo: backlog Wave-A (#7/#8) → Marco 1 `clientes`
definitivo → Marco 2 `equipamentos`. **Modo:** AUTÔNOMO.

## Virada de método (decisão Roldão 2026-05-19)

Remendo auditoria-a-auditoria não convergia — causa de fundo: o ritual
Spec Kit foi pulado em F-A/F-B. Decisão: recriar spec FORWARD do zero
(governa o código) + ritual completo + reconciliar código existente.
Programa P1..P9: F-A primeiro, F-B sobre F-A fechada (lição C1⇄C3).

Trabalho válido anterior NÃO descartado — foi validado pela spec
(FB-C1+C3 `32aa278`, FB-C2 `53e3cc2`, FB-C4+C5 `7924390` seguem de pé).

## F-A FECHADA via ritual (commits `4951389`..`f3711d7`)

- P1 spec forward `docs/faseamento/F-A/spec.md` (substitui stories-f-a).
- P2 plan + review 3 subagentes (tech-lead/advogado/RBC) → bloqueantes
  absorvidos (eliminação×imutabilidade LGPD, marco de corte CGCRE,
  grants test=prod, etc.).
- P3 matriz: núcleo OK; 8 GAPs → T-FA-01..08.
- P4: 7 fechados causa-raiz + T-FA-08→ADR-0020. Suite 280, hooks
  130/130, makemigrations limpo.
- P5: **3 auditores Família 5 = PASS, ZERO CRÍTICO/ALTO/MÉDIO.**
  Reparos MÉDIO/BAIXO resolvidos na causa-raiz (INV-RITUAL-001 —
  MÉDIO bloqueia fechamento). Consolidado:
  `docs/faseamento/F-A/auditoria-familia5.md`.

Gates Wave A rastreados (não bloqueiam F-A dogfooding): GATE-1..7
(B2/WORM, verificação periódica, NTP, ciclo chave PII, hash
AcessoDadosCliente, ADR-0020, higiene pattern `::uuid`).

## F-B FECHADA via ritual (P6..P9)

P6 spec forward → P7 plan + review tech-lead+advogado (bloqueantes
absorvidos: binding, vigência única, ip_hash HMAC contexto,
atomicidade≠commit, allowlist anti-PII, GATE-FB-2/3/4) → P8 matriz +
6 T-FB causa-raiz (T-FB-01..06) → P9 **3 auditores Família 5 = PASS,
ZERO CRÍTICO/ALTO/MÉDIO**. Suite 293, cobertura 85.60%, hooks 130/130,
drills verdes. Consolidado: `docs/faseamento/F-B/auditoria-familia5.md`.
Gate de fechamento de fase = INV-RITUAL-001 (MÉDIO bloqueia igual a
CRÍTICO/ALTO; hook `ritual-gate-check.sh`).

**FOUNDATION (F-A + F-B) FECHADA pelo ritual completo.** A virada de
método convergiu — o ritual fechou de forma coerente o que o remendo
não fechava.

## Próximo passo (retomar)

Backlog Wave-A: #7 (lint sweep pré-existente, baseline 208 ruff —
I001/UP035/F401) + #8 (médios rodada 2 F-A) — NÃO reabrem Foundation.
Depois: Marco 1 `clientes` definitivo → Marco 2 `equipamentos` (ritual
orquestrador obrigatório). Gates Wave A (GATE-1..7 + GATE-FB-1..4)
rastreados pré-1º tenant externo.

## Fila

TaskList P9 do programa Spec Kit. Estado vivo aqui;
docs em `docs/faseamento/F-A/` e `docs/faseamento/F-B/`.
