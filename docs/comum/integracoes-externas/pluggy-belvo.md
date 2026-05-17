---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Pluggy / Belvo — Open Banking BaaS

## Resumo

| Item | Detalhe |
|------|---------|
| Função | Acesso a dados bancários do tenant (extrato, conciliação, boleto registrado) |
| Status | ⏳ Wave B (financeiro) |
| Anti-corrosion | `infrastructure/banking/baas_provider.py` |
| Custo aprox | R$ 0,50-2 por conta bancária por mês |

---

## Por que via BaaS

Ver `conformidade/comum/open-banking.md`:
- Certificação direta com BACEN custa R$ 200k+ + 12-18 meses
- BaaS carrega a certificação
- Aferê é consumidor de dados com consentimento do cliente final

---

## Pluggy vs Belvo (decisão pendente)

| Critério | Pluggy | Belvo |
|----------|--------|-------|
| Cobertura BR | 90%+ | 80%+ |
| Sandbox | sim | sim |
| Suporte LatAm | parcial | nativo |
| Custo | R$ 0,50-1,50/conta/mês | R$ 0,80-2/conta/mês |

ADR específica quando Wave B começar.

---

## Fluxo

```
Cliente final do tenant → autoriza acesso via Pluggy/Belvo
                                    ↓
                          BaaS retorna token de acesso
                                    ↓
                          Aferê consome extrato + saldo
                                    ↓
                          Conciliação automática
```

---

## DPA / LGPD

- **Consentimento explícito** registrado
- **Opt-out** disponível a qualquer momento → BaaS revoga token
- **Retenção** de dado bancário: ver `retencao-matriz.md` (categoria regulado)
- **Audit log** de cada acesso

---

## Pendências

- [ ] ADR Wave B
- [ ] Escolher BaaS (Pluggy vs Belvo)
- [ ] DPA específico
- [ ] UX de consentimento + revogação

---

## Referências

- `conformidade/comum/open-banking.md`
- ADR Wave B (a criar)
- `arquitetura/anti-corrosion-layer.md` (porta Banking)
