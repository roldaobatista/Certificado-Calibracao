# Discovery — Riscos

> **Artefato Rodada 0** (agente + Roldão). Inventário do que pode dar errado. Categorizado por tipo + probabilidade × impacto.

---

## Categorias de risco

- **Regulatório:** ANPD/LGPD, INMETRO/CGCRE, Receita Federal, Bacen, ANS, etc.
- **Técnico:** stack inviável, integração impossível, performance, segurança
- **Mercado:** TAM pequeno, concorrência forte, demanda baixa
- **Time / operacional:** 1 pessoa + IA = bottleneck, agente vira inviável, burnout do Roldão
- **Financeiro:** investimento insuficiente, custos crescendo desproporcionalmente
- **Cliente:** "founder is customer" → produto não generaliza, primeiro cliente externo recusa
- **Jurídico:** responsabilidade por dado vazado, IA emitindo certificado regulado

---

## Matriz Probabilidade × Impacto

| Risco | Categoria | P (1–5) | I (1–5) | Score (P×I) | Mitigação | Owner |
|---|---|---|---|---|---|---|
| Customização disfarçada (founder is customer) | Cliente | 4 | 5 | **20** | Discovery rigorosa com 5–10 OUTRAS empresas | Roldão |
| Família 5 (3 auditores) virar vaporware | Operacional | 4 | 5 | **20** | Materializar prompts + triggers + veto na Rodada 4 | Agente |
| Multi-tenant vazamento entre clientes | Técnico/Regulatório | 3 | 5 | **15** | INV-TENANT-001 + RLS + hook + drill | Auditor Segurança |
| TAM ridículo (poucos prospects ICP) | Mercado | 3 | 5 | **15** | Validação ativa antes de comprometer | Roldão |
| ERP de N módulos com 1 pessoa = anos sem MVP | Operacional | 5 | 4 | **20** | Faseamento por módulo + MVP-1 enxuto | Roldão |
| NFS-e em município com padrão próprio | Regulatório/Técnico | 4 | 4 | **16** | Matriz município × padrão + Focus/NFE.io | Auditor Conformidade |
| Conflito tríplice retenção (Receita × ISO × LGPD) | Regulatório | 4 | 5 | **20** | `retencao-matriz.md` + base legal explícita | Auditor Conformidade |
| Prompt injection via MCP GitHub | Técnico/Segurança | 3 | 4 | **12** | `mcp-policy.md` + `agente-input-nao-confiavel.md` | Auditor Segurança |
| Hostinger SPOF (provedor inteiro fora) | Operacional | 2 | 5 | **10** | `dr-plan.md` 3 cenários + IaC pra provedor B | Auditor Operação |
| Token cost explosion (>R$ 50/dia) | Financeiro | 3 | 3 | **9** | Orçamento de contexto + alerta no painel | Roldão |
| Roldão burnout (dono não-técnico sozinho) | Operacional/Humano | 3 | 5 | **15** | Limites de autonomia + status semanal forçando foco | Roldão |
| Stack escolhida se mostra inviável após MVP-1 | Técnico | 2 | 4 | **8** | Spikes técnicos em discovery + ADR-0001 conservadora | Auditor Arquitetura |
| Concorrente (Bling/Tiny) lança features ISO 17025 | Mercado | 2 | 4 | **8** | Foco em diferencial + nicho fiel | Roldão |
| LGPD: incidente de vazamento → multa ANPD | Regulatório/Financeiro | 2 | 5 | **10** | `seguranca-dados.md` + 72h playbook + DPO | Auditor Conformidade |
| Signatário técnico não-disponível (RBC NIT-DICLA-021) | Regulatório | 3 | 5 | **15** | Identificar signatário ANTES de emitir 1º certificado | Roldão |

---

## Top 5 riscos prioritários (≥15)

1. **Customização disfarçada** — Discovery rigorosa OBRIGATÓRIA
2. **Família 5 vaporware** — materializar na Rodada 4
3. **ERP N módulos com 1 pessoa = anos** — faseamento essencial
4. **Conflito tríplice retenção** — `retencao-matriz.md` urgente
5. **Multi-tenant vazamento** — INV-TENANT-* + hooks

---

## Riscos "cisnes negros" (P baixa, I catastrófico)

- Anthropic descontinua API (todo agente para)
- Hostinger BR sai do ar permanentemente
- ANPD multa milionária em SaaS multi-tenant similar (precedente)
- INMETRO mudar política sobre software de calibração com IA

**Mitigação:** observar; sem ação ativa AGORA mas plano de contingência mental.

---

## Como esta lista evolui

- Risco novo descoberto → adicionar imediatamente.
- Mitigação implementada → marcar ✅ + reduzir score.
- Risco materializou → mover pra postmortem + atualizar invariante.
- Revisão obrigatória a cada milestone (síntese, MVP-1, 1º deploy, etc.).
