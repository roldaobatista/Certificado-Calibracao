# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Fase/Marco/US.

**Fase:** Foundation reconstruída via ritual Spec Kit. **F-A FECHADA**
(2026-05-19). Próximo: **P6** (F-B spec forward). **Modo:** AUTÔNOMO.

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
  118/118, makemigrations limpo.
- P5: **3 auditores Família 5 = PASS, ZERO CRÍTICO/ALTO.** Reparos
  MÉDIO/BAIXO resolvidos. Consolidado:
  `docs/faseamento/F-A/auditoria-familia5.md`.

Gates Wave A rastreados (não bloqueiam F-A dogfooding): GATE-1..7
(B2/WORM, verificação periódica, NTP, ciclo chave PII, hash
AcessoDadosCliente, ADR-0020, higiene pattern `::uuid`).

## Próximo passo (P6 — retomar)

F-B spec forward → P7 plan+review subagentes → P8 reconciliação
(absorve ALTOs FB-A1/A4/A5/A6/A7 como GAPs) + conserto → P9 Família 5
+ **fechar Foundation**. Depois: backlog Wave-A (#7/#8), Marco 1
`clientes` definitivo → Marco 2 `equipamentos`.

## Fila

TaskList P9 do programa Spec Kit. Estado vivo aqui;
docs em `docs/faseamento/F-A/` e `docs/faseamento/F-B/`.
