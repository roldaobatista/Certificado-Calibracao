---
owner: roldao
revisado-em: 2026-05-23
status: stable
diataxis: reference
audiencia: agente
fase: Foundation F-C1
tipo: matriz-reconciliacao-P2
relacionados:
  - docs/faseamento/F-C1/spec.md
  - docs/faseamento/F-C1/plan.md
---

# F-C1 — Matriz de reconciliação P2 (3 reviews paralelos)

> **Pra quê:** consolidar achados dos 3 humano-substitutos (tech-lead-saas-regulado, advogado-saas-regulado, corretora-seguros-saas) detectando convergências (≥2 reviewers apontam o mesmo gap → eleva severidade) e divergências (disputas que Roldão decide).
>
> Padrão dos Marcos anteriores (M1, M2, M3 P2).

---

## 1. Resumo por reviewer

| Reviewer | Veredito | BLOQ | MED | BAIXO |
|---|---|---|---|---|
| tech-lead-saas-regulado | OK_COM_AJUSTES | 2 (TL-01, TL-02) | 8 | 0 |
| advogado-saas-regulado | OK_COM_AJUSTES | 2 (LGP-01, LGP-02) | 4 | 1 |
| corretora-seguros-saas | OK_COM_AJUSTES | 0 fase / 1 apólice (SEG-02) | 3 | 3 |
| consultor-rbc-iso17025 | **N/A** (F-C1 é hardening de infra, não toca calibração/cert/RT) | — | — | — |

**Total bruto:** 4 BLOQ (fase) + 1 BLOQ (apólice) + 15 MED + 4 BAIXO.

---

## 2. Convergências (≥2 reviewers apontam mesmo gap)

Convergência eleva severidade para BLOQ — entra em P3 retrofit obrigatório.

### CONV-FC1-A — SSRF guard incompleto (TL-03 + SEG-FC1-02)

| Reviewer | ID original | Severidade original | Lacuna apontada |
|---|---|---|---|
| tech-lead | TL-03 | MED | IPv6 ULA `fc00::/7`, CGNAT `100.64.0.0/10`, k8s/consul/etcd, `0.0.0.0/8` |
| corretora | SEG-FC1-02 | BLOQ-apólice | `fc00::/7`, `0.0.0.0/8`, `100.64.0.0/10` |

**Severidade reconciliada: BLOQ** (P3 retrofit).
**Decisão:** AC-FC1-003-3 expandido para cobrir as 4 faixas + sufixos DNS de descoberta interna.

### CONV-FC1-B — Retenção `admin_access` ausente (TL-05 + LGP-FC1-01 + SEG-FC1-04)

| Reviewer | ID original | Severidade original | Lacuna apontada |
|---|---|---|---|
| tech-lead | TL-05 | MED | Sem retenção declarada (LGPD art. 16 vs SEC-LOG ISO 27001) |
| advogado | LGP-FC1-01 | BLOQ | Sem finalidade + base legal + retenção + DPIA |
| corretora | SEG-FC1-04 | MED | Apólice E&O exige retenção ≥18 meses + cópia B2 WORM |

**Severidade reconciliada: BLOQ** (P3 retrofit — convergência de 3 reviewers).
**Decisão:**
- AC-FC1-002-3 expandido: finalidade declarada, base legal (LGPD art. 7º IX + art. 37), retenção **24 meses rolling** (atende ISO 27001 ≥6mo + ANPD orientação + apólice E&O ≥18mo), cópia espelho B2 WORM (preparação F-C2).
- AC-FC1-002-7 (novo): após 90 dias, substituir `usuario_id` por `usuario_id_hash` HMAC (pseudonimização — atende conflito art. 18 × auditoria imutável).
- Entregável adicional: `docs/conformidade/dpia/admin-access.md` (template ANPD) — DPIA não-bloqueante de F-C1 mas obrigatório antes do 1º tenant externo (GATE-LGPD-DPIA-ADMIN).

### CONV-FC1-C — Break-glass admin sem procedimento (TL-07 + SEG-FC1-01)

| Reviewer | ID original | Severidade original | Lacuna apontada |
|---|---|---|---|
| tech-lead | TL-07 | MED | "Lock-out garantido em incidente real" se MFA pessoal cair |
| corretora | SEG-FC1-01 | MED | Apólice exige procedimento de acesso emergencial documentado com aprovação dupla |

**Severidade reconciliada: MED** (entra em P4 como US adicional, não bloqueia P3).
**Decisão:** US-FC1-006 (novo) — conta `admin-recovery` com U2F físico (YubiKey ou similar) + alerta crítico em qualquer login + procedimento documentado em runbook.

### CONV-FC1-D — Rotação dogfooding sem destruição efetiva (LGP-FC1-05 + TL-08)

| Reviewer | ID original | Severidade original | Lacuna apontada |
|---|---|---|---|
| advogado | LGP-FC1-05 | MED | LGPD art. 16: chave antiga em backup/dotfile do Roldão indefinidamente |
| tech-lead | TL-08 | MED | Manual `.env` não escala pra produtivo (KMS MRK F-C3) |

**Severidade reconciliada: MED** (entra em P4 estendendo US-FC1-004).
**Decisão:**
- AC-FC1-004 expandido: (a) `shred -u` no `.env` antigo, (b) checklist "eliminar chave em ~/.bash_history, OneDrive, Google Drive, qualquer cópia", (c) declaração de "eliminação efetiva" datada no log, (d) mapeamento 1:1 procedimento manual → comando AWS KMS equivalente (preparação F-C3).

---

## 3. BLOQs únicos (sem convergência mas bloqueantes)

### TL-01 — Settings prod incompletos (proxy + form bomb)

`SECURE_PROXY_SSL_HEADER` + `CSRF_TRUSTED_ORIGINS` faltam — Hostinger fica atrás de proxy/Cloudflare. Sem isso, `is_secure()` retorna False e HSTS/SSL_REDIRECT entra em loop infinito (redirect-loop incident).

`DATA_UPLOAD_MAX_MEMORY_SIZE` + `DATA_UPLOAD_MAX_NUMBER_FIELDS` faltam — vetor de DoS via form bomb.

**Decisão:** AC-FC1-001-1 expandido com os 4 settings.

### TL-02 — HMAC sem canonical string explícito

Spec atual diz "HMAC-SHA256 do payload" sem definir QUAL string é assinada. Vulnerabilidade clássica de signature stripping (header poisoning, replay parcial).

**Decisão:** AC-FC1-003-3 cravar canonical string = `f"{timestamp}.{method}.{path}.{sha256(body)}"` + janela aceitação ≤5min + event_id em `consumer_idempotencia` (já existe ADR-0033).

### LGP-FC1-02 — DPA com destinos webhook out

Cada destino webhook out (Asaas, INMETRO, e-mail provider) é um **operador LGPD** (art. 39 — contrato escrito obrigatório). Adapter sem cadastro de DPA permite chamada antes do contrato existir.

**Decisão:**
- AC-FC1-003-8 (novo): tabela `webhook_destino` com colunas `papel_lgpd`, `dpa_url`, `dpa_assinado_em`, `finalidade`, `categorias_dados`.
- Hook `outbound-webhook-ssrf-check.sh` estendido: bloqueia chamada quando `destino.dpa_assinado_em IS NULL` ou vencido.
- Para Wave A: GATE-LGPD-DPA-WEBHOOK obriga DPA assinado antes do 1º tenant externo pago.

---

## 4. MED sem convergência (entram como sub-tasks em P4 — não bloqueiam P3)

| ID | Reviewer | Achado resumido | Onde entra |
|---|---|---|---|
| TL-04 | tech-lead | DNS rebinding com TTL=0 vs TTL>0 + múltiplos A/AAAA do getaddrinfo | AC-FC1-003-6 detalhamento (P4) |
| TL-06 | tech-lead | Session hijacking pós-MFA: cookie não rebindado a IP/UA hash | US-FC1-002 AC novo (P4) |
| TL-09 | tech-lead | ADR-0054 deve estar em §6 (entregável), não §7 (dependência) | Correção textual em spec (P3) |
| TL-10 | tech-lead | Tamanho da fase: ≤12 T-FC1 em plan.md OU justificar formalmente | plan.md declara estimativa (P3) |
| LGP-FC1-03 | advogado | IP como `ip_hash` HMAC (não em claro) | AC-FC1-002-3 (P3 — alinhar com CONV-FC1-B) |
| LGP-FC1-04 | advogado | Conflito art. 18 × auditoria — pseudonimização após 90d | AC-FC1-002-7 novo (P3 — alinhar com CONV-FC1-B) |
| LGP-FC1-06 | advogado | DPIA de `admin_access` | Entregável adicional não-bloqueante de F-C1 (P3) |
| SEG-FC1-03 | corretora | HMAC com rotação por destino ≤90d | AC novo em US-FC1-003 (P4) |
| SEG-FC1-05 | corretora | Rate-limit fraco vs credential stuffing distribuído | GATE-CYBER-CSTF Wave A (não F-C1) |
| SEG-FC1-06 | corretora | HSTS sem `includeSubDomains; preload` | AC-FC1-001-1 (P3) |

---

## 5. BAIXO / OK (anotados, sem ação na F-C1)

| ID | Reviewer | Status |
|---|---|---|
| LGP-FC1-07 | advogado | OK — screenshot de admin por blogueiro é fair use Lei 9.610/98 art. 46 III |
| SEG-FC1-05 | corretora | BAIXO — rate-limit 5/15min aceitável dogfooding; vira GATE Wave A |
| SEG-FC1-06 | corretora | BAIXO — HSTS preload absorvido em CONV em escopo P3 |
| SEG-FC1-07 | corretora | OK — rotação dogfooding-only explícita; F-C3 endereça produtivo |

---

## 6. GATEs adicionais pra Wave A / 1º tenant externo (não bloqueiam F-C1)

Consolidados dos 3 reviewers:

| GATE | Origem | O que exige |
|---|---|---|
| GATE-CYBER-IPV6 | corretora | SSRF guard cobrir IPv6 ULA + CGN + 0.0.0.0/8 (absorvido em CONV-FC1-A — entra na F-C1 retrofit) |
| GATE-CYBER-BREAKGLASS | corretora + tech-lead | Break-glass procedimento documentado (absorvido em CONV-FC1-C — entra US-FC1-006) |
| GATE-CYBER-HMACROT | corretora | Rotação HMAC ≤90d por destino |
| GATE-CYBER-AUDITRET | corretora | `admin_access` ≥18m + B2 WORM (absorvido em CONV-FC1-B) |
| GATE-CYBER-CSTF | corretora | Bot mitigation / CAPTCHA |
| GATE-CYBER-KMSROT | corretora | Rotação produtiva via KMS MRK (F-C3) |
| GATE-LGPD-DPA-WEBHOOK | advogado | Cada destino webhook out com DPA assinado antes do 1º cliente externo (absorvido em LGP-FC1-02 — entra na F-C1) |
| GATE-LGPD-DPIA-ADMIN | advogado | DPIA de `admin_access` antes do 1º tenant externo |
| GATE-LGPD-REG-TRATAMENTOS | advogado | Registro de tratamentos LGPD art. 37 incluindo F-C1 tabelas |
| GATE-LGPD-POL-RET | advogado | Política de retenção consolidada (matriz Marco 1 + F-C1 tabelas) |
| GATE-FC1-WAF-1 | tech-lead | WAF/Cloudflare/Coraza na frente do Django — F-C2 |
| GATE-FC1-FAIL2BAN-1 | tech-lead | fail2ban no VPS — F-C3 |
| GATE-FC1-LOGROT-1 | tech-lead | Rotação logs Django + admin_access archiver B2 WORM — F-C2 |
| GATE-FC1-OCSP-1 | tech-lead | OCSP/CRL em destinos HTTPS — ADR-0046 (Wave A) |
| GATE-FC1-DDOS-1 | tech-lead | Rate-limit global nginx limit_req — F-C3 |
| GATE-FC1-PENTEST | tech-lead | Pentest externo focado em SSRF/admin antes do 1º tenant pago |

---

## 7. Riscos rastreados (decisões aceitas conscientemente)

| Risco | Origem | Decisão |
|---|---|---|
| R-FC1-01 — F-C1 não cobre WAF/DDoS | tech-lead | Aceito; mitigação Cloudflare antes do 1º tenant pago (consultor humano para config) |
| R-FC1-02 — Pentest externo ainda obrigatório | tech-lead | Aceito; R$ 25-50k orçado pra antes do 1º tenant pago |
| R-FC1-03 — Race conditions sob carga real só aparecem em fuzzing | tech-lead | Aceito; pentest cobre |

---

## 8. Veredito da matriz

**OK_COM_RETROFIT** — F-C1 segue pra P3 (retrofit do spec) absorvendo:

- 4 BLOQs únicos (TL-01, TL-02, LGP-01 → CONV-FC1-B já absorve, LGP-02)
- 4 convergências (CONV-FC1-A SSRF, CONV-FC1-B retenção, CONV-FC1-C break-glass via US-FC1-006, CONV-FC1-D rotação)
- 7 MED não-convergentes que se conectam a ACs (TL-04, TL-06, LGP-03, LGP-04, LGP-06, SEG-03, SEG-06)
- 16 GATEs Wave A registrados em §6

Após P3, F-C1 vai pra P4 (implementação) com escopo total estimado em **12-14 T-FC1**.
