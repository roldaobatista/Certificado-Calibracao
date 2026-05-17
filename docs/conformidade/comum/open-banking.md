---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Open Banking ⚪ (lazy — uso via Pluggy/Belvo BaaS)

> **Status:** ⚪ lazy — Aferê **não é instituição financeira** e **não tem certificação direta com BACEN/Open Finance**. Acesso a dados bancários via **Pluggy ou Belvo** (BaaS — Banking as a Service), que carrega a certificação.

---

## 1. Modelo

```
Cliente final → autoriza Pluggy/Belvo → Aferê consome via API → cobrança/conciliação
```

Aferê é **consumidor de dados** com consentimento do cliente final. Pluggy/Belvo são **iniciadores credenciados** pelo BACEN.

---

## 2. Por que via BaaS

Certificação Open Finance direta:
- Custo: R$ 200k-500k inicial + R$ 100k+/ano operacional
- Tempo: 12-18 meses
- Pessoas: time especializado dedicado
- Fora do escopo do Aferê (não somos fintech)

Via Pluggy/Belvo: custo por transação/conexão (~R$ 0.50-2 por conta-mês).

---

## 3. Decisões pendentes (escolha entre BaaS quando módulo financeiro começar)

| Critério | Pluggy | Belvo |
|----------|--------|-------|
| Cobertura BR | 90%+ | 80%+ |
| Preço | varia | varia |
| Sandbox | sim | sim |
| Suporte LatAm | parcial | nativo |

ADR a criar quando módulo financeiro entrar em desenvolvimento.

---

## 4. Compliance derivado

Mesmo via BaaS, Aferê precisa:
- **Consentimento explícito do cliente final** (UX clara + opt-out a qualquer momento)
- **LGPD RAT-XX:** documentar tratamento de dado bancário
- **Retenção:** dados bancários são `regulado` — ver `retencao-matriz.md`
- **Auditoria:** todo acesso a dado bancário no audit WORM

---

## 5. Riscos

- Pluggy/Belvo falha ou muda termos → fallback (segundo provider OU OFX manual)
- Cliente final revoga consentimento → Aferê remove dados em 15 dias úteis (LGPD art. 18)
- BACEN muda regulamentação → BaaS absorve, Aferê só atualiza integração

---

## 6. Pendências (V2)

- [ ] Escolher provedor BaaS (Pluggy vs Belvo) — ADR
- [ ] DPA específico do parceiro
- [ ] UX de consentimento + revogação
- [ ] Integração técnica (autenticação OAuth, refresh token, webhook)
- [ ] Testes em sandbox antes de produção

---

## 7. Referências

- BACEN Resolução 4.658 (Cybersecurity)
- LGPD lei 13.709
- `lgpd-rat.md`
- `retencao-matriz.md`
- `comum/integracoes-externas/pluggy-belvo.md` (a criar)
