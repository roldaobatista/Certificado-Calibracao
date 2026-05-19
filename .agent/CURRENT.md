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

## Feito nesta sessão (2026-05-19)

- **INV-RITUAL-001** (commit `ca8909e`, no servidor): MÉDIO bloqueia
  avanço de fase, igual a CRÍTICO/ALTO. Regra em REGRAS-INEGOCIAVEIS +
  hook `ritual-gate-check.sh` (PreToolUse Write|Edit) + 3 prompts de
  auditor + ritual. _test-runner 130/130. Pedido explícito do Roldão.
- **Lint sweep #7** (commit `3aeb3d4`, no servidor): ruff 193→0,
  format 100%, avisos de critério na causa-raiz. Suíte 293 verde em
  ordem fixa. NÃO reabre Foundation.
- **Flake visão-360 RESOLVIDO na causa-raiz** (commit `6c3e7b8`, no
  servidor): bug de PRODUÇÃO, não artefato de teste. `sanitizar_payload_audit`
  redigia `cliente_id` quando o UUID coincidia com regex de CPF/telefone
  (~8,4% dos uuid4). `registrar_auditoria` grava `payload_jsonb` cru; o
  endpoint sanitizava só na leitura → filtro do banco acerta evento, mas
  resposta volta com `cliente_id='[REDACTED]'`, quebrando correlação
  evento↔cliente na timeline da visão-360. Pista "depende de
  `pytest-randomly` seed" era ruído amostral (uuid4 vem de `os.urandom`).
  Fix: guard de UUID no ramo string do sanitizador antes das regexes —
  UUID é identificador surrogate, nunca PII (CPF/CNPJ/telefone/e-mail real
  jamais parseia como UUID). Cobre `cliente_id`, `usuario_id`,
  `causation_id`, qualquer chave UUID-valued. Regressão
  `tests/test_sanitizar_payload_audit.py` varre 5000 uuid4. Suíte
  **299 passed** (293→299), cobertura **85.85%** (85.60→85.85), hooks
  130/130. **MÉDIO sob INV-RITUAL-001 destravado.**

## Próximo passo (retomar) — tarefa ativa

Backlog Wave-A #8 (médios rodada 2 F-A) → Marco 1 `clientes` definitivo →
Marco 2 `equipamentos` (ritual obrigatório). Gates Wave A
(GATE-1..7 + GATE-FB-1..4) rastreados pré-1º tenant externo.

## Fila

#7 lint sweep ✅ + #6 flake visão-360 ✅ — fila zera com Foundation
intacta. Próxima: #8. Estado vivo aqui; docs em `docs/faseamento/F-A/` e
`.../F-B/`.
