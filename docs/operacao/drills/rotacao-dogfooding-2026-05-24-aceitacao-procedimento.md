---
owner: roldao
revisado-em: 2026-05-24
status: stable
diataxis: reference
audiencia: auditor
tipo: drill-aceitacao
relacionados:
  - docs/operacao/rotacao-credenciais-dogfooding.md
  - docs/faseamento/F-C1/spec.md
---

# Drill — Aceitação do procedimento de rotação dogfooding (T-FC1-12)

> **Não é um drill de rotação real.** É a aceitação formal do procedimento canônico criado em `rotacao-credenciais-dogfooding.md`. A primeira execução real depende de Roldão (toca o `.env` real do host).

## Contexto

T-FC1-12 da F-C1 P4 entrega o procedimento documentado de rotação dogfooding. O AC binário (AC-FC1-004-1..5) exige:

- (1) procedimento documentado com checklist passo-a-passo — ✅
- (2) mapeamento 1:1 procedimento manual → comando AWS KMS equivalente — ✅
- (3) drill executado com declaração de eliminação efetiva — ⏳ depende de execução real pelo Roldão
- (4) procedimento referenciado no §10 do runbook.md — ⏳ próximo commit
- (5) `shred -u` no `.env` antigo + checklist eliminação efetiva — ✅ documentado

Itens 1, 2, 5 fechados nesta sub-onda. Itens 3 e 4 ficam para execução real + commit subsequente.

## Aceitação do procedimento

Em 2026-05-24, eu (Claude Code, atuando no escopo da Onda 2 plano-v2 / F-C1 P4):

- Declaro que o procedimento em `docs/operacao/rotacao-credenciais-dogfooding.md` segue as 4 cláusulas do AC-FC1-004 expandidas no P3 retrofit (CONV-FC1-D + LGP-FC1-05 + TL-08).
- Confirmo que o procedimento cobre as 5 credenciais alvo (DJANGO_SECRET_KEY, PII_HASH_KEY + ID, QR_HMAC_KEY + ID, QR_IP_RATELIMIT_SALT, ADMIN_ACCESS_HASH_SALT da F-C1).
- Confirmo que o mapeamento manual → KMS (§4) explicita os 7 passos do dogfooding e seus equivalentes produtivos em F-C3.
- Confirmo que o template de declaração datada (§3.7) cobre LGPD art. 16 (eliminação efetiva da chave anterior).

## Próximos drills (a executar pelo Roldão)

| Drill | Quando | Arquivo arquivado |
|---|---|---|
| 1º real (qualquer chave) | Antes do P5 auditores | `rotacao-dogfooding-YYYY-MM-DD.md` |
| Recorrência mensal (a partir do 1º) | Mensal | idem com data |
| GATE-CYBER-KMSROT (F-C3) | Antes do 1º deploy externo | Diferente — KMS automático |

## Status do AC-FC1-004

| AC | Status pós aceitação do procedimento |
|---|---|
| AC-FC1-004-1 (procedimento documentado + mapeamento KMS) | ✅ FECHADO |
| AC-FC1-004-2 (drill executado com sessões inválidas) | ⏳ aguarda execução real |
| AC-FC1-004-3 (log do drill arquivado com declaração datada) | ⏳ aguarda execução real |
| AC-FC1-004-4 (procedimento referenciado em runbook §10) | ⏳ próximo commit (T-FC1-12 finalização) |
| AC-FC1-004-5 (shred + checklist eliminação) | ✅ FECHADO (documentado) |

T-FC1-12 fica como **PARCIAL** até a execução real do drill (Roldão). Conta como "documental fechado" pra avançar pra T-FC1-13 e T-FC1-14; **bloqueia** P5 (auditores) até execução real arquivada.

## GATE

- **GATE-FC1-ROTACAO-DRILL-REAL**: antes do P5 da F-C1, Roldão executa rotação de pelo menos 1 chave dogfooding com log arquivado em `rotacao-dogfooding-YYYY-MM-DD.md`.
