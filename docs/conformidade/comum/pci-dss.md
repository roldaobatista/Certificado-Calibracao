---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# PCI-DSS ⚪ (lazy — escopo fora do MVP-1)

> **Status:** ⚪ lazy — Aferê **não armazena nem processa cartão de crédito diretamente** na janela atual. PCI-DSS fora do escopo.
>
> **Pra quê (futuro):** se algum dia Aferê processar cartão direto, este doc orienta conformidade.

---

## 1. Por que está fora do escopo agora

Decisão arquitetural (PRD §5 non-goals):
> ❌ Pagamento direto com cartão (PCI-DSS escopo)

Pagamentos aceitos pelo Aferê:
- **Boleto** (gerado via gateway — sem dados de cartão)
- **PIX** (sem dados de cartão)
- **Transferência** (sem dados de cartão)

Cartão **só via redirect** pro gateway (Pluggy/Asaas/etc.) — dados nunca tocam servidor Aferê.

---

## 2. Quando se aplica (V2 ou V3 hipotético)

Se Aferê algum dia processar pagamento direto:
- Nível 4 PCI-DSS provavelmente (até 20k transações/ano)
- SAQ A-EP (Self-Assessment Questionnaire para e-commerce com redirect)
- Validação anual + ASV scan trimestral
- Custo: R$ 5-15k/ano + auditor PCI

---

## 3. O que evitar

Mesmo sem PCI no escopo, **nunca logar ou armazenar**:
- Número do cartão (PAN — Primary Account Number)
- CVV / CVC
- Banda magnética / chip data
- PIN

Hook `secrets-scanner` cobre commit; hook `log-redaction` cobre runtime.

---

## 4. Referências

- PCI-DSS v4.0
- PRD §5 (non-goals)
- `seguranca-dados.md`
