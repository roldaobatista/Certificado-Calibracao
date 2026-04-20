# compliance/approved-claims.md — Claim-set aprovado

> **Owner:** `copy-compliance`. Aprovação jurídica: `legal-counsel` + `product-governance`.
> **Regra dura:** claim que aparece em site, portal, e-mails, docs comerciais, PRD ou README **precisa** estar nesta lista. Claim ausente = bloqueado por CI.

## Status

- **Versão:** 0.1.0-draft (2026-04-19)
- **Revisado por:** pendente (`legal-counsel` ainda não implementado — aprovação jurídica humana exigida antes de P0-5 virar `[x] Aprovado`)
- **Próxima revisão:** a cada claim novo + auditoria trimestral.

## Claims aprovados

### Sobre conformidade

✅ **"o sistema bloqueia as não conformidades listadas em [§9 do PRD] e impossibilita violação das regras declaradas"**
- Base: verificável, referencia lista concreta.
- Onde usar: site, portal, onboarding, ToS.

✅ **"conformidade sistêmica com ISO/IEC 17025 depende da operação — o sistema sustenta, não substitui"**
- Base: limitação honesta declarada em `AGENTS.md` §8.
- Onde usar: FAQ, site, portal, contrato.

✅ **"pré-auditoria automatizada antes de release"**
- Base: fluxo dos 3 auditores em `harness/16-agentes-auditores-externos.md`.
- Onde usar: site técnico, docs comerciais.

### Sobre assinatura eletrônica

✅ **"assinatura eletrônica em conformidade com MP 2.200-2/2001"**
- Base: requer parecer jurídico datado em `compliance/legal-opinions/`.
- Onde usar: ToS, documentação técnica.

✅ **"ICP-Brasil disponível como add-on opt-in"** (quando implementado)
- Base: Fase 2 do PRD §6.7.
- Onde usar: página de planos.

### Sobre LGPD

✅ **"dados armazenados em região brasileira (sa-east-1 ou equivalente)"**
- Base: requisito de WORM declarado em `harness/05-guardrails.md` Gate 4.
- Onde usar: DPA, Política de Privacidade.

## Claims proibidos (rules em `packages/copy-lint/rules.yaml`)

❌ `passa(m)? em qualquer auditoria` — promessa de conformidade absoluta.
❌ `100\s*%\s*conforme` — promessa indevida.
❌ `garantimos?\s+(ISO|acreditação|Inmetro|Cgcre)` — garantia indevida.
❌ `aprovado (pelo|pela) (Inmetro|Cgcre)` — claim falso de aprovação oficial.
❌ `substitui (o|a) auditori[ao]` — substitui auditoria.
⚠️ `conformidade\s+total` — warning, exige revisão jurídica.

## Fluxo para claim novo

1. Autor propõe claim em PR alterando este arquivo.
2. `copy-compliance` pré-revisa: enquadramento, alternativas.
3. `legal-counsel` emite parecer em `compliance/audits/legal/claim-<slug>.md`.
4. `product-governance` aprova no merge.
5. Após merge, claim entra em rotação via CI.

## Histórico

- **2026-04-19** — versão 0.1.0-draft criada no bootstrap do harness (P0-5 ainda `[ ] Proposto`).
