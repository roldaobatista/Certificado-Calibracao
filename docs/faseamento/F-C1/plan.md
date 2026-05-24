---
owner: roldao
revisado-em: 2026-05-23
status: stable
diataxis: reference
audiencia: agente
fase: Foundation F-C1
tipo: plan-ata-P2
relacionados:
  - docs/faseamento/F-C1/spec.md
  - docs/faseamento/F-C1/matriz-reconciliacao.md
---

# Foundation F-C1 — Plan (ata P2 + plano P3/P4/P5)

> **Ata da fase P2 do ritual Spec Kit** + plano operacional das fases seguintes. Reconciliação detalhada em `matriz-reconciliacao.md`.

---

## 1. P1 — spec FORWARD

- ✅ Entregue 2026-05-23 (`spec.md` 220L, draft).
- Escopo: 4 frentes (settings prod, /admin/ hardening, ADR-0054 webhook out aceita+implementada, rotação dogfooding).
- 5 user stories (US-FC1-001..005) com AC binários.
- 6 invariantes propostas (INV-ADMIN-001, INV-PROD-SET-001, INV-WEBHOOK-OUT-001..004).

## 2. P2 — 3 reviews paralelos (2026-05-23)

Reviewers acionados:

| Reviewer | Veredito | Achados (BLOQ / MED / BAIXO) | Arquivo do output |
|---|---|---|---|
| tech-lead-saas-regulado | OK_COM_AJUSTES | 2 / 8 / 0 | embed na matriz §1 |
| advogado-saas-regulado | OK_COM_AJUSTES | 2 / 4 / 1 | embed na matriz §1 |
| corretora-seguros-saas | OK_COM_AJUSTES | 0 fase + 1 apólice / 3 / 3 | embed na matriz §1 |
| consultor-rbc-iso17025 | **N/A** | — | F-C1 é hardening de infra; não toca calibração/cert/RT/ISO 17025 |

**Convergências fortes (≥2 reviewers):** 4 (SSRF, retenção `admin_access`, break-glass admin, rotação sem destruição efetiva).

**Detalhe completo:** `matriz-reconciliacao.md`.

## 3. P3 — retrofit do spec (próximo passo)

Spec.md deve ser atualizado absorvendo:

### Retrofit obrigatório (BLOQ — bloqueia avanço a P4)

| Item | Origem | Mudança no spec.md |
|---|---|---|
| R-1 | TL-01 | AC-FC1-001-1 expandido com `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS`, `DATA_UPLOAD_MAX_MEMORY_SIZE`, `DATA_UPLOAD_MAX_NUMBER_FIELDS`. HSTS com `includeSubDomains; preload` (absorve SEG-FC1-06). |
| R-2 | TL-02 | AC-FC1-003-3 com canonical string explícita: `f"{timestamp}.{method}.{path}.{sha256(body)}"` + janela ≤5min + event_id em `consumer_idempotencia`. |
| R-3 | CONV-FC1-A (TL-03 + SEG-02) | AC-FC1-003-3 SSRF guard expandido: + IPv6 ULA `fc00::/7`, + CGNAT `100.64.0.0/10`, + `0.0.0.0/8`, + sufixos DNS internos. |
| R-4 | CONV-FC1-B (TL-05 + LGP-01 + SEG-04) | AC-FC1-002-3 expandido: finalidade declarada, base legal (LGPD art. 7º IX + art. 37), retenção **24 meses rolling**, cópia espelho B2 WORM. AC-FC1-002-7 novo: pseudonimização `usuario_id` → `usuario_id_hash` HMAC após 90d. |
| R-5 | LGP-FC1-02 | AC-FC1-003-8 novo: tabela `webhook_destino` com DPA registrado; hook bloqueia chamada sem DPA assinado. |
| R-6 | TL-09 | Reposicionar ADR-0054 — sai de §7 (dependência) e entra como item 9 do §6 (entregável). |
| R-7 | TL-10 | Declarar estimativa: 12-14 T-FC1 (P4). Acima disso exige justificativa formal. |

### Retrofit dirigido (MED não-convergente — entra em ACs P4)

| Item | Origem | Onde absorve |
|---|---|---|
| R-8 | TL-04 | AC-FC1-003-6 detalhamento DNS rebinding (TTL=0 vs TTL>0 + múltiplos A/AAAA) |
| R-9 | TL-06 | US-FC1-002 AC novo: middleware grava `session['admin_ip_hash']`+`admin_ua_hash` e valida em cada request |
| R-10 | LGP-FC1-03 | Alinhado com R-4: IP como `ip_hash` HMAC (não em claro) |
| R-11 | LGP-FC1-04 | Alinhado com R-4 (AC-FC1-002-7 pseudonimização) |
| R-12 | LGP-FC1-06 | Entregável adicional: `docs/conformidade/dpia/admin-access.md` (template ANPD; não bloqueia F-C1; GATE-LGPD-DPIA-ADMIN antes do 1º tenant externo) |
| R-13 | SEG-FC1-03 | US-FC1-003 AC novo: chave HMAC por destino tem `expires_at`; rotação ≤90d documentada |
| R-14 | CONV-FC1-C | **US-FC1-006 novo:** conta `admin-recovery` com U2F físico + alerta crítico em qualquer login + procedimento documentado em runbook |
| R-15 | CONV-FC1-D | AC-FC1-004 expandido: `shred -u` no `.env` antigo, checklist eliminação efetiva, declaração datada, mapeamento manual → comando KMS |

### GATEs Wave A (não entram em F-C1; rastreados pra checklists futuros)

- 16 GATEs listados em `matriz-reconciliacao.md §6`. Não bloqueiam fechamento de F-C1.

## 4. P4 — implementação (após P3 fechar)

### Estimativa de T-FC1 (12-14 tarefas)

| Bloco | Tarefas estimadas | Conteúdo |
|---|---|---|
| Settings prod | T-FC1-01..03 (3) | hook `prod-settings-check.sh` + `config/settings/prod.py` revisto + casos teste |
| /admin/ hardening | T-FC1-04..07 (4) | middleware `AdminHardeningMiddleware` + migration `0017_admin_access` (RLS + trigger anti-mutation) + hook `admin-hardening-check.sh` + middleware session-rebind |
| ADR-0054 implementação | T-FC1-08..11 (4) | porta `OutboundWebhookProvider` (Protocol) + adapter `RequestsWebhookOut` + hook `outbound-webhook-ssrf-check.sh` + tabela `webhook_destino` |
| Rotação dogfooding | T-FC1-12 (1) | `docs/operacao/rotacao-credenciais-dogfooding.md` + drill arquivado |
| Break-glass admin | T-FC1-13 (1) | conta `admin-recovery` + procedimento + runbook §11 |
| Drill validador | T-FC1-14 (1) | comando `validar_f_c1` (6 drills end-to-end) |

**Total: 14 tarefas — dentro do orçamento. Acima disso, justificativa formal exigida.**

### Ordem sugerida (dependências)

```
T-FC1-01 (hook prod-settings) → T-FC1-02 (settings/prod.py) → T-FC1-03 (testes)
                                                                ↓
T-FC1-04 (middleware admin) ← T-FC1-05 (migration admin_access) ← T-FC1-06 (hook admin) ← T-FC1-07 (session-rebind)
                                                                                              ↓
T-FC1-08 (Protocol webhook) → T-FC1-09 (adapter) → T-FC1-10 (hook SSRF) → T-FC1-11 (webhook_destino+DPA)
                                                                                              ↓
T-FC1-12 (rotação dogfooding) → T-FC1-13 (break-glass) → T-FC1-14 (validar_f_c1)
```

Paralelizações possíveis: T-FC1-01..03 (settings) pode rodar em paralelo a T-FC1-08..11 (webhook); T-FC1-04..07 (admin) depende de F-B (MFA já fechado).

## 5. P5 — 10 auditores Família 5 + auditoria-familia5.md

Após P4 fechar com `validar_f_c1` 6/6 PASS, disparar 10 auditores em paralelo. Critério de fechamento: ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO (INV-RITUAL-001).

Se houver MED+, abrir conserto causa-raiz e 2ª passada (padrão M2 P5).

## 6. Critério de saída da F-C1

- [ ] P3 retrofit aplicado em `spec.md` (4 BLOQs + 4 convergências + 7 MED dirigidos)
- [ ] Spec promovida `draft` → `proposta` em P3
- [ ] P4 entrega 12-14 T-FC1 com testes verdes
- [ ] `validar_f_c1` 6/6 PASS
- [ ] Suite total verde (hooks 250+ + pytest 621+)
- [ ] P5 10 auditores ZERO C/A/M
- [ ] Spec promovida `proposta` → `stable`
- [ ] AGENTS §11: ADR-0054 promovida `proposta` → `aceito` (foi aceito DENTRO desta fase)
- [ ] REGRAS-INEGOCIAVEIS.md: INV-ADMIN-001, INV-PROD-SET-001, INV-WEBHOOK-OUT-001..004 cravadas
- [ ] `docs/conformidade/dpia/admin-access.md` criado (não bloqueia F-C1; bloqueia 1º tenant externo)

## 7. Histórico

- 2026-05-23: P1 entregue (spec.md draft).
- 2026-05-23: P2 entregue (3 reviews paralelos + matriz reconciliação + esta ata).
- Próximo passo: P3 retrofit do spec.md absorvendo 4 BLOQs + 4 convergências + 7 MED dirigidos. Após Roldão aprovar a matriz.
