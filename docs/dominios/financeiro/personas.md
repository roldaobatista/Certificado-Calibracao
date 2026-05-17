---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Personas do domínio Financeiro

> Detalhe rico em `docs/discovery/personas-detalhadas.md`. Aqui ficam só as **financeiras**.

---

## P-FIN-01 — Responsável financeiro do tenant

**Quem é:** 25-50 anos. Emite NFS-e, controla cobrança, faz conferência. Pode ser pessoa dedicada (em tenant maior) ou acumular com gerente/dono (em tenant pequeno).

**Goals:**
- Emitir NFS-e sem ansiedade (Dor #10)
- Conciliar pagamento ao OFX/extrato em < 5 min
- Cobrar inadimplente sem ofender bom pagador (régua escalonada)
- Saber quanto vai entrar mês que vem (fluxo projetado)
- Não pagar boleto em dia errado (contas a pagar — V2)

**Frustrations:**
- "NFS-e municipal de SP vs RJ vs BH — cada um diferente"
- "Banco mudou layout do OFX outra vez"
- Tenant fala 'pix' e Receita vê CNPJ errado

**Permissões:** Financeiro — NFS-e + cobrança + comissões + relatórios financeiros + caixa do tenant.

---

## P-FIN-02 — Dono (vê DRE/fluxo de caixa)

Persona transversal P1 do `docs/comum/personas.md`. Toca financeiro ao **ler o painel-do-dono** + decidir reajuste/aceleração/recorte.

Goals (financeiros):
- Ver no painel: receita do mês, inadimplência > 30 dias, contas a pagar próximas, comissão devida.
- Decidir se compra equipamento novo ou paga adiantamento técnico.

**Permissões:** Dono — tudo, inclusive sensível.

---

## P-FIN-03 — Vendedor / técnico (vê comissão própria)

Toca financeiro pela aba **"Minha comissão"** no app:
- Previsão da comissão do mês (pipeline + recebido)
- Demonstrativo individual (JTBD-072)
- Reconstruir histórico se contestar (JTBD-078)

Detalhes em `docs/dominios/comercial/personas.md` P-COM-02 e `docs/dominios/operacao/personas.md` P-OP-01.

**Permissões:** Próprio demonstrativo + contestação.

---

## P-FIN-04 — Técnico de campo (caixa do técnico)

Toca financeiro pelo app mobile:
- Solicitar adiantamento (JTBD-060)
- Lançar despesa com foto do recibo (JTBD-061)
- Prestar contas em 5 min (JTBD-062)
- Pedir reembolso de km (JTBD-064)

Detalhes em `docs/dominios/operacao/personas.md` P-OP-01.

---

## P-FIN-05 — Contador externo (V2)

**Quem é:** Profissional externo (não-funcionário do tenant) que cuida de impostos + apuração mensal.

**Goals:**
- Receber export SPED em formato padrão (V2)
- Ver lista de NFS-e emitidas + canceladas + corrigidas no período
- Apurar imposto mensal sem retrabalho

**Frustrations (do mundo atual):**
- "Tenant manda PDFs soltos — eu monto a planilha à mão"

**Permissões:** Auditor read-only externo — acesso temporário com audit reforçado (V2).

---

## P-FIN-06 — Auditor fiscal (CONFAZ / Receita / municipal) — V2+

**Quem é:** Auditor externo que fiscaliza o tenant. Aferê fornece evidência via export estruturado.

**Permissões:** Acesso indireto via tenant; nunca acesso direto.

---

## Anti-personas

- **Sub-fornecedor de Aferê** que pede acesso direto ao painel financeiro — não permitido
- **Tenant que quer regime fiscal exótico não suportado** (Lucro Real complexo, ZFM com SUFRAMA particular) — não-MVP

---

## Referências

- `docs/discovery/personas-detalhadas.md` (Persona 4 financeiro)
- `docs/discovery/jobs-to-be-done.md` (BIG-04, BIG-08, BIG-09)
- ADR-0008 (fiscal)
- `docs/conformidade/comum/fiscal.md`
