---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: proposta
diataxis: explanation
audiencia: agente
relacionados:
  - docs/adr/0008-fiscal-pluggable.md
  - docs/dominios/financeiro/modulos/contabilidade-export/prd.md
  - docs/dominios/financeiro/modulos/fiscal/prd.md
---

# ADR-0053 — Export SPED contábil + layouts contadores externos (Sage/Domínio/Alterdata)

> **Status:** proposta. **PRÉ-REQUISITO Wave A** — contador externo bloqueia 1º tenant pago se não houver export. Resolve achado **G-INT-3**.
> **Decisor:** Roldão + `consultor-rbc-iso17025` (auditor fiscal externo).
> **Bloqueia:** primeiro tenant externo pago (qualquer empresa com contabilidade terceirizada — 90% do mercado PME BR).

---

## Glossário

| Termo | Tradução |
|---|---|
| **SPED** | "Caixa-preta digital" que a Receita Federal exige todo mês com toda movimentação contábil. |
| **ECF** | Escrituração Contábil Fiscal (ano-base). |
| **EFD Contribuições** | PIS/COFINS mensal. |
| **Sage/Domínio/Alterdata** | Softwares contábeis que TODO contador BR usa. Exportam layout próprio. |

---

## Contexto

Cliente paga R$ 89-1500/mês no Aferê, mas o contador dele cobra R$ 800-3000 pra "digitar tudo de novo" no Sage/Domínio porque o Aferê não exporta no layout do contador. Esse atrito mata venda no PME BR — contador é decisor técnico oculto. SPED contábil não basta (é Receita Federal); contador precisa do **layout próprio do software dele** (Sage/Domínio/Alterdata/Contmatic).

## Decisão

Criar módulo `financeiro/contabilidade-export` (PRD novo, esqueleto Wave A) com 4 layouts:

| Layout | Obrigatório / Opcional | Frequência |
|---|---|---|
| **SPED ECF** | Obrigatório (Receita) | Anual |
| **SPED EFD Contribuições** | Obrigatório (Receita) | Mensal |
| **Sage / Domínio / Alterdata / Contmatic** | Opcional (contador) | Configurável |
| **CSV genérico (debit/credit/conta/historico)** | Opcional (contador artesanal) | Mensal |

### INV-SPED-001

**Toda fatura SaaS paga + NFS-e emitida + lançamento financeiro alimenta plano de contas mapeado (`PlanoContasMapeamento` por tenant); export SPED não gera linha sem conta contábil mapeada.** Veredito: ALTO. Hook bloqueia release que adicione lançamento sem mapeamento.

### Modelo simplificado

```
PlanoContasMapeamento (por tenant)
├── conta_origem_afere: str  # ex: "receita_assinatura_saas"
├── conta_destino_contador: str  # ex: "3.1.1.01.001"
├── historico_padrao: str
```

Export é **assíncrono** (job procrastinate); resultado fica em B2 WORM por 5 anos (Receita).

## Alternativas rejeitadas

1. **Não exportar; deixar contador digitar** — bloqueia venda PME (90% mercado).
2. **Integração API direta com Sage/Domínio** — Sage cobra licença API (R$ 5k/mês); Domínio não tem API pública.
3. **Só CSV genérico** — contador BR não aceita; quer layout do software dele.

## Consequências

**Positivas:** desbloqueia venda PME; contador vira aliado em vez de bloqueador.
**Negativas:** manter 4 layouts é débito crônico (cada um tem versionamento próprio); SPED Receita muda regras anualmente.

## Referências

- Instrução Normativa RFB 2.004/2021 (SPED ECF)
- IN RFB 1.252/2012 (EFD Contribuições)
- Layout Domínio Sistemas v9.8+ (público, documentado)
